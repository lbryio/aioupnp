import os
import json
from collections import OrderedDict
from aioupnp.fault import UPnPError
from tests import AsyncioTestCase, mock_tcp_and_udp
from aioupnp.gateway import Gateway, get_action_list
from aioupnp.serialization.ssdp import SSDPDatagram
from aioupnp.serialization.soap import serialize_soap_post
from aioupnp.upnp import UPnP


def gen_get_bytes(location: str, host: str) -> bytes:
    return (
            'GET %s HTTP/1.1\r\nAccept-Encoding: gzip\r\nHost: %s\r\nConnection: Close\r\n\r\n' % (location, host)
    ).encode()


class TestParseActionList(AsyncioTestCase):
    test_action_list = {'actionList': {
        'action': [OrderedDict([('name', 'SetConnectionType'), ('argumentList', OrderedDict([('argument', OrderedDict(
            [('name', 'NewConnectionType'), ('direction', 'in'), ('relatedStateVariable', 'ConnectionType')]))]))]),
                   OrderedDict([('name', 'GetConnectionTypeInfo'), ('argumentList', OrderedDict([('argument', [
                       OrderedDict([('name', 'NewConnectionType'), ('direction', 'out'),
                                    ('relatedStateVariable', 'ConnectionType')]), OrderedDict(
                           [('name', 'NewPossibleConnectionTypes'), ('direction', 'out'),
                            ('relatedStateVariable', 'PossibleConnectionTypes')])])]))]),
                   OrderedDict([('name', 'RequestConnection')]), OrderedDict([('name', 'ForceTermination')]),
                   OrderedDict([('name', 'GetStatusInfo'), ('argumentList', OrderedDict([('argument', [OrderedDict(
                       [('name', 'NewConnectionStatus'), ('direction', 'out'),
                        ('relatedStateVariable', 'ConnectionStatus')]), OrderedDict(
                       [('name', 'NewLastConnectionError'), ('direction', 'out'),
                        ('relatedStateVariable', 'LastConnectionError')]), OrderedDict(
                       [('name', 'NewUptime'), ('direction', 'out'), ('relatedStateVariable', 'Uptime')])])]))]),
                   OrderedDict([('name', 'GetNATRSIPStatus'), ('argumentList', OrderedDict([('argument', [OrderedDict(
                       [('name', 'NewRSIPAvailable'), ('direction', 'out'),
                        ('relatedStateVariable', 'RSIPAvailable')]), OrderedDict(
                       [('name', 'NewNATEnabled'), ('direction', 'out'),
                        ('relatedStateVariable', 'NATEnabled')])])]))]), OrderedDict(
                [('name', 'GetGenericPortMappingEntry'), ('argumentList', OrderedDict([('argument', [OrderedDict(
                    [('name', 'NewPortMappingIndex'), ('direction', 'in'),
                     ('relatedStateVariable', 'PortMappingNumberOfEntries')]), OrderedDict(
                    [('name', 'NewRemoteHost'), ('direction', 'out'), ('relatedStateVariable', 'RemoteHost')]),
                    OrderedDict(
                        [('name', 'NewExternalPort'), ('direction', 'out'), ('relatedStateVariable', 'ExternalPort')]),
                    OrderedDict(
                        [('name', 'NewProtocol'), ('direction', 'out'),
                         ('relatedStateVariable', 'PortMappingProtocol')]),
                    OrderedDict([('name',
                                  'NewInternalPort'),
                                 ('direction',
                                  'out'), (
                                     'relatedStateVariable',
                                     'InternalPort')]),
                    OrderedDict([('name',
                                  'NewInternalClient'),
                                 ('direction',
                                  'out'), (
                                     'relatedStateVariable',
                                     'InternalClient')]),
                    OrderedDict([('name',
                                  'NewEnabled'),
                                 ('direction',
                                  'out'), (
                                     'relatedStateVariable',
                                     'PortMappingEnabled')]),
                    OrderedDict([('name',
                                  'NewPortMappingDescription'),
                                 ('direction',
                                  'out'), (
                                     'relatedStateVariable',
                                     'PortMappingDescription')]),
                    OrderedDict([('name',
                                  'NewLeaseDuration'),
                                 ('direction',
                                  'out'), (
                                     'relatedStateVariable',
                                     'PortMappingLeaseDuration')])])]))]),
                   OrderedDict([('name', 'GetSpecificPortMappingEntry'), ('argumentList', OrderedDict([('argument', [
                       OrderedDict(
                           [('name', 'NewRemoteHost'), ('direction', 'in'), ('relatedStateVariable', 'RemoteHost')]),
                       OrderedDict([('name', 'NewExternalPort'), ('direction', 'in'),
                                    ('relatedStateVariable', 'ExternalPort')]), OrderedDict(
                           [('name', 'NewProtocol'), ('direction', 'in'),
                            ('relatedStateVariable', 'PortMappingProtocol')]), OrderedDict(
                           [('name', 'NewInternalPort'), ('direction', 'out'),
                            ('relatedStateVariable', 'InternalPort')]), OrderedDict(
                           [('name', 'NewInternalClient'), ('direction', 'out'),
                            ('relatedStateVariable', 'InternalClient')]), OrderedDict(
                           [('name', 'NewEnabled'), ('direction', 'out'),
                            ('relatedStateVariable', 'PortMappingEnabled')]), OrderedDict(
                           [('name', 'NewPortMappingDescription'), ('direction', 'out'),
                            ('relatedStateVariable', 'PortMappingDescription')]), OrderedDict(
                           [('name', 'NewLeaseDuration'), ('direction', 'out'),
                            ('relatedStateVariable', 'PortMappingLeaseDuration')])])]))]), OrderedDict(
                [('name', 'AddPortMapping'), ('argumentList', OrderedDict([('argument', [
                    OrderedDict(
                        [('name', 'NewRemoteHost'), ('direction', 'in'), ('relatedStateVariable', 'RemoteHost')]),
                    OrderedDict(
                        [('name', 'NewExternalPort'), ('direction', 'in'), ('relatedStateVariable', 'ExternalPort')]),
                    OrderedDict(
                        [('name', 'NewProtocol'), ('direction', 'in'),
                         ('relatedStateVariable', 'PortMappingProtocol')]),
                    OrderedDict(
                        [('name', 'NewInternalPort'), ('direction', 'in'), ('relatedStateVariable', 'InternalPort')]),
                    OrderedDict(
                        [('name', 'NewInternalClient'), ('direction', 'in'),
                         ('relatedStateVariable', 'InternalClient')]),
                    OrderedDict(
                        [('name', 'NewEnabled'), ('direction', 'in'), ('relatedStateVariable', 'PortMappingEnabled')]),
                    OrderedDict([('name', 'NewPortMappingDescription'), ('direction', 'in'),
                                 ('relatedStateVariable', 'PortMappingDescription')]), OrderedDict(
                        [('name', 'NewLeaseDuration'), ('direction', 'in'),
                         ('relatedStateVariable', 'PortMappingLeaseDuration')])])]))]), OrderedDict(
                [('name', 'DeletePortMapping'), ('argumentList', OrderedDict([('argument', [
                    OrderedDict(
                        [('name', 'NewRemoteHost'), ('direction', 'in'), ('relatedStateVariable', 'RemoteHost')]),
                    OrderedDict(
                        [('name', 'NewExternalPort'), ('direction', 'in'), ('relatedStateVariable', 'ExternalPort')]),
                    OrderedDict(
                        [('name', 'NewProtocol'), ('direction', 'in'),
                         ('relatedStateVariable', 'PortMappingProtocol')])])]))]),
                   OrderedDict([('name', 'GetExternalIPAddress'),
                                ('argumentList', OrderedDict(
                                    [('argument', OrderedDict([('name', 'NewExternalIPAddress'),
                                                               ('direction', 'out'),
                                                               ('relatedStateVariable', 'ExternalIPAddress')]))]))])]}}

    def test_parse_expected_action_list(self):
        expected = [('SetConnectionType', ['NewConnectionType'], []),
                    ('GetConnectionTypeInfo', [], ['NewConnectionType', 'NewPossibleConnectionTypes']),
                    ('RequestConnection', [], []), ('ForceTermination', [], []),
                    ('GetStatusInfo', [], ['NewConnectionStatus', 'NewLastConnectionError', 'NewUptime']),
                    ('GetNATRSIPStatus', [], ['NewRSIPAvailable', 'NewNATEnabled']), (
                        'GetGenericPortMappingEntry', ['NewPortMappingIndex'],
                        ['NewRemoteHost', 'NewExternalPort', 'NewProtocol', 'NewInternalPort', 'NewInternalClient',
                         'NewEnabled', 'NewPortMappingDescription', 'NewLeaseDuration']), (
                        'GetSpecificPortMappingEntry', ['NewRemoteHost', 'NewExternalPort', 'NewProtocol'],
                        ['NewInternalPort', 'NewInternalClient', 'NewEnabled', 'NewPortMappingDescription',
                         'NewLeaseDuration']), ('AddPortMapping',
                                                ['NewRemoteHost', 'NewExternalPort', 'NewProtocol', 'NewInternalPort',
                                                 'NewInternalClient', 'NewEnabled', 'NewPortMappingDescription',
                                                 'NewLeaseDuration'], []),
                    ('DeletePortMapping', ['NewRemoteHost', 'NewExternalPort', 'NewProtocol'], []),
                    ('GetExternalIPAddress', [], ['NewExternalIPAddress'])]
        self.assertEqual(expected, get_action_list(self.test_action_list))


