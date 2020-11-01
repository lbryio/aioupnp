import logging
import typing
import re
from collections import OrderedDict
import asyncio
from asyncio.protocols import Protocol
from aioupnp.fault import UPnPError
from aioupnp.util import get_dict_val_case_insensitive
from aioupnp.serialization.scpd import deserialize_scpd_get_response
from aioupnp.serialization.scpd import serialize_scpd_get
from aioupnp.serialization.soap import serialize_soap_post, deserialize_soap_post_response


log = logging.getLogger(__name__)


HTTP_CODE_REGEX = re.compile(b"^HTTP[\/]{0,1}1\.[1|0] (\d\d\d)(.*)$")


def parse_http_response_code(http_response: bytes) -> typing.Tuple[bytes, bytes]:
    parsed: typing.List[typing.Tuple[bytes, bytes]] = HTTP_CODE_REGEX.findall(http_response)
    return parsed[0]


def parse_headers(response: bytes) -> typing.Tuple[typing.Dict[bytes, bytes], int, bytes]:
    lines = response.split(b'\r\n')
    headers: typing.Dict[bytes, bytes] = OrderedDict([
        (l.split(b':')[0], b':'.join(l.split(b':')[1:]).lstrip(b' ').rstrip(b' '))
        for l in response.split(b'\r\n')
    ])
    if len(lines) != len(headers):
        raise ValueError("duplicate headers")
    header_keys: typing.List[bytes] = list(headers.keys())
    http_response = header_keys[0]
    response_code, message = parse_http_response_code(http_response)
    del headers[http_response]
    return headers, int(response_code), message


class SCPDHTTPClientProtocol(Protocol):
    """
    This class will make HTTP GET and POST requests

    It differs from spec HTTP in that the version string can be invalid, all we care about is the xml body
    and devices respond with an invalid HTTP version line
    """

    def __init__(self, message: bytes, finished: 'asyncio.Future[typing.Tuple[bytes, bytes, int, bytes]]',
                 soap_method: typing.Optional[str] = None, soap_service_id: typing.Optional[str] = None) -> None:
        self.message = message
        self.response_buff = b""
        self.finished = finished
        self.soap_method = soap_method
        self.soap_service_id = soap_service_id
        self._response_code = 0
        self._response_msg = b""
        self._content_length = 0
        self._got_headers = False
        self._has_content_length = True
        self._headers: typing.Dict[bytes, bytes] = {}
        self._body = b""
        self.transport: typing.Optional[asyncio.WriteTransport] = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        assert isinstance(transport, asyncio.WriteTransport)
        self.transport = transport
        self.transport.write(self.message)
        return None

    def data_received(self, data: bytes) -> None:
        if self.finished.done():  # possible to hit during tests
            return
        self.response_buff += data
        for i, line in enumerate(self.response_buff.split(b'\r\n')):
            if not line:  # we hit the blank line between the headers and the body
                if i == (len(self.response_buff.split(b'\r\n')) - 1):
                    return None  # the body is still yet to be written
                if not self._got_headers:
                    try:
                        self._headers, self._response_code, self._response_msg = parse_headers(
                            b'\r\n'.join(self.response_buff.split(b'\r\n')[:i])
                        )
                    except ValueError as err:
                        self.finished.set_exception(UPnPError(str(err)))
                        return
                    content_length = get_dict_val_case_insensitive(
                        self._headers, b'Content-Length'
                    )
                    if content_length is not None:
                        self._content_length = int(content_length)
                    else:
                        self._has_content_length = False
                    self._got_headers = True
                if self._got_headers and self._has_content_length:
                    body = b'\r\n'.join(self.response_buff.split(b'\r\n')[i+1:])
                    if self._content_length == len(body):
                        self.finished.set_result((self.response_buff, body, self._response_code, self._response_msg))
                    elif self._content_length > len(body):
                        pass
                    else:
                        self.finished.set_exception(
                            UPnPError(
                                "too many bytes written to response (%i vs %i expected)" % (
                                    len(body), self._content_length
                                )
                            )
                        )
                elif any(map(self.response_buff.endswith, (b"</root>\r\n", b"</scpd>\r\n"))):
                    # Actiontec has a router that doesn't give a Content-Length for the gateway xml
                    body = b'\r\n'.join(self.response_buff.split(b'\r\n')[i+1:])
                    self.finished.set_result((self.response_buff, body, self._response_code, self._response_msg))
                elif len(self.response_buff) >= 65535:
                    self.finished.set_exception(
                        UPnPError(
                            "too many bytes written to response (%i) with unspecified content length" % len(self.response_buff)
                            )
                        )
                    return
                else:
                    # needed for the actiontec case
                    pass
                return None
        return None


