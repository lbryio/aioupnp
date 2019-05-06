import unittest
from typing import ByteString, AnyStr, Any, Mapping, Union, Dict, NoReturn, List
from collections import OrderedDict
from aioupnp.serialization.scpd import serialize_scpd_get, deserialize_scpd_get_response
from aioupnp.device import Device
from aioupnp.util import get_dict_val_case_insensitive


class TestSCPDSerialization(unittest.TestCase):
    path: str = "/IGDdevicedesc_brlan0.xml"
    lan_address: str = "10.1.10.1"
    get_request: ByteString = b'GET /IGDdevicedesc_brlan0.xml HTTP/1.1\r\n' \
                              b'Accept-Encoding: gzip\r\nHost: 10.1.10.1\r\nConnection: Close\r\n\r\n'

    response: ByteString = b'HTTP/1.1 200 OK\r\n' \
                           b'CONTENT-LENGTH: 2972\r\n' \
                           b'CONTENT-TYPE: text/xml\r\n' \
                           b'DATE: Thu, 18 Oct 2018 01:20:23 GMT\r\n' \
                           b'LAST-MODIFIED: Fri, 28 Sep 2018 18:35:48 GMT\r\n' \
                           b'SERVER: Linux/3.14.28-Prod_17.2, UPnP/1.0, Portable SDK for UPnP devices/1.6.22\r\n' \
                           b'X-User-Agent: redsonic\r\n' \
                           b'CONNECTION: close\r\n' \
                           b'\r\n' \
                           b'<?xml version="1.0"?>\n<root xmlns="urn:schemas-upnp-org:device-1-0">\n<specVersion>\n' \
                           b'<major>1</major>\n<minor>0</minor>\n</specVersion>\n<device>\n<deviceType>urn:schemas' \
                           b'-upnp-org:device:InternetGatewayDevice:1</deviceType>\n<friendlyName>CGA4131COM' \
                           b'</friendlyName>\n<manufacturer>Cisco</manufacturer>\n<manufacturerURL>http://www.cisco' \
                           b'.com/</manufacturerURL>\n<modelDescription>CGA4131COM</modelDescription>\n<modelName' \
                           b'>CGA4131COM</modelName>\n<modelNumber>CGA4131COM</modelNumber>\n<modelURL>http://www' \
                           b'.cisco.com</modelURL>\n<serialNumber></serialNumber>\n<UDN>uuid:11111111-2222-3333-4444' \
                           b'-555555555556</UDN>\n<UPC>CGA4131COM</UPC>\n<serviceList>\n<service>\n<serviceType>urn' \
                           b':schemas-upnp-org:service:Layer3Forwarding:1</serviceType>\n<serviceId>urn:upnp-org' \
                           b':serviceId:L3Forwarding1</serviceId>\n<SCPDURL>/Layer3ForwardingSCPD.xml</SCPDURL>\n' \
                           b'<controlURL>/upnp/control/Layer3Forwarding</controlURL>\n<eventSubURL>/upnp/event' \
                           b'/Layer3Forwarding</eventSubURL>\n</service>\n</serviceList>\n<deviceList>\n<device>\n' \
                           b'<deviceType>urn:schemas-upnp-org:device:WANDevice:1</deviceType>\n<friendlyName' \
                           b'>WANDevice:1</friendlyName>\n<manufacturer>Cisco</manufacturer>\n<manufacturerURL>http' \
                           b'://www.cisco.com/</manufacturerURL>\n<modelDescription>CGA4131COM</modelDescription>\n' \
                           b'<modelName>CGA4131COM</modelName>\n<modelNumber>CGA4131COM</modelNumber>\n<modelURL>http' \
                           b'://www.cisco.com</modelURL>\n<serialNumber></serialNumber>\n<UDN>uuid:11111111-2222-3333' \
                           b'-4444-555555555556</UDN>\n<UPC>CGA4131COM</UPC>\n<serviceList>\n<service>\n<serviceType' \
                           b'>urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1</serviceType>\n<serviceId>urn' \
                           b':upnp-org:serviceId:WANCommonIFC1</serviceId>\n<SCPDURL>/WANCommonInterfaceConfigSCPD' \
                           b'.xml</SCPDURL>\n<controlURL>/upnp/control/WANCommonInterfaceConfig0</controlURL>\n' \
                           b'<eventSubURL>/upnp/event/WANCommonInterfaceConfig0</eventSubURL>\n</service>\n' \
                           b'</serviceList>\n<deviceList>\n    <device>\n        ' \
                           b'<deviceType>urn:schemas-upnp-org:device:WANConnectionDevice:1</deviceType>\n        ' \
                           b'<friendlyName>WANConnectionDevice:1</friendlyName>\n        ' \
                           b'<manufacturer>Cisco</manufacturer>\n        ' \
                           b'<manufacturerURL>http://www.cisco.com/</manufacturerURL>\n        ' \
                           b'<modelDescription>CGA4131COM</modelDescription>\n        ' \
                           b'<modelName>CGA4131COM</modelName>\n        <modelNumber>CGA4131COM</modelNumber>\n       ' \
                           b' <modelURL>http://www.cisco.com</modelURL>\n        <serialNumber></serialNumber>\n      ' \
                           b'  <UDN>uuid:11111111-2222-3333-4444-555555555555</UDN>\n        <UPC>CGA4131COM</UPC>\n  ' \
                           b'      <serviceList>\n       <service>\n           ' \
                           b'<serviceType>urn:schemas-upnp-org:service:WANIPConnection:1</serviceType>\n           ' \
                           b'<serviceId>urn:upnp-org:serviceId:WANIPConn1</serviceId>\n           ' \
                           b'<SCPDURL>/WANIPConnectionServiceSCPD.xml</SCPDURL>\n           ' \
                           b'<controlURL>/upnp/control/WANIPConnection0</controlURL>\n           ' \
                           b'<eventSubURL>/upnp/event/WANIPConnection0</eventSubURL>\n       </service>\n        ' \
                           b'</serviceList>\n    ' \
                           b'</device>\n</deviceList>\n</device>\n</deviceList>\n<presentationURL>http://10.1.10.1' \
                           b'/</presentationURL></device>\n</root>\n '

    expected_parsed: Mapping[str, Union[str, Mapping[str, Dict]]] = {
        'specVersion': {'major': "1", 'minor': "0"},
        'device': {
            'deviceType': "urn:schemas-upnp-org:device:InternetGatewayDevice:1",
            'friendlyName': "CGA4131COM",
            'manufacturer': "Cisco",
            'manufacturerURL': "http://www.cisco.com/",
            'modelDescription': "CGA4131COM",
            'modelName': "CGA4131COM",
            'modelNumber': "CGA4131COM",
            'modelURL': "http://www.cisco.com",
            'UDN': "uuid:11111111-2222-3333-4444-555555555556",
            'UPC': "CGA4131COM",
            'serviceList': {
                'service':      {
                    'serviceType': "urn:schemas-upnp-org:service:Layer3Forwarding:1",
                    'serviceId': "urn:upnp-org:serviceId:L3Forwarding1",
                    'SCPDURL': "/Layer3ForwardingSCPD.xml",
                    'controlURL': "/upnp/control/Layer3Forwarding",
                    'eventSubURL': "/upnp/event/Layer3Forwarding"
                }
            },
            'deviceList': {
                'device':   {
                    'deviceType': "urn:schemas-upnp-org:device:WANDevice:1",
                    'friendlyName': "WANDevice:1",
                    'manufacturer': "Cisco",
                    'manufacturerURL': "http://www.cisco.com/",
                    'modelDescription': "CGA4131COM",
                    'modelName': "CGA4131COM",
                    'modelNumber': "CGA4131COM",
                    'modelURL': "http://www.cisco.com",
                    'UDN': "uuid:11111111-2222-3333-4444-555555555556",
                    'UPC': "CGA4131COM",
                    'serviceList': {
                        'service': {
                            'serviceType': "urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1",
                            'serviceId': "urn:upnp-org:serviceId:WANCommonIFC1",
                            'SCPDURL': "/WANCommonInterfaceConfigSCPD.xml",
                            'controlURL': "/upnp/control/WANCommonInterfaceConfig0",
                            'eventSubURL': "/upnp/event/WANCommonInterfaceConfig0"
                        }
                    },
                    "deviceList": {
                        'device': {
                            'deviceType': "urn:schemas-upnp-org:device:WANConnectionDevice:1",
                            'friendlyName': "WANConnectionDevice:1",
                            'manufacturer': "Cisco",
                            'manufacturerURL': "http://www.cisco.com/",
                            'modelDescription': "CGA4131COM",
                            'modelName': "CGA4131COM",
                            'modelNumber': "CGA4131COM",
                            'modelURL': "http://www.cisco.com",
                            'UDN': "uuid:11111111-2222-3333-4444-555555555555",
                            'UPC': "CGA4131COM",
                            'serviceList': {
                                'service': {
                                    'serviceType': "urn:schemas-upnp-org:service:WANIPConnection:1",
                                    'serviceId': "urn:upnp-org:serviceId:WANIPConn1",
                                    'SCPDURL': "/WANIPConnectionServiceSCPD.xml",

                                    'controlURL': "/upnp/control/WANIPConnection0",
                                    'eventSubURL': "/upnp/event/WANIPConnection0"
                                }
                            }
                        }
                    }
                }
            },
            'presentationURL': "http://10.1.10.1/"
        }
    }

    def test_serialize_get(self) -> NoReturn:
        self.assertEqual(serialize_scpd_get(self.path, self.lan_address), self.get_request)

    def test_deserialize_get_response(self) -> NoReturn:
        self.assertDictEqual(deserialize_scpd_get_response(self.response), self.expected_parsed)

    def test_deserialize_blank(self) -> NoReturn:
        self.assertDictEqual(deserialize_scpd_get_response(b''), {})

    def test_deserialize_to_device_object(self):
        devices: List = []
        services: List = []
        device = Device(devices, services, **get_dict_val_case_insensitive(OrderedDict(self.expected_parsed), "device"))
        expected_result = {
            'deviceType': "urn:schemas-upnp-org:device:InternetGatewayDevice:1",
            'friendlyName': "CGA4131COM",
            'manufacturer': "Cisco",
            'manufacturerURL': "http://www.cisco.com/",
            'modelDescription': "CGA4131COM",
            'modelName': "CGA4131COM",
            'modelNumber': "CGA4131COM",
            'modelURL': "http://www.cisco.com",
            'udn': "uuid:11111111-2222-3333-4444-555555555556",
            'upc': "CGA4131COM",
            'serviceList': {
                'service': {
                    'serviceType': "urn:schemas-upnp-org:service:Layer3Forwarding:1",
                    'serviceId': "urn:upnp-org:serviceId:L3Forwarding1",
                    'SCPDURL': "/Layer3ForwardingSCPD.xml",
                    'controlURL': "/upnp/control/Layer3Forwarding",
                    'eventSubURL': "/upnp/event/Layer3Forwarding"
                }
            },
            'deviceList': {
                'device': {
                    'deviceType': "urn:schemas-upnp-org:device:WANDevice:1",
                    'friendlyName': "WANDevice:1",
                    'manufacturer': "Cisco",
                    'manufacturerURL': "http://www.cisco.com/",
                    'modelDescription': "CGA4131COM",
                    'modelName': "CGA4131COM",
                    'modelNumber': "CGA4131COM",
                    'modelURL': "http://www.cisco.com",
                    'UDN': "uuid:11111111-2222-3333-4444-555555555556",
                    'UPC': "CGA4131COM",
                    'serviceList': {
                        'service': {
                            'serviceType': "urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1",
                            'serviceId': "urn:upnp-org:serviceId:WANCommonIFC1",
                            'SCPDURL': "/WANCommonInterfaceConfigSCPD.xml",
                            'controlURL': "/upnp/control/WANCommonInterfaceConfig0",
                            'eventSubURL': "/upnp/event/WANCommonInterfaceConfig0"
                        }
                    },
                    'deviceList': {
                        'device': {
                            'deviceType': "urn:schemas-upnp-org:device:WANConnectionDevice:1",
                            'friendlyName': "WANConnectionDevice:1",
                            'manufacturer': "Cisco",
                            'manufacturerURL': "http://www.cisco.com/",
                            'modelDescription': "CGA4131COM",
                            'modelName': "CGA4131COM",
                            'modelNumber': "CGA4131COM",
                            'modelURL': "http://www.cisco.com",
                            'UDN': "uuid:11111111-2222-3333-4444-555555555555",
                            'UPC': "CGA4131COM",
                            'serviceList': {
                                'service': {
                                    'serviceType': "urn:schemas-upnp-org:service:WANIPConnection:1",
                                    'serviceId': "urn:upnp-org:serviceId:WANIPConn1",
                                    'SCPDURL': "/WANIPConnectionServiceSCPD.xml",
                                    'controlURL': "/upnp/control/WANIPConnection0",
                                    'eventSubURL': "/upnp/event/WANIPConnection0"
                                }
                            }
                        }
                    }
                }
            }, 'presentationURL': "http://10.1.10.1/"
        }
        self.assertDictEqual(expected_result, device.as_dict())