class TestDiscoverDLinkDIR890L(AsyncioTestCase):
    gateway_info = \
        {'manufacturer_string': 'D-Link DIR-890L', 'gateway_address': '10.0.0.1',
         'server': 'Linux, UPnP/1.0, DIR-890L Ver 1.20', 'urlBase': 'http://10.0.0.1:49152',
         'location': 'http://10.0.0.1:49152/InternetGatewayDevice.xml', 'specVersion': {'major': '1', 'minor': '0'},
         'usn': 'uuid:11111111-2222-3333-4444-555555555555::urn:schemas-upnp-org:device:WANDevice:1',
         'urn': 'urn:schemas-upnp-org:device:WANDevice:1',
         'gateway_xml': 'HTTP/1.1 200 OK\r\nServer: WebServer\r\nDate: Thu, 11 Oct 2018 22:16:16 GMT\r\nContent-Type: text/xml\r\nContent-Length: 3921\r\nLast-Modified: Thu, 09 Aug 2018 12:41:07 GMT\r\nConnection: close\r\n\r\n<?xml version="1.0"?>\n<root xmlns="urn:schemas-upnp-org:device-1-0">\n\t<specVersion>\n\t\t<major>1</major>\n\t\t<minor>0</minor>\n\t</specVersion>\n\t<URLBase>http://10.0.0.1:49152</URLBase>\n\t<device>\n\t\t<deviceType>urn:schemas-upnp-org:device:InternetGatewayDevice:1</deviceType>\n\t\t<friendlyName>Wireless Broadband Router</friendlyName>\n\t\t<manufacturer>D-Link Corporation</manufacturer>\n\t\t<manufacturerURL>http://www.dlink.com</manufacturerURL>\n\t\t<modelDescription>D-Link Router</modelDescription>\n\t\t<modelName>D-Link Router</modelName>\n\t\t<modelNumber>DIR-890L</modelNumber>\n\t\t<modelURL>http://www.dlink.com</modelURL>\n\t\t<serialNumber>120</serialNumber>\n\t\t<UDN>uuid:11111111-2222-3333-4444-555555555555</UDN>\n\t\t<iconList>\n\t\t\t<icon>\n\t\t\t\t<mimetype>image/gif</mimetype>\n\t\t\t\t<width>118</width>\n\t\t\t\t<height>119</height>\n\t\t\t\t<depth>8</depth>\n\t\t\t\t<url>/ligd.gif</url>\n\t\t\t</icon>\n\t\t</iconList>\n\t\t<serviceList>\n\t\t\t<service>\n\t\t\t\t<serviceType>urn:schemas-microsoft-com:service:OSInfo:1</serviceType>\n\t\t\t\t<serviceId>urn:microsoft-com:serviceId:OSInfo1</serviceId>\n\t\t\t\t<controlURL>/soap.cgi?service=OSInfo1</controlURL>\n\t\t\t\t<eventSubURL>/gena.cgi?service=OSInfo1</eventSubURL>\n\t\t\t\t<SCPDURL>/OSInfo.xml</SCPDURL>\n\t\t\t</service>\n\t\t\t<service>\n\t\t\t\t<serviceType>urn:schemas-upnp-org:service:Layer3Forwarding:1</serviceType>\n\t\t\t\t<serviceId>urn:upnp-org:serviceId:L3Forwarding1</serviceId>\n\t\t\t\t<controlURL>/soap.cgi?service=L3Forwarding1</controlURL>\n\t\t\t\t<eventSubURL>/gena.cgi?service=L3Forwarding1</eventSubURL>\n\t\t\t\t<SCPDURL>/Layer3Forwarding.xml</SCPDURL>\n\t\t\t</service>\n\t\t</serviceList>\n\t\t<deviceList>\n\t\t\t<device>\n\t\t\t\t<deviceType>urn:schemas-upnp-org:device:WANDevice:1</deviceType>\n\t\t\t\t<friendlyName>WANDevice</friendlyName>\n\t\t\t\t<manufacturer>D-Link</manufacturer>\n\t\t\t\t<manufacturerURL>http://www.dlink.com</manufacturerURL>\n\t\t\t\t<modelDescription>WANDevice</modelDescription>\n\t\t\t\t<modelName>DIR-890L</modelName>\n\t\t\t\t<modelNumber>1</modelNumber>\n\t\t\t\t<modelURL>http://www.dlink.com</modelURL>\n\t\t\t\t<serialNumber>120</serialNumber>\n\t\t\t\t<UDN>uuid:11111111-2222-3333-4444-555555555555</UDN>\n\t\t\t\t<serviceList>\n\t\t\t\t\t<service>\n\t\t\t\t\t\t<serviceType>urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1</serviceType>\n\t\t\t\t\t\t<serviceId>urn:upnp-org:serviceId:WANCommonIFC1</serviceId>\n\t\t\t\t\t\t<controlURL>/soap.cgi?service=WANCommonIFC1</controlURL>\n\t\t\t\t\t\t<eventSubURL>/gena.cgi?service=WANCommonIFC1</eventSubURL>\n\t\t\t\t\t\t<SCPDURL>/WANCommonInterfaceConfig.xml</SCPDURL>\n\t\t\t\t\t</service>\n\t\t\t\t</serviceList>\n\t\t\t\t<deviceList>\n\t\t\t\t\t<device>\n\t\t\t\t\t\t<deviceType>urn:schemas-upnp-org:device:WANConnectionDevice:1</deviceType>\n\t\t\t\t\t\t<friendlyName>WANConnectionDevice</friendlyName>\n\t\t\t\t\t\t<manufacturer>D-Link</manufacturer>\n\t\t\t\t\t\t<manufacturerURL>http://www.dlink.com</manufacturerURL>\n\t\t\t\t\t\t<modelDescription>WanConnectionDevice</modelDescription>\n\t\t\t\t\t\t<modelName>DIR-890L</modelName>\n\t\t\t\t\t\t<modelNumber>1</modelNumber>\n\t\t\t\t\t\t<modelURL>http://www.dlink.com</modelURL>\n\t\t\t\t\t\t<serialNumber>120</serialNumber>\n\t\t\t\t\t\t<UDN>uuid:11111111-2222-3333-4444-555555555555</UDN>\n\t\t\t\t\t\t<serviceList>\n\t\t\t\t\t\t\t<service>\n\t\t\t\t\t\t\t\t<serviceType>urn:schemas-upnp-org:service:WANEthernetLinkConfig:1</serviceType>\n\t\t\t\t\t\t\t\t<serviceId>urn:upnp-org:serviceId:WANEthLinkC1</serviceId>\n\t\t\t\t\t\t\t\t<controlURL>/soap.cgi?service=WANEthLinkC1</controlURL>\n\t\t\t\t\t\t\t\t<eventSubURL>/gena.cgi?service=WANEthLinkC1</eventSubURL>\n\t\t\t\t\t\t\t\t<SCPDURL>/WANEthernetLinkConfig.xml</SCPDURL>\n\t\t\t\t\t\t\t</service>\n\t\t\t\t\t\t\t<service>\n\t\t\t\t\t\t\t\t<serviceType>urn:schemas-upnp-org:service:WANIPConnection:1</serviceType>\n\t\t\t\t\t\t\t\t<serviceId>urn:upnp-org:serviceId:WANIPConn1</serviceId>\n\t\t\t\t\t\t\t\t<controlURL>/soap.cgi?service=WANIPConn1</controlURL>\n\t\t\t\t\t\t\t\t<eventSubURL>/gena.cgi?service=WANIPConn1</eventSubURL>\n\t\t\t\t\t\t\t\t<SCPDURL>/WANIPConnection.xml</SCPDURL>\n\t\t\t\t\t\t\t</service>\n\t\t\t\t\t\t</serviceList>\n\t\t\t\t\t</device>\n\t\t\t\t</deviceList>\n\t\t\t</device>\n\t\t</deviceList>\n\t\t<presentationURL>http://10.0.0.1</presentationURL>\n\t</device>\n</root>\n',
         'services_xml': {
             '/OSInfo.xml': 'HTTP/1.1 200 OK\r\nServer: WebServer\r\nDate: Thu, 11 Oct 2018 22:16:16 GMT\r\nContent-Type: text/xml\r\nContent-Length: 219\r\nLast-Modified: Thu, 09 Aug 2018 12:41:07 GMT\r\nConnection: close\r\n\r\n<?xml version="1.0"?>\n<scpd xmlns="urn:schemas-upnp-org:service-1-0">\n\t<specVersion>\n\t\t<major>1</major>\n\t\t<minor>0</minor>\n\t</specVersion>\n\t<actionList>\n\t</actionList>\n\t<serviceStateTable>\n\t</serviceStateTable>\n</scpd>\n',
             '/Layer3Forwarding.xml': 'HTTP/1.1 200 OK\r\nServer: WebServer\r\nDate: Thu, 11 Oct 2018 22:16:16 GMT\r\nContent-Type: text/xml\r\nContent-Length: 920\r\nLast-Modified: Thu, 09 Aug 2018 12:41:07 GMT\r\nConnection: close\r\n\r\n<?xml version="1.0"?>\n<scpd xmlns="urn:schemas-upnp-org:service-1-0">\n\t<specVersion>\n\t\t<major>1</major>\n\t\t<minor>0</minor>\n\t</specVersion>\n\t<actionList>\n\t\t<action>\n\t\t\t<name>GetDefaultConnectionService</name>\n\t\t\t<argumentList>\n\t\t\t\t<argument>\n\t\t\t\t\t<name>NewDefaultConnectionService</name>\n\t\t\t\t\t<direction>out</direction>\n\t\t\t\t\t<relatedStateVariable>DefaultConnectionService</relatedStateVariable>\n\t\t\t\t</argument>\n\t\t\t</argumentList>\n\t\t</action>\n\t\t<action>\n\t\t\t<name>SetDefaultConnectionService</name>\n\t\t\t<argumentList>\n\t\t\t\t<argument>\n\t\t\t\t\t<name>NewDefaultConnectionService</name>\n\t\t\t\t\t<direction>in</direction>\n\t\t\t\t\t<relatedStateVariable>DefaultConnectionService</relatedStateVariable>\n\t\t\t\t</argument>\n\t\t\t</argumentList>\n\t\t</action>\n\t</actionList>\n\t<serviceStateTable>\n\t\t<stateVariable sendEvents="yes">\n\t\t\t<name>DefaultConnectionService</name>\n\t\t\t<dataType>string</dataType>\n\t\t</stateVariable>\n\t</serviceStateTable>\n</scpd>\n',
             '/WANCommonInterfaceConfig.xml': 'HTTP/1.1 200 OK\r\nServer: WebServer\r\nDate: Thu, 11 Oct 2018 22:16:16 GMT\r\nContent-Type: text/xml\r\nContent-Length: 5343\r\nLast-Modified: Thu, 09 Aug 2018 12:41:07 GMT\r\nConnection: close\r\n\r\n<?xml version="1.0"?>\r\n<scpd xmlns="urn:schemas-upnp-org:service-1-0">\r\n\t<specVersion>\r\n\t\t<major>1</major>\r\n\t\t<minor>0</minor>\r\n\t</specVersion>\r\n\t<actionList>\r\n\t\t<action>\r\n\t\t\t<name>GetCommonLinkProperties</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewWANAccessType</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>WANAccessType</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewLayer1UpstreamMaxBitRate</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>Layer1UpstreamMaxBitRate</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewLayer1DownstreamMaxBitRate</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>Layer1DownstreamMaxBitRate</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewPhysicalLinkStatus</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PhysicalLinkStatus</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetTotalBytesSent</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewTotalBytesSent</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalBytesSent</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetTotalBytesReceived</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewTotalBytesReceived</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalBytesReceived</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetTotalPacketsSent</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewTotalPacketsSent</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalPacketsSent</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetTotalPacketsReceived</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewTotalPacketsReceived</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalPacketsReceived</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>X_GetICSStatistics</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>TotalBytesSent</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalBytesSent</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>TotalBytesReceived</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalBytesReceived</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>TotalPacketsSent</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalPacketsSent</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>TotalPacketsReceived</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>TotalPacketsReceived</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>Layer1DownstreamMaxBitRate</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>Layer1DownstreamMaxBitRate</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>Uptime</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>X_Uptime</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t</actionList>\r\n\t<serviceStateTable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>WANAccessType</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t\t<allowedValueList>\r\n\t\t\t\t<allowedValue>DSL</allowedValue>\r\n\t\t\t\t<allowedValue>POTS</allowedValue>\r\n\t\t\t\t<allowedValue>Cable</allowedValue>\r\n\t\t\t\t<allowedValue>Ethernet</allowedValue>\r\n\t\t\t\t<allowedValue>Other</allowedValue>\r\n\t\t\t</allowedValueList>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>Layer1UpstreamMaxBitRate</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>Layer1DownstreamMaxBitRate</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="yes">\r\n\t\t\t<name>PhysicalLinkStatus</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t\t<allowedValueList>\r\n\t\t\t\t<allowedValue>Up</allowedValue>\r\n\t\t\t\t<allowedValue>Down</allowedValue>\r\n\t\t\t\t<allowedValue>Initializing</allowedValue>\r\n\t\t\t\t<allowedValue>Unavailable</allowedValue>\r\n\t\t\t</allowedValueList>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>WANAccessProvider</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>MaximumActiveConnections</name>\r\n\t\t\t<dataType>ui2</dataType>\r\n\t\t\t<allowedValueRange>\r\n\t\t\t\t<minimum>1</minimum>\r\n\t\t\t\t<maximum></maximum>\r\n\t\t\t\t<step>1</step>\r\n\t\t\t</allowedValueRange>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>TotalBytesSent</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>TotalBytesReceived</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>TotalPacketsSent</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>TotalPacketsReceived</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>X_PersonalFirewallEnabled</name>\r\n\t\t\t<dataType>boolean</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>X_Uptime</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t</stateVariable>\r\n\t</serviceStateTable>\r\n</scpd>\r\n',
             '/WANEthernetLinkConfig.xml': 'HTTP/1.1 200 OK\r\nServer: WebServer\r\nDate: Thu, 11 Oct 2018 22:16:16 GMT\r\nContent-Type: text/xml\r\nContent-Length: 773\r\nLast-Modified: Thu, 09 Aug 2018 12:41:07 GMT\r\nConnection: close\r\n\r\n<?xml version="1.0"?>\n<scpd xmlns="urn:schemas-upnp-org:service-1-0">\n\t<specVersion>\n\t\t<major>1</major>\n\t\t<minor>0</minor>\n\t</specVersion>\n\t<actionList>\n\t\t<action>\n\t\t\t<name>GetEthernetLinkStatus</name>\n\t\t\t<argumentList>\n\t\t\t\t<argument>\n\t\t\t\t\t<name>NewEthernetLinkStatus</name>\n\t\t\t\t\t<direction>out</direction>\n\t\t\t\t\t<relatedStateVariable>EthernetLinkStatus</relatedStateVariable>\n\t\t\t\t</argument>\n\t\t\t</argumentList>\n\t\t</action>\n\t</actionList>\n\t<serviceStateTable>\n\t\t<stateVariable sendEvents="yes">\n\t\t\t<name>EthernetLinkStatus</name>\n\t\t\t<dataType>string</dataType>\n\t\t\t<allowedValueList>\n\t\t\t\t<allowedValue>Up</allowedValue>\n\t\t\t\t<allowedValue>Down</allowedValue>\n\t\t\t\t<allowedValue>Unavailable</allowedValue>\n\t\t\t</allowedValueList>\n\t\t</stateVariable>\n\t</serviceStateTable>\n</scpd>\n',
             '/WANIPConnection.xml': 'HTTP/1.1 200 OK\r\nServer: WebServer\r\nDate: Thu, 11 Oct 2018 22:16:16 GMT\r\nContent-Type: text/xml\r\nContent-Length: 12078\r\nLast-Modified: Thu, 09 Aug 2018 12:41:07 GMT\r\nConnection: close\r\n\r\n<?xml version="1.0"?>\r\n<scpd xmlns="urn:schemas-upnp-org:service-1-0">\r\n\t<specVersion>\r\n\t\t<major>1</major>\r\n\t\t<minor>0</minor>\r\n\t</specVersion>\r\n\t<actionList>\r\n\t\t<action>\r\n\t\t\t<name>SetConnectionType</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewConnectionType</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>ConnectionType</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action> \r\n\t\t<action>\r\n\t\t\t<name>GetConnectionTypeInfo</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewConnectionType</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>ConnectionType</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewPossibleConnectionTypes</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PossibleConnectionTypes</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>RequestConnection</name>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>ForceTermination</name>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetStatusInfo</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewConnectionStatus</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>ConnectionStatus</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewLastConnectionError</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>LastConnectionError</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewUptime</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>Uptime</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetNATRSIPStatus</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewRSIPAvailable</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>RSIPAvailable</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewNATEnabled</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>NATEnabled</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetGenericPortMappingEntry</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewPortMappingIndex</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingNumberOfEntries</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewRemoteHost</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>RemoteHost</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewExternalPort</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>ExternalPort</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewProtocol</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingProtocol</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewInternalPort</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>InternalPort</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewInternalClient</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>InternalClient</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewEnabled</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingEnabled</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewPortMappingDescription</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingDescription</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewLeaseDuration</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingLeaseDuration</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetSpecificPortMappingEntry</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewRemoteHost</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>RemoteHost</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewExternalPort</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>ExternalPort</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewProtocol</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingProtocol</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewInternalPort</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>InternalPort</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewInternalClient</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>InternalClient</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewEnabled</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingEnabled</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewPortMappingDescription</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingDescription</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewLeaseDuration</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingLeaseDuration</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>AddPortMapping</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewRemoteHost</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>RemoteHost</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewExternalPort</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>ExternalPort</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewProtocol</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingProtocol</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewInternalPort</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>InternalPort</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewInternalClient</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>InternalClient</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewEnabled</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingEnabled</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewPortMappingDescription</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingDescription</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewLeaseDuration</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingLeaseDuration</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>DeletePortMapping</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewRemoteHost</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>RemoteHost</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewExternalPort</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>ExternalPort</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewProtocol</name>\r\n\t\t\t\t\t<direction>in</direction>\r\n\t\t\t\t\t<relatedStateVariable>PortMappingProtocol</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t\t<action>\r\n\t\t\t<name>GetExternalIPAddress</name>\r\n\t\t\t<argumentList>\r\n\t\t\t\t<argument>\r\n\t\t\t\t\t<name>NewExternalIPAddress</name>\r\n\t\t\t\t\t<direction>out</direction>\r\n\t\t\t\t\t<relatedStateVariable>ExternalIPAddress</relatedStateVariable>\r\n\t\t\t\t</argument>\r\n\t\t\t</argumentList>\r\n\t\t</action>\r\n\t</actionList>\r\n\t<serviceStateTable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>ConnectionType</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t\t<defaultValue>Unconfigured</defaultValue>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="yes">\r\n\t\t\t<name>PossibleConnectionTypes</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t\t<allowedValueList>\r\n\t\t\t\t<allowedValue>Unconfigured</allowedValue>\r\n\t\t\t\t<allowedValue>IP_Routed</allowedValue>\r\n\t\t\t\t<allowedValue>IP_Bridged</allowedValue>\r\n\t\t\t</allowedValueList>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="yes">\r\n\t\t\t<name>ConnectionStatus</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t\t<defaultValue>Unconfigured</defaultValue>\r\n\t\t\t<allowedValueList>\r\n\t\t\t\t<allowedValue>Unconfigured</allowedValue>\r\n\t\t\t\t<allowedValue>Connecting</allowedValue>\r\n\t\t\t\t<allowedValue>Authenticating</allowedValue>\r\n\t\t\t\t<allowedValue>PendingDisconnect</allowedValue>\r\n\t\t\t\t<allowedValue>Disconnecting</allowedValue>\r\n\t\t\t\t<allowedValue>Disconnected</allowedValue>\r\n\t\t\t\t<allowedValue>Connected</allowedValue>\r\n\t\t\t</allowedValueList>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>Uptime</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t\t<defaultValue>0</defaultValue>\r\n\t\t\t<allowedValueRange>\r\n\t\t\t\t<minimum>0</minimum>\r\n\t\t\t\t<maximum></maximum>\r\n\t\t\t\t<step>1</step>\r\n\t\t\t</allowedValueRange>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>RSIPAvailable</name>\r\n\t\t<dataType>boolean</dataType>\r\n\t\t\t<defaultValue>0</defaultValue>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>NATEnabled</name>\r\n\t\t\t<dataType>boolean</dataType>\r\n\t\t\t<defaultValue>1</defaultValue>\r\n\t\t</stateVariable>  \r\n\t\t<stateVariable sendEvents="yes">\r\n\t\t\t<name>X_Name</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>LastConnectionError</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t\t<defaultValue>ERROR_NONE</defaultValue>\r\n\t\t\t<allowedValueList>\r\n\t\t\t\t<allowedValue>ERROR_NONE</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_ISP_TIME_OUT</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_COMMAND_ABORTED</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_NOT_ENABLED_FOR_INTERNET</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_BAD_PHONE_NUMBER</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_USER_DISCONNECT</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_ISP_DISCONNECT</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_IDLE_DISCONNECT</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_FORCED_DISCONNECT</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_SERVER_OUT_OF_RESOURCES</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_RESTRICTED_LOGON_HOURS</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_ACCOUNT_DISABLED</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_ACCOUNT_EXPIRED</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_PASSWORD_EXPIRED</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_AUTHENTICATION_FAILURE</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_NO_DIALTONE</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_NO_CARRIER</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_NO_ANSWER</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_LINE_BUSY</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_UNSUPPORTED_BITSPERSECOND</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_TOO_MANY_LINE_ERRORS</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_IP_CONFIGURATION</allowedValue>\r\n\t\t\t\t<allowedValue>ERROR_UNKNOWN</allowedValue>\r\n\t\t\t</allowedValueList>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="yes">\r\n\t\t\t<name>ExternalIPAddress</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>RemoteHost</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>ExternalPort</name>\r\n\t\t\t<dataType>ui2</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>InternalPort</name>\r\n\t\t\t<dataType>ui2</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>PortMappingProtocol</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t\t<allowedValueList>\r\n\t\t\t\t<allowedValue>TCP</allowedValue>\r\n\t\t\t\t<allowedValue>UDP</allowedValue>\r\n\t\t\t</allowedValueList>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>InternalClient</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>PortMappingDescription</name>\r\n\t\t\t<dataType>string</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>PortMappingEnabled</name>\r\n\t\t\t<dataType>boolean</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="no">\r\n\t\t\t<name>PortMappingLeaseDuration</name>\r\n\t\t\t<dataType>ui4</dataType>\r\n\t\t</stateVariable>\r\n\t\t<stateVariable sendEvents="yes">\r\n\t\t\t<name>PortMappingNumberOfEntries</name>\r\n\t\t\t<dataType>ui2</dataType>\r\n\t\t</stateVariable>\r\n\t</serviceStateTable>\r\n</scpd>\r\n'},
         'services': {'/OSInfo.xml': OrderedDict([('serviceType', 'urn:schemas-microsoft-com:service:OSInfo:1'),
                                                  ('serviceId', 'urn:microsoft-com:serviceId:OSInfo1'),
                                                  ('controlURL', '/soap.cgi?service=OSInfo1'),
                                                  ('eventSubURL', '/gena.cgi?service=OSInfo1'),
                                                  ('SCPDURL', '/OSInfo.xml')]), '/Layer3Forwarding.xml': OrderedDict(
             [('serviceType', 'urn:schemas-upnp-org:service:Layer3Forwarding:1'),
              ('serviceId', 'urn:upnp-org:serviceId:L3Forwarding1'), ('controlURL', '/soap.cgi?service=L3Forwarding1'),
              ('eventSubURL', '/gena.cgi?service=L3Forwarding1'), ('SCPDURL', '/Layer3Forwarding.xml')]),
                      '/WANCommonInterfaceConfig.xml': OrderedDict(
                          [('serviceType', 'urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1'),
                           ('serviceId', 'urn:upnp-org:serviceId:WANCommonIFC1'),
                           ('controlURL', '/soap.cgi?service=WANCommonIFC1'),
                           ('eventSubURL', '/gena.cgi?service=WANCommonIFC1'),
                           ('SCPDURL', '/WANCommonInterfaceConfig.xml')]), '/WANEthernetLinkConfig.xml': OrderedDict(
                 [('serviceType', 'urn:schemas-upnp-org:service:WANEthernetLinkConfig:1'),
                  ('serviceId', 'urn:upnp-org:serviceId:WANEthLinkC1'),
                  ('controlURL', '/soap.cgi?service=WANEthLinkC1'), ('eventSubURL', '/gena.cgi?service=WANEthLinkC1'),
                  ('SCPDURL', '/WANEthernetLinkConfig.xml')]), '/WANIPConnection.xml': OrderedDict(
                 [('serviceType', 'urn:schemas-upnp-org:service:WANIPConnection:1'),
                  ('serviceId', 'urn:upnp-org:serviceId:WANIPConn1'), ('controlURL', '/soap.cgi?service=WANIPConn1'),
                  ('eventSubURL', '/gena.cgi?service=WANIPConn1'), ('SCPDURL', '/WANIPConnection.xml')])},
         'reply': OrderedDict(
            [('CACHE_CONTROL', 'max-age=1800'), ('LOCATION', 'http://10.0.0.1:49152/InternetGatewayDevice.xml'),
             ('SERVER', 'Linux, UPnP/1.0, DIR-890L Ver 1.20'), ('ST', 'urn:schemas-upnp-org:device:WANDevice:1'),
             ('USN', 'uuid:11111111-2222-3333-4444-555555555555::urn:schemas-upnp-org:device:WANDevice:1')]),
         'soap_port': 49152,
         'registered_soap_commands': {'GetGenericPortMappingEntry': 'urn:schemas-upnp-org:service:WANIPConnection:1',
                                      'GetSpecificPortMappingEntry': 'urn:schemas-upnp-org:service:WANIPConnection:1',
                                      'AddPortMapping': 'urn:schemas-upnp-org:service:WANIPConnection:1',
                                      'DeletePortMapping': 'urn:schemas-upnp-org:service:WANIPConnection:1',
                                      'GetExternalIPAddress': 'urn:schemas-upnp-org:service:WANIPConnection:1'},
         'unsupported_soap_commands': {
             'urn:schemas-upnp-org:service:Layer3Forwarding:1': ['GetDefaultConnectionService',
                                                                 'SetDefaultConnectionService'],
             'urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1': ['GetCommonLinkProperties', 'GetTotalBytesSent',
                                                                         'GetTotalBytesReceived', 'GetTotalPacketsSent',
                                                                         'GetTotalPacketsReceived',
                                                                         'X_GetICSStatistics'],
             'urn:schemas-upnp-org:service:WANEthernetLinkConfig:1': ['GetEthernetLinkStatus'],
             'urn:schemas-upnp-org:service:WANIPConnection:1': ['SetConnectionType', 'GetConnectionTypeInfo',
                                                                'RequestConnection', 'ForceTermination',
                                                                'GetStatusInfo', 'GetNATRSIPStatus']},
         'soap_requests': []}

    client_address = "10.0.0.2"

    def setUp(self) -> None:
        self.replies = {
            (
                f"GET {path} HTTP/1.1\r\n"
                f"Accept-Encoding: gzip\r\n"
                f"Host: {self.gateway_info['gateway_address']}\r\n"
                f"Connection: Close\r\n"
                f"\r\n"
            ).encode(): xml_bytes.encode()
            for path, xml_bytes in self.gateway_info['services_xml'].items()
        }
        self.replies.update({
            (
                f"GET /{self.gateway_info['location'].lstrip(self.gateway_info['urlBase'])} HTTP/1.1\r\n"
                f"Accept-Encoding: gzip\r\n"
                f"Host: {self.gateway_info['gateway_address']}\r\n"
                f"Connection: Close\r\n"
                f"\r\n"
            ).encode(): self.gateway_info['gateway_xml'].encode()
        })
        super().setUp()

    async def test_discover_gateway(self):
        with self.assertRaises(UPnPError) as e1:
            with mock_tcp_and_udp(self.loop):
                await Gateway.discover_gateway(self.client_address, self.gateway_info['gateway_address'], 2,
                                               loop=self.loop)
        with self.assertRaises(UPnPError) as e2:
            with mock_tcp_and_udp(self.loop):
                await Gateway.discover_gateway(self.client_address, self.gateway_info['gateway_address'], 2,
                                               loop=self.loop)
        self.assertEqual(str(e1.exception), f"M-SEARCH for {self.gateway_info['gateway_address']}:1900 timed out")
        self.assertEqual(str(e2.exception), f"M-SEARCH for {self.gateway_info['gateway_address']}:1900 timed out")

    async def test_discover_commands(self):
        with mock_tcp_and_udp(self.loop, tcp_replies=self.replies):
            gateway = Gateway(
                SSDPDatagram("OK", self.gateway_info['reply']),
                self.client_address, self.gateway_info['gateway_address'], loop=self.loop
            )
            await gateway.discover_commands()
            self.assertDictEqual(self.gateway_info['registered_soap_commands'], gateway._registered_commands)
            self.assertDictEqual(gateway.debug_gateway(), self.gateway_info)


