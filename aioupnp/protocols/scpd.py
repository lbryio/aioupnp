import logging
import socket
import typing
from xml.etree import ElementTree
import asyncio
from asyncio.protocols import Protocol
from aioupnp.fault import UPnPError
from aioupnp.serialization.scpd import deserialize_scpd_get_response
from aioupnp.serialization.scpd import serialize_scpd_get
from aioupnp.serialization.soap import serialize_soap_post, deserialize_soap_post_response


log = logging.getLogger(__name__)


class SCPDHTTPClientProtocol(Protocol):
    POST = 'POST'
    GET = 'GET'

    def __init__(self, method: str, message: bytes, finished: asyncio.Future, soap_method: str=None,
                 soap_service_id: str=None, close_after_send: bool = False) -> None:
        self.method = method
        assert soap_service_id is not None and soap_method is not None if method == 'POST' else True, \
            'soap args not provided'
        self.message = message
        self.response_buff = b""
        self.finished = finished
        self.soap_method = soap_method
        self.soap_service_id = soap_service_id
        self.close_after_send = close_after_send

    def connection_made(self, transport):
        transport.write(self.message)
        if self.close_after_send:
            self.finished.set_result(None)

    def data_received(self, data):
        self.response_buff += data
        if self.method == self.GET:
            try:
                packet = deserialize_scpd_get_response(self.response_buff)
                if packet:
                    self.finished.set_result(packet)
                    return
            except ElementTree.ParseError:
                pass
            except UPnPError as err:
                self.finished.set_exception(err)
        elif self.method == self.POST:
            try:
                packet = deserialize_soap_post_response(self.response_buff, self.soap_method, self.soap_service_id)
                if packet:
                    self.finished.set_result(packet)
                    return
            except ElementTree.ParseError:
                pass
            except UPnPError as err:
                self.finished.set_exception(err)


async def scpd_get(control_url: str, address: str, port: int) -> typing.Tuple[typing.Dict, bytes]:
    loop = asyncio.get_running_loop()
    finished: asyncio.Future = asyncio.Future()
    packet = serialize_scpd_get(control_url, address)
    transport, protocol = await loop.create_connection(
        lambda : SCPDHTTPClientProtocol('GET', packet, finished),  address, port
    )
    assert isinstance(protocol, SCPDHTTPClientProtocol)
    parsed: typing.Dict = {}
    try:
        parsed = await asyncio.wait_for(finished, 1.0)
    except UPnPError:
        return parsed, protocol.response_buff
    finally:
        transport.close()
    return parsed, protocol.response_buff


async def scpd_post(control_url: str, address: str, port: int, method: str, param_names: list, service_id: bytes,
                    close_after_send: bool, soap_socket: socket.socket = None,
                    **kwargs) -> typing.Tuple[typing.Dict, bytes]:
    loop = asyncio.get_running_loop()
    finished: asyncio.Future = asyncio.Future()
    packet = serialize_soap_post(method, param_names, service_id, address.encode(), control_url.encode(), **kwargs)
    transport, protocol = await loop.create_connection(
        lambda : SCPDHTTPClientProtocol(
            'POST', packet, finished, soap_method=method, soap_service_id=service_id.decode(),
            close_after_send=close_after_send
        ), address, port, sock=soap_socket
    )
    assert isinstance(protocol, SCPDHTTPClientProtocol)
    parsed: typing.Dict = {}
    try:
        parsed = await asyncio.wait_for(finished, 1.0)
    except UPnPError:
        return parsed, protocol.response_buff
    finally:
        transport.close()
    return parsed, protocol.response_buff
