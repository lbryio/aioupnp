import re
from xml.etree import ElementTree

from typing import Union, Pattern, AnyStr, Any, Dict, List

from aioupnp.constants import XML_VERSION
from aioupnp.util import etree_to_dict, flatten_keys

CONTENT_PATTERN: Union[Pattern, AnyStr] = re.compile("(\<\?xml version=\"1\.0\"\?\>(\s*.)*|\>)".encode())

XML_ROOT_SANITY_PATTERN: Union[Pattern, AnyStr] = re.compile(
    r'(?i)(\{|(urn:schemas-[\w|\d]*-(com|org|net))[:|-](device|service)[:|-]([\w|\d|\:|\-|\_]*)|\}([\w|\d|\:|\-|\_]*))'
)

XML_OTHER_KEYS: Union[Pattern, AnyStr] = re.compile(r'{[\w|\:\/\.]*}|(\w*)')


def serialize_scpd_get(path: AnyStr, address: AnyStr) -> Any[AnyStr]:
    if "http://" in address:
        host = address.split("http://")[1]
    else:
        host = address
    if ":" in host:
        host = host.split(":")[0]
    if not path.startswith("/"):
        path = "/" + path
    return f"""
    GET {host} HTTP/1.1\r\n'
    Accept-Encoding: gzip\r\n'
    Host: {path}\r\n
    Connection: Close\r\n
    \r\n""".encode()


def deserialize_scpd_get_response(content: AnyStr) -> Any[Dict[AnyStr], Dict[None]]:
    if XML_VERSION.encode() in content:
        parsed = CONTENT_PATTERN.findall(content)
        content = b'' if not parsed else parsed[0][0]
        xml_dict = etree_to_dict(ElementTree.fromstring(content.decode()))
        return parse_device_dict(xml_dict)
    return {}


def parse_device_dict(xml_dict: Dict[AnyStr]) -> Any[Dict[AnyStr], Dict[None]]:
    keys: List[AnyStr] = [xml_dict.keys()]
    for k in keys:
        m = XML_ROOT_SANITY_PATTERN.findall(k)
        if len(m) == 3 and m[1][0] and m[2][5]:
            schema_key = m[1][0]
            root = m[2][5]
            xml_dict = flatten_keys(xml_dict, "{%s}" % schema_key)[root]
            break
    result = {}
    for k, v in xml_dict.items():
        if isinstance(xml_dict[k], dict):
            inner_d = {}
            for inner_k, inner_v in xml_dict[k].items():
                parsed_k = XML_OTHER_KEYS.findall(inner_k)
                if len(parsed_k) == 2:
                    inner_d[parsed_k[0]] = inner_v
                else:
                    assert len(parsed_k) == 3
                    inner_d[parsed_k[1]] = inner_v
            result[k] = inner_d
        else:
            result[k] = v
    return result
