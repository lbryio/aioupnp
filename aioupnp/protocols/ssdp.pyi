from asyncio import Future, Handle, AbstractEventLoop, DatagramTransport
from collections import OrderedDict

from typing import runtime, Union, Pattern, Set, Optional, AnyStr, Any, Tuple, NoReturn, List, SupportsFloat, SupportsBytes, SupportsInt, Generic, Text

from aioupnp.serialization.ssdp import SSDPDatagram
from .multicast import MulticastProtocol

ADDRESS_REGEX: Union[Pattern, AnyStr]

@runtime
class SSDPProtocol(MulticastProtocol):
    def __init__(self, multicast_address: str, lan_address: str, ignored: Set[str] = None, unicast: bool = False) -> NoReturn:
        super().__init__(multicast_address, lan_address)
        self._unicast: bool = unicast
        self._ignored: Set[str] = ignored or set()  # ignored locations
        self._pending_searches: List[Tuple[str, str, Future, Handle]] = []
        self.notifications: Any[List[None], List[str]] = []

    def disconnect(self) -> NoReturn:
        ...

    def _callback_m_search_ok(self, address: str, packet: SSDPDatagram) -> NoReturn:
        ...

    def send_many_m_searches(self, address: str, packets: List[SSDPDatagram]) -> NoReturn:
        ...

    async def m_search(self, address: str, timeout: Any[float, int], datagrams: List[OrderedDict[bytes]]) -> SSDPDatagram:
        fut: Future = Future()
        packets: List[SSDPDatagram] = []
        ...

    def datagram_received(self, data: Union[Text, bytes], addr: str) -> NoReturn:
        ...

async def listen_ssdp(lan_address: str, gateway_address: str, loop: Any[AbstractEventLoop, None] = None, ignored: Any[Optional[Set[str]], None] = None, unicast: bool = False) -> Tuple[DatagramTransport, SSDPProtocol, str, str]:
    ...

async def m_search(lan_address: str, gateway_address: str, datagram_args: OrderedDict, timeout: Union[float, int], loop: Union[AbstractEventLoop, None], ignored: Set, unicast: bool = False) -> SSDPDatagram:
    ...

async def _fuzzy_m_search(lan_address: str, gateway_address: str, timeout: Any[float, int] = 30, loop: Any[Optional[AbstractEventLoop], None] = None, ignored: Any[Optional[Set[bytes]], None] = None, unicast: bool = False) -> List[OrderedDict]:
    ...

async def fuzzy_m_search(lan_address: str, gateway_address: str, timeout: Any[float, int] = 30, loop: Any[Optional[AbstractEventLoop], None] = None, ignored: Any[Optional[Set[bytes]], None] = None, unicast: bool = False) -> Tuple[OrderedDict, SSDPDatagram]:
    ...
