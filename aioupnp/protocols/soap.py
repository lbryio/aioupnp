import logging
import socket
import asyncio
import typing
import time
from aioupnp.protocols.scpd import scpd_post
from aioupnp.fault import UPnPError

log = logging.getLogger(__name__)


def safe_type(t):
    if t is typing.Tuple:
        return tuple
    if t is typing.List:
        return list
    if t is typing.Dict:
        return dict
    if t is typing.Set:
        return set
    return t


class SOAPCommand:
    def __init__(self, gateway_address: str, service_port: int, control_url: str, service_id: bytes, method: str,
                 param_types: dict, return_types: dict, param_order: list, return_order: list,
                 soap_socket: socket.socket = None) -> None:
        self.gateway_address = gateway_address
        self.service_port = service_port
        self.control_url = control_url
        self.service_id = service_id
        self.method = method
        self.param_types = param_types
        self.param_order = param_order
        self.return_types = return_types
        self.return_order = return_order
        self.soap_socket = soap_socket
        self._requests: typing.List = []

    async def __call__(self, **kwargs) -> typing.Union[None, typing.Dict, typing.List, typing.Tuple]:
        if set(kwargs.keys()) != set(self.param_types.keys()):
            raise Exception("argument mismatch: %s vs %s" % (kwargs.keys(), self.param_types.keys()))
        soap_kwargs = {n: safe_type(self.param_types[n])(kwargs[n]) for n in self.param_types.keys()}
        response, xml_bytes, err = await scpd_post(
            self.control_url, self.gateway_address, self.service_port, self.method, self.param_order,
            self.service_id, self.soap_socket, **soap_kwargs
        )
        if err is not None:
            self._requests.append((soap_kwargs, xml_bytes, None, err, time.time()))
            raise err
        if not response:
            result = None
        else:
            recast_result = tuple([safe_type(self.return_types[n])(response.get(n)) for n in self.return_order])
            if len(recast_result) == 1:
                result = recast_result[0]
            else:
                result = recast_result
        self._requests.append((soap_kwargs, xml_bytes, result, None, time.time()))
        return result
