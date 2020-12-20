import contextlib
from io import StringIO
from tests import AsyncioTestCase, mock_tcp_and_udp
from collections import OrderedDict
from aioupnp.serialization.ssdp import SSDPDatagram
from aioupnp.protocols.m_search_patterns import packet_generator
from aioupnp.__main__ import main


m_search_cli_result = """{
  "lan_address": "10.0.0.2",
  "gateway_address": "10.0.0.1",
  "discover_reply": {
    "CACHE_CONTROL": "max-age=1800",
    "LOCATION": "http://10.0.0.1:49152/InternetGatewayDevice.xml",
    "SERVER": "Linux, UPnP/1.0, DIR-890L Ver 1.20",
    "ST": "urn:schemas-upnp-org:device:WANDevice:1",
    "USN": "uuid:22222222-3333-4444-5555-666666666666::urn:schemas-upnp-org:device:WANDevice:1"
  }
}\n"""


m_search_help_msg = """aioupnp [-h] [--debug_logging] m_search [--lan_address=<str>] [--gateway_address=<str>]
  [--timeout=<int>] [--interface_name=<str>] [--<header key>=<header value>, ...]

Perform a M-SEARCH for a upnp gateway.

:param lan_address: (str) the local interface ipv4 address
:param gateway_address: (str) the gateway ipv4 address
:param timeout: (int) m search timeout
:param interface_name: (str) name of the network interface
:param igd_args: (dict) case sensitive M-SEARCH headers. if used all headers to be used must be provided.

:return: {
    'lan_address': (str) lan address,
    'gateway_address': (str) gateway address,
    'm_search_kwargs': (str) equivalent igd_args ,
    'discover_reply': (dict) SSDP response datagram
}\n
"""

expected_usage = """aioupnp [-h] [--debug_logging] [--interface=<interface>] [--gateway_address=<gateway_address>]
  [--lan_address=<lan_address>] [--timeout=<timeout>] [(--<header_key>=<value>)...]

If m-search headers are provided as keyword arguments all of the headers to be used must be provided,
in the order they are to be used. For example:
  aioupnp --HOST=239.255.255.250:1900 --MAN="ssdp:discover" --MX=1 --ST=upnp:rootdevice m_search

Commands:
  m_search | get_external_ip | add_port_mapping | get_port_mapping_by_index | get_redirects |
  get_specific_port_mapping | delete_port_mapping | get_next_mapping | gather_debug_info

For help with a specific command:  aioupnp help <command>
"""

expected_get_external_ip_usage = """aioupnp [-h] [--debug_logging] get_external_ip

Get the external ip address from the gateway

:return: (str) external ip

"""

expected_add_port_mapping_usage = """aioupnp [-h] [--debug_logging] add_port_mapping [--external_port=<int>] [--protocol=<str>]
  [--internal_port=<int>] [--lan_address=<str>] [--description=<str>] [--lease_time=<int>]

Add a new port mapping

:param external_port: (int) external port to map
:param protocol: (str) UDP | TCP
:param internal_port: (int) internal port
:param lan_address: (str) internal lan address
:param description: (str) mapping description
:param lease_time: (int) lease time in seconds
:return: None

"""

expected_get_next_mapping_usage = """aioupnp [-h] [--debug_logging] get_next_mapping [--port=<int>] [--protocol=<str>]
  [--description=<str>] [--internal_port=<typing.Union[int, NoneType]>] [--lease_time=<int>]

Get a new port mapping. If the requested port is not available, increment until the next free port is mapped

:param port: (int) external port
:param protocol: (str) UDP | TCP
:param description: (str) mapping description
:param internal_port: (int) internal port
:param lease_time: (int) lease time in seconds

:return: (int) mapped port

"""


expected_delete_port_mapping_usage = """aioupnp [-h] [--debug_logging] delete_port_mapping [--external_port=<int>] [--protocol=<str>]

Delete a port mapping

:param external_port: (int) port number of mapping
:param protocol: (str) TCP | UDP
:return: None

"""

expected_get_specific_port_mapping_usage = """aioupnp [-h] [--debug_logging] get_specific_port_mapping [--external_port=<int>] [--protocol=<str>]

Get information about a port mapping by port number and protocol

:param external_port: (int) port number
:param protocol: (str) UDP | TCP
:return: NamedTuple[
    internal_port: int
    lan_address: str
    enabled: bool
    description: str
    lease_time: int
]

"""
expected_get_redirects_usage = """aioupnp [-h] [--debug_logging] get_redirects

Get information about all mapped ports

:return: List[
    NamedTuple[
        gateway_address: str
        external_port: int
        protocol: str
        internal_port: int
        lan_address: str
        enabled: bool
        description: str
        lease_time: int
    ]
]

"""
expected_get_port_mapping_by_index_usage = """aioupnp [-h] [--debug_logging] get_port_mapping_by_index [--index=<int>]

Get information about a port mapping by index number

:param index: (int) mapping index number
:return: NamedTuple[
    gateway_address: str
    external_port: int
    protocol: str
    internal_port: int
    lan_address: str
    enabled: bool
    description: str
    lease_time: int
]

"""