class TestDiscoverNetgearNighthawkAC2350(TestDiscoverDLinkDIR890L):
    gateway_info = {'manufacturer_string': 'NETGEAR NETGEAR Nighthawk X4 AC2350 Smart WiFi Router',
                    'gateway_address': '192.168.0.1', 'server': 'R7500v2 UPnP/1.0 miniupnpd/1.0',
                    'urlBase': 'http://192.168.0.1:5555', 'location': 'http://192.168.0.1:5555/rootDesc.xml',
                    'specVersion': {'major': '1', 'minor': '0'},
                    'usn': 'uuid:11111111-2222-3333-4444-555555555555::upnp:rootdevice', 'urn': 'upnp:rootdevice',
                    'gateway_xml': 'HTTP/1.1 200 OK\r\nContent-Type: text/xml; charset="utf-8"\r\nConnection: close\r\nContent-Length: 3720\r\nServer: R7500v2 UPnP/1.0 miniupnpd/1.0\r\nExt: \r\nContent-Language: en-US\r\n\r\n<?xml version="1.0"?>\n<root xmlns="urn:schemas-upnp-org:device-1-0" \txmlns:pnpx="http://schemas.microsoft.com/windows/pnpx/2005/11" \txmlns:df="http://schemas.microsoft.com/windows/2008/09/devicefoundation"><specVersion><major>1</major><minor>0</minor></specVersion><URLBase>http://192.168.0.1:5555</URLBase><device><pnpx:X_hardwareId>VEN_01f2&amp;DEV_0018&amp;REV_02 VEN_01f2&amp;DEV_8000&amp;SUBSYS_01&amp;REV_01 VEN_01f2&amp;DEV_8000&amp;REV_01 VEN_0033&amp;DEV_0008&amp;REV_01</pnpx:X_hardwareId><pnpx:X_compatibleId>urn:schemas-upnp-org:device:InternetGatewayDevice:1</pnpx:X_compatibleId><pnpx:X_deviceCategory>NetworkInfrastructure.Router</pnpx:X_deviceCategory><df:X_deviceCategory>Network.Router.Wireless</df:X_deviceCategory><deviceType>urn:schemas-upnp-org:device:InternetGatewayDevice:1</deviceType><friendlyName>R7500v2 (Gateway)</friendlyName><manufacturer>NETGEAR, Inc.</manufacturer><manufacturerURL>http://www.netgear.com</manufacturerURL><modelDescription>NETGEAR R7500v2 NETGEAR Nighthawk X4 AC2350 Smart WiFi Router</modelDescription><modelName>NETGEAR Nighthawk X4 AC2350 Smart WiFi Router</modelName><modelNumber>R7500v2</modelNumber><modelURL>http://www.netgear.com/home/products/wirelessrouters</modelURL><serialNumber>v1</serialNumber><UDN>uuid:11111111-2222-3333-4444-555555555555</UDN><UPC>606449084528</UPC><serviceList><service><serviceType>urn:schemas-upnp-org:service:Layer3Forwarding:1</serviceType><serviceId>urn:upnp-org:serviceId:L3Forwarding1</serviceId><controlURL>/ctl/L3Forwarding</controlURL><eventSubURL>/evt/L3Forwarding</eventSubURL><SCPDURL>/Layer3F.xml</SCPDURL></service></serviceList><deviceList><device><deviceType>urn:schemas-upnp-org:device:WANDevice:1</deviceType><friendlyName>WAN Device</friendlyName><manufacturer>NETGEAR</manufacturer><manufacturerURL>http://www.netgear.com</manufacturerURL><modelDescription>WAN Device on NETGEAR R7500v2 Wireless Router</modelDescription><modelName>NETGEAR Nighthawk X4 AC2350 Smart WiFi Router</modelName><modelNumber>R7500v2</modelNumber><modelURL>http://www.netgear.com</modelURL><serialNumber>v1</serialNumber><UDN>uuid:11111111-2222-3333-4444-555555555555</UDN><UPC>1234567890ab</UPC><serviceList><service><serviceType>urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1</serviceType><serviceId>urn:upnp-org:serviceId:WANCommonIFC1</serviceId><controlURL>/ctl/CommonIfCfg</controlURL><eventSubURL>/evt/CommonIfCfg</eventSubURL><SCPDURL>/WANCfg.xml</SCPDURL></service></serviceList><deviceList><device><deviceType>urn:schemas-upnp-org:device:WANConnectionDevice:1</deviceType><friendlyName>WAN Connection Device</friendlyName><manufacturer>NETGEAR</manufacturer><manufacturerURL>http://www.netgear.com</manufacturerURL><modelDescription>WANConnectionDevice on NETGEAR R7500v2 Wireless Router</modelDescription><modelName>NETGEAR Nighthawk X4 AC2350 Smart WiFi Router</modelName><modelNumber>R7500v2</modelNumber><modelURL>http://www.netgear.com</modelURL><serialNumber>v1</serialNumber><UDN>uuid:4d696e69-444c-164e-9d44-b0b98a4cd3c3</UDN><UPC>1234567890ab</UPC><serviceList><service><serviceType>urn:schemas-upnp-org:service:WANEthernetLinkConfig:1</serviceType><serviceId>urn:upnp-org:serviceId:WANEthLinkC1</serviceId><controlURL>/ctl/WanEth</controlURL><eventSubURL>/evt/WanEth</eventSubURL><SCPDURL>/WanEth.xml</SCPDURL></service><service><serviceType>urn:schemas-upnp-org:service:WANIPConnection:1</serviceType><serviceId>urn:upnp-org:serviceId:WANIPConn1</serviceId><controlURL>/ctl/IPConn</controlURL><eventSubURL>/evt/IPConn</eventSubURL><SCPDURL>/WANIPCn.xml</SCPDURL></service></serviceList></device></deviceList></device></deviceList><presentationURL>http://www.routerlogin.net</presentationURL></device></root>',
                    'services_xml': {
                        '/Layer3F.xml': 'HTTP/1.1 200 OK\r\nContent-Type: text/xml; charset="utf-8"\r\nConnection: close\r\nContent-Length: 794\r\nServer: R7500v2 UPnP/1.0 miniupnpd/1.0\r\nExt: \r\nContent-Language: en-US\r\n\r\n<?xml version="1.0"?>\n<scpd xmlns="urn:schemas-upnp-org:service-1-0"><specVersion><major>1</major><minor>0</minor></specVersion><actionList><action><name>SetDefaultConnectionService</name><argumentList><argument><name>NewDefaultConnectionService</name><direction>in</direction><relatedStateVariable>DefaultConnectionService</relatedStateVariable></argument></argumentList></action><action><name>GetDefaultConnectionService</name><argumentList><argument><name>NewDefaultConnectionService</name><direction>out</direction><relatedStateVariable>DefaultConnectionService</relatedStateVariable></argument></argumentList></action></actionList><serviceStateTable><stateVariable sendEvents="yes"><name>DefaultConnectionService</name><dataType>string</dataType></stateVariable></serviceStateTable></scpd>',
                        '/WANCfg.xml': 'HTTP/1.1 200 OK\r\nContent-Type: text/xml; charset="utf-8"\r\nConnection: close\r\nContent-Length: 2942\r\nServer: R7500v2 UPnP/1.0 miniupnpd/1.0\r\nExt: \r\nContent-Language: en-US\r\n\r\n<?xml version="1.0"?>\n<scpd xmlns="urn:schemas-upnp-org:service-1-0"><specVersion><major>1</major><minor>0</minor></specVersion><actionList><action><name>GetCommonLinkProperties</name><argumentList><argument><name>NewWANAccessType</name><direction>out</direction><relatedStateVariable>WANAccessType</relatedStateVariable></argument><argument><name>NewLayer1UpstreamMaxBitRate</name><direction>out</direction><relatedStateVariable>Layer1UpstreamMaxBitRate</relatedStateVariable></argument><argument><name>NewLayer1DownstreamMaxBitRate</name><direction>out</direction><relatedStateVariable>Layer1DownstreamMaxBitRate</relatedStateVariable></argument><argument><name>NewPhysicalLinkStatus</name><direction>out</direction><relatedStateVariable>PhysicalLinkStatus</relatedStateVariable></argument></argumentList></action><action><name>GetTotalBytesSent</name><argumentList><argument><name>NewTotalBytesSent</name><direction>out</direction><relatedStateVariable>TotalBytesSent</relatedStateVariable></argument></argumentList></action><action><name>GetTotalBytesReceived</name><argumentList><argument><name>NewTotalBytesReceived</name><direction>out</direction><relatedStateVariable>TotalBytesReceived</relatedStateVariable></argument></argumentList></action><action><name>GetTotalPacketsSent</name><argumentList><argument><name>NewTotalPacketsSent</name><direction>out</direction><relatedStateVariable>TotalPacketsSent</relatedStateVariable></argument></argumentList></action><action><name>GetTotalPacketsReceived</name><argumentList><argument><name>NewTotalPacketsReceived</name><direction>out</direction><relatedStateVariable>TotalPacketsReceived</relatedStateVariable></argument></argumentList></action></actionList><serviceStateTable><stateVariable sendEvents="no"><name>WANAccessType</name><dataType>string</dataType><allowedValueList><allowedValue>DSL</allowedValue><allowedValue>POTS</allowedValue><allowedValue>Cable</allowedValue><allowedValue>Ethernet</allowedValue></allowedValueList></stateVariable><stateVariable sendEvents="no"><name>Layer1UpstreamMaxBitRate</name><dataType>ui4</dataType></stateVariable><stateVariable sendEvents="no"><name>Layer1DownstreamMaxBitRate</name><dataType>ui4</dataType></stateVariable><stateVariable sendEvents="yes"><name>PhysicalLinkStatus</name><dataType>string</dataType><allowedValueList><allowedValue>Up</allowedValue><allowedValue>Down</allowedValue><allowedValue>Initializing</allowedValue><allowedValue>Unavailable</allowedValue></allowedValueList></stateVariable><stateVariable sendEvents="no"><name>TotalBytesSent</name><dataType>ui4</dataType></stateVariable><stateVariable sendEvents="no"><name>TotalBytesReceived</name><dataType>ui4</dataType></stateVariable><stateVariable sendEvents="no"><name>TotalPacketsSent</name><dataType>ui4</dataType></stateVariable><stateVariable sendEvents="no"><name>TotalPacketsReceived</name><dataType>ui4</dataType></stateVariable></serviceStateTable></scpd>',
                        '/WanEth.xml': 'HTTP/1.1 200 OK\r\nContent-Type: text/xml; charset="utf-8"\r\nConnection: close\r\nContent-Length: 711\r\nServer: R7500v2 UPnP/1.0 miniupnpd/1.0\r\nExt: \r\nContent-Language: en-US\r\n\r\n<?xml version="1.0"?>\n<scpd xmlns="urn:schemas-upnp-org:service-1-0"><specVersion><major>1</major><minor>0</minor></specVersion><actionList><action><name>GetEthernetLinkStatus</name><argumentList><argument><name>NewEthernetLinkStatus</name><direction>out</direction><relatedStateVariable>EthernetLinkStatus</relatedStateVariable></argument></argumentList></action></actionList><serviceStateTable><stateVariable sendEvents="yes"><name>EthernetLinkStatus</name><dataType>string</dataType><allowedValueList><allowedValue>Up</allowedValue><allowedValue>Down</allowedValue><allowedValue>Initializing</allowedValue><allowedValue>Unavailable</allowedValue></allowedValueList></stateVariable></serviceStateTable></scpd>',
                        '/WANIPCn.xml': 'HTTP/1.1 200 OK\r\nContent-Type: text/xml; charset="utf-8"\r\nConnection: close\r\nContent-Length: 8400\r\nServer: R7500v2 UPnP/1.0 miniupnpd/1.0\r\nExt: \r\nContent-Language: en-US\r\n\r\n<?xml version="1.0"?>\n<scpd xmlns="urn:schemas-upnp-org:service-1-0"><specVersion><major>1</major><minor>0</minor></specVersion><actionList><action><name>AddPortMapping</name><argumentList><argument><name>NewRemoteHost</name><direction>in</direction><relatedStateVariable>RemoteHost</relatedStateVariable></argument><argument><name>NewExternalPort</name><direction>in</direction><relatedStateVariable>ExternalPort</relatedStateVariable></argument><argument><name>NewProtocol</name><direction>in</direction><relatedStateVariable>PortMappingProtocol</relatedStateVariable></argument><argument><name>NewInternalPort</name><direction>in</direction><relatedStateVariable>InternalPort</relatedStateVariable></argument><argument><name>NewInternalClient</name><direction>in</direction><relatedStateVariable>InternalClient</relatedStateVariable></argument><argument><name>NewEnabled</name><direction>in</direction><relatedStateVariable>PortMappingEnabled</relatedStateVariable></argument><argument><name>NewPortMappingDescription</name><direction>in</direction><relatedStateVariable>PortMappingDescription</relatedStateVariable></argument><argument><name>NewLeaseDuration</name><direction>in</direction><relatedStateVariable>PortMappingLeaseDuration</relatedStateVariable></argument></argumentList></action><action><name>GetExternalIPAddress</name><argumentList><argument><name>NewExternalIPAddress</name><direction>out</direction><relatedStateVariable>ExternalIPAddress</relatedStateVariable></argument></argumentList></action><action><name>DeletePortMapping</name><argumentList><argument><name>NewRemoteHost</name><direction>in</direction><relatedStateVariable>RemoteHost</relatedStateVariable></argument><argument><name>NewExternalPort</name><direction>in</direction><relatedStateVariable>ExternalPort</relatedStateVariable></argument><argument><name>NewProtocol</name><direction>in</direction><relatedStateVariable>PortMappingProtocol</relatedStateVariable></argument></argumentList></action><action><name>SetConnectionType</name><argumentList><argument><name>NewConnectionType</name><direction>in</direction><relatedStateVariable>ConnectionType</relatedStateVariable></argument></argumentList></action><action><name>GetConnectionTypeInfo</name><argumentList><argument><name>NewConnectionType</name><direction>out</direction><relatedStateVariable>ConnectionType</relatedStateVariable></argument><argument><name>NewPossibleConnectionTypes</name><direction>out</direction><relatedStateVariable>PossibleConnectionTypes</relatedStateVariable></argument></argumentList></action><action><name>RequestConnection</name></action><action><name>ForceTermination</name></action><action><name>GetStatusInfo</name><argumentList><argument><name>NewConnectionStatus</name><direction>out</direction><relatedStateVariable>ConnectionStatus</relatedStateVariable></argument><argument><name>NewLastConnectionError</name><direction>out</direction><relatedStateVariable>LastConnectionError</relatedStateVariable></argument><argument><name>NewUptime</name><direction>out</direction><relatedStateVariable>Uptime</relatedStateVariable></argument></argumentList></action><action><name>GetNATRSIPStatus</name><argumentList><argument><name>NewRSIPAvailable</name><direction>out</direction><relatedStateVariable>RSIPAvailable</relatedStateVariable></argument><argument><name>NewNATEnabled</name><direction>out</direction><relatedStateVariable>NATEnabled</relatedStateVariable></argument></argumentList></action><action><name>GetGenericPortMappingEntry</name><argumentList><argument><name>NewPortMappingIndex</name><direction>in</direction><relatedStateVariable>PortMappingNumberOfEntries</relatedStateVariable></argument><argument><name>NewRemoteHost</name><direction>out</direction><relatedStateVariable>RemoteHost</relatedStateVariable></argument><argument><name>NewExternalPort</name><direction>out</direction><relatedStateVariable>ExternalPort</relatedStateVariable></argument><argument><name>NewProtocol</name><direction>out</direction><relatedStateVariable>PortMappingProtocol</relatedStateVariable></argument><argument><name>NewInternalPort</name><direction>out</direction><relatedStateVariable>InternalPort</relatedStateVariable></argument><argument><name>NewInternalClient</name><direction>out</direction><relatedStateVariable>InternalClient</relatedStateVariable></argument><argument><name>NewEnabled</name><direction>out</direction><relatedStateVariable>PortMappingEnabled</relatedStateVariable></argument><argument><name>NewPortMappingDescription</name><direction>out</direction><relatedStateVariable>PortMappingDescription</relatedStateVariable></argument><argument><name>NewLeaseDuration</name><direction>out</direction><relatedStateVariable>PortMappingLeaseDuration</relatedStateVariable></argument></argumentList></action><action><name>GetSpecificPortMappingEntry</name><argumentList><argument><name>NewRemoteHost</name><direction>in</direction><relatedStateVariable>RemoteHost</relatedStateVariable></argument><argument><name>NewExternalPort</name><direction>in</direction><relatedStateVariable>ExternalPort</relatedStateVariable></argument><argument><name>NewProtocol</name><direction>in</direction><relatedStateVariable>PortMappingProtocol</relatedStateVariable></argument><argument><name>NewInternalPort</name><direction>out</direction><relatedStateVariable>InternalPort</relatedStateVariable></argument><argument><name>NewInternalClient</name><direction>out</direction><relatedStateVariable>InternalClient</relatedStateVariable></argument><argument><name>NewEnabled</name><direction>out</direction><relatedStateVariable>PortMappingEnabled</relatedStateVariable></argument><argument><name>NewPortMappingDescription</name><direction>out</direction><relatedStateVariable>PortMappingDescription</relatedStateVariable></argument><argument><name>NewLeaseDuration</name><direction>out</direction><relatedStateVariable>PortMappingLeaseDuration</relatedStateVariable></argument></argumentList></action></actionList><serviceStateTable><stateVariable sendEvents="no"><name>ConnectionType</name><dataType>string</dataType></stateVariable><stateVariable sendEvents="yes"><name>PossibleConnectionTypes</name><dataType>string</dataType><allowedValueList><allowedValue>Unconfigured</allowedValue><allowedValue>IP_Routed</allowedValue><allowedValue>IP_Bridged</allowedValue></allowedValueList></stateVariable><stateVariable sendEvents="yes"><name>ConnectionStatus</name><dataType>string</dataType><allowedValueList><allowedValue>Unconfigured</allowedValue><allowedValue>Connecting</allowedValue><allowedValue>Connected</allowedValue><allowedValue>PendingDisconnect</allowedValue><allowedValue>Disconnecting</allowedValue><allowedValue>Disconnected</allowedValue></allowedValueList></stateVariable><stateVariable sendEvents="no"><name>Uptime</name><dataType>ui4</dataType></stateVariable><stateVariable sendEvents="no"><name>LastConnectionError</name><dataType>string</dataType><allowedValueList><allowedValue>ERROR_NONE</allowedValue></allowedValueList></stateVariable><stateVariable sendEvents="no"><name>RSIPAvailable</name><dataType>boolean</dataType></stateVariable><stateVariable sendEvents="no"><name>NATEnabled</name><dataType>boolean</dataType></stateVariable><stateVariable sendEvents="yes"><name>ExternalIPAddress</name><dataType>string</dataType></stateVariable><stateVariable sendEvents="yes"><name>PortMappingNumberOfEntries</name><dataType>ui2</dataType></stateVariable><stateVariable sendEvents="no"><name>PortMappingEnabled</name><dataType>boolean</dataType></stateVariable><stateVariable sendEvents="no"><name>PortMappingLeaseDuration</name><dataType>ui4</dataType></stateVariable><stateVariable sendEvents="no"><name>RemoteHost</name><dataType>string</dataType></stateVariable><stateVariable sendEvents="no"><name>ExternalPort</name><dataType>ui2</dataType></stateVariable><stateVariable sendEvents="no"><name>InternalPort</name><dataType>ui2</dataType></stateVariable><stateVariable sendEvents="no"><name>PortMappingProtocol</name><dataType>string</dataType><allowedValueList><allowedValue>TCP</allowedValue><allowedValue>UDP</allowedValue></allowedValueList></stateVariable><stateVariable sendEvents="no"><name>InternalClient</name><dataType>string</dataType></stateVariable><stateVariable sendEvents="no"><name>PortMappingDescription</name><dataType>string</dataType></stateVariable></serviceStateTable></scpd>'},
                    'services': {'/Layer3F.xml': OrderedDict(
                        [('serviceType', 'urn:schemas-upnp-org:service:Layer3Forwarding:1'),
                         ('serviceId', 'urn:upnp-org:serviceId:L3Forwarding1'), ('controlURL', '/ctl/L3Forwarding'),
                         ('eventSubURL', '/evt/L3Forwarding'), ('SCPDURL', '/Layer3F.xml')]),
                                 '/WANCfg.xml': OrderedDict(
                                     [('serviceType', 'urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1'),
                                      ('serviceId', 'urn:upnp-org:serviceId:WANCommonIFC1'),
                                      ('controlURL', '/ctl/CommonIfCfg'), ('eventSubURL', '/evt/CommonIfCfg'),
                                      ('SCPDURL', '/WANCfg.xml')]), '/WanEth.xml': OrderedDict(
                            [('serviceType', 'urn:schemas-upnp-org:service:WANEthernetLinkConfig:1'),
                             ('serviceId', 'urn:upnp-org:serviceId:WANEthLinkC1'), ('controlURL', '/ctl/WanEth'),
                             ('eventSubURL', '/evt/WanEth'), ('SCPDURL', '/WanEth.xml')]), '/WANIPCn.xml': OrderedDict(
                            [('serviceType', 'urn:schemas-upnp-org:service:WANIPConnection:1'),
                             ('serviceId', 'urn:upnp-org:serviceId:WANIPConn1'), ('controlURL', '/ctl/IPConn'),
                             ('eventSubURL', '/evt/IPConn'), ('SCPDURL', '/WANIPCn.xml')])},
                    'reply': OrderedDict(
            [('CACHE_CONTROL', 'max-age=1800'), ('ST', 'upnp:rootdevice'),
             ('USN', 'uuid:11111111-2222-3333-4444-555555555555::upnp:rootdevice'),
             ('Server', 'R7500v2 UPnP/1.0 miniupnpd/1.0'), ('Location', 'http://192.168.0.1:5555/rootDesc.xml')]),
                    'soap_port': 5555,
                    'registered_soap_commands': {'AddPortMapping': 'urn:schemas-upnp-org:service:WANIPConnection:1',
                                                 'GetExternalIPAddress': 'urn:schemas-upnp-org:service:WANIPConnection:1',
                                                 'DeletePortMapping': 'urn:schemas-upnp-org:service:WANIPConnection:1',
                                                 'GetGenericPortMappingEntry': 'urn:schemas-upnp-org:service:WANIPConnection:1',
                                                 'GetSpecificPortMappingEntry': 'urn:schemas-upnp-org:service:WANIPConnection:1'},
                    'unsupported_soap_commands': {
                        'urn:schemas-upnp-org:service:Layer3Forwarding:1': ['SetDefaultConnectionService',
                                                                            'GetDefaultConnectionService'],
                        'urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1': ['GetCommonLinkProperties',
                                                                                    'GetTotalBytesSent',
                                                                                    'GetTotalBytesReceived',
                                                                                    'GetTotalPacketsSent',
                                                                                    'GetTotalPacketsReceived'],
                        'urn:schemas-upnp-org:service:WANEthernetLinkConfig:1': ['GetEthernetLinkStatus'],
                        'urn:schemas-upnp-org:service:WANIPConnection:1': ['SetConnectionType', 'GetConnectionTypeInfo',
                                                                           'RequestConnection', 'ForceTermination',
                                                                           'GetStatusInfo', 'GetNATRSIPStatus']},
                    'soap_requests': []}


