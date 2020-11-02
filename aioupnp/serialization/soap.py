import re
import typing
import json
from aioupnp.util import flatten_keys
from aioupnp.fault import UPnPError
from aioupnp.constants import XML_VERSION, ENVELOPE, BODY, FAULT, CONTROL
from aioupnp.serialization.xml import xml_to_dict

CONTENT_NO_XML_VERSION_PATTERN = re.compile(
    b"(\<([^:>]*)\:Envelope xmlns\:[^:>]*=\"http\:\/\/schemas\.xmlsoap\.org\/soap\/envelope\/\"(\s*.)*\>)"
)


def serialize_soap_post(method: str, param_names: typing.List[str], service_id: bytes, gateway_address: bytes,
                        control_url: bytes, **kwargs: typing.Dict[str, str]) -> bytes:
    args = "".join(f"<{param_name}>{kwargs.get(param_name, '')}</{param_name}>" for param_name in param_names)
    soap_body = (f'\r\n{XML_VERSION}\r\n<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
                 f's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body>'
                 f'<u:{method} xmlns:u="{service_id.decode()}">{args}</u:{method}></s:Body></s:Envelope>')
    if "http://" in gateway_address.decode():
        host = gateway_address.decode().split("http://")[1]
    else:
        host = gateway_address.decode()
    return (
        f'POST {control_url.decode()} HTTP/1.1\r\n'  # could be just / even if it shouldn't be
        f'Host: {host}\r\n'
        f'User-Agent: python3/aioupnp, UPnP/1.0, MiniUPnPc/1.9\r\n'
        f'Content-Length: {len(soap_body)}\r\n'
        f'Content-Type: text/xml\r\n'
        f'SOAPAction: \"{service_id.decode()}#{method}\"\r\n'
        f'Connection: Close\r\n'
        f'Cache-Control: no-cache\r\n'
        f'Pragma: no-cache\r\n'
        f'{soap_body}'
        f'\r\n'
    ).encode()


def deserialize_soap_post_response(response: bytes, method: str,
                                   service_id: str) -> typing.Dict[str, typing.Dict[str, str]]:
    parsed: typing.List[typing.List[bytes]] = CONTENT_NO_XML_VERSION_PATTERN.findall(response)
    content = b'' if not parsed else parsed[0][0]
    content_dict = xml_to_dict(content.decode())
    envelope = content_dict[ENVELOPE]
    if not isinstance(envelope[BODY], dict):
        # raise UPnPError('blank response')
        return {}  # TODO: raise
    response_body: typing.Dict[str, typing.Dict[str, typing.Dict[str, str]]] = flatten_keys(
        envelope[BODY], f"{'{' + service_id + '}'}"
    )
    if not response_body:
        # raise UPnPError('blank response')
        return {}  # TODO: raise
    if FAULT in response_body:
        fault: typing.Dict[str, typing.Dict[str, typing.Dict[str, str]]] = flatten_keys(
            response_body[FAULT], "{%s}" % CONTROL
        )
        try:
            raise UPnPError(fault['detail']['UPnPError']['errorDescription'])
        except (KeyError, TypeError, ValueError):
            raise UPnPError(f"Failed to decode error response: {json.dumps(fault)}")
    response_key = None
    for key in response_body:
        if method in key:
            response_key = key
            break
    if not response_key:
        raise UPnPError(f"unknown response fields for {method}: {response_body}")
    return response_body[response_key]
