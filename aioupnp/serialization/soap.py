import re
from xml.etree import ElementTree
from aioupnp.util import etree_to_dict, flatten_keys
from aioupnp.fault import handle_fault, UPnPError
from aioupnp.constants import XML_VERSION, ENVELOPE, BODY

CONTENT_NO_XML_VERSION_PATTERN = re.compile(
    "(\<s\:Envelope xmlns\:s=\"http\:\/\/schemas\.xmlsoap\.org\/soap\/envelope\/\"(\s*.)*\>)".encode()
)


def serialize_soap_post(method: str, param_names: list, service_id: bytes, gateway_address: bytes,
                        control_url: bytes, **kwargs) -> bytes:
    args = "".join("<%s>%s</%s>" % (n, kwargs.get(n), n) for n in param_names)
    soap_body = ('\r\n%s\r\n<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
                 's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body>'
                 '<u:%s xmlns:u="%s">%s</u:%s></s:Body></s:Envelope>' % (
                     XML_VERSION, method, service_id.decode(),
                     args, method))
    if "http://" in gateway_address.decode():
        host = gateway_address.decode().split("http://")[1]
    else:
        host = gateway_address.decode()
    return (
            (
                'POST %s HTTP/1.1\r\n'
                'Host: %s\r\n'
                'User-Agent: python3/aioupnp, UPnP/1.0, MiniUPnPc/1.9\r\n'
                'Content-Length: %i\r\n'
                'Content-Type: text/xml\r\n'
                'SOAPAction: \"%s#%s\"\r\n'
                'Connection: Close\r\n'
                'Cache-Control: no-cache\r\n'
                'Pragma: no-cache\r\n'
                '%s'
                '\r\n'
            ) % (
                control_url.decode(),  # could be just / even if it shouldn't be
                host,
                len(soap_body),
                service_id.decode(),  # maybe no quotes
                method,
                soap_body
            )
    ).encode()


def deserialize_soap_post_response(response: bytes, method: str, service_id: str) -> dict:
    parsed = CONTENT_NO_XML_VERSION_PATTERN.findall(response)
    content = b'' if not parsed else parsed[0][0]
    content_dict = etree_to_dict(ElementTree.fromstring(content.decode()))
    envelope = content_dict[ENVELOPE]
    response_body = flatten_keys(envelope[BODY], "{%s}" % service_id)
    body = handle_fault(response_body)  # raises UPnPError if there is a fault
    response_key = None
    if not body:
        return {}
    for key in body:
        if method in key:
            response_key = key
            break
    if not response_key:
        raise UPnPError("unknown response fields for %s: %s" % (method, body))
    return body[response_key]