class TestActiontec(AsyncioTestCase):
    name = "Actiontec GT784WN"
    _location_key = 'Location'

    @property
    def data_path(self):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "replays", self.name)

    def _get_location(self):
        # return self.gateway_info['reply']['Location'].split(self.gateway_address)[-1]
        return self.gateway_info['reply'][self._location_key].split(f"{self.gateway_address}:{self.gateway_info['soap_port']}")[-1]

    def setUp(self) -> None:
        with open(self.data_path, 'r') as f:
            data = json.loads(f.read())
            self.gateway_info = data['gateway']
            self.client_address = data['client_address']
        self.gateway_address = self.gateway_info['gateway_address']
        self.udp_replies = {
            (SSDPDatagram('M-SEARCH', self.gateway_info['m_search_args']).encode().encode(), ("239.255.255.250", 1900)): SSDPDatagram("OK", self.gateway_info['reply']).encode().encode()
        }
        self.tcp_replies = {
            (
                f"GET {path} HTTP/1.1\r\n"
                f"Accept-Encoding: gzip\r\n"
                f"Host: {self.gateway_info['gateway_address']}\r\n"
                f"Connection: Close\r\n"
                f"\r\n"
            ).encode(): xml_bytes.encode()
            for path, xml_bytes in self.gateway_info['service_descriptors'].items()
        }
        self.tcp_replies.update({
            (
                f"GET {self._get_location()} HTTP/1.1\r\n"
                f"Accept-Encoding: gzip\r\n"
                f"Host: {self.gateway_info['gateway_address']}\r\n"
                f"Connection: Close\r\n"
                f"\r\n"
            ).encode(): self.gateway_info['gateway_xml'].encode()
        })
        self.registered_soap_commands = self.gateway_info['registered_soap_commands']
        super().setUp()

    async def setup_request_replay(self, u: UPnP):
        for method, reqs in self.gateway_info['soap_requests'].items():
            if not reqs:
                continue
            self.tcp_replies.update({
                serialize_soap_post(
                    method, list(args.keys()), self.registered_soap_commands[method].encode(),
                    self.gateway_address.encode(), u.gateway.services[self.registered_soap_commands[method]].controlURL.encode()
                ): response.encode() for args, response in reqs
            })

    async def replay(self, u: UPnP):
        self.assertEqual('11.222.33.111', await u.get_external_ip())

    async def test_replay(self):
        with mock_tcp_and_udp(self.loop, udp_replies=self.udp_replies, tcp_replies=self.tcp_replies, udp_expected_addr=self.gateway_address, tcp_chunk_size=1450):
            u = await UPnP.discover(lan_address=self.client_address, gateway_address=self.gateway_address, loop=self.loop)
            await self.setup_request_replay(u)
            await self.replay(u)


class TestNewMediaNet(TestActiontec):
    name = "NewMedia-NET GmbH Generic X86"

    async def replay(self, u: UPnP):
        self.assertEqual('11.222.33.111', await u.get_external_ip())
        await u.get_redirects()
        # print(await u.get_next_mapping(4567, 'UDP', 'aioupnp test mapping'))
