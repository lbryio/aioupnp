import unittest
from aioupnp.fault import UPnPError
from aioupnp.serialization.scpd import serialize_scpd_get, deserialize_scpd_get_response
from aioupnp.serialization.xml import xml_to_dict
from aioupnp.device import Device
from aioupnp.util import get_dict_val_case_insensitive


class TestSCPDSerialization(unittest.TestCase):
    path, lan_address = '/IGDdevicedesc_brlan0.xml', '10.1.10.1'
    get_request = b'GET /IGDdevicedesc_brlan0.xml HTTP/1.1\r\n' \
                  b'Accept-Encoding: gzip\r\nHost: 10.1.10.1\r\nConnection: Close\r\n\r\n'

    response = b"HTTP/1.1 200 OK\r\n" \
               b"CONTENT-LENGTH: 2972\r\n" \
               b"CONTENT-TYPE: text/xml\r\n" \
               b"DATE: Thu, 18 Oct 2018 01:20:23 GMT\r\n" \
               b"LAST-MODIFIED: Fri, 28 Sep 2018 18:35:48 GMT\r\n" \
               b"SERVER: Linux/3.14.28-Prod_17.2, UPnP/1.0, Portable SDK for UPnP devices/1.6.22\r\n" \
               b"X-User-Agent: redsonic\r\n" \
               b"CONNECTION: close\r\n" \
               b"\r\n" \
               b"<?xml version=\"1.0\"?>\n<root xmlns=\"urn:schemas-upnp-org:device-1-0\">\n<specVersion>\n<major>1</major>\n<minor>0</minor>\n</specVersion>\n<device>\n<deviceType>urn:schemas-upnp-org:device:InternetGatewayDevice:1</deviceType>\n<friendlyName>CGA4131COM</friendlyName>\n<manufacturer>Cisco</manufacturer>\n<manufacturerURL>http://www.cisco.com/</manufacturerURL>\n<modelDescription>CGA4131COM</modelDescription>\n<modelName>CGA4131COM</modelName>\n<modelNumber>CGA4131COM</modelNumber>\n<modelURL>http://www.cisco.com</modelURL>\n<serialNumber></serialNumber>\n<UDN>uuid:11111111-2222-3333-4444-555555555556</UDN>\n<UPC>CGA4131COM</UPC>\n<serviceList>\n<service>\n<serviceType>urn:schemas-upnp-org:service:Layer3Forwarding:1</serviceType>\n<serviceId>urn:upnp-org:serviceId:L3Forwarding1</serviceId>\n<SCPDURL>/Layer3ForwardingSCPD.xml</SCPDURL>\n<controlURL>/upnp/control/Layer3Forwarding</controlURL>\n<eventSubURL>/upnp/event/Layer3Forwarding</eventSubURL>\n</service>\n</serviceList>\n<deviceList>\n<device>\n<deviceType>urn:schemas-upnp-org:device:WANDevice:1</deviceType>\n<friendlyName>WANDevice:1</friendlyName>\n<manufacturer>Cisco</manufacturer>\n<manufacturerURL>http://www.cisco.com/</manufacturerURL>\n<modelDescription>CGA4131COM</modelDescription>\n<modelName>CGA4131COM</modelName>\n<modelNumber>CGA4131COM</modelNumber>\n<modelURL>http://www.cisco.com</modelURL>\n<serialNumber></serialNumber>\n<UDN>uuid:11111111-2222-3333-4444-555555555556</UDN>\n<UPC>CGA4131COM</UPC>\n<serviceList>\n<service>\n<serviceType>urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1</serviceType>\n<serviceId>urn:upnp-org:serviceId:WANCommonIFC1</serviceId>\n<SCPDURL>/WANCommonInterfaceConfigSCPD.xml</SCPDURL>\n<controlURL>/upnp/control/WANCommonInterfaceConfig0</controlURL>\n<eventSubURL>/upnp/event/WANCommonInterfaceConfig0</eventSubURL>\n</service>\n</serviceList>\n<deviceList>\n    <device>\n        <deviceType>urn:schemas-upnp-org:device:WANConnectionDevice:1</deviceType>\n        <friendlyName>WANConnectionDevice:1</friendlyName>\n        <manufacturer>Cisco</manufacturer>\n        <manufacturerURL>http://www.cisco.com/</manufacturerURL>\n        <modelDescription>CGA4131COM</modelDescription>\n        <modelName>CGA4131COM</modelName>\n        <modelNumber>CGA4131COM</modelNumber>\n        <modelURL>http://www.cisco.com</modelURL>\n        <serialNumber></serialNumber>\n        <UDN>uuid:11111111-2222-3333-4444-555555555555</UDN>\n        <UPC>CGA4131COM</UPC>\n        <serviceList>\n       <service>\n           <serviceType>urn:schemas-upnp-org:service:WANIPConnection:1</serviceType>\n           <serviceId>urn:upnp-org:serviceId:WANIPConn1</serviceId>\n           <SCPDURL>/WANIPConnectionServiceSCPD.xml</SCPDURL>\n           <controlURL>/upnp/control/WANIPConnection0</controlURL>\n           <eventSubURL>/upnp/event/WANIPConnection0</eventSubURL>\n       </service>\n        </serviceList>\n    </device>\n</deviceList>\n</device>\n</deviceList>\n<presentationURL>http://10.1.10.1/</presentationURL></device>\n</root>\n"

    response_bad_root_device_name = b"HTTP/1.1 200 OK\r\n" \
               b"CONTENT-LENGTH: 2972\r\n" \
               b"CONTENT-TYPE: text/xml\r\n" \
               b"DATE: Thu, 18 Oct 2018 01:20:23 GMT\r\n" \
               b"LAST-MODIFIED: Fri, 28 Sep 2018 18:35:48 GMT\r\n" \
               b"SERVER: Linux/3.14.28-Prod_17.2, UPnP/1.0, Portable SDK for UPnP devices/1.6.22\r\n" \
               b"X-User-Agent: redsonic\r\n" \
               b"CONNECTION: close\r\n" \
               b"\r\n" \
               b"<?xml version=\"1.0\"?>\n<root xmlns=\"urn:schemas-upnp-org:device-1-?\">\n<specVersion>\n<major>1</major>\n<minor>0</minor>\n</specVersion>\n<device>\n<deviceType>urn:schemas-upnp-org:device:InternetGatewayDevic3:1</deviceType>\n<friendlyName>CGA4131COM</friendlyName>\n<manufacturer>Cisco</manufacturer>\n<manufacturerURL>http://www.cisco.com/</manufacturerURL>\n<modelDescription>CGA4131COM</modelDescription>\n<modelName>CGA4131COM</modelName>\n<modelNumber>CGA4131COM</modelNumber>\n<modelURL>http://www.cisco.com</modelURL>\n<serialNumber></serialNumber>\n<UDN>uuid:11111111-2222-3333-4444-555555555556</UDN>\n<UPC>CGA4131COM</UPC>\n<serviceList>\n<service>\n<serviceType>urn:schemas-upnp-org:service:Layer3Forwarding:1</serviceType>\n<serviceId>urn:upnp-org:serviceId:L3Forwarding1</serviceId>\n<SCPDURL>/Layer3ForwardingSCPD.xml</SCPDURL>\n<controlURL>/upnp/control/Layer3Forwarding</controlURL>\n<eventSubURL>/upnp/event/Layer3Forwarding</eventSubURL>\n</service>\n</serviceList>\n<deviceList>\n<device>\n<deviceType>urn:schemas-upnp-org:device:WANDevice:1</deviceType>\n<friendlyName>WANDevice:1</friendlyName>\n<manufacturer>Cisco</manufacturer>\n<manufacturerURL>http://www.cisco.com/</manufacturerURL>\n<modelDescription>CGA4131COM</modelDescription>\n<modelName>CGA4131COM</modelName>\n<modelNumber>CGA4131COM</modelNumber>\n<modelURL>http://www.cisco.com</modelURL>\n<serialNumber></serialNumber>\n<UDN>uuid:11111111-2222-3333-4444-555555555556</UDN>\n<UPC>CGA4131COM</UPC>\n<serviceList>\n<service>\n<serviceType>urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1</serviceType>\n<serviceId>urn:upnp-org:serviceId:WANCommonIFC1</serviceId>\n<SCPDURL>/WANCommonInterfaceConfigSCPD.xml</SCPDURL>\n<controlURL>/upnp/control/WANCommonInterfaceConfig0</controlURL>\n<eventSubURL>/upnp/event/WANCommonInterfaceConfig0</eventSubURL>\n</service>\n</serviceList>\n<deviceList>\n    <device>\n        <deviceType>urn:schemas-upnp-org:device:WANConnectionDevice:1</deviceType>\n        <friendlyName>WANConnectionDevice:1</friendlyName>\n        <manufacturer>Cisco</manufacturer>\n        <manufacturerURL>http://www.cisco.com/</manufacturerURL>\n        <modelDescription>CGA4131COM</modelDescription>\n        <modelName>CGA4131COM</modelName>\n        <modelNumber>CGA4131COM</modelNumber>\n        <modelURL>http://www.cisco.com</modelURL>\n        <serialNumber></serialNumber>\n        <UDN>uuid:11111111-2222-3333-4444-555555555555</UDN>\n        <UPC>CGA4131COM</UPC>\n        <serviceList>\n       <service>\n           <serviceType>urn:schemas-upnp-org:service:WANIPConnection:1</serviceType>\n           <serviceId>urn:upnp-org:serviceId:WANIPConn1</serviceId>\n           <SCPDURL>/WANIPConnectionServiceSCPD.xml</SCPDURL>\n           <controlURL>/upnp/control/WANIPConnection0</controlURL>\n           <eventSubURL>/upnp/event/WANIPConnection0</eventSubURL>\n       </service>\n        </serviceList>\n    </device>\n</deviceList>\n</device>\n</deviceList>\n<presentationURL>http://10.1.10.1/</presentationURL></device>\n</root>\n"

    response_bad_root_xmls = b"HTTP/1.1 200 OK\r\n" \
               b"CONTENT-LENGTH: 2972\r\n" \
               b"CONTENT-TYPE: text/xml\r\n" \
               b"DATE: Thu, 18 Oct 2018 01:20:23 GMT\r\n" \
               b"LAST-MODIFIED: Fri, 28 Sep 2018 18:35:48 GMT\r\n" \
               b"SERVER: Linux/3.14.28-Prod_17.2, UPnP/1.0, Portable SDK for UPnP devices/1.6.22\r\n" \
               b"X-User-Agent: redsonic\r\n" \
               b"CONNECTION: close\r\n" \
               b"\r\n" \
               b"<?xml version=\"1.0\"?>\n<root xmlns=\"urn:schemas-upnp--org:device-1-0\">\n<specVersion>\n<major>1</major>\n<minor>0</minor>\n</specVersion>\n<device>\n<deviceType>urn:schemas-upnp-org:device:InternetGatewayDevic3:1</deviceType>\n<friendlyName>CGA4131COM</friendlyName>\n<manufacturer>Cisco</manufacturer>\n<manufacturerURL>http://www.cisco.com/</manufacturerURL>\n<modelDescription>CGA4131COM</modelDescription>\n<modelName>CGA4131COM</modelName>\n<modelNumber>CGA4131COM</modelNumber>\n<modelURL>http://www.cisco.com</modelURL>\n<serialNumber></serialNumber>\n<UDN>uuid:11111111-2222-3333-4444-555555555556</UDN>\n<UPC>CGA4131COM</UPC>\n<serviceList>\n<service>\n<serviceType>urn:schemas-upnp-org:service:Layer3Forwarding:1</serviceType>\n<serviceId>urn:upnp-org:serviceId:L3Forwarding1</serviceId>\n<SCPDURL>/Layer3ForwardingSCPD.xml</SCPDURL>\n<controlURL>/upnp/control/Layer3Forwarding</controlURL>\n<eventSubURL>/upnp/event/Layer3Forwarding</eventSubURL>\n</service>\n</serviceList>\n<deviceList>\n<device>\n<deviceType>urn:schemas-upnp-org:device:WANDevice:1</deviceType>\n<friendlyName>WANDevice:1</friendlyName>\n<manufacturer>Cisco</manufacturer>\n<manufacturerURL>http://www.cisco.com/</manufacturerURL>\n<modelDescription>CGA4131COM</modelDescription>\n<modelName>CGA4131COM</modelName>\n<modelNumber>CGA4131COM</modelNumber>\n<modelURL>http://www.cisco.com</modelURL>\n<serialNumber></serialNumber>\n<UDN>uuid:11111111-2222-3333-4444-555555555556</UDN>\n<UPC>CGA4131COM</UPC>\n<serviceList>\n<service>\n<serviceType>urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1</serviceType>\n<serviceId>urn:upnp-org:serviceId:WANCommonIFC1</serviceId>\n<SCPDURL>/WANCommonInterfaceConfigSCPD.xml</SCPDURL>\n<controlURL>/upnp/control/WANCommonInterfaceConfig0</controlURL>\n<eventSubURL>/upnp/event/WANCommonInterfaceConfig0</eventSubURL>\n</service>\n</serviceList>\n<deviceList>\n    <device>\n        <deviceType>urn:schemas-upnp-org:device:WANConnectionDevice:1</deviceType>\n        <friendlyName>WANConnectionDevice:1</friendlyName>\n        <manufacturer>Cisco</manufacturer>\n        <manufacturerURL>http://www.cisco.com/</manufacturerURL>\n        <modelDescription>CGA4131COM</modelDescription>\n        <modelName>CGA4131COM</modelName>\n        <modelNumber>CGA4131COM</modelNumber>\n        <modelURL>http://www.cisco.com</modelURL>\n        <serialNumber></serialNumber>\n        <UDN>uuid:11111111-2222-3333-4444-555555555555</UDN>\n        <UPC>CGA4131COM</UPC>\n        <serviceList>\n       <service>\n           <serviceType>urn:schemas-upnp-org:service:WANIPConnection:1</serviceType>\n           <serviceId>urn:upnp-org:serviceId:WANIPConn1</serviceId>\n           <SCPDURL>/WANIPConnectionServiceSCPD.xml</SCPDURL>\n           <controlURL>/upnp/control/WANIPConnection0</controlURL>\n           <eventSubURL>/upnp/event/WANIPConnection0</eventSubURL>\n       </service>\n        </serviceList>\n    </device>\n</deviceList>\n</device>\n</deviceList>\n<presentationURL>http://10.1.10.1/</presentationURL></device>\n</root>\n"

    expected_parsed = {
        'specVersion': {'major': '1', 'minor': '0'},
        'device': {
            'deviceType': 'urn:schemas-upnp-org:device:InternetGatewayDevice:1',
            'friendlyName': 'CGA4131COM',
            'manufacturer': 'Cisco',
            'manufacturerURL': 'http://www.cisco.com/',
            'modelDescription': 'CGA4131COM',
            'modelName': 'CGA4131COM',
            'modelNumber': 'CGA4131COM',
            'modelURL': 'http://www.cisco.com',
            'UDN': 'uuid:11111111-2222-3333-4444-555555555556',
            'UPC': 'CGA4131COM',
            'serviceList': {
                'service': {
                    'serviceType': 'urn:schemas-upnp-org:service:Layer3Forwarding:1',
                    'serviceId': 'urn:upnp-org:serviceId:L3Forwarding1',
                    'SCPDURL': '/Layer3ForwardingSCPD.xml',
                    'controlURL': '/upnp/control/Layer3Forwarding',
                    'eventSubURL': '/upnp/event/Layer3Forwarding'
                }
            },
            'deviceList': {
                'device': {
                    'deviceType': 'urn:schemas-upnp-org:device:WANDevice:1',
                    'friendlyName': 'WANDevice:1',
                    'manufacturer': 'Cisco',
                    'manufacturerURL': 'http://www.cisco.com/',
                    'modelDescription': 'CGA4131COM',
                    'modelName': 'CGA4131COM',
                    'modelNumber': 'CGA4131COM',
                    'modelURL': 'http://www.cisco.com',
                    'UDN': 'uuid:11111111-2222-3333-4444-555555555556',
                    'UPC': 'CGA4131COM',
                    'serviceList': {
                        'service': {
                            'serviceType': 'urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1',
                            'serviceId': 'urn:upnp-org:serviceId:WANCommonIFC1',
                            'SCPDURL': '/WANCommonInterfaceConfigSCPD.xml',
                            'controlURL': '/upnp/control/WANCommonInterfaceConfig0',
                            'eventSubURL': '/upnp/event/WANCommonInterfaceConfig0'
                        }
                    },
                    'deviceList': {
                        'device': {
                            'deviceType': 'urn:schemas-upnp-org:device:WANConnectionDevice:1',
                            'friendlyName': 'WANConnectionDevice:1',
                            'manufacturer': 'Cisco',
                            'manufacturerURL': 'http://www.cisco.com/',
                            'modelDescription': 'CGA4131COM',
                            'modelName': 'CGA4131COM',
                            'modelNumber': 'CGA4131COM',
                            'modelURL': 'http://www.cisco.com',
                            'UDN': 'uuid:11111111-2222-3333-4444-555555555555',
                            'UPC': 'CGA4131COM',
                            'serviceList': {
                                'service': {
                                    'serviceType': 'urn:schemas-upnp-org:service:WANIPConnection:1',
                                    'serviceId': 'urn:upnp-org:serviceId:WANIPConn1',
                                    'SCPDURL': '/WANIPConnectionServiceSCPD.xml',
                                    'controlURL': '/upnp/control/WANIPConnection0',
                                    'eventSubURL': '/upnp/event/WANIPConnection0'
                                }
                            }
                        }
                    }
                }
            },
            'presentationURL': 'http://10.1.10.1/'
        }
    }

    def test_serialize_get(self):
        self.assertEqual(serialize_scpd_get(self.path, self.lan_address), self.get_request)
        self.assertEqual(serialize_scpd_get(self.path, 'http://' + self.lan_address), self.get_request)
        self.assertEqual(serialize_scpd_get(self.path, 'http://' + self.lan_address + ':1337'), self.get_request)
        self.assertEqual(serialize_scpd_get(self.path, self.lan_address + ':1337'), self.get_request)

    def test_parse_device_response_xml(self):
        self.assertDictEqual(
            xml_to_dict('<?xml version="1.0"?>\n<root xmlns="urn:schemas-upnp-org:device-1-0">\n\t<specVersion>\n\t\t<major>1</major>\n\t\t<minor>0</minor>\n\t</specVersion>\n\t<URLBase>http://10.0.0.1:49152</URLBase>\n\t<device>\n\t\t<deviceType>urn:schemas-upnp-org:device:InternetGatewayDevice:1</deviceType>\n\t\t<friendlyName>Wireless Broadband Router</friendlyName>\n\t\t<manufacturer>D-Link Corporation</manufacturer>\n\t\t<manufacturerURL>http://www.dlink.com</manufacturerURL>\n\t\t<modelDescription>D-Link Router</modelDescription>\n\t\t<modelName>D-Link Router</modelName>\n\t\t<modelNumber>DIR-890L</modelNumber>\n\t\t<modelURL>http://www.dlink.com</modelURL>\n\t\t<serialNumber>120</serialNumber>\n\t\t<UDN>uuid:11111111-2222-3333-4444-555555555555</UDN>\n\t\t<iconList>\n\t\t\t<icon>\n\t\t\t\t<mimetype>image/gif</mimetype>\n\t\t\t\t<width>118</width>\n\t\t\t\t<height>119</height>\n\t\t\t\t<depth>8</depth>\n\t\t\t\t<url>/ligd.gif</url>\n\t\t\t</icon>\n\t\t</iconList>\n\t\t<serviceList>\n\t\t\t<service>\n\t\t\t\t<serviceType>urn:schemas-microsoft-com:service:OSInfo:1</serviceType>\n\t\t\t\t<serviceId>urn:microsoft-com:serviceId:OSInfo1</serviceId>\n\t\t\t\t<controlURL>/soap.cgi?service=OSInfo1</controlURL>\n\t\t\t\t<eventSubURL>/gena.cgi?service=OSInfo1</eventSubURL>\n\t\t\t\t<SCPDURL>/OSInfo.xml</SCPDURL>\n\t\t\t</service>\n\t\t\t<service>\n\t\t\t\t<serviceType>urn:schemas-upnp-org:service:Layer3Forwarding:1</serviceType>\n\t\t\t\t<serviceId>urn:upnp-org:serviceId:L3Forwarding1</serviceId>\n\t\t\t\t<controlURL>/soap.cgi?service=L3Forwarding1</controlURL>\n\t\t\t\t<eventSubURL>/gena.cgi?service=L3Forwarding1</eventSubURL>\n\t\t\t\t<SCPDURL>/Layer3Forwarding.xml</SCPDURL>\n\t\t\t</service>\n\t\t</serviceList>\n\t\t<deviceList>\n\t\t\t<device>\n\t\t\t\t<deviceType>urn:schemas-upnp-org:device:WANDevice:1</deviceType>\n\t\t\t\t<friendlyName>WANDevice</friendlyName>\n\t\t\t\t<manufacturer>D-Link</manufacturer>\n\t\t\t\t<manufacturerURL>http://www.dlink.com</manufacturerURL>\n\t\t\t\t<modelDescription>WANDevice</modelDescription>\n\t\t\t\t<modelName>DIR-890L</modelName>\n\t\t\t\t<modelNumber>1</modelNumber>\n\t\t\t\t<modelURL>http://www.dlink.com</modelURL>\n\t\t\t\t<serialNumber>120</serialNumber>\n\t\t\t\t<UDN>uuid:11111111-2222-3333-4444-555555555555</UDN>\n\t\t\t\t<serviceList>\n\t\t\t\t\t<service>\n\t\t\t\t\t\t<serviceType>urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1</serviceType>\n\t\t\t\t\t\t<serviceId>urn:upnp-org:serviceId:WANCommonIFC1</serviceId>\n\t\t\t\t\t\t<controlURL>/soap.cgi?service=WANCommonIFC1</controlURL>\n\t\t\t\t\t\t<eventSubURL>/gena.cgi?service=WANCommonIFC1</eventSubURL>\n\t\t\t\t\t\t<SCPDURL>/WANCommonInterfaceConfig.xml</SCPDURL>\n\t\t\t\t\t</service>\n\t\t\t\t</serviceList>\n\t\t\t\t<deviceList>\n\t\t\t\t\t<device>\n\t\t\t\t\t\t<deviceType>urn:schemas-upnp-org:device:WANConnectionDevice:1</deviceType>\n\t\t\t\t\t\t<friendlyName>WANConnectionDevice</friendlyName>\n\t\t\t\t\t\t<manufacturer>D-Link</manufacturer>\n\t\t\t\t\t\t<manufacturerURL>http://www.dlink.com</manufacturerURL>\n\t\t\t\t\t\t<modelDescription>WanConnectionDevice</modelDescription>\n\t\t\t\t\t\t<modelName>DIR-890L</modelName>\n\t\t\t\t\t\t<modelNumber>1</modelNumber>\n\t\t\t\t\t\t<modelURL>http://www.dlink.com</modelURL>\n\t\t\t\t\t\t<serialNumber>120</serialNumber>\n\t\t\t\t\t\t<UDN>uuid:11111111-2222-3333-4444-555555555555</UDN>\n\t\t\t\t\t\t<serviceList>\n\t\t\t\t\t\t\t<service>\n\t\t\t\t\t\t\t\t<serviceType>urn:schemas-upnp-org:service:WANEthernetLinkConfig:1</serviceType>\n\t\t\t\t\t\t\t\t<serviceId>urn:upnp-org:serviceId:WANEthLinkC1</serviceId>\n\t\t\t\t\t\t\t\t<controlURL>/soap.cgi?service=WANEthLinkC1</controlURL>\n\t\t\t\t\t\t\t\t<eventSubURL>/gena.cgi?service=WANEthLinkC1</eventSubURL>\n\t\t\t\t\t\t\t\t<SCPDURL>/WANEthernetLinkConfig.xml</SCPDURL>\n\t\t\t\t\t\t\t</service>\n\t\t\t\t\t\t\t<service>\n\t\t\t\t\t\t\t\t<serviceType>urn:schemas-upnp-org:service:WANIPConnection:1</serviceType>\n\t\t\t\t\t\t\t\t<serviceId>urn:upnp-org:serviceId:WANIPConn1</serviceId>\n\t\t\t\t\t\t\t\t<controlURL>/soap.cgi?service=WANIPConn1</controlURL>\n\t\t\t\t\t\t\t\t<eventSubURL>/gena.cgi?service=WANIPConn1</eventSubURL>\n\t\t\t\t\t\t\t\t<SCPDURL>/WANIPConnection.xml</SCPDURL>\n\t\t\t\t\t\t\t</service>\n\t\t\t\t\t\t</serviceList>\n\t\t\t\t\t</device>\n\t\t\t\t</deviceList>\n\t\t\t</device>\n\t\t</deviceList>\n\t\t<presentationURL>http://10.0.0.1</presentationURL>\n\t</device>\n</root>\n'),
            {'{urn:schemas-upnp-org:device-1-0}root': {
                '{urn:schemas-upnp-org:device-1-0}specVersion': {'{urn:schemas-upnp-org:device-1-0}major': '1',
                                                                 '{urn:schemas-upnp-org:device-1-0}minor': '0'},
                '{urn:schemas-upnp-org:device-1-0}URLBase': 'http://10.0.0.1:49152',
                '{urn:schemas-upnp-org:device-1-0}device': {
                    '{urn:schemas-upnp-org:device-1-0}deviceType': 'urn:schemas-upnp-org:device:InternetGatewayDevice:1',
                    '{urn:schemas-upnp-org:device-1-0}friendlyName': 'Wireless Broadband Router',
                    '{urn:schemas-upnp-org:device-1-0}manufacturer': 'D-Link Corporation',
                    '{urn:schemas-upnp-org:device-1-0}manufacturerURL': 'http://www.dlink.com',
                    '{urn:schemas-upnp-org:device-1-0}modelDescription': 'D-Link Router',
                    '{urn:schemas-upnp-org:device-1-0}modelName': 'D-Link Router',
                    '{urn:schemas-upnp-org:device-1-0}modelNumber': 'DIR-890L',
                    '{urn:schemas-upnp-org:device-1-0}modelURL': 'http://www.dlink.com',
                    '{urn:schemas-upnp-org:device-1-0}serialNumber': '120',
                    '{urn:schemas-upnp-org:device-1-0}UDN': 'uuid:11111111-2222-3333-4444-555555555555',
                    '{urn:schemas-upnp-org:device-1-0}iconList': {'{urn:schemas-upnp-org:device-1-0}icon': {
                        '{urn:schemas-upnp-org:device-1-0}mimetype': 'image/gif',
                        '{urn:schemas-upnp-org:device-1-0}width': '118',
                        '{urn:schemas-upnp-org:device-1-0}height': '119', '{urn:schemas-upnp-org:device-1-0}depth': '8',
                        '{urn:schemas-upnp-org:device-1-0}url': '/ligd.gif'}},
                    '{urn:schemas-upnp-org:device-1-0}serviceList': {'{urn:schemas-upnp-org:device-1-0}service': [
                        {'{urn:schemas-upnp-org:device-1-0}serviceType': 'urn:schemas-microsoft-com:service:OSInfo:1',
                         '{urn:schemas-upnp-org:device-1-0}serviceId': 'urn:microsoft-com:serviceId:OSInfo1',
                         '{urn:schemas-upnp-org:device-1-0}controlURL': '/soap.cgi?service=OSInfo1',
                         '{urn:schemas-upnp-org:device-1-0}eventSubURL': '/gena.cgi?service=OSInfo1',
                         '{urn:schemas-upnp-org:device-1-0}SCPDURL': '/OSInfo.xml'}, {
                            '{urn:schemas-upnp-org:device-1-0}serviceType': 'urn:schemas-upnp-org:service:Layer3Forwarding:1',
                            '{urn:schemas-upnp-org:device-1-0}serviceId': 'urn:upnp-org:serviceId:L3Forwarding1',
                            '{urn:schemas-upnp-org:device-1-0}controlURL': '/soap.cgi?service=L3Forwarding1',
                            '{urn:schemas-upnp-org:device-1-0}eventSubURL': '/gena.cgi?service=L3Forwarding1',
                            '{urn:schemas-upnp-org:device-1-0}SCPDURL': '/Layer3Forwarding.xml'}]},
                    '{urn:schemas-upnp-org:device-1-0}deviceList': {'{urn:schemas-upnp-org:device-1-0}device': {
                        '{urn:schemas-upnp-org:device-1-0}deviceType': 'urn:schemas-upnp-org:device:WANDevice:1',
                        '{urn:schemas-upnp-org:device-1-0}friendlyName': 'WANDevice',
                        '{urn:schemas-upnp-org:device-1-0}manufacturer': 'D-Link',
                        '{urn:schemas-upnp-org:device-1-0}manufacturerURL': 'http://www.dlink.com',
                        '{urn:schemas-upnp-org:device-1-0}modelDescription': 'WANDevice',
                        '{urn:schemas-upnp-org:device-1-0}modelName': 'DIR-890L',
                        '{urn:schemas-upnp-org:device-1-0}modelNumber': '1',
                        '{urn:schemas-upnp-org:device-1-0}modelURL': 'http://www.dlink.com',
                        '{urn:schemas-upnp-org:device-1-0}serialNumber': '120',
                        '{urn:schemas-upnp-org:device-1-0}UDN': 'uuid:11111111-2222-3333-4444-555555555555',
                        '{urn:schemas-upnp-org:device-1-0}serviceList': {'{urn:schemas-upnp-org:device-1-0}service': {
                            '{urn:schemas-upnp-org:device-1-0}serviceType': 'urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1',
                            '{urn:schemas-upnp-org:device-1-0}serviceId': 'urn:upnp-org:serviceId:WANCommonIFC1',
                            '{urn:schemas-upnp-org:device-1-0}controlURL': '/soap.cgi?service=WANCommonIFC1',
                            '{urn:schemas-upnp-org:device-1-0}eventSubURL': '/gena.cgi?service=WANCommonIFC1',
                            '{urn:schemas-upnp-org:device-1-0}SCPDURL': '/WANCommonInterfaceConfig.xml'}},
                        '{urn:schemas-upnp-org:device-1-0}deviceList': {'{urn:schemas-upnp-org:device-1-0}device': {
                            '{urn:schemas-upnp-org:device-1-0}deviceType': 'urn:schemas-upnp-org:device:WANConnectionDevice:1',
                            '{urn:schemas-upnp-org:device-1-0}friendlyName': 'WANConnectionDevice',
                            '{urn:schemas-upnp-org:device-1-0}manufacturer': 'D-Link',
                            '{urn:schemas-upnp-org:device-1-0}manufacturerURL': 'http://www.dlink.com',
                            '{urn:schemas-upnp-org:device-1-0}modelDescription': 'WanConnectionDevice',
                            '{urn:schemas-upnp-org:device-1-0}modelName': 'DIR-890L',
                            '{urn:schemas-upnp-org:device-1-0}modelNumber': '1',
                            '{urn:schemas-upnp-org:device-1-0}modelURL': 'http://www.dlink.com',
                            '{urn:schemas-upnp-org:device-1-0}serialNumber': '120',
                            '{urn:schemas-upnp-org:device-1-0}UDN': 'uuid:11111111-2222-3333-4444-555555555555',
                            '{urn:schemas-upnp-org:device-1-0}serviceList': {
                                '{urn:schemas-upnp-org:device-1-0}service': [{
                                                                                 '{urn:schemas-upnp-org:device-1-0}serviceType': 'urn:schemas-upnp-org:service:WANEthernetLinkConfig:1',
                                                                                 '{urn:schemas-upnp-org:device-1-0}serviceId': 'urn:upnp-org:serviceId:WANEthLinkC1',
                                                                                 '{urn:schemas-upnp-org:device-1-0}controlURL': '/soap.cgi?service=WANEthLinkC1',
                                                                                 '{urn:schemas-upnp-org:device-1-0}eventSubURL': '/gena.cgi?service=WANEthLinkC1',
                                                                                 '{urn:schemas-upnp-org:device-1-0}SCPDURL': '/WANEthernetLinkConfig.xml'},
                                                                             {
                                                                                 '{urn:schemas-upnp-org:device-1-0}serviceType': 'urn:schemas-upnp-org:service:WANIPConnection:1',
                                                                                 '{urn:schemas-upnp-org:device-1-0}serviceId': 'urn:upnp-org:serviceId:WANIPConn1',
                                                                                 '{urn:schemas-upnp-org:device-1-0}controlURL': '/soap.cgi?service=WANIPConn1',
                                                                                 '{urn:schemas-upnp-org:device-1-0}eventSubURL': '/gena.cgi?service=WANIPConn1',
                                                                                 '{urn:schemas-upnp-org:device-1-0}SCPDURL': '/WANIPConnection.xml'}]}}}}},
                    '{urn:schemas-upnp-org:device-1-0}presentationURL': 'http://10.0.0.1'}}}
        )

    def test_deserialize_get_response(self):
        self.assertDictEqual(deserialize_scpd_get_response(self.response), self.expected_parsed)

    def test_deserialize_blank(self):
        self.assertDictEqual(deserialize_scpd_get_response(b''), {})

    def test_fail_to_deserialize_invalid_root_device(self):
        with self.assertRaises(UPnPError):
            deserialize_scpd_get_response(self.response_bad_root_device_name)

    def test_fail_to_deserialize_invalid_root_xmls(self):
        with self.assertRaises(UPnPError):
            deserialize_scpd_get_response(self.response_bad_root_xmls)

    def test_deserialize_to_device_object(self):
        devices = []
        services = []
        device = Device(devices, services, **get_dict_val_case_insensitive(self.expected_parsed, "device"))
        expected_result = {
            'deviceType': 'urn:schemas-upnp-org:device:InternetGatewayDevice:1',
            'friendlyName': 'CGA4131COM',
            'manufacturer': 'Cisco',
            'manufacturerURL': 'http://www.cisco.com/',
            'modelDescription': 'CGA4131COM',
            'modelName': 'CGA4131COM',
            'modelNumber': 'CGA4131COM',
            'modelURL': 'http://www.cisco.com',
            'udn': 'uuid:11111111-2222-3333-4444-555555555556',
            'upc': 'CGA4131COM',
            'serviceList': {
                'service': {
                    'serviceType': 'urn:schemas-upnp-org:service:Layer3Forwarding:1',
                    'serviceId': 'urn:upnp-org:serviceId:L3Forwarding1',
                    'SCPDURL': '/Layer3ForwardingSCPD.xml',
                    'controlURL': '/upnp/control/Layer3Forwarding',
                    'eventSubURL': '/upnp/event/Layer3Forwarding'
                }
            },
            'deviceList': {
                'device': {
                    'deviceType': 'urn:schemas-upnp-org:device:WANDevice:1',
                    'friendlyName': 'WANDevice:1',
                    'manufacturer': 'Cisco',
                    'manufacturerURL': 'http://www.cisco.com/',
                    'modelDescription': 'CGA4131COM',
                    'modelName': 'CGA4131COM',
                    'modelNumber': 'CGA4131COM',
                    'modelURL': 'http://www.cisco.com',
                    'UDN': 'uuid:11111111-2222-3333-4444-555555555556',
                    'UPC': 'CGA4131COM',
                    'serviceList': {
                        'service': {
                            'serviceType': 'urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1',
                            'serviceId': 'urn:upnp-org:serviceId:WANCommonIFC1',
                            'SCPDURL': '/WANCommonInterfaceConfigSCPD.xml',
                            'controlURL': '/upnp/control/WANCommonInterfaceConfig0',
                            'eventSubURL': '/upnp/event/WANCommonInterfaceConfig0'
                        }
                    },
                    'deviceList': {
                        'device': {
                            'deviceType': 'urn:schemas-upnp-org:device:WANConnectionDevice:1',
                            'friendlyName': 'WANConnectionDevice:1',
                            'manufacturer': 'Cisco',
                            'manufacturerURL': 'http://www.cisco.com/',
                            'modelDescription': 'CGA4131COM',
                            'modelName': 'CGA4131COM',
                            'modelNumber': 'CGA4131COM',
                            'modelURL': 'http://www.cisco.com',
                            'UDN': 'uuid:11111111-2222-3333-4444-555555555555',
                            'UPC': 'CGA4131COM',
                            'serviceList': {
                                'service': {
                                    'serviceType': 'urn:schemas-upnp-org:service:WANIPConnection:1',
                                    'serviceId': 'urn:upnp-org:serviceId:WANIPConn1',
                                    'SCPDURL': '/WANIPConnectionServiceSCPD.xml',
                                    'controlURL': '/upnp/control/WANIPConnection0',
                                    'eventSubURL': '/upnp/event/WANIPConnection0'
                                }
                            }
                        }
                    }
                }
            }, 'presentationURL': 'http://10.1.10.1/'
        }
        self.assertDictEqual(expected_result, device.as_dict())

    def test_deserialize_another_device(self):
        xml_bytes = b"<?xml version=\"1.0\"?>\n<root xmlns=\"urn:schemas-upnp-org:device-1-0\">\n<specVersion>\n<major>1</major>\n<minor>0</minor>\n</specVersion>\n<device>\n<deviceType>urn:schemas-upnp-org:device:InternetGatewayDevice:1</deviceType>\n<friendlyName>CGA4131COM</friendlyName>\n<manufacturer>Cisco</manufacturer>\n<manufacturerURL>http://www.cisco.com/</manufacturerURL>\n<modelDescription>CGA4131COM</modelDescription>\n<modelName>CGA4131COM</modelName>\n<modelNumber>CGA4131COM</modelNumber>\n<modelURL>http://www.cisco.com</modelURL>\n<serialNumber></serialNumber>\n<UDN>uuid:11111111-2222-3333-4444-555555555556</UDN>\n<UPC>CGA4131COM</UPC>\n<serviceList>\n<service>\n<serviceType>urn:schemas-upnp-org:service:Layer3Forwarding:1</serviceType>\n<serviceId>urn:upnp-org:serviceId:L3Forwarding1</serviceId>\n<SCPDURL>/Layer3ForwardingSCPD.xml</SCPDURL>\n<controlURL>/upnp/control/Layer3Forwarding</controlURL>\n<eventSubURL>/upnp/event/Layer3Forwarding</eventSubURL>\n</service>\n</serviceList>\n<deviceList>\n<device>\n<deviceType>urn:schemas-upnp-org:device:WANDevice:1</deviceType>\n<friendlyName>WANDevice:1</friendlyName>\n<manufacturer>Cisco</manufacturer>\n<manufacturerURL>http://www.cisco.com/</manufacturerURL>\n<modelDescription>CGA4131COM</modelDescription>\n<modelName>CGA4131COM</modelName>\n<modelNumber>CGA4131COM</modelNumber>\n<modelURL>http://www.cisco.com</modelURL>\n<serialNumber></serialNumber>\n<UDN>uuid:ebf5a0a0-1dd1-11b2-a92f-603d266f9915</UDN>\n<UPC>CGA4131COM</UPC>\n<serviceList>\n<service>\n<serviceType>urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1</serviceType>\n<serviceId>urn:upnp-org:serviceId:WANCommonIFC1</serviceId>\n<SCPDURL>/WANCommonInterfaceConfigSCPD.xml</SCPDURL>\n<controlURL>/upnp/control/WANCommonInterfaceConfig0</controlURL>\n<eventSubURL>/upnp/event/WANCommonInterfaceConfig0</eventSubURL>\n</service>\n</serviceList>\n<deviceList>\n    <device>\n        <deviceType>urn:schemas-upnp-org:device:WANConnectionDevice:1</deviceType>\n        <friendlyName>WANConnectionDevice:1</friendlyName>\n        <manufacturer>Cisco</manufacturer>\n        <manufacturerURL>http://www.cisco.com/</manufacturerURL>\n        <modelDescription>CGA4131COM</modelDescription>\n        <modelName>CGA4131COM</modelName>\n        <modelNumber>CGA4131COM</modelNumber>\n        <modelURL>http://www.cisco.com</modelURL>\n        <serialNumber></serialNumber>\n        <UDN>uuid:11111111-2222-3333-4444-555555555555</UDN>\n        <UPC>CGA4131COM</UPC>\n        <serviceList>\n       <service>\n           <serviceType>urn:schemas-upnp-org:service:WANIPConnection:1</serviceType>\n           <serviceId>urn:upnp-org:serviceId:WANIPConn1</serviceId>\n           <SCPDURL>/WANIPConnectionServiceSCPD.xml</SCPDURL>\n           <controlURL>/upnp/control/WANIPConnection0</controlURL>\n           <eventSubURL>/upnp/event/WANIPConnection0</eventSubURL>\n       </service>\n        </serviceList>\n    </device>\n</deviceList>\n</device>\n</deviceList>\n<presentationURL>http://10.1.10.1/</presentationURL></device>\n</root>\n"
        expected_parsed = {
            'specVersion': {'major': '1', 'minor': '0'},
            'device': {
                'deviceType': 'urn:schemas-upnp-org:device:InternetGatewayDevice:1',
                'friendlyName': 'CGA4131COM',
                'manufacturer': 'Cisco',
                'manufacturerURL': 'http://www.cisco.com/',
                'modelDescription': 'CGA4131COM',
                'modelName': 'CGA4131COM',
                'modelNumber': 'CGA4131COM',
                'modelURL': 'http://www.cisco.com',
                'UDN': 'uuid:11111111-2222-3333-4444-555555555556',
                'UPC': 'CGA4131COM',
                'serviceList': {
                    'service': {
                        'serviceType': 'urn:schemas-upnp-org:service:Layer3Forwarding:1',
                        'serviceId': 'urn:upnp-org:serviceId:L3Forwarding1',
                        'SCPDURL': '/Layer3ForwardingSCPD.xml',
                        'controlURL': '/upnp/control/Layer3Forwarding',
                        'eventSubURL': '/upnp/event/Layer3Forwarding'
                    }
                },
                'deviceList': {
                    'device': {
                        'deviceType': 'urn:schemas-upnp-org:device:WANDevice:1',
                        'friendlyName': 'WANDevice:1',
                        'manufacturer': 'Cisco',
                        'manufacturerURL': 'http://www.cisco.com/',
                        'modelDescription': 'CGA4131COM',
                        'modelName': 'CGA4131COM',
                        'modelNumber': 'CGA4131COM',
                        'modelURL': 'http://www.cisco.com',
                        'UDN': 'uuid:ebf5a0a0-1dd1-11b2-a92f-603d266f9915',
                        'UPC': 'CGA4131COM',
                        'serviceList': {
                            'service': {
                                'serviceType': 'urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1',
                                'serviceId': 'urn:upnp-org:serviceId:WANCommonIFC1',
                                'SCPDURL': '/WANCommonInterfaceConfigSCPD.xml',
                                'controlURL': '/upnp/control/WANCommonInterfaceConfig0',
                                'eventSubURL': '/upnp/event/WANCommonInterfaceConfig0'
                            }
                        },
                        'deviceList': {
                            'device': {
                                'deviceType': 'urn:schemas-upnp-org:device:WANConnectionDevice:1',
                                'friendlyName': 'WANConnectionDevice:1',
                                'manufacturer': 'Cisco',
                                'manufacturerURL': 'http://www.cisco.com/',
                                'modelDescription': 'CGA4131COM',
                                'modelName': 'CGA4131COM',
                                'modelNumber': 'CGA4131COM',
                                'modelURL': 'http://www.cisco.com',
                                'UDN': 'uuid:11111111-2222-3333-4444-555555555555',
                                'UPC': 'CGA4131COM',
                                'serviceList': {
                                    'service': {
                                        'serviceType': 'urn:schemas-upnp-org:service:WANIPConnection:1',
                                        'serviceId': 'urn:upnp-org:serviceId:WANIPConn1',
                                        'SCPDURL': '/WANIPConnectionServiceSCPD.xml',
                                        'controlURL': '/upnp/control/WANIPConnection0',
                                        'eventSubURL': '/upnp/event/WANIPConnection0'
                                    }
                                }
                            }
                        }
                    }
                },
                'presentationURL': 'http://10.1.10.1/'
            }
        }
        self.assertDictEqual(expected_parsed, deserialize_scpd_get_response(xml_bytes))