class TestCLI(AsyncioTestCase):
    gateway_address = "10.0.0.1"
    soap_port = 49152
    m_search_args = OrderedDict([
        ("HOST", "239.255.255.250:1900"),
        ("MAN", "ssdp:discover"),
        ("MX", 1),
        ("ST", "urn:schemas-upnp-org:device:WANDevice:1")
    ])
    reply = SSDPDatagram("OK", OrderedDict([
        ("CACHE_CONTROL", "max-age=1800"),
        ("LOCATION", "http://10.0.0.1:49152/InternetGatewayDevice.xml"),
        ("SERVER", "Linux, UPnP/1.0, DIR-890L Ver 1.20"),
        ("ST", "urn:schemas-upnp-org:device:WANDevice:1"),
        ("USN", "uuid:11111111-2222-3333-4444-555555555555::urn:schemas-upnp-org:device:WANDevice:1")
    ]))

    scpd_replies = {
        b'GET /InternetGatewayDevice.xml HTTP/1.1\r\nAccept-Encoding: gzip\r\nHost: 10.0.0.1\r\nConnection: Close\r\n\r\n': b"HTTP/1.1 200 OK\r\nServer: WebServer\r\nDate: Thu, 11 Oct 2018 22:16:16 GMT\r\nContent-Type: text/xml\r\nContent-Length: 3921\r\nLast-Modified: Thu, 09 Aug 2018 12:41:07 GMT\r\nConnection: close\r\n\r\n<?xml version=\"1.0\"?>\n<root xmlns=\"urn:schemas-upnp-org:device-1-0\">\n\t<specVersion>\n\t\t<major>1</major>\n\t\t<minor>0</minor>\n\t</specVersion>\n\t<URLBase>http://10.0.0.1:49152</URLBase>\n\t<device>\n\t\t<deviceType>urn:schemas-upnp-org:device:InternetGatewayDevice:1</deviceType>\n\t\t<friendlyName>Wireless Broadband Router</friendlyName>\n\t\t<manufacturer>D-Link Corporation</manufacturer>\n\t\t<manufacturerURL>http://www.dlink.com</manufacturerURL>\n\t\t<modelDescription>D-Link Router</modelDescription>\n\t\t<modelName>D-Link Router</modelName>\n\t\t<modelNumber>DIR-890L</modelNumber>\n\t\t<modelURL>http://www.dlink.com</modelURL>\n\t\t<serialNumber>120</serialNumber>\n\t\t<UDN>uuid:11111111-2222-3333-4444-555555555555</UDN>\n\t\t<iconList>\n\t\t\t<icon>\n\t\t\t\t<mimetype>image/gif</mimetype>\n\t\t\t\t<width>118</width>\n\t\t\t\t<height>119</height>\n\t\t\t\t<depth>8</depth>\n\t\t\t\t<url>/ligd.gif</url>\n\t\t\t</icon>\n\t\t</iconList>\n\t\t<serviceList>\n\t\t\t<service>\n\t\t\t\t<serviceType>urn:schemas-microsoft-com:service:OSInfo:1</serviceType>\n\t\t\t\t<serviceId>urn:microsoft-com:serviceId:OSInfo1</serviceId>\n\t\t\t\t<controlURL>/soap.cgi?service=OSInfo1</controlURL>\n\t\t\t\t<eventSubURL>/gena.cgi?service=OSInfo1</eventSubURL>\n\t\t\t\t<SCPDURL>/OSInfo.xml</SCPDURL>\n\t\t\t</service>\n\t\t\t<service>\n\t\t\t\t<serviceType>urn:schemas-upnp-org:service:Layer3Forwarding:1</serviceType>\n\t\t\t\t<serviceId>urn:upnp-org:serviceId:L3Forwarding1</serviceId>\n\t\t\t\t<controlURL>/soap.cgi?service=L3Forwarding1</controlURL>\n\t\t\t\t<eventSubURL>/gena.cgi?service=L3Forwarding1</eventSubURL>\n\t\t\t\t<SCPDURL>/Layer3Forwarding.xml</SCPDURL>\n\t\t\t</service>\n\t\t</serviceList>\n\t\t<deviceList>\n\t\t\t<device>\n\t\t\t\t<deviceType>urn:schemas-upnp-org:device:WANDevice:1</deviceType>\n\t\t\t\t<friendlyName>WANDevice</friendlyName>\n\t\t\t\t<manufacturer>D-Link</manufacturer>\n\t\t\t\t<manufacturerURL>http://www.dlink.com</manufacturerURL>\n\t\t\t\t<modelDescription>WANDevice</modelDescription>\n\t\t\t\t<modelName>DIR-890L</modelName>\n\t\t\t\t<modelNumber>1</modelNumber>\n\t\t\t\t<modelURL>http://www.dlink.com</modelURL>\n\t\t\t\t<serialNumber>120</serialNumber>\n\t\t\t\t<UDN>uuid:11111111-2222-3333-4444-555555555555</UDN>\n\t\t\t\t<serviceList>\n\t\t\t\t\t<service>\n\t\t\t\t\t\t<serviceType>urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1</serviceType>\n\t\t\t\t\t\t<serviceId>urn:upnp-org:serviceId:WANCommonIFC1</serviceId>\n\t\t\t\t\t\t<controlURL>/soap.cgi?service=WANCommonIFC1</controlURL>\n\t\t\t\t\t\t<eventSubURL>/gena.cgi?service=WANCommonIFC1</eventSubURL>\n\t\t\t\t\t\t<SCPDURL>/WANCommonInterfaceConfig.xml</SCPDURL>\n\t\t\t\t\t</service>\n\t\t\t\t</serviceList>\n\t\t\t\t<deviceList>\n\t\t\t\t\t<device>\n\t\t\t\t\t\t<deviceType>urn:schemas-upnp-org:device:WANConnectionDevice:1</deviceType>\n\t\t\t\t\t\t<friendlyName>WANConnectionDevice</friendlyName>\n\t\t\t\t\t\t<manufacturer>D-Link</manufacturer>\n\t\t\t\t\t\t<manufacturerURL>http://www.dlink.com</manufacturerURL>\n\t\t\t\t\t\t<modelDescription>WanConnectionDevice</modelDescription>\n\t\t\t\t\t\t<modelName>DIR-890L</modelName>\n\t\t\t\t\t\t<modelNumber>1</modelNumber>\n\t\t\t\t\t\t<modelURL>http://www.dlink.com</modelURL>\n\t\t\t\t\t\t<serialNumber>120</serialNumber>\n\t\t\t\t\t\t<UDN>uuid:11111111-2222-3333-4444-555555555555</UDN>\n\t\t\t\t\t\t<serviceList>\n\t\t\t\t\t\t\t<service>\n\t\t\t\t\t\t\t\t<serviceType>urn:schemas-upnp-org:service:WANEthernetLinkConfig:1</serviceType>\n\t\t\t\t\t\t\t\t<serviceId>urn:upnp-org:serviceId:WANEthLinkC1</serviceId>\n\t\t\t\t\t\t\t\t<controlURL>/soap.cgi?service=WANEthLinkC1</controlURL>\n\t\t\t\t\t\t\t\t<eventSubURL>/gena.cgi?service=WANEthLinkC1</eventSubURL>\n\t\t\t\t\t\t\t\t<SCPDURL>/WANEthernetLinkConfig.xml</SCPDURL>\n\t\t\t\t\t\t\t</service>\n\t\t\t\t\t\t\t<service>\n\t\t\t\t\t\t\t\t<serviceType>urn:schemas-upnp-org:service:WANIPConnection:1</serviceType>\n\t\t\t\t\t\t\t\t<serviceId>urn:upnp-org:serviceId:WANIPConn1</serviceId>\n\t\t\t\t\t\t\t\t<controlURL>/soap.cgi?service=WANIPConn1</controlURL>\n\t\t\t\t\t\t\t\t<eventSubURL>/gena.cgi?service=WANIPConn1</eventSubURL>\n\t\t\t\t\t\t\t\t<SCPDURL>/WANIPConnection.xml</SCPDURL>\n\t\t\t\t\t\t\t</service>\n\t\t\t\t\t\t</serviceList>\n\t\t\t\t\t</device>\n\t\t\t\t</deviceList>\n\t\t\t</device>\n\t\t</deviceList>\n\t\t<presentationURL>http://10.0.0.1</presentationURL>\n\t</device>\n</root>\n",
        b'GET /OSInfo.xml HTTP/1.1\r\nAccept-Encoding: gzip\r\nHost: 10.0.0.1\r\nConnection: Close\r\n\r\n': b"HTTP/1.1 200 OK\r\nServer: WebServer\r\nDate: Thu, 11 Oct 2018 22:16:16 GMT\r\nContent-Type: text/xml\r\nContent-Length: 219\r\nLast-Modified: Thu, 09 Aug 2018 12:41:07 GMT\r\nConnection: close\r\n\r\n<?xml version=\"1.0\"?>\n<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\">\n\t<specVersion>\n\t\t<major>1</major>\n\t\t<minor>0</minor>\n\t</specVersion>\n\t<actionList>\n\t</actionList>\n\t<serviceStateTable>\n\t</serviceStateTable>\n</scpd>\n",
        b'GET /Layer3Forwarding.xml HTTP/1.1\r\nAccept-Encoding: gzip\r\nHost: 10.0.0.1\r\nConnection: Close\r\n\r\n': b"HTTP/1.1 200 OK\r\nServer: WebServer\r\nDate: Thu, 11 Oct 2018 22:16:16 GMT\r\nContent-Type: text/xml\r\nContent-Length: 920\r\nLast-Modified: Thu, 09 Aug 2018 12:41:07 GMT\r\nConnection: close\r\n\r\n<?xml version=\"1.0\"?>\n<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\">\n\t<specVersion>\n\t\t<major>1</major>\n\t\t<minor>0</minor>\n\t</specVersion>\n\t<actionList>\n\t\t<action>\n\t\t\t<name>GetDefaultConnectionService</name>\n\t\t\t<argumentList>\n\t\t\t\t<argument>\n\t\t\t\t\t<name>NewDefaultConnectionService</name>\n\t\t\t\t\t<direction>out</direction>\n\t\t\t\t\t<relatedStateVariable>DefaultConnectionService</relatedStateVariable>\n\t\t\t\t</argument>\n\t\t\t</argumentList>\n\t\t</action>\n\t\t<action>\n\t\t\t<name>SetDefaultConnectionService</name>\n\t\t\t<argumentList>\n\t\t\t\t<argument>\n\t\t\t\t\t<name>NewDefaultConnectionService</name>\n\t\t\t\t\t<direction>in</direction>\n\t\t\t\t\t<relatedStateVariable>DefaultConnectionService</relatedStateVariable>\n\t\t\t\t</argument>\n\t\t\t</argumentList>\n\t\t</action>\n\t</actionList>\n\t<serviceStateTable>\n\t\t<stateVariable sendEvents=\"yes\">\n\t\t\t<name>DefaultConnectionService</name>\n\t\t\t<dataType>string</dataType>\n\t\t</stateVariable>\n\t</serviceStateTable>\n</scpd>\n",
        b'GET /WANCommonInterfaceConfig.xml HTTP/1.1\r\nAccept-Encoding: gzip\r\nHost: 10.0.0.1\r\nConnection: Close\r\n\r\n': b"HTTP/1.1 200 OK\r\nServer: WebServer\r\nDate: Thu, 11 Oct 2018 22:16:16 GMT\r\nContent-Type: text/xml\r\nContent-Length: 5343\r\nLast-Modified: Thu, 09 Aug 2018 12:41:07 GMT\r\nConnection: close\r\n\r\n<?xml version=\"1.0\"?>\r\n<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\">\r\n\t<specVersion>\r\n\t\t<major>1</major>\r\n\t\t<minor>0</minor>\r\n\t</specVersion>\r\n\t<actionList>\r\n\t\t<action>\r\n\t\t\t<name>GetCommonLinkProperties</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewWANAccessType</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>WANAccessType</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewLayer1UpstreamMaxBitRate</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>Layer1UpstreamMaxBitRate</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewLayer1DownstreamMaxBitRate</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>Layer1DownstreamMaxBitRate</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewPhysicalLinkStatus</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PhysicalLinkStatus</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetTotalBytesSent</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewTotalBytesSent</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalBytesSent</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetTotalBytesReceived</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewTotalBytesReceived</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalBytesReceived</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetTotalPacketsSent</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewTotalPacketsSent</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalPacketsSent</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetTotalPacketsReceived</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewTotalPacketsReceived</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalPacketsReceived</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>X_GetICSStatistics</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>TotalBytesSent</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalBytesSent</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>TotalBytesReceived</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalBytesReceived</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>TotalPacketsSent</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalPacketsSent</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>TotalPacketsReceived</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalPacketsReceived</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>Layer1DownstreamMaxBitRate</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>Layer1DownstreamMaxBitRate</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>Uptime</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>X_Uptime</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t</actionList>\r\n\t<serviceStateTable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>WANAccessType</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t\t<allowedValueList>\r\n\t\t\t\t<allowedValue>DSL</allowedValue>\r\n\t\t\t\t<allowedValue>POTS</allowedValue>\r\n\t\t\t\t<allowedValue>Cable</allowedValue>\r\n\t\t\t\t<allowedValue>Ethernet</allowedValue>\r\n\t\t\t\t<allowedValue>Other</allowedValue>\r\n\t\t\t</allowedValueList>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>Layer1UpstreamMaxBitRate</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>Layer1DownstreamMaxBitRate</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"yes\">\r\n\t\t\t<name>PhysicalLinkStatus</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t\t<allowedValueList>\r\n\t\t\t\t<allowedValue>Up</allowedValue>\r\n\t\t\t\t<allowedValue>Down</allowedValue>\r\n\t\t\t\t<allowedValue>Initializing</allowedValue>\r\n\t\t\t\t<allowedValue>Unavailable</allowedValue>\r\n\t\t\t</allowedValueList>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>WANAccessProvider</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>MaximumActiveConnections</name>\r\n\t\t\t<dataType>ui2</dataType>\r\n\t\t\t<allowedValueRange>\r\n\t\t\t\t<minimum>1</minimum>\r\n\t\t\t\t<maximum></maximum>\r\n\t\t\t\t<step>1</step>\r\n\t\t\t</allowedValueRange>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>TotalBytesSent</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>TotalBytesReceived</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>TotalPacketsSent</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>TotalPacketsReceived</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>X_PersonalFirewallEnabled</name>\r\n\t\t\t<dataType>boolean</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>X_Uptime</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t</stateVariable>\r\n\t</serviceStateTable>\r\n</scpd>\r\n",
        b'GET /WANEthernetLinkConfig.xml HTTP/1.1\r\nAccept-Encoding: gzip\r\nHost: 10.0.0.1\r\nConnection: Close\r\n\r\n': b"HTTP/1.1 200 OK\r\nServer: WebServer\r\nDate: Thu, 11 Oct 2018 22:16:16 GMT\r\nContent-Type: text/xml\r\nContent-Length: 773\r\nLast-Modified: Thu, 09 Aug 2018 12:41:07 GMT\r\nConnection: close\r\n\r\n<?xml version=\"1.0\"?>\n<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\">\n\t<specVersion>\n\t\t<major>1</major>\n\t\t<minor>0</minor>\n\t</specVersion>\n\t<actionList>\n\t\t<action>\n\t\t\t<name>GetEthernetLinkStatus</name>\n\t\t\t<argumentList>\n\t\t\t\t<argument>\n\t\t\t\t\t<name>NewEthernetLinkStatus</name>\n\t\t\t\t\t<direction>out</direction>\n\t\t\t\t\t<relatedStateVariable>EthernetLinkStatus</relatedStateVariable>\n\t\t\t\t</argument>\n\t\t\t</argumentList>\n\t\t</action>\n\t</actionList>\n\t<serviceStateTable>\n\t\t<stateVariable sendEvents=\"yes\">\n\t\t\t<name>EthernetLinkStatus</name>\n\t\t\t<dataType>string</dataType>\n\t\t\t<allowedValueList>\n\t\t\t\t<allowedValue>Up</allowedValue>\n\t\t\t\t<allowedValue>Down</allowedValue>\n\t\t\t\t<allowedValue>Unavailable</allowedValue>\n\t\t\t</allowedValueList>\n\t\t</stateVariable>\n\t</serviceStateTable>\n</scpd>\n",
        b'GET /WANIPConnection.xml HTTP/1.1\r\nAccept-Encoding: gzip\r\nHost: 10.0.0.1\r\nConnection: Close\r\n\r\n': b"HTTP/1.1 200 OK\r\nServer: WebServer\r\nDate: Thu, 11 Oct 2018 22:16:16 GMT\r\nContent-Type: text/xml\r\nContent-Length: 12078\r\nLast-Modified: Thu, 09 Aug 2018 12:41:07 GMT\r\nConnection: close\r\n\r\n<?xml version=\"1.0\"?>\r\n<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\">\r\n\t<specVersion>\r\n\t\t<major>1</major>\r\n\t\t<minor>0</minor>\r\n\t</specVersion>\r\n\t<actionList>\r\n\t\t<action>\r\n\t\t\t<name>SetConnectionType</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewConnectionType</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>ConnectionType</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action> \r\n\t\t<action>\r\n\t\t\t<name>GetConnectionTypeInfo</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewConnectionType</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>ConnectionType</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewPossibleConnectionTypes</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PossibleConnectionTypes</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>RequestConnection</name>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>ForceTermination</name>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetStatusInfo</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewConnectionStatus</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>ConnectionStatus</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewLastConnectionError</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>LastConnectionError</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewUptime</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>Uptime</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetNATRSIPStatus</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewRSIPAvailable</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>RSIPAvailable</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewNATEnabled</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>NATEnabled</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetGenericPortMappingEntry</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewPortMappingIndex</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingNumberOfEntries</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewRemoteHost</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>RemoteHost</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewExternalPort</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>ExternalPort</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewProtocol</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingProtocol</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewInternalPort</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>InternalPort</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewInternalClient</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>InternalClient</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewEnabled</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingEnabled</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewPortMappingDescription</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingDescription</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewLeaseDuration</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingLeaseDuration</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetSpecificPortMappingEntry</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewRemoteHost</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>RemoteHost</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewExternalPort</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>ExternalPort</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewProtocol</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingProtocol</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewInternalPort</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>InternalPort</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewInternalClient</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>InternalClient</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewEnabled</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingEnabled</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewPortMappingDescription</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingDescription</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewLeaseDuration</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingLeaseDuration</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>AddPortMapping</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewRemoteHost</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>RemoteHost</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewExternalPort</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>ExternalPort</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewProtocol</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingProtocol</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewInternalPort</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>InternalPort</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewInternalClient</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>InternalClient</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewEnabled</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingEnabled</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewPortMappingDescription</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingDescription</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewLeaseDuration</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingLeaseDuration</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>DeletePortMapping</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewRemoteHost</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>RemoteHost</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewExternalPort</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>ExternalPort</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewProtocol</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingProtocol</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetExternalIPAddress</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewExternalIPAddress</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>ExternalIPAddress</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t</actionList>\r\n\t<serviceStateTable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>ConnectionType</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t\t<defaultValue>Unconfigured</defaultValue>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"yes\">\r\n\t\t\t<name>PossibleConnectionTypes</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t\t<allowedValueList>\r\n\t\t\t\t<allowedValue>Unconfigured</allowedValue>\r\n\t\t\t\t<allowedValue>IP_Routed</allowedValue>\r\n\t\t\t\t<allowedValue>IP_Bridged</allowedValue>\r\n\t\t\t</allowedValueList>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"yes\">\r\n\t\t\t<name>ConnectionStatus</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t\t<defaultValue>Unconfigured</defaultValue>\r\n\t\t\t<allowedValueList>\r\n\t\t\t\t<allowedValue>Unconfigured</allowedValue>\r\n\t\t\t\t<allowedValue>Connecting</allowedValue>\r\n\t\t\t\t<allowedValue>Authenticating</allowedValue>\r\n\t\t\t\t<allowedValue>PendingDisconnect</allowedValue>\r\n\t\t\t\t<allowedValue>Disconnecting</allowedValue>\r\n\t\t\t\t<allowedValue>Disconnected</allowedValue>\r\n\t\t\t\t<allowedValue>Connected</allowedValue>\r\n\t\t\t</allowedValueList>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>Uptime</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t\t<defaultValue>0</defaultValue>\r\n\t\t\t<allowedValueRange>\r\n\t\t\t\t<minimum>0</minimum>\r\n\t\t\t\t<maximum></maximum>\r\n\t\t\t\t<step>1</step>\r\n\t\t\t</allowedValueRange>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>RSIPAvailable</name>\r\n\t\t<dataType>boolean</dataType>\r\n\t\t\t<defaultValue>0</defaultValue>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>NATEnabled</name>\r\n\t\t\t<dataType>boolean</dataType>\r\n\t\t\t<defaultValue>1</defaultValue>\r\n\t\t</stateVariable>  \r\n\t\t<stateVariable sendEvents=\"yes\">\r\n\t\t\t<name>X_Name</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>LastConnectionError</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t\t<defaultValue>ERROR_NONE</defaultValue>\r\n\t\t\t<allowedValueList>\r\n\t\t\t\t<allowedValue>ERROR_NONE</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_ISP_TIME_OUT</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_COMMAND_ABORTED</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_NOT_ENABLED_FOR_INTERNET</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_BAD_PHONE_NUMBER</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_USER_DISCONNECT</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_ISP_DISCONNECT</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_IDLE_DISCONNECT</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_FORCED_DISCONNECT</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_SERVER_OUT_OF_RESOURCES</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_RESTRICTED_LOGON_HOURS</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_ACCOUNT_DISABLED</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_ACCOUNT_EXPIRED</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_PASSWORD_EXPIRED</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_AUTHENTICATION_FAILURE</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_NO_DIALTONE</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_NO_CARRIER</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_NO_ANSWER</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_LINE_BUSY</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_UNSUPPORTED_BITSPERSECOND</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_TOO_MANY_LINE_ERRORS</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_IP_CONFIGURATION</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_UNKNOWN</allowedValue>\r\n\t\t\t</allowedValueList>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"yes\">\r\n\t\t\t<name>ExternalIPAddress</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>RemoteHost</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>ExternalPort</name>\r\n\t\t\t<dataType>ui2</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>InternalPort</name>\r\n\t\t\t<dataType>ui2</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>PortMappingProtocol</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t\t<allowedValueList>\r\n\t\t\t\t<allowedValue>TCP</allowedValue>\r\n\t\t\t\t<allowedValue>UDP</allowedValue>\r\n\t\t\t</allowedValueList>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>InternalClient</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>PortMappingDescription</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>PortMappingEnabled</name>\r\n\t\t\t<dataType>boolean</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>PortMappingLeaseDuration</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents=\"yes\">\r\n\t\t\t<name>PortMappingNumberOfEntries</name>\r\n\t\t\t<dataType>ui2</dataType>\r\n\t\t</stateVariable>\r\n\t</serviceStateTable>\r\n</scpd>\r\n",
        b'POST /soap.cgi?service=WANIPConn1 HTTP/1.1\r\nHost: 10.0.0.1\r\nUser-Agent: python3/aioupnp, UPnP/1.0, MiniUPnPc/1.9\r\nContent-Length: 285\r\nContent-Type: text/xml\r\nSOAPAction: "urn:schemas-upnp-org:service:WANIPConnection:1#GetExternalIPAddress"\r\nConnection: Close\r\nCache-Control: no-cache\r\nPragma: no-cache\r\n\r\n<?xml version="1.0"?>\r\n<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body><u:GetExternalIPAddress xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1"></u:GetExternalIPAddress></s:Body></s:Envelope>\r\n': b"HTTP/1.1 200 OK\r\nCONTENT-LENGTH: 340\r\nCONTENT-TYPE: text/xml; charset=\"utf-8\"\r\nDATE: Thu, 18 Oct 2018 01:20:23 GMT\r\nEXT:\r\nSERVER: Linux/3.14.28-Prod_17.2, UPnP/1.0, Portable SDK for UPnP devices/1.6.22\r\nX-User-Agent: redsonic\r\n\r\n<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"><s:Body>\n<u:GetExternalIPAddressResponse xmlns:u=\"urn:schemas-upnp-org:service:WANIPConnection:1\">\r\n<NewExternalIPAddress>11.22.33.44</NewExternalIPAddress>\r\n</u:GetExternalIPAddressResponse>\r\n</s:Body> </s:Envelope>"
    }

    packet_args = list(packet_generator())
    byte_packets = [SSDPDatagram("M-SEARCH", p).encode().encode() for p in packet_args]

    successful_args = OrderedDict([
        ("HOST", "239.255.255.250:1900"),
        ("MAN", "ssdp:discover"),
        ("MX", 1),
        ("ST", "urn:schemas-upnp-org:device:WANDevice:1")
    ])
    query_packet = SSDPDatagram("M-SEARCH", successful_args)

    reply_args = OrderedDict([
        ("CACHE_CONTROL", "max-age=1800"),
        ("LOCATION", "http://10.0.0.1:49152/InternetGatewayDevice.xml"),
        ("SERVER", "Linux, UPnP/1.0, DIR-890L Ver 1.20"),
        ("ST", "urn:schemas-upnp-org:device:WANDevice:1"),
        ("USN", "uuid:22222222-3333-4444-5555-666666666666::urn:schemas-upnp-org:device:WANDevice:1")
    ])
    reply_packet = SSDPDatagram("OK", reply_args)

    udp_replies = {
        (query_packet.encode().encode(), ("10.0.0.1", 1900)): reply_packet.encode().encode()
    }

    def test_get_external_ip(self):
        actual_output = StringIO()
        with contextlib.redirect_stdout(actual_output):
            with mock_tcp_and_udp(self.loop, '10.0.0.1', tcp_replies=self.scpd_replies, udp_replies=self.udp_replies):
                main(
                    [None, '--timeout=1', '--gateway_address=10.0.0.1', '--lan_address=10.0.0.2', 'get-external-ip'],
                    self.loop
                )
        self.assertEqual("11.22.33.44\n", actual_output.getvalue())

    def test_m_search(self):
        actual_output = StringIO()
        timeout_msg = "aioupnp encountered an error: M-SEARCH for 10.0.0.1:1900 timed out\n"
        with contextlib.redirect_stdout(actual_output):
            with mock_tcp_and_udp(self.loop, '10.0.0.1', tcp_replies={}, udp_replies={}):
                main(
                    [None, '--timeout=1', '--gateway_address=10.0.0.1', '--lan_address=10.0.0.2', 'm-search'],
                    self.loop
                )
        self.assertEqual(timeout_msg, actual_output.getvalue())

        actual_output = StringIO()
        with contextlib.redirect_stdout(actual_output):
            with mock_tcp_and_udp(self.loop, '10.0.0.1', tcp_replies=self.scpd_replies, udp_replies=self.udp_replies):
                main(
                    [None, '--timeout=1', '--gateway_address=10.0.0.1', '--lan_address=10.0.0.2', 'm-search'],
                    self.loop
                )
        self.assertEqual(m_search_cli_result, actual_output.getvalue())

    def test_usage(self):
        actual_output = StringIO()
        with contextlib.redirect_stdout(actual_output):
            main(
                [None, 'help'],
                self.loop
            )
        self.assertEqual(expected_usage, actual_output.getvalue())

        actual_output = StringIO()
        with contextlib.redirect_stdout(actual_output):
            main(
                [None, 'help', 'test'],
                self.loop
            )
        self.assertEqual(expected_usage, actual_output.getvalue())

        actual_output = StringIO()
        with contextlib.redirect_stdout(actual_output):
            main(
                [None, 'test', 'help'],
                self.loop
            )
        self.assertEqual("aioupnp encountered an error: \"test\" is not a recognized command\n", actual_output.getvalue())

        actual_output = StringIO()
        with contextlib.redirect_stdout(actual_output):
            main(
                [None, 'test'],
                self.loop
            )
        self.assertEqual("aioupnp encountered an error: \"test\" is not a recognized command\n", actual_output.getvalue())

        actual_output = StringIO()
        with contextlib.redirect_stdout(actual_output):
            main(
                [None],
                self.loop
            )
        self.assertEqual(expected_usage, actual_output.getvalue())

        actual_output = StringIO()
        with contextlib.redirect_stdout(actual_output):
            main(
                [None, "--something=test"],
                self.loop
            )
        self.assertEqual("no command given\n" + expected_usage, actual_output.getvalue())

    def test_commands_help(self):
        actual_output = StringIO()
        with contextlib.redirect_stdout(actual_output):
            main(
                [None, 'help', 'm-search'],
                self.loop
            )
        self.assertEqual(m_search_help_msg, actual_output.getvalue())

        actual_output = StringIO()
        with contextlib.redirect_stdout(actual_output):
            main(
                [None, 'help', 'get-external-ip'],
                self.loop
            )

        self.assertEqual(expected_get_external_ip_usage, actual_output.getvalue())

        actual_output = StringIO()
        with contextlib.redirect_stdout(actual_output):
            main(
                [None, 'help', 'add-port-mapping'],
                self.loop
            )
        self.assertEqual(expected_add_port_mapping_usage, actual_output.getvalue())
        actual_output = StringIO()
        with contextlib.redirect_stdout(actual_output):
            main(
                [None, 'help', 'get-next-mapping'],
                self.loop
            )
        self.assertEqual(expected_get_next_mapping_usage, actual_output.getvalue())

        actual_output = StringIO()
        with contextlib.redirect_stdout(actual_output):
            main(
                [None, 'help', 'delete_port_mapping'],
                self.loop
            )
        self.assertEqual(expected_delete_port_mapping_usage, actual_output.getvalue())

        actual_output = StringIO()
        with contextlib.redirect_stdout(actual_output):
            main(
                [None, 'help', 'get_specific_port_mapping'],
                self.loop
            )
        self.assertEqual(expected_get_specific_port_mapping_usage, actual_output.getvalue())

        actual_output = StringIO()
        with contextlib.redirect_stdout(actual_output):
            main(
                [None, 'help', 'get_redirects'],
                self.loop
            )
        self.assertEqual(expected_get_redirects_usage, actual_output.getvalue())

        actual_output = StringIO()
        with contextlib.redirect_stdout(actual_output):
            main(
                [None, 'help', 'get_port_mapping_by_index'],
                self.loop
            )
        self.assertEqual(expected_get_port_mapping_by_index_usage, actual_output.getvalue())
