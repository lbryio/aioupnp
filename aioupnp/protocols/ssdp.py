import asyncio
import binascii
import logging
import re

from aioupnp.constants import SSDP_IP_ADDRESS, SSDP_PORT
from aioupnp.fault import UPnPError
from aioupnp.protocols.m_search_patterns import packet_generator
from aioupnp.protocols.multicast import MulticastProtocol
from aioupnp.serialization.ssdp import SSDPDatagram

ADDRESS_REGEX = re.compile(
    r'^http:\/\/(\d+\.\d+\.\d+\.\d+)\:(\d*)(\/[\w|\/|\:|\-|\.]*)$'
)  # TODO: refactor

log = logging.getLogger(__name__)


class SSDPProtocol(MulticastProtocol):
    def __init__(self, multicast_address, lan_address, ignored, unicast):
        super().__init__(multicast_address, lan_address)
        self._unicast = unicast
        self._ignored = ignored or set()  # ignored locations
        self._pending_searches = []
        self.notifications = []

    def disconnect(self):
        if self.transport:
            self.transport.close()
        while self._pending_searches:
            pending = self._pending_searches.pop()[2]
            if not pending.cancelled() and not pending.done():
                pending.cancel()

    def _callback_m_search_ok(self, address, packet):
        if packet.location in self._ignored:
            return
        tmp = []
        set_futures = []
        while self._pending_searches:
            t: tuple = self._pending_searches.pop()
            a, s = t[0], t[1]
            if (address == a) and (s in [packet.st, "upnp:rootdevice"]):
                f = t[2]
                if f not in set_futures:
                    set_futures.append(f)
                    if not f.done():
                        f.set_result(packet)
            elif t[2] not in set_futures:
                tmp.append(t)
        while tmp:
            self._pending_searches.append(tmp.pop())

    def send_many_m_searches(self, address, packets):
        dest = address if self._unicast else SSDP_IP_ADDRESS
        for packet in packets:
            log.debug("Send m search to %s: %s.", dest, packet.st)
            self.transport.sendto(packet.encode(), (dest, SSDP_PORT))

    async def m_search(self, address, datagrams):
        fut = asyncio.Future()
        packets = []
        for datagram in datagrams:
            packet = SSDPDatagram(SSDPDatagram._M_SEARCH, **datagram)
            assert packet.st is not None
            self._pending_searches.append((address, packet.st, fut))
            packets.append(packet)
        self.send_many_m_searches(address, packets),
        return await fut

    def datagram_received(self, data, address):
        if address[0] == self.bind_address:
            return
        try:
            packet = SSDPDatagram.decode(data)
            log.debug("Decoded packet from %s:%i: %s.", address[0], address[1], packet)
        except UPnPError as err:
            log.error("Failed to decode SSDP packet from %s:%i (%s): %s.", address[0], address[1], err,
                      binascii.hexlify(data))
            return

        if packet._packet_type == packet._OK:
            self._callback_m_search_ok(address[0], packet)
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


async def listen_ssdp(lan_address, gateway_address, loop=None, ignored=None, unicast=False):
    loop = loop or asyncio.get_event_loop_policy().get_event_loop()
    protocol = None
    try:
        sock = SSDPProtocol.create_multicast_socket(lan_address)
        listen_result = await loop.create_datagram_endpoint(
            lambda: SSDPProtocol(SSDP_IP_ADDRESS, lan_address, ignored, unicast), sock=sock
        )
        transport = listen_result[0]
        protocol = listen_result[1].connection_made(transport)
        protocol.join_group(protocol.multicast_address, protocol.bind_address)
        protocol.set_ttl(1)
    except asyncio.TimeoutError as err:
        print(err)
        raise UPnPError(err)
    except Exception as err:
        protocol.disconnect()
        raise UPnPError(err)
    return transport, protocol, gateway_address, lan_address


async def m_search(lan_address, gateway_address, datagram_args, timeout=1, loop=None, ignored=None, unicast=False):
    transport, protocol, gateway_address, lan_address = await listen_ssdp(
        lan_address, gateway_address, loop, ignored, unicast
    )
    try:
        return await asyncio.wait_for(
            protocol.m_search(address=gateway_address, timeout=timeout, datagrams=[datagram_args]), timeout
        )
    except (asyncio.TimeoutError, asyncio.CancelledError):
        raise UPnPError("M-SEARCH for {}:{} timed out.".format(gateway_address, SSDP_PORT))
    finally:
        protocol.disconnect()


async def _fuzzy_m_search(lan_address, gateway_address, timeout=30, loop=None, ignored=None, unicast=False):
    transport, protocol, gateway_address, lan_address = await listen_ssdp(
        lan_address, gateway_address, loop, ignored, unicast
    )
    packet_args = list(packet_generator())
    batch_size = 2
    batch_timeout = float(timeout) / float(len(packet_args))
    while packet_args:
        args = packet_args[:batch_size]
        packet_args = packet_args[batch_size:]
        log.debug("Sending batch of %i M-SEARCH attempts.", batch_size)
        try:
            await asyncio.wait_for(protocol.m_search(gateway_address, batch_timeout, args), batch_timeout)
            protocol.disconnect()
            return args
        except asyncio.TimeoutError:
            continue
    protocol.disconnect()
    raise UPnPError("M-SEARCH for {}:{} timed out.".format(gateway_address, SSDP_PORT))


async def fuzzy_m_search(lan_address, gateway_address, timeout=30, loop=None, ignored=None, unicast=False):
    # we don't know which packet the gateway replies to, so send small batches at a time
    args_to_try = await _fuzzy_m_search(lan_address, gateway_address, timeout, loop, ignored, unicast)
    # check the args in the batch that got a reply one at a time to see which one worked
    for args in args_to_try:
        try:
            packet = await m_search(lan_address, gateway_address, args, 3, loop=loop, ignored=ignored, unicast=unicast)
            return args, packet
        except UPnPError:
            continue
    raise UPnPError("Failed to discover gateway.")
