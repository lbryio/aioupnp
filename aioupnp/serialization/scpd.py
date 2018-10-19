import re
from typing import Dict
from xml.etree import ElementTree
from aioupnp.constants import XML_VERSION, DEVICE, ROOT
from aioupnp.util import etree_to_dict, flatten_keys


CONTENT_PATTERN = re.compile(
    "(\<\?xml version=\"1\.0\"\?\>(\s*.)*|\>)".encode()
)

XML_ROOT_SANITY_PATTERN = re.compile(
    "(?i)(\{|(urn:schemas-[\w|\d]*-(com|org|net))[:|-](device|service)[:|-]([\w|\d|\:|\-|\_]*)|\}([\w|\d|\:|\-|\_]*))"
)


def serialize_scpd_get(path: str, address: str) -> bytes:
    if "http://" in address:
        host = address.split("http://")[1]
    else:
        host = address
    if ":" in host:
        host = host.split(":")[0]
    if not path.startswith("/"):
        path = "/" + path
    return (
            (
                'GET %s HTTP/1.1\r\n'
                'Accept-Encoding: gzip\r\n'
                'Host: %s\r\n'
                'Connection: Close\r\n'
                '\r\n'
            ) % (path, host)
    ).encode()


def deserialize_scpd_get_response(content: bytes) -> Dict:
    if XML_VERSION.encode() in content:
        parsed = CONTENT_PATTERN.findall(content)
        content = b'' if not parsed else parsed[0][0]
        xml_dict = etree_to_dict(ElementTree.fromstring(content.decode()))
        schema_key = DEVICE
        root = ROOT
        for k in xml_dict.keys():
            m = XML_ROOT_SANITY_PATTERN.findall(k)
            if len(m) == 3 and m[1][0] and m[2][5]:
                schema_key = m[1][0]
                root = m[2][5]
                break
        return flatten_keys(xml_dict, "{%s}" % schema_key)[root]
    return {}
