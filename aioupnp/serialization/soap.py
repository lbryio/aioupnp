import re
from xml.etree import ElementTree

from typing import Union, Pattern, List, Dict

from aioupnp.constants import XML_VERSION, ENVELOPE, BODY
from aioupnp.fault import handle_fault, UPnPError
from aioupnp.util import etree_to_dict, flatten_keys

CONTENT_NO_XML_VERSION_PATTERN: Union[Pattern, bytes] = re.compile(
    r'(\<s\:Envelope xmlns\:s=\"http\:\/\/schemas\.xmlsoap\.org\/soap\/envelope\/\"(\s*.)*\>)'.encode()
)


def serialize_soap_post(method: str, param_names: List[str], service_id: str,
                        gateway_address: str, control_url: str, **kwargs) -> bytes:
    """Serialize SOAP post data.

    :param str method:
    :param list param_names:
    :param str or bytes service_id:
    :param str or bytes gateway_address:
    :param str or bytes control_url:
    :param kwargs:
    :return str or bytes:
    """
    args: str = ""
    for name in param_names:
        args += f'<{name}>{kwargs.get(name)}</{name}>\r\n'
    soap_body: str = '\r\n'.join([
        "", f'{XML_VERSION}',
        "<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\""
        "s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"><s:Body>"
        f'<u:{method} xmlns:u=\"{service_id}\">{args}</u:{method}></s:Body></s:Envelope>'
    ])

    host: str = gateway_address
    content_length: int = len(soap_body)
    if "http://" in host:
        host = gateway_address.split("http://")[1]

    return '\r\n'.join([
        f'POST {control_url} HTTP/1.1',
        f'Host: {host}',
        "User-Agent: python3/aioupnp, UPnP/1.0, MiniUPnPc/1.9",
        f'Content-Length: {content_length}',
        f'SOAPAction: \"{service_id}#{method}\"',
        "Connection: Close",
        "Pragma: no-cache",
        f'{soap_body}',
    ]).encode()


def deserialize_soap_post_response(response: bytes, method: bytes, service_id: bytes) -> Union[Dict, UPnPError]:
    """Deserialize SOAP post.

    :param bytes response:
    :param str method:
    :param str service_id:
    :return dict or UPnPError:
    """
    parsed = CONTENT_NO_XML_VERSION_PATTERN.findall(response)
    content = b'' if not parsed else parsed[0][0]
    content_dict = etree_to_dict(ElementTree.fromstring(content.decode()))
    envelope = content_dict[ENVELOPE]
    response_body = flatten_keys(envelope[BODY], f'{service_id}')
    body = handle_fault(response_body)  # raises UPnPError if there is a fault
    response_key = None
    if not body:
        return {}
    for key in body:
        if method in key:
            response_key = key
            break
    if not response_key:
        raise UPnPError(f'Unknown response fields for {method}: {body}.')
    return body[response_key]
