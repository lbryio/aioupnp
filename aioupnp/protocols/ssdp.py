import re
import socket
import binascii
import asyncio
import logging
from typing import Dict, List, Tuple
from asyncio.futures import Future
from asyncio.transports import DatagramTransport
from aioupnp.fault import UPnPError
from aioupnp.serialization.ssdp import SSDPDatagram
from aioupnp.constants import UPNP_ORG_IGD, SSDP_IP_ADDRESS, SSDP_PORT, SSDP_DISCOVER, SSDP_ROOT_DEVICE
from aioupnp.protocols.multicast import MulticastProtocol

ADDRESS_REGEX = re.compile("^http:\/\/(\d+\.\d+\.\d+\.\d+)\:(\d*)(\/[\w|\/|\:|\-|\.]*)$")

log = logging.getLogger(__name__)


class SSDPProtocol(MulticastProtocol):
    def __init__(self, multicast_address: str, lan_address: str) -> None:
        super().__init__(multicast_address, lan_address)
        self.lan_address = lan_address
        self.discover_callbacks: Dict = {}
        self.notifications: List = []
        self.replies: List = []

    async def m_search(self, address, timeout: int = 1, service=UPNP_ORG_IGD) -> SSDPDatagram:
        if (address, service) in self.discover_callbacks:
            return self.discover_callbacks[(address, service)]
        packet = SSDPDatagram(
            SSDPDatagram._M_SEARCH, host="{}:{}".format(SSDP_IP_ADDRESS, SSDP_PORT), st=service, man=SSDP_DISCOVER,
            mx=1
        )
        self.transport.sendto(packet.encode().encode(), (address, SSDP_PORT))
        f: Future = Future()
        self.discover_callbacks[(address, service)] = f
        return await asyncio.wait_for(f, timeout)

    def datagram_received(self, data, addr) -> None:
        if addr[0] == self.lan_address:
            return
        try:
            packet = SSDPDatagram.decode(data)
            log.debug("decoded %s from %s:%i:\n%s", packet.get_friendly_name(), addr[0], addr[1], packet.encode())
        except UPnPError as err:
            log.error("failed to decode SSDP packet from %s:%i: %s\npacket: %s", addr[0], addr[1], err,
                      binascii.hexlify(data))
            return

        if packet._packet_type == packet._OK:
            log.debug("%s:%i sent us an OK", addr[0], addr[1])
            if (addr[0], packet.st) in self.discover_callbacks:
                if packet.st not in map(lambda p: p['st'], self.replies):
                    self.replies.append(packet)
                ok_fut: Future = self.discover_callbacks.pop((addr[0], packet.st))
                ok_fut.set_result(packet)
                return

        elif packet._packet_type == packet._NOTIFY:
            if packet.nt == SSDP_ROOT_DEVICE:
                address, port, path = ADDRESS_REGEX.findall(packet.location)[0]
                key = None
                for (addr, service) in self.discover_callbacks:
                    if addr == address:
                        key = (addr, service)
                        break
                if key:
                    log.debug("got a notification with the requested m-search info")
                    notify_fut: Future = self.discover_callbacks.pop(key)
                    notify_fut.set_result(SSDPDatagram(
                        SSDPDatagram._OK, cache_control='', location=packet.location, server=packet.server,
                        st=UPNP_ORG_IGD, usn=packet.usn
                    ))
                self.notifications.append(packet.as_dict())
                return


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
        protocol.set_ttl(1)
    except Exception:
        log.exception("failed to create multicast socket %s:%i", lan_address, SSDP_PORT)
        raise
    return transport, protocol, gateway_address, lan_address


async def m_search(lan_address: str, gateway_address: str, timeout: int = 1,
                   service: str = UPNP_ORG_IGD, ssdp_socket: socket.socket = None) -> SSDPDatagram:
    transport, protocol, gateway_address, lan_address = await listen_ssdp(
        lan_address, gateway_address, ssdp_socket
    )
    try:
        return await protocol.m_search(address=gateway_address, timeout=timeout, service=service)
    except asyncio.TimeoutError:
        raise UPnPError("M-SEARCH for {}:{} timed out".format(gateway_address, SSDP_PORT))
    finally:
        transport.close()
