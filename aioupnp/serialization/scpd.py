import re
from typing import Dict, Any, List, Tuple
from aioupnp.fault import UPnPError
from aioupnp.constants import XML_VERSION_PREFIX
from aioupnp.serialization.xml import xml_to_dict
from aioupnp.util import flatten_keys


CONTENT_PATTERN = re.compile(
    "(\<\?xml version=\"1\.0\"[^>]*\?\>(\s*.)*|\>)"
)

XML_ROOT_SANITY_PATTERN = re.compile(
    "(?i)(\{|(urn:schemas-[\w|\d]*-(com|org|net))[:|-](device|service)[:|-]([\w|\d|\:|\-|\_]*)|\}([\w|\d|\:|\-|\_]*))"
)

XML_OTHER_KEYS = re.compile(
    "{[\w|\:\/\.]*}|(\w*)"
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
        f'GET {path} HTTP/1.1\r\n'
        f'Accept-Encoding: gzip\r\n'
        f'Host: {host}\r\n'
        f'Connection: Close\r\n'
        f'\r\n'
    ).encode()


def deserialize_scpd_get_response(content: bytes) -> Dict[str, Any]:
    if XML_VERSION_PREFIX.encode() in content:
        parsed: List[Tuple[str, str]] = CONTENT_PATTERN.findall(content.decode())
        xml_dict = xml_to_dict('' if not parsed else parsed[0][0])
        return parse_device_dict(xml_dict)
    return {}


def parse_device_dict(xml_dict: Dict[str, Any]) -> Dict[str, Any]:
    keys = list(xml_dict.keys())
    found = False
    for k in keys:
        m: List[Tuple[str, str, str, str, str, str]] = XML_ROOT_SANITY_PATTERN.findall(k)
        if len(m) == 3 and m[1][0] and m[2][5]:
            schema_key: str = m[1][0]
            root: str = m[2][5]
            flattened = flatten_keys(xml_dict, "{%s}" % schema_key)
            if root not in flattened:
                raise UPnPError("root device not found")
            xml_dict = flattened[root]
            found = True
            break
    if not found:
        raise UPnPError("device not found")
    result = {}
    for k, v in xml_dict.items():
        if isinstance(xml_dict[k], dict):
            inner_d = {}
            for inner_k, inner_v in xml_dict[k].items():
                parsed_k = XML_OTHER_KEYS.findall(inner_k)
                if len(parsed_k) == 2:
                    inner_d[parsed_k[0]] = inner_v
                else:
                    assert len(parsed_k) == 3, f"expected len=3, got {len(parsed_k)}"
                    inner_d[parsed_k[1]] = inner_v
            result[k] = inner_d
        else:
            result[k] = v
    return result
