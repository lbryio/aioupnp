import re
import binascii
import asyncio
import logging
import typing
import socket
from asyncio.transports import DatagramTransport
from aioupnp.fault import UPnPError
from aioupnp.serialization.ssdp import SSDPDatagram
from aioupnp.constants import SSDP_IP_ADDRESS, SSDP_PORT
from aioupnp.protocols.multicast import MulticastProtocol
from aioupnp.protocols.m_search_patterns import packet_generator

ADDRESS_REGEX = re.compile("^http:\/\/(\d+\.\d+\.\d+\.\d+)\:(\d*)(\/[\w|\/|\:|\-|\.]*)$")

log = logging.getLogger(__name__)


class SSDPProtocol(MulticastProtocol):
    def __init__(self, multicast_address: str, lan_address: str, ignored: typing.Optional[typing.Set[str]] = None,
                 unicast: bool = False, loop: typing.Optional[asyncio.AbstractEventLoop] = None) -> None:
        super().__init__(multicast_address, lan_address)
        self.loop: asyncio.AbstractEventLoop = loop or asyncio.get_event_loop()
        self.transport: typing.Optional[DatagramTransport] = None
        self._unicast = unicast
        self._ignored: typing.Set[str] = ignored or set()  # ignored locations
        self._pending_searches: typing.List[typing.Tuple[str, str, 'asyncio.Future[SSDPDatagram]', asyncio.Handle]] = []
        self.notifications: typing.List[SSDPDatagram] = []
        self.connected = asyncio.Event(loop=self.loop)

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
        if packet.location not in self._ignored:
            # TODO: fix this
            tmp: typing.List[typing.Tuple[str, str, 'asyncio.Future[SSDPDatagram]', asyncio.Handle]] = []
            set_futures: typing.List['asyncio.Future[SSDPDatagram]'] = []
            while len(self._pending_searches):
                t = self._pending_searches.pop()
                if (address == t[0]) and (t[1] in [packet.st, "upnp:rootdevice"]):
                    f = t[2]
                    if f not in set_futures:
                        set_futures.append(f)
                        if not f.done():
                            f.set_result(packet)
                elif t[2] not in set_futures:
                    tmp.append(t)
            while tmp:
                self._pending_searches.append(tmp.pop())
        return None

    def _send_m_search(self, address: str, packet: SSDPDatagram, fut: 'asyncio.Future[SSDPDatagram]') -> None:
        dest = address if self._unicast else SSDP_IP_ADDRESS
        if not self.transport:
            if not fut.done():
                fut.set_exception(UPnPError("SSDP transport not connected"))
            return None
        log.debug("send m search to %s: %s", dest, packet.st)
        self.transport.sendto(packet.encode().encode(), (dest, SSDP_PORT))
        return None

    async def m_search(self, address: str, timeout: float,
                       datagrams: typing.List[typing.Dict[str, typing.Union[str, int]]]) -> SSDPDatagram:
        fut: 'asyncio.Future[SSDPDatagram]' = asyncio.Future(loop=self.loop)
        for datagram in datagrams:
            packet = SSDPDatagram("M-SEARCH", datagram)
            assert packet.st is not None
            self._pending_searches.append(
                (address, packet.st, fut, self.loop.call_soon(self._send_m_search, address, packet, fut))
            )
        return await asyncio.wait_for(fut, timeout)

    def datagram_received(self, data: bytes, addr: typing.Tuple[str, int]) -> None:  # type: ignore
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


async def listen_ssdp(lan_address: str, gateway_address: str, loop: typing.Optional[asyncio.AbstractEventLoop] = None,
                      ignored: typing.Optional[typing.Set[str]] = None,
                      unicast: bool = False) -> typing.Tuple[SSDPProtocol, str, str]:
    loop = loop or asyncio.get_event_loop()
    try:
        sock: socket.socket = SSDPProtocol.create_multicast_socket(lan_address)
        listen_result: typing.Tuple[asyncio.BaseTransport, asyncio.BaseProtocol] = await loop.create_datagram_endpoint(
            lambda: SSDPProtocol(SSDP_IP_ADDRESS, lan_address, ignored, unicast), sock=sock
        )
        protocol = listen_result[1]
        assert isinstance(protocol, SSDPProtocol)
    except Exception as err:
        raise UPnPError(err)
    else:
        protocol.join_group(protocol.multicast_address, protocol.bind_address)
        protocol.set_ttl(1)
    return protocol, gateway_address, lan_address


async def m_search(lan_address: str, gateway_address: str, datagram_args: typing.Dict[str, typing.Union[int, str]],
                   timeout: int = 1, loop: typing.Optional[asyncio.AbstractEventLoop] = None,
                   ignored: typing.Set[str] = None, unicast: bool = False) -> SSDPDatagram:
    protocol, gateway_address, lan_address = await listen_ssdp(
        lan_address, gateway_address, loop, ignored, unicast
    )
    try:
        return await protocol.m_search(address=gateway_address, timeout=timeout, datagrams=[datagram_args])
    except (asyncio.TimeoutError, asyncio.CancelledError):
        raise UPnPError("M-SEARCH for {}:{} timed out".format(gateway_address, SSDP_PORT))
    finally:
        protocol.disconnect()


async def _fuzzy_m_search(lan_address: str, gateway_address: str, timeout: int = 30,
                          loop: typing.Optional[asyncio.AbstractEventLoop] = None,
                          ignored: typing.Set[str] = None,
                          unicast: bool = False) -> typing.List[typing.Dict[str, typing.Union[int, str]]]:
    protocol, gateway_address, lan_address = await listen_ssdp(
        lan_address, gateway_address, loop, ignored, unicast
    )
    await protocol.connected.wait()
    packet_args = list(packet_generator())
    batch_size = 2
    batch_timeout = float(timeout) / float(len(packet_args))
    while packet_args:
        args = packet_args[:batch_size]
        packet_args = packet_args[batch_size:]
        log.debug("sending batch of %i M-SEARCH attempts", batch_size)
        try:
            await protocol.m_search(gateway_address, batch_timeout, args)
        except asyncio.TimeoutError:
            continue
        else:
            protocol.disconnect()
            return args
    protocol.disconnect()
    raise UPnPError("M-SEARCH for {}:{} timed out".format(gateway_address, SSDP_PORT))


async def fuzzy_m_search(lan_address: str, gateway_address: str, timeout: int = 30,
                         loop: typing.Optional[asyncio.AbstractEventLoop] = None,
                         ignored: typing.Set[str] = None,
                         unicast: bool = False) -> typing.Tuple[typing.Dict[str,
                                                                            typing.Union[int, str]], SSDPDatagram]:
    # we don't know which packet the gateway replies to, so send small batches at a time
    args_to_try = await _fuzzy_m_search(lan_address, gateway_address, timeout, loop, ignored, unicast)
    # check the args in the batch that got a reply one at a time to see which one worked
    for args in args_to_try:
        try:
            packet = await m_search(lan_address, gateway_address, args, 3, loop=loop, ignored=ignored, unicast=unicast)
            return args, packet
        except UPnPError:
            continue
    raise UPnPError("failed to discover gateway")
