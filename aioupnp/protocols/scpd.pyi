import collections
import typing
import asyncio

HTTPD_CODE_REGEX: typing.Pattern[bytes]

def parse_headers(response: bytes) -> typing.Tuple[collections.OrderedDict, int, bytes]:
    ...

class SCPDHTTPClientProtocol(typing.runtime(asyncio.DatagramProtocol)):
    def __init__(self, message: bytes, finished: asyncio.Future, soap_method: typing.Optional[str] = None, soap_service_id: typing.Optional[str] = None) -> typing.NoReturn:
        self.message: bytes = message
        self.response_buff: bytes = b''
        self.finished: asyncio.Future = finished
        self.soap_method: typing.Any[str, None] = soap_method
        self.soap_service_id: typing.Any[str, None] = soap_service_id
        self._response_code: int = 0
        self._response_msg: bytes = b''
        self._content_length: int = 0
        self._got_headers: bool = False
        self._headers: typing.Dict = {}
        self._body: bytes = b''


    def connection_made(self, transport: asyncio.Transport) -> typing.NoReturn:
        ...

    def data_received(self, data: bytes) -> typing.NoReturn:
        ...

async def scpd_get(control_url: str, address: str, port: int, loop: asyncio.AbstractEventLoop = None) -> typing.Tuple[typing.Dict, bytes, typing.Optional[Exception]]:
    ...

async def scpd_post(control_url: str, address: str, port: int, method: str, param_names: typing.List[str], service_id: bytes, loop: asyncio.AbstractEventLoop = None, **kwargs) -> typing.Tuple[typing.Dict, bytes, typing.Optional[Exception]]:
    ...