async def scpd_get(control_url: str, address: str, port: int,
                   loop: typing.Optional[asyncio.AbstractEventLoop] = None) -> typing.Tuple[
                                                     typing.Dict[str, typing.Any], bytes, typing.Optional[Exception]]:
    loop = loop or asyncio.get_event_loop()
    packet = serialize_scpd_get(control_url, address)
    finished: 'asyncio.Future[typing.Tuple[bytes, bytes, int, bytes]]' = loop.create_future()
    proto_factory: typing.Callable[[], SCPDHTTPClientProtocol] = lambda: SCPDHTTPClientProtocol(packet, finished)
    try:
        connect_tup: typing.Tuple[asyncio.BaseTransport, asyncio.BaseProtocol] = await loop.create_connection(
            proto_factory, address, port
        )
    except ConnectionError as err:
        return {}, b'', UPnPError(f"{err.__class__.__name__}({str(err)})")
    protocol = connect_tup[1]
    transport = connect_tup[0]
    assert isinstance(protocol, SCPDHTTPClientProtocol)

    error = None
    wait_task: typing.Awaitable[typing.Tuple[bytes, bytes, int, bytes]] = asyncio.wait_for(protocol.finished, 1.0, loop=loop)
    body = b''
    raw_response = b''
    try:
        raw_response, body, response_code, response_msg = await wait_task
    except asyncio.TimeoutError:
        error = UPnPError("get request timed out")
    except UPnPError as err:
        error = err
        raw_response = protocol.response_buff
    finally:
        transport.close()
    if not error:
        try:
            return deserialize_scpd_get_response(body), raw_response, None
        except Exception as err:
            error = UPnPError(err)

    return {}, raw_response, error


async def scpd_post(control_url: str, address: str, port: int, method: str, param_names: list, service_id: bytes,
                    loop: typing.Optional[asyncio.AbstractEventLoop] = None,
                    **kwargs: typing.Dict[str, typing.Any]
                    ) -> typing.Tuple[typing.Dict, bytes, typing.Optional[Exception]]:
    loop = loop or asyncio.get_event_loop()
    finished: 'asyncio.Future[typing.Tuple[bytes, bytes, int, bytes]]' = loop.create_future()
    packet = serialize_soap_post(method, param_names, service_id, address.encode(), control_url.encode(), **kwargs)
    proto_factory: typing.Callable[[], SCPDHTTPClientProtocol] = lambda:\
        SCPDHTTPClientProtocol(packet, finished, soap_method=method, soap_service_id=service_id.decode())
    try:
        connect_tup: typing.Tuple[asyncio.BaseTransport, asyncio.BaseProtocol] = await loop.create_connection(
            proto_factory, address, port
        )
    except ConnectionError as err:
        return {}, b'', UPnPError(f"{err.__class__.__name__}({str(err)})")
    protocol = connect_tup[1]
    transport = connect_tup[0]
    assert isinstance(protocol, SCPDHTTPClientProtocol)

    try:
        wait_task: typing.Awaitable[typing.Tuple[bytes, bytes, int, bytes]] = asyncio.wait_for(finished, 1.0, loop=loop)
        raw_response, body, response_code, response_msg = await wait_task
    except asyncio.TimeoutError:
        return {}, b'', UPnPError("Timeout")
    except UPnPError as err:
        return {}, protocol.response_buff, err
    finally:
        transport.close()
    try:
        return (
            deserialize_soap_post_response(body, method, service_id.decode()), raw_response, None
        )
    except Exception as err:
        return {}, raw_response, UPnPError(err)
