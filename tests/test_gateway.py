from aioupnp.fault import UPnPError
from tests import TestBase
from tests.mocks import mock_tcp_and_udp
from collections import OrderedDict
from aioupnp.gateway import Gateway
from aioupnp.serialization.ssdp import SSDPDatagram


def gen_get_bytes(location: str, host: str) -> bytes:
    return '\r\n'.join([
        f'GET {location} HTTP/1.1',
        "Accept-Encoding: gzip",
        f'Host: {host}',
        "Connection: Close",
    ]).encode()


class TestDiscoverDLinkDIR890L(TestBase):
    gateway_address = "10.0.0.1"
    client_address = "10.0.0.2"
    soap_port = 49152

    m_search_args = OrderedDict([
        ("HOST", "239.255.255.250:1900"),
        ("MAN", "ssdp:discover"),
        ("MX", 1),
        ("ST", "urn:schemas-upnp-org:device:WANDevice:1")
    ])

    reply = SSDPDatagram("OK", **OrderedDict([
        ("CACHE_CONTROL", "max-age=1800"),
        ("LOCATION", "http://10.0.0.1:49152/InternetGatewayDevice.xml"),
        ("SERVER", "Linux, UPnP/1.0, DIR-890L Ver 1.20"),
        ("ST", "urn:schemas-upnp-org:device:WANDevice:1"),
        ("USN", "uuid:11111111-2222-3333-4444-555555555555::urn:schemas-upnp-org:device:WANDevice:1")
    ]))

    # TODO: make generator for xml samples.
    replies = {
        b'GET /InternetGatewayDevice.xml HTTP/1.1\r\nAccept-Encoding: gzip\r\nHost: 10.0.0.1\r\nConnection: '
        b'Close\r\n\r\n':
            b"HTTP/1.1 200 OK\r\nServer: WebServer\r\nDate: Thu, 11 Oct 2018 22:16:16 "
            b"GMT\r\nContent-Type: text/xml\r\nContent-Length: 3921\r\nLast-Modified: Thu, 09 Aug 2018 "
            b"12:41:07 GMT\r\nConnection: close\r\n\r\n<?xml version=\"1.0\"?>\n<root "
            b"xmlns=\"urn:schemas-upnp-org:device-1-0\">\n\t<specVersion>\n\t\t<major>1</major>\n\t\t"
            b"<minor>0</minor>\n\t</specVersion>\n\t<URLBase>http://10.0.0.1:49152</URLBase>\n\t<device"
            b">\n\t\t<deviceType>urn:schemas-upnp-org:device:InternetGatewayDevice:1</deviceType>\n\t\t"
            b"<friendlyName>Wireless Broadband Router</friendlyName>\n\t\t<manufacturer>D-Link "
            b"Corporation</manufacturer>\n\t\t<manufacturerURL>http://www.dlink.com</manufacturerURL>\n"
            b"\t\t<modelDescription>D-Link Router</modelDescription>\n\t\t<modelName>D-Link "
            b"Router</modelName>\n\t\t<modelNumber>DIR-890L</modelNumber>\n\t\t<modelURL>http://www"
            b".dlink.com</modelURL>\n\t\t<serialNumber>120</serialNumber>\n\t\t<UDN>uuid:11111111-2222"
            b"-3333-4444-555555555555</UDN>\n\t\t<iconList>\n\t\t\t<icon>\n\t\t\t\t<mimetype>image/gif"
            b"</mimetype>\n\t\t\t\t<width>118</width>\n\t\t\t\t<height>119</height>\n\t\t\t\t<depth>8"
            b"</depth>\n\t\t\t\t<url>/ligd.gif</url>\n\t\t\t</icon>\n\t\t</iconList>\n\t\t<serviceList"
            b">\n\t\t\t<service>\n\t\t\t\t<serviceType>urn:schemas-microsoft-com:service:OSInfo:1"
            b"</serviceType>\n\t\t\t\t<serviceId>urn:microsoft-com:serviceId:OSInfo1</serviceId>\n\t\t"
            b"\t\t<controlURL>/soap.cgi?service=OSInfo1</controlURL>\n\t\t\t\t<eventSubURL>/gena.cgi"
            b"?service=OSInfo1</eventSubURL>\n\t\t\t\t<SCPDURL>/OSInfo.xml</SCPDURL>\n\t\t\t</service"
            b">\n\t\t\t<service>\n\t\t\t\t<serviceType>urn:schemas-upnp-org:service:Layer3Forwarding:1"
            b"</serviceType>\n\t\t\t\t<serviceId>urn:upnp-org:serviceId:L3Forwarding1</serviceId>\n\t\t"
            b"\t\t<controlURL>/soap.cgi?service=L3Forwarding1</controlURL>\n\t\t\t\t<eventSubURL>/gena"
            b".cgi?service=L3Forwarding1</eventSubURL>\n\t\t\t\t<SCPDURL>/Layer3Forwarding.xml</SCPDURL"
            b">\n\t\t\t</service>\n\t\t</serviceList>\n\t\t<deviceList>\n\t\t\t<device>\n\t\t\t\t"
            b"<deviceType>urn:schemas-upnp-org:device:WANDevice:1</deviceType>\n\t\t\t\t<friendlyName"
            b">WANDevice</friendlyName>\n\t\t\t\t<manufacturer>D-Link</manufacturer>\n\t\t\t\t"
            b"<manufacturerURL>http://www.dlink.com</manufacturerURL>\n\t\t\t\t<modelDescription"
            b">WANDevice</modelDescription>\n\t\t\t\t<modelName>DIR-890L</modelName>\n\t\t\t\t"
            b"<modelNumber>1</modelNumber>\n\t\t\t\t<modelURL>http://www.dlink.com</modelURL>\n\t\t\t\t"
            b"<serialNumber>120</serialNumber>\n\t\t\t\t<UDN>uuid:11111111-2222-3333-4444-555555555555"
            b"</UDN>\n\t\t\t\t<serviceList>\n\t\t\t\t\t<service>\n\t\t\t\t\t\t<serviceType>urn:schemas"
            b"-upnp-org:service:WANCommonInterfaceConfig:1</serviceType>\n\t\t\t\t\t\t<serviceId>urn"
            b":upnp-org:serviceId:WANCommonIFC1</serviceId>\n\t\t\t\t\t\t<controlURL>/soap.cgi?service"
            b"=WANCommonIFC1</controlURL>\n\t\t\t\t\t\t<eventSubURL>/gena.cgi?service=WANCommonIFC1"
            b"</eventSubURL>\n\t\t\t\t\t\t<SCPDURL>/WANCommonInterfaceConfig.xml</SCPDURL>\n\t\t\t\t\t"
            b"</service>\n\t\t\t\t</serviceList>\n\t\t\t\t<deviceList>\n\t\t\t\t\t<device>\n\t\t\t\t\t"
            b"\t<deviceType>urn:schemas-upnp-org:device:WANConnectionDevice:1</deviceType>\n\t\t\t\t\t"
            b"\t<friendlyName>WANConnectionDevice</friendlyName>\n\t\t\t\t\t\t<manufacturer>D-Link"
            b"</manufacturer>\n\t\t\t\t\t\t<manufacturerURL>http://www.dlink.com</manufacturerURL>\n\t"
            b"\t\t\t\t\t<modelDescription>WanConnectionDevice</modelDescription>\n\t\t\t\t\t\t"
            b"<modelName>DIR-890L</modelName>\n\t\t\t\t\t\t<modelNumber>1</modelNumber>\n\t\t\t\t\t\t"
            b"<modelURL>http://www.dlink.com</modelURL>\n\t\t\t\t\t\t<serialNumber>120</serialNumber>\n"
            b"\t\t\t\t\t\t<UDN>uuid:11111111-2222-3333-4444-555555555555</UDN>\n\t\t\t\t\t\t"
            b"<serviceList>\n\t\t\t\t\t\t\t<service>\n\t\t\t\t\t\t\t\t<serviceType>urn:schemas-upnp-org"
            b":service:WANEthernetLinkConfig:1</serviceType>\n\t\t\t\t\t\t\t\t<serviceId>urn:upnp-org"
            b":serviceId:WANEthLinkC1</serviceId>\n\t\t\t\t\t\t\t\t<controlURL>/soap.cgi?service"
            b"=WANEthLinkC1</controlURL>\n\t\t\t\t\t\t\t\t<eventSubURL>/gena.cgi?service=WANEthLinkC1"
            b"</eventSubURL>\n\t\t\t\t\t\t\t\t<SCPDURL>/WANEthernetLinkConfig.xml</SCPDURL>\n\t\t\t\t\t"
            b"\t\t</service>\n\t\t\t\t\t\t\t<service>\n\t\t\t\t\t\t\t\t<serviceType>urn:schemas-upnp"
            b"-org:service:WANIPConnection:1</serviceType>\n\t\t\t\t\t\t\t\t<serviceId>urn:upnp-org"
            b":serviceId:WANIPConn1</serviceId>\n\t\t\t\t\t\t\t\t<controlURL>/soap.cgi?service"
            b"=WANIPConn1</controlURL>\n\t\t\t\t\t\t\t\t<eventSubURL>/gena.cgi?service=WANIPConn1"
            b"</eventSubURL>\n\t\t\t\t\t\t\t\t<SCPDURL>/WANIPConnection.xml</SCPDURL>\n\t\t\t\t\t\t\t"
            b"</service>\n\t\t\t\t\t\t</serviceList>\n\t\t\t\t\t</device>\n\t\t\t\t</deviceList>\n\t\t"
            b"\t</device>\n\t\t</deviceList>\n\t\t<presentationURL>http://10.0.0.1</presentationURL>\n"
            b"\t</device>\n</root>\n",
        b'GET /OSInfo.xml HTTP/1.1\r\nAccept-Encoding: gzip\r\nHost: 10.0.0.1\r\n'
        b'Connection: Close\r\n\r\n':
            b"HTTP/1.1 200 OK\r\nServer: WebServer\r\nDate: Thu, 11 Oct 2018 22:16:16 GMT\r\nContent-Type: "
            b"text/xml\r\nContent-Length: 219\r\nLast-Modified: Thu, 09 Aug 2018 12:41:07 GMT\r\nConnection: "
            b"close\r\n\r\n<?xml version=\"1.0\"?>\n<scpd "
            b"xmlns=\"urn:schemas-upnp-org:service-1-0\">\n\t<specVersion>\n\t\t<major>1</major>\n\t\t<minor>0</minor"
            b">\n\t</specVersion>\n\t<actionList>\n\t</actionList>\n\t<serviceStateTable>\n\t</serviceStateTable>\n"
            b"</scpd>\n",
        b'GET /Layer3Forwarding.xml HTTP/1.1\r\nAccept-Encoding: gzip\r\nHost: 10.0.0.1\r\n'
        b'Connection: Close\r\n\r\n':
            b"HTTP/1.1 200 OK\r\nServer: WebServer\r\nDate: Thu, 11 Oct 2018 22:16:16 GMT\r\nContent-Type: "
            b"text/xml\r\nContent-Length: 920\r\nLast-Modified: Thu, 09 Aug 2018 12:41:07 GMT\r\nConnection: "
            b"close\r\n\r\n<?xml version=\"1.0\"?>\n<scpd "
            b"xmlns=\"urn:schemas-upnp-org:service-1-0\">\n\t<specVersion>\n\t\t<major>1</major>\n\t\t<minor>0</minor"
            b">\n\t</specVersion>\n\t<actionList>\n\t\t<action>\n\t\t\t<name>GetDefaultConnectionService</name>\n\t\t"
            b"\t<argumentList>\n\t\t\t\t<argument>\n\t\t\t\t\t<name>NewDefaultConnectionService</name>\n\t\t\t\t\t"
            b"<direction>out</direction>\n\t\t\t\t\t<relatedStateVariable>DefaultConnectionService"
            b"</relatedStateVariable>\n\t\t\t\t</argument>\n\t\t\t</argumentList>\n\t\t</action>\n\t\t<action>\n\t\t"
            b"\t<name>SetDefaultConnectionService</name>\n\t\t\t<argumentList>\n\t\t\t\t<argument>\n\t\t\t\t\t<name"
            b">NewDefaultConnectionService</name>\n\t\t\t\t\t<direction>in</direction>\n\t\t\t\t\t"
            b"<relatedStateVariable>DefaultConnectionService</relatedStateVariable>\n\t\t\t\t</argument>\n\t\t\t"
            b"</argumentList>\n\t\t</action>\n\t</actionList>\n\t<serviceStateTable>\n\t\t<stateVariable "
            b"sendEvents=\"yes\">\n\t\t\t<name>DefaultConnectionService</name>\n\t\t\t<dataType>string</dataType>\n\t"
            b"\t</stateVariable>\n\t</serviceStateTable>\n</scpd>\n",
        b'GET /WANCommonInterfaceConfig.xml HTTP/1.1\r\nAccept-Encoding: gzip\r\nHost: 10.0.0.1\r\n'
        b'Connection: Close\r\n\r\n':
            b"HTTP/1.1 200 OK\r\nServer: WebServer\r\nDate: Thu, 11 Oct 2018 22:16:16 GMT\r\nContent-Type: "
            b"text/xml\r\nContent-Length: 5343\r\nLast-Modified: Thu, 09 Aug 2018 12:41:07 GMT\r\nConnection: "
            b"close\r\n\r\n<?xml version=\"1.0\"?>\r\n<scpd "
            b"xmlns=\"urn:schemas-upnp-org:service-1-0\">\r\n\t<specVersion>\r\n\t\t<major>1</major>\r\n\t\t<minor>0"
            b"</minor>\r\n\t</specVersion>\r\n\t<actionList>\r\n\t\t<action>\r\n\t\t\t<name>GetCommonLinkProperties"
            b"</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewWANAccessType</name>\r\n\t"
            b"\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>WANAccessType"
            b"</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name"
            b">NewLayer1UpstreamMaxBitRate</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t"
            b"<relatedStateVariable>Layer1UpstreamMaxBitRate</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t"
            b"\t<argument>\r\n\t\t\t\t\t<name>NewLayer1DownstreamMaxBitRate</name>\r\n\t\t\t\t\t<direction>out"
            b"</direction>\r\n\t\t\t\t\t<relatedStateVariable>Layer1DownstreamMaxBitRate</relatedStateVariable>\r\n\t"
            b"\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewPhysicalLinkStatus</name>\r\n\t\t\t\t\t"
            b"<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PhysicalLinkStatus</relatedStateVariable"
            b">\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name"
            b">GetTotalBytesSent</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name"
            b">NewTotalBytesSent</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable"
            b">TotalBytesSent</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action"
            b">\r\n\t\t<action>\r\n\t\t\t<name>GetTotalBytesReceived</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t"
            b"<argument>\r\n\t\t\t\t\t<name>NewTotalBytesReceived</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n"
            b"\t\t\t\t\t<relatedStateVariable>TotalBytesReceived</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t"
            b"\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetTotalPacketsSent</name>\r\n\t\t"
            b"\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewTotalPacketsSent</name>\r\n\t\t\t\t\t"
            b"<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalPacketsSent</relatedStateVariable>\r"
            b"\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name"
            b">GetTotalPacketsReceived</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name"
            b">NewTotalPacketsReceived</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t"
            b"<relatedStateVariable>TotalPacketsReceived</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t"
            b"</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>X_GetICSStatistics</name>\r\n\t\t\t"
            b"<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>TotalBytesSent</name>\r\n\t\t\t\t\t<direction"
            b">out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalBytesSent</relatedStateVariable>\r\n\t\t\t\t"
            b"</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>TotalBytesReceived</name>\r\n\t\t\t\t\t<direction"
            b">out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalBytesReceived</relatedStateVariable>\r\n\t\t\t"
            b"\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>TotalPacketsSent</name>\r\n\t\t\t\t\t<direction"
            b">out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalPacketsSent</relatedStateVariable>\r\n\t\t\t\t"
            b"</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>TotalPacketsReceived</name>\r\n\t\t\t\t\t"
            b"<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalPacketsReceived"
            b"</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name"
            b">Layer1DownstreamMaxBitRate</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t"
            b"<relatedStateVariable>Layer1DownstreamMaxBitRate</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t"
            b"\t\t<argument>\r\n\t\t\t\t\t<name>Uptime</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t"
            b"<relatedStateVariable>X_Uptime</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r"
            b"\n\t\t</action>\r\n\t</actionList>\r\n\t<serviceStateTable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>WANAccessType</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t\t"
            b"<allowedValueList>\r\n\t\t\t\t<allowedValue>DSL</allowedValue>\r\n\t\t\t\t<allowedValue>POTS"
            b"</allowedValue>\r\n\t\t\t\t<allowedValue>Cable</allowedValue>\r\n\t\t\t\t<allowedValue>Ethernet"
            b"</allowedValue>\r\n\t\t\t\t<allowedValue>Other</allowedValue>\r\n\t\t\t</allowedValueList>\r\n\t\t"
            b"</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>Layer1UpstreamMaxBitRate</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n"
            b"\t\t</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>Layer1DownstreamMaxBitRate</name>\r\n\t\t\t<dataType>ui4</dataType>\r"
            b"\n\t\t</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"yes\">\r\n\t\t\t<name>PhysicalLinkStatus</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t"
            b"\t\t<allowedValueList>\r\n\t\t\t\t<allowedValue>Up</allowedValue>\r\n\t\t\t\t<allowedValue>Down"
            b"</allowedValue>\r\n\t\t\t\t<allowedValue>Initializing</allowedValue>\r\n\t\t\t\t<allowedValue"
            b">Unavailable</allowedValue>\r\n\t\t\t</allowedValueList>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>WANAccessProvider</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t"
            b"</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>MaximumActiveConnections</name>\r\n\t\t\t<dataType>ui2</dataType>\r\n"
            b"\t\t\t<allowedValueRange>\r\n\t\t\t\t<minimum>1</minimum>\r\n\t\t\t\t<maximum></maximum>\r\n\t\t\t\t"
            b"<step>1</step>\r\n\t\t\t</allowedValueRange>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>TotalBytesSent</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t"
            b"</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>TotalBytesReceived</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t"
            b"</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>TotalPacketsSent</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t"
            b"</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>TotalPacketsReceived</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t"
            b"</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>X_PersonalFirewallEnabled</name>\r\n\t\t\t<dataType>boolean</dataType"
            b">\r\n\t\t</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>X_Uptime</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t"
            b"</stateVariable>\r\n\t</serviceStateTable>\r\n</scpd>\r\n",
        b'GET /WANEthernetLinkConfig.xml HTTP/1.1\r\nAccept-Encoding: gzip\r\nHost: 10.0.0.1\r\n'
        b'Connection: Close\r\n\r\n':
            b"HTTP/1.1 200 OK\r\nServer: WebServer\r\nDate: Thu, 11 Oct 2018 22:16:16 GMT\r\nContent-Type: "
            b"text/xml\r\nContent-Length: 773\r\nLast-Modified: Thu, 09 Aug 2018 12:41:07 GMT\r\nConnection: "
            b"close\r\n\r\n<?xml version=\"1.0\"?>\n<scpd "
            b"xmlns=\"urn:schemas-upnp-org:service-1-0\">\n\t<specVersion>\n\t\t<major>1</major>\n\t\t<minor>0</minor"
            b">\n\t</specVersion>\n\t<actionList>\n\t\t<action>\n\t\t\t<name>GetEthernetLinkStatus</name>\n\t\t\t"
            b"<argumentList>\n\t\t\t\t<argument>\n\t\t\t\t\t<name>NewEthernetLinkStatus</name>\n\t\t\t\t\t<direction"
            b">out</direction>\n\t\t\t\t\t<relatedStateVariable>EthernetLinkStatus</relatedStateVariable>\n\t\t\t\t"
            b"</argument>\n\t\t\t</argumentList>\n\t\t</action>\n\t</actionList>\n\t<serviceStateTable>\n\t\t"
            b"<stateVariable sendEvents=\"yes\">\n\t\t\t<name>EthernetLinkStatus</name>\n\t\t\t<dataType>string"
            b"</dataType>\n\t\t\t<allowedValueList>\n\t\t\t\t<allowedValue>Up</allowedValue>\n\t\t\t\t<allowedValue"
            b">Down</allowedValue>\n\t\t\t\t<allowedValue>Unavailable</allowedValue>\n\t\t\t</allowedValueList>\n\t\t"
            b"</stateVariable>\n\t</serviceStateTable>\n</scpd>\n",
        b'GET /WANIPConnection.xml HTTP/1.1\r\nAccept-Encoding: gzip\r\nHost: 10.0.0.1\r\n'
        b'Connection: Close\r\n\r\n':
            b"HTTP/1.1 200 OK\r\nServer: WebServer\r\nDate: Thu, 11 Oct 2018 22:16:16 GMT\r\nContent-Type: "
            b"text/xml\r\nContent-Length: 12078\r\nLast-Modified: Thu, 09 Aug 2018 12:41:07 GMT\r\nConnection: "
            b"close\r\n\r\n<?xml version=\"1.0\"?>\r\n<scpd "
            b"xmlns=\"urn:schemas-upnp-org:service-1-0\">\r\n\t<specVersion>\r\n\t\t<major>1</major>\r\n\t\t<minor>0"
            b"</minor>\r\n\t</specVersion>\r\n\t<actionList>\r\n\t\t<action>\r\n\t\t\t<name>SetConnectionType</name"
            b">\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewConnectionType</name>\r\n\t\t\t\t"
            b"\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>ConnectionType</relatedStateVariable>\r"
            b"\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action> "
            b"\r\n\t\t<action>\r\n\t\t\t<name>GetConnectionTypeInfo</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t"
            b"<argument>\r\n\t\t\t\t\t<name>NewConnectionType</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t"
            b"\t\t\t<relatedStateVariable>ConnectionType</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t"
            b"<argument>\r\n\t\t\t\t\t<name>NewPossibleConnectionTypes</name>\r\n\t\t\t\t\t<direction>out</direction"
            b">\r\n\t\t\t\t\t<relatedStateVariable>PossibleConnectionTypes</relatedStateVariable>\r\n\t\t\t\t"
            b"</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>RequestConnection"
            b"</name>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>ForceTermination</name>\r\n\t\t</action>\r\n\t"
            b"\t<action>\r\n\t\t\t<name>GetStatusInfo</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t"
            b"\t\t<name>NewConnectionStatus</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t"
            b"<relatedStateVariable>ConnectionStatus</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t"
            b"<argument>\r\n\t\t\t\t\t<name>NewLastConnectionError</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n"
            b"\t\t\t\t\t<relatedStateVariable>LastConnectionError</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t"
            b"\t\t\t<argument>\r\n\t\t\t\t\t<name>NewUptime</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t"
            b"\t\t<relatedStateVariable>Uptime</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList"
            b">\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetNATRSIPStatus</name>\r\n\t\t\t<argumentList>\r\n\t"
            b"\t\t\t<argument>\r\n\t\t\t\t\t<name>NewRSIPAvailable</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n"
            b"\t\t\t\t\t<relatedStateVariable>RSIPAvailable</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t"
            b"<argument>\r\n\t\t\t\t\t<name>NewNATEnabled</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t"
            b"\t<relatedStateVariable>NATEnabled</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t"
            b"</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetGenericPortMappingEntry</name>\r\n\t"
            b"\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewPortMappingIndex</name>\r\n\t\t\t\t\t"
            b"<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingNumberOfEntries"
            b"</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewRemoteHost"
            b"</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>RemoteHost"
            b"</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewExternalPort"
            b"</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>ExternalPort"
            b"</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewProtocol"
            b"</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingProtocol"
            b"</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewInternalPort"
            b"</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>InternalPort"
            b"</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name"
            b">NewInternalClient</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable"
            b">InternalClient</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name"
            b">NewEnabled</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable"
            b">PortMappingEnabled</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t"
            b"<name>NewPortMappingDescription</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t"
            b"<relatedStateVariable>PortMappingDescription</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t"
            b"<argument>\r\n\t\t\t\t\t<name>NewLeaseDuration</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t"
            b"\t\t<relatedStateVariable>PortMappingLeaseDuration</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t"
            b"\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetSpecificPortMappingEntry</name"
            b">\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewRemoteHost</name>\r\n\t\t\t\t\t"
            b"<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>RemoteHost</relatedStateVariable>\r\n\t\t"
            b"\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewExternalPort</name>\r\n\t\t\t\t\t<direction"
            b">in</direction>\r\n\t\t\t\t\t<relatedStateVariable>ExternalPort</relatedStateVariable>\r\n\t\t\t\t"
            b"</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewProtocol</name>\r\n\t\t\t\t\t<direction>in"
            b"</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingProtocol</relatedStateVariable>\r\n\t\t\t\t"
            b"</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewInternalPort</name>\r\n\t\t\t\t\t<direction>out"
            b"</direction>\r\n\t\t\t\t\t<relatedStateVariable>InternalPort</relatedStateVariable>\r\n\t\t\t\t"
            b"</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewInternalClient</name>\r\n\t\t\t\t\t<direction"
            b">out</direction>\r\n\t\t\t\t\t<relatedStateVariable>InternalClient</relatedStateVariable>\r\n\t\t\t\t"
            b"</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewEnabled</name>\r\n\t\t\t\t\t<direction>out"
            b"</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingEnabled</relatedStateVariable>\r\n\t\t\t\t"
            b"</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewPortMappingDescription</name>\r\n\t\t\t\t\t"
            b"<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingDescription"
            b"</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name"
            b">NewLeaseDuration</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable"
            b">PortMappingLeaseDuration</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t"
            b"\t</action>\r\n\t\t<action>\r\n\t\t\t<name>AddPortMapping</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t"
            b"<argument>\r\n\t\t\t\t\t<name>NewRemoteHost</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t"
            b"<relatedStateVariable>RemoteHost</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r"
            b"\n\t\t\t\t\t<name>NewExternalPort</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t"
            b"<relatedStateVariable>ExternalPort</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument"
            b">\r\n\t\t\t\t\t<name>NewProtocol</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t"
            b"<relatedStateVariable>PortMappingProtocol</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t"
            b"<argument>\r\n\t\t\t\t\t<name>NewInternalPort</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t"
            b"\t<relatedStateVariable>InternalPort</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument"
            b">\r\n\t\t\t\t\t<name>NewInternalClient</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t"
            b"<relatedStateVariable>InternalClient</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument"
            b">\r\n\t\t\t\t\t<name>NewEnabled</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t"
            b"<relatedStateVariable>PortMappingEnabled</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t"
            b"<argument>\r\n\t\t\t\t\t<name>NewPortMappingDescription</name>\r\n\t\t\t\t\t<direction>in</direction>\r"
            b"\n\t\t\t\t\t<relatedStateVariable>PortMappingDescription</relatedStateVariable>\r\n\t\t\t\t</argument"
            b">\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewLeaseDuration</name>\r\n\t\t\t\t\t<direction>in"
            b"</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingLeaseDuration</relatedStateVariable>\r\n\t\t"
            b"\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name"
            b">DeletePortMapping</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name"
            b">NewRemoteHost</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable"
            b">RemoteHost</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name"
            b">NewExternalPort</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable"
            b">ExternalPort</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name"
            b">NewProtocol</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable"
            b">PortMappingProtocol</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t"
            b"</action>\r\n\t\t<action>\r\n\t\t\t<name>GetExternalIPAddress</name>\r\n\t\t\t<argumentList>\r\n\t\t\t"
            b"\t<argument>\r\n\t\t\t\t\t<name>NewExternalIPAddress</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n"
            b"\t\t\t\t\t<relatedStateVariable>ExternalIPAddress</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t"
            b"\t</argumentList>\r\n\t\t</action>\r\n\t</actionList>\r\n\t<serviceStateTable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>ConnectionType</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t\t"
            b"<defaultValue>Unconfigured</defaultValue>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"yes\">\r\n\t\t\t<name>PossibleConnectionTypes</name>\r\n\t\t\t<dataType>string</dataType"
            b">\r\n\t\t\t<allowedValueList>\r\n\t\t\t\t<allowedValue>Unconfigured</allowedValue>\r\n\t\t\t\t"
            b"<allowedValue>IP_Routed</allowedValue>\r\n\t\t\t\t<allowedValue>IP_Bridged</allowedValue>\r\n\t\t\t"
            b"</allowedValueList>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"yes\">\r\n\t\t\t<name>ConnectionStatus</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t"
            b"\t<defaultValue>Unconfigured</defaultValue>\r\n\t\t\t<allowedValueList>\r\n\t\t\t\t<allowedValue"
            b">Unconfigured</allowedValue>\r\n\t\t\t\t<allowedValue>Connecting</allowedValue>\r\n\t\t\t\t"
            b"<allowedValue>Authenticating</allowedValue>\r\n\t\t\t\t<allowedValue>PendingDisconnect</allowedValue>\r"
            b"\n\t\t\t\t<allowedValue>Disconnecting</allowedValue>\r\n\t\t\t\t<allowedValue>Disconnected"
            b"</allowedValue>\r\n\t\t\t\t<allowedValue>Connected</allowedValue>\r\n\t\t\t</allowedValueList>\r\n\t\t"
            b"</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>Uptime</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t\t"
            b"<defaultValue>0</defaultValue>\r\n\t\t\t<allowedValueRange>\r\n\t\t\t\t<minimum>0</minimum>\r\n\t\t\t\t"
            b"<maximum></maximum>\r\n\t\t\t\t<step>1</step>\r\n\t\t\t</allowedValueRange>\r\n\t\t</stateVariable>\r\n"
            b"\t\t<stateVariable sendEvents=\"no\">\r\n\t\t\t<name>RSIPAvailable</name>\r\n\t\t<dataType>boolean"
            b"</dataType>\r\n\t\t\t<defaultValue>0</defaultValue>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>NATEnabled</name>\r\n\t\t\t<dataType>boolean</dataType>\r\n\t\t\t"
            b"<defaultValue>1</defaultValue>\r\n\t\t</stateVariable>  \r\n\t\t<stateVariable "
            b"sendEvents=\"yes\">\r\n\t\t\t<name>X_Name</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t"
            b"</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>LastConnectionError</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t"
            b"\t\t<defaultValue>ERROR_NONE</defaultValue>\r\n\t\t\t<allowedValueList>\r\n\t\t\t\t<allowedValue"
            b">ERROR_NONE</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_ISP_TIME_OUT</allowedValue>\r\n\t\t\t\t"
            b"<allowedValue>ERROR_COMMAND_ABORTED</allowedValue>\r\n\t\t\t\t<allowedValue"
            b">ERROR_NOT_ENABLED_FOR_INTERNET</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_BAD_PHONE_NUMBER"
            b"</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_USER_DISCONNECT</allowedValue>\r\n\t\t\t\t<allowedValue"
            b">ERROR_ISP_DISCONNECT</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_IDLE_DISCONNECT</allowedValue>\r\n"
            b"\t\t\t\t<allowedValue>ERROR_FORCED_DISCONNECT</allowedValue>\r\n\t\t\t\t<allowedValue"
            b">ERROR_SERVER_OUT_OF_RESOURCES</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_RESTRICTED_LOGON_HOURS"
            b"</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_ACCOUNT_DISABLED</allowedValue>\r\n\t\t\t\t<allowedValue"
            b">ERROR_ACCOUNT_EXPIRED</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_PASSWORD_EXPIRED</allowedValue>\r"
            b"\n\t\t\t\t<allowedValue>ERROR_AUTHENTICATION_FAILURE</allowedValue>\r\n\t\t\t\t<allowedValue"
            b">ERROR_NO_DIALTONE</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_NO_CARRIER</allowedValue>\r\n\t\t\t\t"
            b"<allowedValue>ERROR_NO_ANSWER</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_LINE_BUSY</allowedValue>\r"
            b"\n\t\t\t\t<allowedValue>ERROR_UNSUPPORTED_BITSPERSECOND</allowedValue>\r\n\t\t\t\t<allowedValue"
            b">ERROR_TOO_MANY_LINE_ERRORS</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_IP_CONFIGURATION"
            b"</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_UNKNOWN</allowedValue>\r\n\t\t\t</allowedValueList>\r\n"
            b"\t\t</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"yes\">\r\n\t\t\t<name>ExternalIPAddress</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t"
            b"\t</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>RemoteHost</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t"
            b"</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>ExternalPort</name>\r\n\t\t\t<dataType>ui2</dataType>\r\n\t\t"
            b"</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>InternalPort</name>\r\n\t\t\t<dataType>ui2</dataType>\r\n\t\t"
            b"</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>PortMappingProtocol</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t"
            b"\t\t<allowedValueList>\r\n\t\t\t\t<allowedValue>TCP</allowedValue>\r\n\t\t\t\t<allowedValue>UDP"
            b"</allowedValue>\r\n\t\t\t</allowedValueList>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>InternalClient</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t"
            b"</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>PortMappingDescription</name>\r\n\t\t\t<dataType>string</dataType>\r"
            b"\n\t\t</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>PortMappingEnabled</name>\r\n\t\t\t<dataType>boolean</dataType>\r\n\t"
            b"\t</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"no\">\r\n\t\t\t<name>PortMappingLeaseDuration</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n"
            b"\t\t</stateVariable>\r\n\t\t<stateVariable "
            b"sendEvents=\"yes\">\r\n\t\t\t<name>PortMappingNumberOfEntries</name>\r\n\t\t\t<dataType>ui2</dataType"
            b">\r\n\t\t</stateVariable>\r\n\t</serviceStateTable>\r\n</scpd>\r\n "
    }

    expected_commands = {
        'GetDefaultConnectionService': "urn:schemas-upnp-org:service:Layer3Forwarding:1",
        'SetDefaultConnectionService': "urn:schemas-upnp-org:service:Layer3Forwarding:1",
        'GetCommonLinkProperties': "urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1",
        'GetTotalBytesSent': "urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1",
        'GetTotalBytesReceived': "urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1",
        'GetTotalPacketsSent': "urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1",
        'GetTotalPacketsReceived': "urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1",
        'X_GetICSStatistics': "urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1",
        'SetConnectionType': "urn:schemas-upnp-org:service:WANIPConnection:1",
        'GetConnectionTypeInfo': "urn:schemas-upnp-org:service:WANIPConnection:1",
        'RequestConnection': "urn:schemas-upnp-org:service:WANIPConnection:1",
        'ForceTermination': "urn:schemas-upnp-org:service:WANIPConnection:1",
        'GetStatusInfo': "urn:schemas-upnp-org:service:WANIPConnection:1",
        'GetNATRSIPStatus': "urn:schemas-upnp-org:service:WANIPConnection:1",
        'GetGenericPortMappingEntry': "urn:schemas-upnp-org:service:WANIPConnection:1",
        'GetSpecificPortMappingEntry': "urn:schemas-upnp-org:service:WANIPConnection:1",
        'AddPortMapping': "urn:schemas-upnp-org:service:WANIPConnection:1",
        'DeletePortMapping': "urn:schemas-upnp-org:service:WANIPConnection:1",
        'GetExternalIPAddress': "urn:schemas-upnp-org:service:WANIPConnection:1",
    }

    async def test_discover_gateway(self):
        with self.assertRaises(UPnPError) as e1:
            with mock_tcp_and_udp(self.loop):
                await Gateway.discover_gateway("10.0.0.2", "10.0.0.1", 2)
        with self.assertRaises(UPnPError) as e2:
            with mock_tcp_and_udp(self.loop):
                await Gateway.discover_gateway("10.0.0.2", "10.0.0.1", 2, unicast=False)
        self.assertEqual(str(e1.exception), "M-SEARCH for 10.0.0.1:1900 timed out.")
        self.assertEqual(str(e2.exception), "M-SEARCH for 10.0.0.1:1900 timed out.")

    async def test_discover_commands(self):
        with mock_tcp_and_udp(self.loop, tcp_replies=self.replies):
            gateway = Gateway(self.reply, self.m_search_args, self.client_address, self.gateway_address)
            await gateway.discover_commands(self.loop)
            self.assertDictEqual(self.expected_commands, dict(gateway._registered_commands))


