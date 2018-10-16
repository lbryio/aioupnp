"""
Alleged SSDP discovery documentation

M-SEARCH * HTTP/1.1

Headers
HOST
    Required. Multicast channel and port reserved for SSDP by Internet Assigned Numbers Authority (IANA). Must be
    239.255.255.250:1900. If the port number (“:1900”) is omitted, the receiver should assume the default SSDP port
    number of 1900.
MAN
    Required by HTTP Extension Framework. Unlike the NTS and ST headers, the value of the MAN header is enclosed in
    double quotes; it defines the scope (namespace) of the extension. Must be "ssdp:discover".
MX
    Required. Maximum wait time in seconds. Should be between 1 and 120 inclusive. Device responses should be delayed a
    random duration between 0 and this many seconds to balance load for the control point when it processes responses.
    This value may be increased if a large number of devices are expected to respond. The MX value should not be
    increased to accommodate network characteristics such as latency or propagation delay (for more details, see the
    explanation below). Specified by UPnP vendor. Integer.
ST
    Required. Search Target. Must be one of the following. (cf. NT header in NOTIFY with ssdp:alive above.) Single URI.

    ssdp:all
        Search for all devices and services.

    upnp:rootdevice
        Search for root devices only.

    uuid:device-UUID
        Search for a particular device. Device UUID specified by UPnP vendor.

    urn:schemas-upnp-org:device:deviceType:v
        Search for any device of this type. Device type and version defined by UPnP Forum working committee.

    urn:schemas-upnp-org:service:serviceType:v
        Search for any service of this type. Service type and version defined by UPnP Forum working committee.

    urn:domain-name:device:deviceType:v
        Search for any device of this type. Domain name, device type and version defined by UPnP vendor. Period
        characters in the domain name must be replaced with hyphens in accordance with RFC 2141.

    urn:domain-name:service:serviceType:v
        Search for any service of this type. Domain name, service type and version defined by UPnP vendor. Period
        characters in the domain name must be replaced with hyphens in accordance with RFC 2141.
"""

from collections import OrderedDict
from aioupnp.constants import SSDP_DISCOVER, SSDP_HOST

SEARCH_TARGETS = [
    'upnp:rootdevice',
    'urn:schemas-upnp-org:device:InternetGatewayDevice:1',
    'urn:schemas-wifialliance-org:device:WFADevice:1',
    'urn:schemas-upnp-org:device:WANDevice:1',
    "urn:schemas-upnp-org:service:WANIPConnection:1",
    "urn:schemas-upnp-org:service:WANPPPConnection:1",
    'ssdp:all'
]


def format_packet_args(order: list, **kwargs):
    args = []
    for o in order:
        for k, v in kwargs.items():
            if k.lower() == o.lower():
                args.append((k, v))
                break
    return OrderedDict(args)


def packet_generator():
    for st in SEARCH_TARGETS:
        order = ["HOST", "MAN", "MX", "ST"]
        yield format_packet_args(order, HOST=SSDP_HOST, MAN='"%s"' % SSDP_DISCOVER, MX=1, ST=st)
        yield format_packet_args(order, Host=SSDP_HOST, Man='"%s"' % SSDP_DISCOVER, MX=1, ST=st)
        yield format_packet_args(order, HOST=SSDP_HOST, MAN=SSDP_DISCOVER, MX=1, ST=st)
        yield format_packet_args(order, Host=SSDP_HOST, Man=SSDP_DISCOVER, MX=1, ST=st)

        order = ["HOST", "MAN", "ST", "MX"]
        yield format_packet_args(order, HOST=SSDP_HOST, MAN='"%s"' % SSDP_DISCOVER, MX=1, ST=st)
        yield format_packet_args(order, HOST=SSDP_HOST, MAN=SSDP_DISCOVER, MX=1, ST=st)

        order = ["HOST", "ST", "MAN", "MX"]
        yield format_packet_args(order, HOST=SSDP_HOST, MAN='"%s"' % SSDP_DISCOVER, MX=1, ST=st)
        yield format_packet_args(order, HOST=SSDP_HOST, MAN=SSDP_DISCOVER, MX=1, ST=st)
