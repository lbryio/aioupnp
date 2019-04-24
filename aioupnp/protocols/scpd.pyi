from asyncio import DatagramProtocol, Future, transports, protocols, DatagramTransport, AbstractEventLoop
from collections import OrderedDict

from typing import Pattern, AnyStr, Any, Mapping, Union, List, Tuple, runtime, Optional, NoReturn, \
                   SupportsBytes, Sized, SupportsInt, Generic, Awaitable, IO, BinaryIO, Text

HTTPD_CODE_REGEX: Union[Pattern, AnyStr, SupportsBytes]


def parse_headers(response: Union[AnyStr, SupportsBytes]) -> Tuple[OrderedDict, Union[Sized, SupportsInt], Union[AnyStr, SupportsBytes]]:
    ...


@runtime
class SCPDHTTPClientProtocol(DatagramProtocol):
    def __init__(self, message: str, finished: Future, soap_method: Any[Optional[bytes], None] = None, soap_service_id: Any[Optional[bytes], None] = None) -> None:
        self.message: str = message
        self.response_buff: bytes = b''
        self.finished: Future = finished
        self.soap_method: Any[Optional[bytes], None] = soap_method
        self.soap_service_id: Any[Optional[bytes], None] = soap_service_id
        self._response_code: int = 0
        self._response_msg: bytes = b''
        self._content_length: int = 0
        self._got_headers: bool = False
        self._headers: Any[Mapping[None], Mapping[str, str]] = {}
        self._body: bytes = b''

    def connection_made(self, transport:  transports.DatagramTransport = DatagramTransport) -> NoReturn:
        ...

    def data_received(self, data: Union[bytes, Text]) -> NoReturn:
        ...


async def scpd_get(control_url: str, address: str, port: int, loop: Any[Optional[AbstractEventLoop], None] = None) -> Tuple[Mapping[str, str], str, Optional[Exception]]:
    ...


async def scpd_post(control_url: str, address: str, port: int, method: str, param_names: List[str], service_id: bytes, loop: Any[Optional[AbstractEventLoop], None] = None, **kwargs) -> Tuple[Mapping[str, str], str, Optional[Exception]]:
    ...
