import re
import socket
import binascii
import asyncio
import logging
from collections import OrderedDict
from typing import Dict, List, Tuple
from asyncio.futures import Future
from asyncio.transports import DatagramTransport
from aioupnp.fault import UPnPError
from aioupnp.serialization.ssdp import SSDPDatagram
from aioupnp.constants import UPNP_ORG_IGD, WIFI_ALLIANCE_ORG_IGD
from aioupnp.constants import SSDP_IP_ADDRESS, SSDP_PORT, SSDP_DISCOVER, SSDP_ROOT_DEVICE, SSDP_ALL
from aioupnp.protocols.multicast import MulticastProtocol
from aioupnp.protocols.m_search_patterns import M_SEARCH_ARG_PATTERNS

ADDRESS_REGEX = re.compile("^http:\/\/(\d+\.\d+\.\d+\.\d+)\:(\d*)(\/[\w|\/|\:|\-|\.]*)$")

log = logging.getLogger(__name__)


class SSDPProtocol(MulticastProtocol):
    def __init__(self, multicast_address: str, lan_address: str) -> None:
        super().__init__(multicast_address, lan_address)
        self.lan_address = lan_address
        self.discover_callbacks: Dict = {}
        self.notifications: List = []
        self.replies: List = []

    def m_search(self, address: str, timeout: int, datagram_args: OrderedDict) -> Future:
        packet = SSDPDatagram(SSDPDatagram._M_SEARCH, datagram_args)
        f: Future = Future()
        futs = self.discover_callbacks.get((address, packet.st), [])
        futs.append(f)
        self.discover_callbacks[(address, packet.st)] = futs
        log.debug("send m search to %s: %s", address, packet)
        self.transport.sendto(packet.encode().encode(), (address, SSDP_PORT))

        r: Future = asyncio.ensure_future(asyncio.wait_for(f, timeout))
        return r

    def datagram_received(self, data, addr) -> None:
        if addr[0] == self.lan_address:
            return
        try:
            packet = SSDPDatagram.decode(data)
            log.debug("decoded packet from %s:%i: %s", addr[0], addr[1], packet)
        except UPnPError as err:
            log.error("failed to decode SSDP packet from %s:%i (%s): %s", addr[0], addr[1], err,
                      binascii.hexlify(data))
            return

        if packet._packet_type == packet._OK:
            if (addr[0], packet.st) in self.discover_callbacks:
                log.debug("%s:%i replied to our m-search", addr[0], addr[1])
                if packet.st not in map(lambda p: p['st'], self.replies):
                    self.replies.append(packet)
                for ok_fut in self.discover_callbacks[(addr[0], packet.st)]:
                    ok_fut.set_result(packet)
                del self.discover_callbacks[(addr[0], packet.st)]
                return

        # elif packet._packet_type == packet._NOTIFY:
        #     log.debug("%s:%i sent us a notification: %s", packet)
        #     if packet.nt == SSDP_ROOT_DEVICE:
        #         address, port, path = ADDRESS_REGEX.findall(packet.location)[0]
        #         key = None
        #         for (addr, service) in self.discover_callbacks:
        #             if addr == address:
        #                 key = (addr, service)
        #                 break
        #         if key:
        #             log.debug("got a notification with the requested m-search info")
        #             notify_fut: Future = self.discover_callbacks.pop(key)
        #             notify_fut.set_result(SSDPDatagram(
        #                 SSDPDatagram._OK, cache_control='', location=packet.location, server=packet.server,
        #                 st=UPNP_ORG_IGD, usn=packet.usn
        #             ))
        #         self.notifications.append(packet.as_dict())
        #         return


async def listen_ssdp(lan_address: str, gateway_address: str,
                      ssdp_socket: socket.socket = None) -> Tuple[DatagramTransport, SSDPProtocol,
                                                                  str, str]:
    loop = asyncio.get_running_loop()
    try:
        sock = ssdp_socket or SSDPProtocol.create_multicast_socket(lan_address)
        listen_result: Tuple = await loop.create_datagram_endpoint(
            lambda: SSDPProtocol(SSDP_IP_ADDRESS, lan_address), sock=sock
        )
        transport: DatagramTransport = listen_result[0]
        protocol: SSDPProtocol = listen_result[1]
    except Exception as err:
        raise UPnPError(err)
    try:
        protocol.join_group(protocol.multicast_address, protocol.bind_address)
        protocol.set_ttl(1)
    except Exception as err:
        transport.close()
        raise UPnPError(err)

    return transport, protocol, gateway_address, lan_address


async def m_search(lan_address: str, gateway_address: str, datagram_args: OrderedDict, timeout: int = 1,
                   ssdp_socket: socket.socket = None) -> SSDPDatagram:
    transport, protocol, gateway_address, lan_address = await listen_ssdp(
        lan_address, gateway_address, ssdp_socket
    )
    try:
        return await protocol.m_search(address=gateway_address, timeout=timeout, datagram_args=datagram_args)
    except asyncio.TimeoutError:
        raise UPnPError("M-SEARCH for {}:{} timed out".format(gateway_address, SSDP_PORT))
    finally:
        transport.close()


async def fuzzy_m_search(lan_address: str, gateway_address: str, timeout: int = 1,
                            ssdp_socket: socket.socket = None) -> SSDPDatagram:
    transport, protocol, gateway_address, lan_address = await listen_ssdp(
        lan_address, gateway_address, ssdp_socket
    )
    datagram_kwargs: list = []
    services = [UPNP_ORG_IGD, SSDP_ALL, WIFI_ALLIANCE_ORG_IGD]
    mans = [SSDP_DISCOVER, SSDP_ROOT_DEVICE]
    mx = 1

    for service in services:
        for man in mans:
            for arg_pattern in M_SEARCH_ARG_PATTERNS:
                dgram_kwargs: OrderedDict = OrderedDict()
                for k, l in arg_pattern:
                    if k.lower() == 'host':
                        dgram_kwargs[k] = l(SSDP_IP_ADDRESS)
                    elif k.lower() == 'st':
                        dgram_kwargs[k] = l(service)
                    elif k.lower() == 'man':
                        dgram_kwargs[k] = l(man)
                    elif k.lower() == 'mx':
                        dgram_kwargs[k] = l(mx)
                datagram_kwargs.append(dgram_kwargs)

    for i, args in enumerate(datagram_kwargs):
        try:
            result = await protocol.m_search(address=gateway_address, timeout=timeout, datagram_args=args)
            transport.close()
            return result
        except asyncio.TimeoutError:
            pass
        except Exception as err:
            log.error(err)
    transport.close()
    raise UPnPError("M-SEARCH for {}:{} timed out".format(gateway_address, SSDP_PORT))