class TestDiscoverNetgearNighthawkAC2350(TestDiscoverDLinkDIR890L):
    gateway_address = "192.168.0.1"
    client_address = "192.168.0.6"
    soap_port = 5555

    m_search_args = OrderedDict([
        ("HOST", "239.255.255.250:1900"),
        ("MAN", "\"ssdp:discover\""),
        ("MX", 1),
        ("ST", "upnp:rootdevice")
    ])

    reply = SSDPDatagram("OK", **OrderedDict([
        ("CACHE_CONTROL", "max-age=1800"),
        ("ST", "upnp:rootdevice"),
        ("USN", "uuid:11111111-2222-3333-4444-555555555555::upnp:rootdevice"),
        ("Server", "R7500v2 UPnP/1.0 miniupnpd/1.0"),
        ("Location", "http://192.168.0.1:5555/rootDesc.xml"),
    ]))

    replies = {
        b'GET /rootDesc.xml HTTP/1.1\r\nAccept-Encoding: gzip\r\nHost: 192.168.0.1\r\n'
        b'Connection: Close\r\n\r\n':
            b'HTTP/1.1 200 OK\r\nContent-Type: text/xml; charset="utf-8"\r\nConnection: close\r\nContent-Length: '
            b'3720\r\nServer: R7500v2 UPnP/1.0 miniupnpd/1.0\r\nExt: \r\nContent-Language: en-US\r\n\r\n<?xml '
            b'version="1.0"?>\n<root xmlns="urn:schemas-upnp-org:device-1-0" '
            b'\txmlns:pnpx="http://schemas.microsoft.com/windows/pnpx/2005/11" '
            b'\txmlns:df="http://schemas.microsoft.com/windows/2008/09/devicefoundation"><specVersion><major>1</major'
            b'><minor>0</minor></specVersion><URLBase>http://192.168.0.1:5555</URLBase><device><pnpx:X_hardwareId'
            b'>VEN_01f2&amp;DEV_0018&amp;REV_02 VEN_01f2&amp;DEV_8000&amp;SUBSYS_01&amp;REV_01 '
            b'VEN_01f2&amp;DEV_8000&amp;REV_01 '
            b'VEN_0033&amp;DEV_0008&amp;REV_01</pnpx:X_hardwareId><pnpx:X_compatibleId>urn:schemas-upnp-org:device'
            b':InternetGatewayDevice:1</pnpx:X_compatibleId><pnpx:X_deviceCategory>NetworkInfrastructure.Router</pnpx'
            b':X_deviceCategory><df:X_deviceCategory>Network.Router.Wireless</df:X_deviceCategory><deviceType>urn'
            b':schemas-upnp-org:device:InternetGatewayDevice:1</deviceType><friendlyName>R7500v2 ('
            b'Gateway)</friendlyName><manufacturer>NETGEAR, '
            b'Inc.</manufacturer><manufacturerURL>http://www.netgear.com</manufacturerURL><modelDescription>NETGEAR '
            b'R7500v2 NETGEAR Nighthawk X4 AC2350 Smart WiFi Router</modelDescription><modelName>NETGEAR Nighthawk X4 '
            b'AC2350 Smart WiFi Router</modelName><modelNumber>R7500v2</modelNumber><modelURL>http://www.netgear.com'
            b'/home/products/wirelessrouters</modelURL><serialNumber>v1</serialNumber><UDN>uuid:11111111-2222-3333'
            b'-4444-555555555555</UDN><UPC>606449084528</UPC><serviceList><service><serviceType>urn:schemas-upnp-org'
            b':service:Layer3Forwarding:1</serviceType><serviceId>urn:upnp-org:serviceId:L3Forwarding1</serviceId'
            b'><controlURL>/ctl/L3Forwarding</controlURL><eventSubURL>/evt/L3Forwarding</eventSubURL><SCPDURL'
            b'>/Layer3F.xml</SCPDURL></service></serviceList><deviceList><device><deviceType>urn:schemas-upnp-org'
            b':device:WANDevice:1</deviceType><friendlyName>WAN '
            b'Device</friendlyName><manufacturer>NETGEAR</manufacturer><manufacturerURL>http://www.netgear.com'
            b'</manufacturerURL><modelDescription>WAN Device on NETGEAR R7500v2 Wireless '
            b'Router</modelDescription><modelName>NETGEAR Nighthawk X4 AC2350 Smart WiFi '
            b'Router</modelName><modelNumber>R7500v2</modelNumber><modelURL>http://www.netgear.com</modelURL'
            b'><serialNumber>v1</serialNumber><UDN>uuid:11111111-2222-3333-4444-555555555555</UDN><UPC>1234567890ab'
            b'</UPC><serviceList><service><serviceType>urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1'
            b'</serviceType><serviceId>urn:upnp-org:serviceId:WANCommonIFC1</serviceId><controlURL>/ctl/CommonIfCfg'
            b'</controlURL><eventSubURL>/evt/CommonIfCfg</eventSubURL><SCPDURL>/WANCfg.xml</SCPDURL></service'
            b'></serviceList><deviceList><device><deviceType>urn:schemas-upnp-org:device:WANConnectionDevice:1'
            b'</deviceType><friendlyName>WAN Connection '
            b'Device</friendlyName><manufacturer>NETGEAR</manufacturer><manufacturerURL>http://www.netgear.com'
            b'</manufacturerURL><modelDescription>WANConnectionDevice on NETGEAR R7500v2 Wireless '
            b'Router</modelDescription><modelName>NETGEAR Nighthawk X4 AC2350 Smart WiFi '
            b'Router</modelName><modelNumber>R7500v2</modelNumber><modelURL>http://www.netgear.com</modelURL'
            b'><serialNumber>v1</serialNumber><UDN>uuid:4d696e69-444c-164e-9d44-b0b98a4cd3c3</UDN><UPC>1234567890ab'
            b'</UPC><serviceList><service><serviceType>urn:schemas-upnp-org:service:WANEthernetLinkConfig:1'
            b'</serviceType><serviceId>urn:upnp-org:serviceId:WANEthLinkC1</serviceId><controlURL>/ctl/WanEth'
            b'</controlURL><eventSubURL>/evt/WanEth</eventSubURL><SCPDURL>/WanEth.xml</SCPDURL></service><service'
            b'><serviceType>urn:schemas-upnp-org:service:WANIPConnection:1</serviceType><serviceId>urn:upnp-org'
            b':serviceId:WANIPConn1</serviceId><controlURL>/ctl/IPConn</controlURL><eventSubURL>/evt/IPConn'
            b'</eventSubURL><SCPDURL>/WANIPCn.xml</SCPDURL></service></serviceList></device></deviceList></device'
            b'></deviceList><presentationURL>http://www.routerlogin.net</presentationURL></device></root>',
        b'GET /Layer3F.xml HTTP/1.1\r\nAccept-Encoding: gzip\r\nHost: 192.168.0.1\r\n'
        b'Connection: Close\r\n\r\n':
            b'HTTP/1.1 200 OK\r\nContent-Type: text/xml; charset="utf-8"\r\nConnection: close\r\nContent-Length: '
            b'794\r\nServer: R7500v2 UPnP/1.0 miniupnpd/1.0\r\nExt: \r\nContent-Language: en-US\r\n\r\n<?xml '
            b'version="1.0"?>\n<scpd xmlns="urn:schemas-upnp-org:service-1-0"><specVersion><major>1</major><minor>0'
            b'</minor></specVersion><actionList><action><name>SetDefaultConnectionService</name><argumentList'
            b'><argument><name>NewDefaultConnectionService</name><direction>in</direction><relatedStateVariable'
            b'>DefaultConnectionService</relatedStateVariable></argument></argumentList></action><action><name'
            b'>GetDefaultConnectionService</name><argumentList><argument><name>NewDefaultConnectionService</name'
            b'><direction>out</direction><relatedStateVariable>DefaultConnectionService</relatedStateVariable'
            b'></argument></argumentList></action></actionList><serviceStateTable><stateVariable '
            b'sendEvents="yes"><name>DefaultConnectionService</name><dataType>string</dataType></stateVariable'
            b'></serviceStateTable></scpd>',
        b'GET /WANCfg.xml HTTP/1.1\r\nAccept-Encoding: gzip\r\nHost: 192.168.0.1\r\n'
        b'Connection: Close\r\n\r\n':
            b'HTTP/1.1 200 OK\r\nContent-Type: text/xml; charset="utf-8"\r\nConnection: close\r\nContent-Length: '
            b'2942\r\nServer: R7500v2 UPnP/1.0 miniupnpd/1.0\r\nExt: \r\nContent-Language: en-US\r\n\r\n<?xml '
            b'version="1.0"?>\n<scpd xmlns="urn:schemas-upnp-org:service-1-0"><specVersion><major>1</major><minor>0'
            b'</minor></specVersion><actionList><action><name>GetCommonLinkProperties</name><argumentList><argument'
            b'><name>NewWANAccessType</name><direction>out</direction><relatedStateVariable>WANAccessType'
            b'</relatedStateVariable></argument><argument><name>NewLayer1UpstreamMaxBitRate</name><direction>out'
            b'</direction><relatedStateVariable>Layer1UpstreamMaxBitRate</relatedStateVariable></argument><argument'
            b'><name>NewLayer1DownstreamMaxBitRate</name><direction>out</direction><relatedStateVariable'
            b'>Layer1DownstreamMaxBitRate</relatedStateVariable></argument><argument><name>NewPhysicalLinkStatus'
            b'</name><direction>out</direction><relatedStateVariable>PhysicalLinkStatus</relatedStateVariable'
            b'></argument></argumentList></action><action><name>GetTotalBytesSent</name><argumentList><argument><name'
            b'>NewTotalBytesSent</name><direction>out</direction><relatedStateVariable>TotalBytesSent'
            b'</relatedStateVariable></argument></argumentList></action><action><name>GetTotalBytesReceived</name'
            b'><argumentList><argument><name>NewTotalBytesReceived</name><direction>out</direction'
            b'><relatedStateVariable>TotalBytesReceived</relatedStateVariable></argument></argumentList></action'
            b'><action><name>GetTotalPacketsSent</name><argumentList><argument><name>NewTotalPacketsSent</name'
            b'><direction>out</direction><relatedStateVariable>TotalPacketsSent</relatedStateVariable></argument'
            b'></argumentList></action><action><name>GetTotalPacketsReceived</name><argumentList><argument><name'
            b'>NewTotalPacketsReceived</name><direction>out</direction><relatedStateVariable>TotalPacketsReceived'
            b'</relatedStateVariable></argument></argumentList></action></actionList><serviceStateTable'
            b'><stateVariable sendEvents="no"><name>WANAccessType</name><dataType>string</dataType><allowedValueList'
            b'><allowedValue>DSL</allowedValue><allowedValue>POTS</allowedValue><allowedValue>Cable</allowedValue'
            b'><allowedValue>Ethernet</allowedValue></allowedValueList></stateVariable><stateVariable '
            b'sendEvents="no"><name>Layer1UpstreamMaxBitRate</name><dataType>ui4</dataType></stateVariable'
            b'><stateVariable sendEvents="no"><name>Layer1DownstreamMaxBitRate</name><dataType>ui4</dataType'
            b'></stateVariable><stateVariable '
            b'sendEvents="yes"><name>PhysicalLinkStatus</name><dataType>string</dataType><allowedValueList'
            b'><allowedValue>Up</allowedValue><allowedValue>Down</allowedValue><allowedValue>Initializing'
            b'</allowedValue><allowedValue>Unavailable</allowedValue></allowedValueList></stateVariable'
            b'><stateVariable sendEvents="no"><name>TotalBytesSent</name><dataType>ui4</dataType></stateVariable'
            b'><stateVariable sendEvents="no"><name>TotalBytesReceived</name><dataType>ui4</dataType></stateVariable'
            b'><stateVariable sendEvents="no"><name>TotalPacketsSent</name><dataType>ui4</dataType></stateVariable'
            b'><stateVariable sendEvents="no"><name>TotalPacketsReceived</name><dataType>ui4</dataType'
            b'></stateVariable></serviceStateTable></scpd>',
        b'GET /WanEth.xml HTTP/1.1\r\nAccept-Encoding: gzip\r\nHost: 192.168.0.1\r\n'
        b'Connection: Close\r\n\r\n':
            b'HTTP/1.1 200 OK\r\nContent-Type: text/xml; charset="utf-8"\r\nConnection: close\r\nContent-Length: '
            b'711\r\nServer: R7500v2 UPnP/1.0 miniupnpd/1.0\r\nExt: \r\nContent-Language: en-US\r\n\r\n<?xml '
            b'version="1.0"?>\n<scpd xmlns="urn:schemas-upnp-org:service-1-0"><specVersion><major>1</major><minor>0'
            b'</minor></specVersion><actionList><action><name>GetEthernetLinkStatus</name><argumentList><argument'
            b'><name>NewEthernetLinkStatus</name><direction>out</direction><relatedStateVariable>EthernetLinkStatus'
            b'</relatedStateVariable></argument></argumentList></action></actionList><serviceStateTable'
            b'><stateVariable sendEvents="yes"><name>EthernetLinkStatus</name><dataType>string</dataType'
            b'><allowedValueList><allowedValue>Up</allowedValue><allowedValue>Down</allowedValue><allowedValue'
            b'>Initializing</allowedValue><allowedValue>Unavailable</allowedValue></allowedValueList></stateVariable'
            b'></serviceStateTable></scpd>',
        b'GET /WANIPCn.xml HTTP/1.1\r\nAccept-Encoding: gzip\r\nHost: 192.168.0.1\r\n'
        b'Connection: Close\r\n\r\n':
            b'HTTP/1.1 200 OK\r\nContent-Type: text/xml; charset="utf-8"\r\nConnection: close\r\nContent-Length: '
            b'8400\r\nServer: R7500v2 UPnP/1.0 miniupnpd/1.0\r\nExt: \r\nContent-Language: en-US\r\n\r\n<?xml '
            b'version="1.0"?>\n<scpd xmlns="urn:schemas-upnp-org:service-1-0"><specVersion><major>1</major><minor>0'
            b'</minor></specVersion><actionList><action><name>AddPortMapping</name><argumentList><argument><name'
            b'>NewRemoteHost</name><direction>in</direction><relatedStateVariable>RemoteHost</relatedStateVariable'
            b'></argument><argument><name>NewExternalPort</name><direction>in</direction><relatedStateVariable'
            b'>ExternalPort</relatedStateVariable></argument><argument><name>NewProtocol</name><direction>in'
            b'</direction><relatedStateVariable>PortMappingProtocol</relatedStateVariable></argument><argument><name'
            b'>NewInternalPort</name><direction>in</direction><relatedStateVariable>InternalPort'
            b'</relatedStateVariable></argument><argument><name>NewInternalClient</name><direction>in</direction'
            b'><relatedStateVariable>InternalClient</relatedStateVariable></argument><argument><name>NewEnabled</name'
            b'><direction>in</direction><relatedStateVariable>PortMappingEnabled</relatedStateVariable></argument'
            b'><argument><name>NewPortMappingDescription</name><direction>in</direction><relatedStateVariable'
            b'>PortMappingDescription</relatedStateVariable></argument><argument><name>NewLeaseDuration</name'
            b'><direction>in</direction><relatedStateVariable>PortMappingLeaseDuration</relatedStateVariable'
            b'></argument></argumentList></action><action><name>GetExternalIPAddress</name><argumentList><argument'
            b'><name>NewExternalIPAddress</name><direction>out</direction><relatedStateVariable>ExternalIPAddress'
            b'</relatedStateVariable></argument></argumentList></action><action><name>DeletePortMapping</name'
            b'><argumentList><argument><name>NewRemoteHost</name><direction>in</direction><relatedStateVariable'
            b'>RemoteHost</relatedStateVariable></argument><argument><name>NewExternalPort</name><direction>in'
            b'</direction><relatedStateVariable>ExternalPort</relatedStateVariable></argument><argument><name'
            b'>NewProtocol</name><direction>in</direction><relatedStateVariable>PortMappingProtocol'
            b'</relatedStateVariable></argument></argumentList></action><action><name>SetConnectionType</name'
            b'><argumentList><argument><name>NewConnectionType</name><direction>in</direction><relatedStateVariable'
            b'>ConnectionType</relatedStateVariable></argument></argumentList></action><action><name'
            b'>GetConnectionTypeInfo</name><argumentList><argument><name>NewConnectionType</name><direction>out'
            b'</direction><relatedStateVariable>ConnectionType</relatedStateVariable></argument><argument><name'
            b'>NewPossibleConnectionTypes</name><direction>out</direction><relatedStateVariable'
            b'>PossibleConnectionTypes</relatedStateVariable></argument></argumentList></action><action><name'
            b'>RequestConnection</name></action><action><name>ForceTermination</name></action><action><name'
            b'>GetStatusInfo</name><argumentList><argument><name>NewConnectionStatus</name><direction>out</direction'
            b'><relatedStateVariable>ConnectionStatus</relatedStateVariable></argument><argument><name'
            b'>NewLastConnectionError</name><direction>out</direction><relatedStateVariable>LastConnectionError'
            b'</relatedStateVariable></argument><argument><name>NewUptime</name><direction>out</direction'
            b'><relatedStateVariable>Uptime</relatedStateVariable></argument></argumentList></action><action><name'
            b'>GetNATRSIPStatus</name><argumentList><argument><name>NewRSIPAvailable</name><direction>out</direction'
            b'><relatedStateVariable>RSIPAvailable</relatedStateVariable></argument><argument><name>NewNATEnabled'
            b'</name><direction>out</direction><relatedStateVariable>NATEnabled</relatedStateVariable></argument'
            b'></argumentList></action><action><name>GetGenericPortMappingEntry</name><argumentList><argument><name'
            b'>NewPortMappingIndex</name><direction>in</direction><relatedStateVariable>PortMappingNumberOfEntries'
            b'</relatedStateVariable></argument><argument><name>NewRemoteHost</name><direction>out</direction'
            b'><relatedStateVariable>RemoteHost</relatedStateVariable></argument><argument><name>NewExternalPort'
            b'</name><direction>out</direction><relatedStateVariable>ExternalPort</relatedStateVariable></argument'
            b'><argument><name>NewProtocol</name><direction>out</direction><relatedStateVariable>PortMappingProtocol'
            b'</relatedStateVariable></argument><argument><name>NewInternalPort</name><direction>out</direction'
            b'><relatedStateVariable>InternalPort</relatedStateVariable></argument><argument><name>NewInternalClient'
            b'</name><direction>out</direction><relatedStateVariable>InternalClient</relatedStateVariable></argument'
            b'><argument><name>NewEnabled</name><direction>out</direction><relatedStateVariable>PortMappingEnabled'
            b'</relatedStateVariable></argument><argument><name>NewPortMappingDescription</name><direction>out'
            b'</direction><relatedStateVariable>PortMappingDescription</relatedStateVariable></argument><argument'
            b'><name>NewLeaseDuration</name><direction>out</direction><relatedStateVariable>PortMappingLeaseDuration'
            b'</relatedStateVariable></argument></argumentList></action><action><name>GetSpecificPortMappingEntry'
            b'</name><argumentList><argument><name>NewRemoteHost</name><direction>in</direction><relatedStateVariable'
            b'>RemoteHost</relatedStateVariable></argument><argument><name>NewExternalPort</name><direction>in'
            b'</direction><relatedStateVariable>ExternalPort</relatedStateVariable></argument><argument><name'
            b'>NewProtocol</name><direction>in</direction><relatedStateVariable>PortMappingProtocol'
            b'</relatedStateVariable></argument><argument><name>NewInternalPort</name><direction>out</direction'
            b'><relatedStateVariable>InternalPort</relatedStateVariable></argument><argument><name>NewInternalClient'
            b'</name><direction>out</direction><relatedStateVariable>InternalClient</relatedStateVariable></argument'
            b'><argument><name>NewEnabled</name><direction>out</direction><relatedStateVariable>PortMappingEnabled'
            b'</relatedStateVariable></argument><argument><name>NewPortMappingDescription</name><direction>out'
            b'</direction><relatedStateVariable>PortMappingDescription</relatedStateVariable></argument><argument'
            b'><name>NewLeaseDuration</name><direction>out</direction><relatedStateVariable>PortMappingLeaseDuration'
            b'</relatedStateVariable></argument></argumentList></action></actionList><serviceStateTable'
            b'><stateVariable sendEvents="no"><name>ConnectionType</name><dataType>string</dataType></stateVariable'
            b'><stateVariable sendEvents="yes"><name>PossibleConnectionTypes</name><dataType>string</dataType'
            b'><allowedValueList><allowedValue>Unconfigured</allowedValue><allowedValue>IP_Routed</allowedValue'
            b'><allowedValue>IP_Bridged</allowedValue></allowedValueList></stateVariable><stateVariable '
            b'sendEvents="yes"><name>ConnectionStatus</name><dataType>string</dataType><allowedValueList'
            b'><allowedValue>Unconfigured</allowedValue><allowedValue>Connecting</allowedValue><allowedValue'
            b'>Connected</allowedValue><allowedValue>PendingDisconnect</allowedValue><allowedValue>Disconnecting'
            b'</allowedValue><allowedValue>Disconnected</allowedValue></allowedValueList></stateVariable'
            b'><stateVariable sendEvents="no"><name>Uptime</name><dataType>ui4</dataType></stateVariable'
            b'><stateVariable sendEvents="no"><name>LastConnectionError</name><dataType>string</dataType'
            b'><allowedValueList><allowedValue>ERROR_NONE</allowedValue></allowedValueList></stateVariable'
            b'><stateVariable sendEvents="no"><name>RSIPAvailable</name><dataType>boolean</dataType></stateVariable'
            b'><stateVariable sendEvents="no"><name>NATEnabled</name><dataType>boolean</dataType></stateVariable'
            b'><stateVariable sendEvents="yes"><name>ExternalIPAddress</name><dataType>string</dataType'
            b'></stateVariable><stateVariable sendEvents="yes"><name>PortMappingNumberOfEntries</name><dataType>ui2'
            b'</dataType></stateVariable><stateVariable '
            b'sendEvents="no"><name>PortMappingEnabled</name><dataType>boolean</dataType></stateVariable'
            b'><stateVariable sendEvents="no"><name>PortMappingLeaseDuration</name><dataType>ui4</dataType'
            b'></stateVariable><stateVariable '
            b'sendEvents="no"><name>RemoteHost</name><dataType>string</dataType></stateVariable><stateVariable '
            b'sendEvents="no"><name>ExternalPort</name><dataType>ui2</dataType></stateVariable><stateVariable '
            b'sendEvents="no"><name>InternalPort</name><dataType>ui2</dataType></stateVariable><stateVariable '
            b'sendEvents="no"><name>PortMappingProtocol</name><dataType>string</dataType><allowedValueList'
            b'><allowedValue>TCP</allowedValue><allowedValue>UDP</allowedValue></allowedValueList></stateVariable'
            b'><stateVariable sendEvents="no"><name>InternalClient</name><dataType>string</dataType></stateVariable'
            b'><stateVariable sendEvents="no"><name>PortMappingDescription</name><dataType>string</dataType'
            b'></stateVariable></serviceStateTable></scpd> '
    }

    expected_commands = {
        'SetDefaultConnectionService': "urn:schemas-upnp-org:service:Layer3Forwarding:1",
        'GetDefaultConnectionService': "urn:schemas-upnp-org:service:Layer3Forwarding:1",
        'GetCommonLinkProperties': "urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1",
        'GetTotalBytesSent': "urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1",
        'GetTotalBytesReceived': "urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1",
        'GetTotalPacketsSent': "urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1",
        'GetTotalPacketsReceived': "urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1",
        'AddPortMapping': "urn:schemas-upnp-org:service:WANIPConnection:1",
        'GetExternalIPAddress': "urn:schemas-upnp-org:service:WANIPConnection:1",
        'DeletePortMapping': "urn:schemas-upnp-org:service:WANIPConnection:1",
        'SetConnectionType': "urn:schemas-upnp-org:service:WANIPConnection:1",
        'GetConnectionTypeInfo': "urn:schemas-upnp-org:service:WANIPConnection:1",
        'RequestConnection': "urn:schemas-upnp-org:service:WANIPConnection:1",
        'ForceTermination': "urn:schemas-upnp-org:service:WANIPConnection:1",
        'GetStatusInfo': "urn:schemas-upnp-org:service:WANIPConnection:1",
        'GetNATRSIPStatus': "urn:schemas-upnp-org:service:WANIPConnection:1",
        'GetGenericPortMappingEntry': "urn:schemas-upnp-org:service:WANIPConnection:1",
        'GetSpecificPortMappingEntry': "urn:schemas-upnp-org:service:WANIPConnection:1",
    }
