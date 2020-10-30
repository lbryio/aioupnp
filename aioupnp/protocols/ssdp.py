import re
import binascii
import asyncio
import logging
import typing
import socket
from typing import List, Set, Dict, Tuple, Optional
from asyncio.transports import DatagramTransport
from aioupnp.fault import UPnPError
from aioupnp.serialization.ssdp import SSDPDatagram
from aioupnp.constants import SSDP_IP_ADDRESS, SSDP_PORT
from aioupnp.protocols.multicast import MulticastProtocol
from aioupnp.protocols.m_search_patterns import packet_generator

ADDRESS_REGEX = re.compile("^http:\/\/(\d+\.\d+\.\d+\.\d+)\:(\d*)(\/[\w|\/|\:|\-|\.]*)$")

log = logging.getLogger(__name__)


class PendingSearch(typing.NamedTuple):
    address: str
    st: str
    fut: 'asyncio.Future[SSDPDatagram]'


class SSDPProtocol(MulticastProtocol):
    def __init__(self, multicast_address: str, lan_address: str,
                 loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        super().__init__(multicast_address, lan_address)
        self.loop: asyncio.AbstractEventLoop = loop or asyncio.get_event_loop()
        self.transport: Optional[DatagramTransport] = None
        self._pending_searches: List[PendingSearch] = []
        self.notifications: List[SSDPDatagram] = []
        self.connected = asyncio.Event(loop=self.loop)
        self.devices: 'asyncio.Queue[SSDPDatagram]' = asyncio.Queue(loop=self.loop)

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:  # type: ignore
        super().connection_made(transport)
        self.connected.set()
        return None

    def disconnect(self) -> None:
        if self.transport:
            self.leave_group(self.multicast_address, self.bind_address)
            self.transport.close()
        self.connected.clear()
        while self._pending_searches:
            pending = self._pending_searches.pop()[2]
            if not pending.cancelled() and not pending.done():
                pending.cancel()
        return None

    def _callback_m_search_ok(self, address: str, packet: SSDPDatagram) -> None:
        futures: Set['asyncio.Future[SSDPDatagram]'] = set()
        replied: List[PendingSearch] = []

        for pending in self._pending_searches:
            # if pending.address == address and pending.st in (packet.st, "upnp:rootdevice"):
            if pending.address == address and pending.st == packet.st:
                replied.append(pending)
                if pending.fut not in futures:
                    futures.add(pending.fut)
        if replied:
            self.devices.put_nowait(packet)

        while replied:
            self._pending_searches.remove(replied.pop())

        while futures:
            fut = futures.pop()
            if not fut.done():
                fut.set_result(packet)

    def _send_m_search(self, address: str, packet: SSDPDatagram, fut: 'asyncio.Future[SSDPDatagram]') -> None:
        if not self.transport:
            if not fut.done():
                fut.set_exception(UPnPError("SSDP transport not connected"))
            return
        assert packet.st is not None
        self._pending_searches.append(
            PendingSearch(address, packet.st, fut)
        )
        self.transport.sendto(packet.encode().encode(), (SSDP_IP_ADDRESS, SSDP_PORT))

        # also send unicast
        log.debug("send m search to %s: %s", address, packet.st)
        self.transport.sendto(packet.encode().encode(), (address, SSDP_PORT))

    def send_m_searches(self, address: str,
                        datagrams: List[Dict[str, typing.Union[str, int]]]) -> 'asyncio.Future[SSDPDatagram]':
        fut: 'asyncio.Future[SSDPDatagram]' = self.loop.create_future()
        for datagram in datagrams:
            packet = SSDPDatagram("M-SEARCH", datagram)
            assert packet.st is not None
            self._send_m_search(address, packet, fut)
        return fut

    async def m_search(self, address: str, timeout: float,
                       datagrams: List[Dict[str, typing.Union[str, int]]]) -> SSDPDatagram:
        fut = self.send_m_searches(address, datagrams)
        return await asyncio.wait_for(fut, timeout, loop=self.loop)

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:  # type: ignore
        if addr[0] == self.bind_address:
            return None
        try:
            packet = SSDPDatagram.decode(data)
            log.debug("decoded packet from %s:%i: %s", addr[0], addr[1], packet)
        except UPnPError as err:
            log.warning("failed to decode SSDP packet from %s:%i (%s): %s", addr[0], addr[1], err,
                        binascii.hexlify(data))
            return None
        if packet._packet_type == packet._OK:
            self._callback_m_search_ok(addr[0], packet)
            return None
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
                      loop: Optional[asyncio.AbstractEventLoop] = None) -> Tuple[SSDPProtocol, str, str]:
    loop = loop or asyncio.get_event_loop()
    try:
        sock: socket.socket = SSDPProtocol.create_multicast_socket(lan_address)
        listen_result: Tuple[asyncio.BaseTransport, asyncio.BaseProtocol] = await loop.create_datagram_endpoint(
            lambda: SSDPProtocol(SSDP_IP_ADDRESS, lan_address), sock=sock
        )
        protocol = listen_result[1]
        assert isinstance(protocol, SSDPProtocol)
    except Exception as err:
        raise UPnPError(err)
    else:
        protocol.join_group(protocol.multicast_address, protocol.bind_address)
        protocol.set_ttl(1)
    return protocol, gateway_address, lan_address


async def m_search(lan_address: str, gateway_address: str, datagram_args: Dict[str, typing.Union[int, str]],
                   timeout: int = 1,
                   loop: Optional[asyncio.AbstractEventLoop] = None) -> SSDPDatagram:
    protocol, gateway_address, lan_address = await listen_ssdp(
        lan_address, gateway_address, loop
    )
    try:
        return await protocol.m_search(address=gateway_address, timeout=timeout, datagrams=[datagram_args])
    except asyncio.TimeoutError:
        raise UPnPError("M-SEARCH for {}:{} timed out".format(gateway_address, SSDP_PORT))
    finally:
        protocol.disconnect()


async def multi_m_search(lan_address: str, gateway_address: str, timeout: int = 3,
                         loop: Optional[asyncio.AbstractEventLoop] = None) -> SSDPProtocol:
    loop = loop or asyncio.get_event_loop()
    protocol, gateway_address, lan_address = await listen_ssdp(
        lan_address, gateway_address, loop
    )
    fut = protocol.send_m_searches(
        address=gateway_address, datagrams=list(packet_generator())
    )
    loop.call_later(timeout, lambda: None if not fut or fut.done() else fut.cancel())
    return protocol
