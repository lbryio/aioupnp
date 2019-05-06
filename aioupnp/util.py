import re
import socket
from collections import defaultdict
from typing import Tuple, Dict, Pattern, Union, List, Any, Mapping, Optional
from xml.etree import ElementTree
import netifaces


BASE_ADDRESS_REGEX: Union[Pattern, bytes] = re.compile(r'^(http:\/\/\d*\.\d*\.\d*\.\d*:\d*)\/.*$'.encode())
BASE_PORT_REGEX: Union[Pattern, bytes] = re.compile(r'^http:\/\/\d*\.\d*\.\d*\.\d*:(\d*)\/.*$'.encode())


def etree_to_dict(t: ElementTree.Element) -> Dict:
    """Return converted XML element tree."""
    d: dict = {}
    if t.attrib:
        d[t.tag] = {}
    children = list(t)
    if children:
        dd: dict = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d[t.tag] = {k: v[0] if len(v) == 1 else v for k, v in dd.items()}
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d


def flatten_keys(d: Union[Tuple[List, Mapping[Any, Any]], List], strip: str) -> Union[Dict, Tuple[List, Dict], List]:
    if not isinstance(d, (list, dict)):
        return d
    if isinstance(d, list):
        return [flatten_keys(i, strip) for i in d]
    t = {}
    for k, v in d.items():
        if strip in k and strip != k:
            t[k.split(strip)[1]] = flatten_keys(v, strip)
        else:
            t[k] = flatten_keys(v, strip)
    return t


def get_dict_val_case_insensitive(d: Dict, k: str) -> Any[Optional[KeyError]]:
    match = list(filter(lambda x: x.lower() == k.lower(), d.keys()))
    if not match:
        return
    if len(match) > 1:
        raise KeyError("Overlapping Keys.")
    return d[match[0]]

# import struct
# import fcntl
# def get_ip_address(ifname):
#     SIOCGIFADDR = 0x8915
#     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     return socket.inet_ntoa(fcntl.ioctl(
#         s.fileno(),
#         SIOCGIFADDR,
#         struct.pack(b'256s', ifname[:15].encode())
#     )[20:24])


def get_interfaces() -> Dict[str, Union[Tuple[str, str], str]]:
    r = {
        interface_name: (router_address, netifaces.ifaddresses(interface_name)[netifaces.AF_INET][0]["addr"])
        for router_address, interface_name, _ in netifaces.gateways()[socket.AF_INET]
    }
    for interface_name in netifaces.interfaces():
        if interface_name in ["lo", "localhost"] or interface_name in r:
            continue
        addresses = netifaces.ifaddresses(interface_name)
        if netifaces.AF_INET in addresses:
            address = addresses[netifaces.AF_INET][0]["addr"]
            gateway_guess = ".".join(address.split(".")[:-1] + ["1"])
            r[interface_name] = (gateway_guess, address)
    r['default'] = r[netifaces.gateways()[0]["default"][netifaces.AF_INET][1]]
    return r


def get_gateway_and_lan_addresses(interface_name: str) -> Tuple[str, str]:
    for iface_name, (gateway, lan) in get_interfaces().items():
        if interface_name == iface_name:
            return gateway, lan
    return "", ""
