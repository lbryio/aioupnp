from asyncio import DatagramProtocol, Future, AbstractEventLoop
from collections import OrderedDict

from typing import Pattern, Union, List, Tuple, runtime

from aioupnp.fault import UPnPError

HTTPD_CODE_REGEX: Union[Pattern, bytes]


def parse_headers(response: bytes) -> Tuple[OrderedDict, int, bytes]:
    ...


@runtime
class SCPDHTTPClientProtocol(DatagramProtocol):
    def __init__(self, message: str, finished: Future, soap_method: Union[bytes, None] = None, soap_service_id: Union[bytes, None] = None) -> None:
        self.message: str = message
        self.response_buff: bytes = b''
        self.finished: Future = finished
        self.soap_method: Union[bytes, None] = soap_method
        self.soap_service_id: Union[bytes, None] = soap_service_id
        self._response_code: int = 0
        self._response_msg: bytes = b''
        self._content_length: int = 0
        self._got_headers: bool = False
        self._headers: OrderedDict = {}
        self._body: bytes = b''


async def scpd_get(control_url: str, address: str, port: int, loop: Union[AbstractEventLoop, None] = None) -> Union[Tuple[OrderedDict, str], UPnPError]:
    ...


async def scpd_post(control_url: str, address: str, port: int, method: str, param_names: List, service_id: bytes, loop: Union[AbstractEventLoop, None] = None, **kwargs: OrderedDict) -> Union[Tuple[OrderedDict, str], UPnPError]:
    ...
