import asyncio
import typing
import collections
from . import multicast
from aioupnp.serialization.ssdp import SSDPDatagram

ADDRESS_REGEX = typing.Pattern[str]

@typing.runtime
class SSDPProtocol(multicast.MulticastProtocol):
    def __init__(self, multicast_address: str, lan_address: str, ignored: typing.Set[str] = None, unicast: typing.Optional[bool] = False) -> typing.NoReturn:
        super().__init__(multicast_address, lan_address)
        self._unicast: bool = unicast
        self._ignored: typing.Set[str] = ignored or set()  # ignored locations
        self._pending_searches: typing.List[typing.Tuple[str, str, asyncio.Future, asyncio.Handle]] = []
        self.notifications: typing.List = []

    def disconnect(self) -> typing.NoReturn:
        ...

    def _callback_m_search_ok(self, address: str, packet: SSDPDatagram) -> typing.NoReturn:
        ...

    def send_many_m_searches(self, address: str, packets: typing.List[SSDPDatagram]) -> typing.NoReturn:
        ...

    async def m_search(self, address: str, timeout: float, datagrams: typing.List[collections.OrderedDict]) -> SSDPDatagram:
        fut: asyncio.Future = asyncio.Future()
        packets: typing.List[SSDPDatagram] = []
        ...

    def datagram_received(self, data: bytes, addr: str) -> typing.NoReturn:
        ...

async def listen_ssdp(lan_address: str, gateway_address: str, loop: asyncio.AbstractEventLoop = None, ignored: typing.Set[str] = None, unicast: bool = False) -> typing.Tuple[asyncio.DatagramTransport, SSDPProtocol, str, str]:
    ...

async def m_search(lan_address: str, gateway_address: str, datagram_args: collections.OrderedDict, timeout: int, loop: asyncio.AbstractEventLoop, ignored: typing.Set[str], unicast: bool = False) -> SSDPDatagram:
    ...

async def _fuzzy_m_search(lan_address: str, gateway_address: str, timeout: int = 30, loop: asyncio.AbstractEventLoop = None, ignored: typing.Set[str] = None, unicast: bool = False) -> typing.List[collections.OrderedDict]:
    ...

async def fuzzy_m_search(lan_address: str, gateway_address: str, timeout: int = 30, loop: asyncio.AbstractEventLoop = None, ignored: typing.Set[str] = None, unicast: bool = False) -> typing.Tuple[collections.OrderedDict, SSDPDatagram]:
    ...
