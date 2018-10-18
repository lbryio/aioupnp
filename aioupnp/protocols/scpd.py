import logging
import socket
import typing
import re
from collections import OrderedDict
from xml.etree import ElementTree
import asyncio
from asyncio.protocols import Protocol
from aioupnp.fault import UPnPError
from aioupnp.util import get_dict_val_case_insensitive
from aioupnp.serialization.scpd import deserialize_scpd_get_response
from aioupnp.serialization.scpd import serialize_scpd_get
from aioupnp.serialization.soap import serialize_soap_post, deserialize_soap_post_response


log = logging.getLogger(__name__)


HTTP_CODE_REGEX = re.compile(b"^HTTP[\/]{0,1}1\.[1|0] (\d\d\d)(.*)$")


def parse_headers(response: bytes) -> typing.Tuple[OrderedDict, int, bytes]:
    lines = response.split(b'\r\n')
    headers = OrderedDict([
        (l.split(b':')[0], b':'.join(l.split(b':')[1:]).lstrip(b' ').rstrip(b' '))
        for l in response.split(b'\r\n')
    ])
    if len(lines) != len(headers):
        raise ValueError("duplicate headers")
    http_response = tuple(headers.keys())[0]
    response_code, message = HTTP_CODE_REGEX.findall(http_response)[0]
    del headers[http_response]
    return headers, int(response_code), message


class SCPDHTTPClientProtocol(Protocol):
    """
    This class will make HTTP GET and POST requests

    It differs from spec HTTP in that the version string can be invalid, all we care about is the xml body
    and devices respond with an invalid HTTP version line
    """

    def __init__(self, message: bytes, finished: asyncio.Future, soap_method: str=None,
                 soap_service_id: str=None) -> None:
        self.message = message
        self.response_buff = b""
        self.finished = finished
        self.soap_method = soap_method
        self.soap_service_id = soap_service_id

        self._response_code: int = 0
        self._response_msg: bytes = b""
        self._content_length: int = 0
        self._got_headers = False
        self._headers: dict = {}
        self._body = b""

    def connection_made(self, transport):
        transport.write(self.message)

    def data_received(self, data):
        self.response_buff += data
        for i, line in enumerate(self.response_buff.split(b'\r\n')):
            if not line:  # we hit the blank line between the headers and the body
                if i == (len(self.response_buff.split(b'\r\n')) - 1):
                    continue  # the body is still yet to be written
                if not self._got_headers:
                    self._headers, self._response_code, self._response_msg = parse_headers(
                        b'\r\n'.join(self.response_buff.split(b'\r\n')[:i])
                    )
                    content_length = get_dict_val_case_insensitive(self._headers, b'Content-Length')
                    if content_length is None:
                        return
                    self._content_length = int(content_length or 0)
                    self._got_headers = True
                body = b'\r\n'.join(self.response_buff.split(b'\r\n')[i+1:])
                if self._content_length == len(body):
                    self.finished.set_result((body, self._response_code, self._response_msg))
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
                return


async def scpd_get(control_url: str, address: str, port: int) -> typing.Tuple[typing.Dict, bytes,
                                                                              typing.Optional[Exception]]:
    loop = asyncio.get_running_loop()
    finished: asyncio.Future = asyncio.Future()
    packet = serialize_scpd_get(control_url, address)
    transport, protocol = await loop.create_connection(
        lambda : SCPDHTTPClientProtocol(packet, finished),  address, port
    )
    assert isinstance(protocol, SCPDHTTPClientProtocol)
    error = None
    try:
        body, response_code, response_msg = await asyncio.wait_for(finished, 1.0)
    except asyncio.TimeoutError:
        error = UPnPError("get request timed out")
        body = b''
    finally:
        transport.close()
    if not error:
        try:
            return deserialize_scpd_get_response(body), body, None
        except ElementTree.ParseError as err:
            error = UPnPError(err)
    return {}, body, error


async def scpd_post(control_url: str, address: str, port: int, method: str, param_names: list, service_id: bytes,
                    soap_socket: socket.socket = None, **kwargs) -> typing.Tuple[typing.Dict, bytes,
                                                                                 typing.Optional[Exception]]:
    loop = asyncio.get_running_loop()
    finished: asyncio.Future = asyncio.Future()
    packet = serialize_soap_post(method, param_names, service_id, address.encode(), control_url.encode(), **kwargs)
    transport, protocol = await loop.create_connection(
        lambda : SCPDHTTPClientProtocol(
            packet, finished, soap_method=method, soap_service_id=service_id.decode(),
        ), address, port, sock=soap_socket
    )
    assert isinstance(protocol, SCPDHTTPClientProtocol)
    try:
        body, response_code, response_msg = await asyncio.wait_for(finished, 1.0)
    except asyncio.TimeoutError:
        return {}, b'', UPnPError("Timeout")
    finally:
        transport.close()
    try:
        return (
            deserialize_soap_post_response(body, method, service_id.decode()), body, None
        )
    except (ElementTree.ParseError, UPnPError) as err:
        return {}, body, UPnPError(err)
