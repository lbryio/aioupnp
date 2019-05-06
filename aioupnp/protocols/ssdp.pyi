from asyncio import Future, AbstractEventLoop, DatagramTransport

from typing import runtime, Union, Pattern, Set, Tuple, NoReturn, List, Dict, Optional, Mapping

from aioupnp.fault import UPnPError
from aioupnp.serialization.ssdp import SSDPDatagram
from .multicast import MulticastProtocol

ADDRESS_REGEX: Union[Pattern, str]

@runtime
class SSDPProtocol(MulticastProtocol):
    def __init__(self, multicast_address: str, lan_address: str, ignored: Optional[Set] = None, unicast: Optional[bool] = False) -> None:
        super().__init__(multicast_address, lan_address)
        self._unicast: bool = unicast
        self._ignored: Set = ignored or set()  # ignored locations
        self._pending_searches: List[Tuple[str, str, Future]] = []
        self.notifications: List = []

    def disconnect(self) -> NoReturn:
        ...

    def _callback_m_search_ok(self, address: str, packet: SSDPDatagram) -> NoReturn:
        ...

    def send_many_m_searches(self, address: str, packets: List[SSDPDatagram]) -> NoReturn:
        ...

    async def m_search(self, address: str, timeout: Union[float, int], datagrams: List) -> SSDPDatagram:
        fut: Future = Future()
        packets: List[SSDPDatagram] = []
        ...

async def listen_ssdp(lan_address: str, gateway_address: str, loop: Optional[AbstractEventLoop] = None, ignored: Optional[Set] = None, unicast: Optional[bool] = False) -> Tuple[DatagramTransport, SSDPProtocol, str, str]:
    ...

async def m_search(lan_address: str, gateway_address: str, datagram_args: Mapping, timeout: Union[float, int], loop: Optional[AbstractEventLoop] = None, ignored: Optional[Set] = None, unicast: Optional[bool] = False) -> SSDPDatagram:
    ...

async def _fuzzy_m_search(lan_address: str, gateway_address: str, timeout: Union[float, int] = 30, loop: Optional[AbstractEventLoop] = None, ignored: Optional[Set] = None, unicast: Optional[bool] = False) -> Union[List[Dict], UPnPError]:
    ...

async def fuzzy_m_search(lan_address: str, gateway_address: str, timeout: Union[float, int] = 30, loop: Optional[AbstractEventLoop] = None, ignored: Optional[Set] = None, unicast: Optional[bool] = False) -> Union[Tuple[Dict, SSDPDatagram], UPnPError]:
    ...
