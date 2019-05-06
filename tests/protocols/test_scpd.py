from aioupnp.fault import UPnPError
from aioupnp.protocols.scpd import scpd_post, scpd_get
from typing import Optional, Mapping, Union, ByteString, G
from tests import TestBase
from tests.mocks import mock_tcp_and_udp


class TestSCPDGet(TestBase):
    path: str = "/IGDdevicedesc_brlan0.xml"
    lan_addr: str = "10.1.10.1"
    port: int = 49152
    get_request: ByteString = b'GET /IGDdevicedesc_brlan0.xml HTTP/1.1\r\n' \
                              b'Accept-Encoding: gzip\r\nHost: 10.1.10.1\r\nConnection: Close\r\n\r\n'
    response: ByteString = b'HTTP/1.1 200 OK\r\n' \
                           b'CONTENT-LENGTH: 2972\r\n' \
                           b'CONTENT-TYPE: text/xml\r\n' \
                           b'DATE: Thu, 18 Oct 2018 01:20:23 GMT\r\n' \
                           b'LAST-MODIFIED: Fri, 28 Sep 2018 18:35:48 GMT\r\n' \
                           b'SERVER: Linux/3.14.28-Prod_17.2, UPnP/1.0, Portable SDK for UPnP devices/1.6.22\r\n' \
                           b'X-User-Agent: redsonic\r\n' \
                           b'CONNECTION: close\r\n\r\n' \
                           b'<?xml version=\"1.0\"?>\n' \
                           b'<root xmlns=\"urn:schemas-upnp-org:device-1-0\">\n' \
                           b'<specVersion>\n<major>1</major>\n<minor>0</minor>\n</specVersion>\n' \
                           b'<device>\n<deviceType>urn:schemas-upnp-org:device:InternetGatewayDevice:1</deviceType>\n' \
                           b'<friendlyName>CGA4131COM</friendlyName>\n<manufacturer>Cisco</manufacturer>\n' \
                           b'<manufacturerURL>http://www.cisco.com/</manufacturerURL>\n<modelDescription>' \
                           b'CGA4131COM</modelDescription>\n<modelName>CGA4131COM</modelName>\n<modelNumber>' \
                           b'CGA4131COM</modelNumber>\n<modelURL>http://www.cisco.com</modelURL>\n<serialNumber>' \
                           b'</serialNumber>\n<UDN>uuid:11111111-2222-3333-4444-555555555556</UDN>\n<UPC>' \
                           b'CGA4131COM</UPC>\n<serviceList>\n<service>\n<serviceType>' \
                           b'urn:schemas-upnp-org:service:Layer3Forwarding:1</serviceType>\n<serviceId>' \
                           b'urn:upnp-org:serviceId:L3Forwarding1</serviceId>\n<SCPDURL>/Layer3ForwardingSCPD.xml' \
                           b'</SCPDURL>\n<controlURL>/upnp/control/Layer3Forwarding</controlURL>\n<eventSubURL>' \
                           b'/upnp/event/Layer3Forwarding</eventSubURL>\n</service>\n</serviceList>\n<deviceList>\n' \
                           b'<device>\n<deviceType>urn:schemas-upnp-org:device:WANDevice:1</deviceType>\n<friendlyName>' \
                           b'WANDevice:1</friendlyName>\n<manufacturer>Cisco</manufacturer>\n<manufacturerURL>' \
                           b'http://www.cisco.com/</manufacturerURL>\n<modelDescription>CGA4131COM</modelDescription>\n' \
                           b'<modelName>CGA4131COM</modelName>\n<modelNumber>CGA4131COM</modelNumber>\n<modelURL>' \
                           b'http://www.cisco.com</modelURL>\n<serialNumber></serialNumber>\n' \
                           b'<UDN>uuid:ebf5a0a0-1dd1-11b2-a92f-603d266f9915</UDN>\n<UPC>CGA4131COM</UPC>\n<serviceList>\n<service>\n' \
                           b'<serviceType>urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1</serviceType>\n' \
                           b'<serviceId>urn:upnp-org:serviceId:WANCommonIFC1</serviceId>\n<SCPDURL>' \
                           b'/WANCommonInterfaceConfigSCPD.xml</SCPDURL>\n<controlURL>/upnp/control/WANCommonInterfaceConfig0' \
                           b'</controlURL>\n<eventSubURL>/upnp/event/WANCommonInterfaceConfig0</eventSubURL>\n</service>\n' \
                           b'</serviceList>\n<deviceList>\n\t<device>\n\t\t<deviceType>urn:schemas-upnp-org:device:WANConnection' \
                           b'Device:1</deviceType>\n\t\t<friendlyName>WANConnectionDevice:1</friendlyName>\n\t\t' \
                           b'<manufacturer>Cisco</manufacturer>\n\t\t<manufacturerURL>http://www.cisco.com/</manufacturerURL>' \
                           b'\n\t\t<modelDescription>CGA4131COM</modelDescription>\n\t\t<modelName>CGA4131COM</modelName>\n\t\t' \
                           b'<modelNumber>CGA4131COM</modelNumber>\n\t\t<modelURL>http://www.cisco.com</modelURL>\n\t\t' \
                           b'<serialNumber></serialNumber>\n\t\t<UDN>uuid:11111111-2222-3333-4444-555555555555</UDN>\n\t\t' \
                           b'<UPC>CGA4131COM</UPC>\n\t\t<serviceList>\n\t\t<service>\n\t\t<serviceType>' \
                           b'urn:schemas-upnp-org:service:WANIPConnection:1</serviceType>\n\t\t<serviceId>' \
                           b'urn:upnp-org:serviceId:WANIPConn1</serviceId>\n\t\t<SCPDURL>/WANIPConnectionServiceSCPD.xml' \
                           b'</SCPDURL>\n\t\t<controlURL>/upnp/control/WANIPConnection0</controlURL>\n\t\t<eventSubURL>' \
                           b'/upnp/event/WANIPConnection0</eventSubURL>\n\t\t</service>\n\t\t</serviceList>\n\t</device>\n' \
                           b'</deviceList>\n</device>\n</deviceList>\n<presentationURL>http://10.1.10.1/' \
                           b'</presentationURL></device>\n</root>\n'

    bad_xml: bytes = b'<?xml version="1.0"?>\n<root xmlns="urn:schemas-upnp-org:device-1-0">\n<specVersion>\n<major>1' \
                     b'</major>\n<minor>0</minor>\n</specVersion>\n<device>\n<deviceType>urn:schemas-upnp-org:device' \
                     b':InternetGatewayDevice:1</deviceType>\n<friendlyName>CGA4131COM</friendlyName>\n<manufacturer>Cisco' \
                     b'</manufacturer>\n<manufacturerURL>http://www.cisco.com/</manufacturerURL>\n<modelDescription' \
                     b'>CGA4131COM</modelDescription>\n<modelName>CGA4131COM</modelName>\n<modelNumber>CGA4131COM' \
                     b'</modelNumber>\n<modelURL>http://www.cisco.com</modelURL>\n<serialNumber></serialNumber>\n<UDN>uuid' \
                     b':11111111-2222-3333-4444-555555555556</UDN>\n<UPC>CGA4131COM</UPC>\n<serviceList>\n<service>\n' \
                     b'<serviceType>urn:schemas-upnp-org:service:Layer3Forwarding:1</serviceType>\n<serviceId>urn:upnp-org' \
                     b':serviceId:L3Forwarding1</serviceId>\n<SCPDURL>/Layer3ForwardingSCPD.xml</SCPDURL>\n<controlURL>/upnp' \
                     b'/control/Layer3Forwarding</controlURL>\n<eventSubURL>/upnp/event/Layer3Forwarding</eventSubURL' \
                     b'>\n' \ 
                     b'</service>\n</serviceList>\n<deviceList>\n<device>\n<deviceType>urn:schemas-upnp-org:device:WANDevice' \
                     b':1</deviceType>\n<friendlyName>WANDevice:1</friendlyName>\n<manufacturer>Cisco</manufacturer>\n' \
                     b'<manufacturerURL>http://www.cisco.com/</manufacturerURL>\n<modelDescription>CGA4131COM' \
                     b'</modelDescription>\n<modelName>CGA4131COM</modelName>\n<modelNumber>CGA4131COM</modelNumber>\n' \
                     b'<modelURL>http://www.cisco.com</modelURL>\n<serialNumber></serialNumber>\n<UDN>uuid:ebf5a0a0-1dd1' \
                     b'-11b2-a92f-603d266f9915</UDN>\n<UPC>CGA4131COM</UPC>\n<serviceList>\n<service>\n<serviceType>urn' \
                     b':schemas-upnp-org:service:WANCommonInterfaceConfig:1</serviceType>\n<serviceId>urn:upnp-org:serviceId' \
                     b':WANCommonIFC1</serviceId>\n<SCPDURL>/WANCommonInterfaceConfigSCPD.xml</SCPDURL>\n<controlURL>/upnp' \
                     b'/control/WANCommonInterfaceConfig0</controlURL>\n<eventSubURL>/upnp/event/WANCommonInterfaceConfig0' \
                     b'</eventSubURL>\n</service>\n</serviceList>\n<deviceList>\n\t<device>\n\t\t' \
                     b'<deviceType>urn:schemas-upnp-org:device:WANConnectionDevice:1</deviceType>\n\t\t' \
                     b'<friendlyName>WANConnectionDevice:1</friendlyName>\n\t\t<manufacturer>Cisco</manufacturer>\n\t\t\t' \
                     b'<manufacturerURL>http://www.cisco.com/</manufacturerURL>\n\t\t' \
                     b'<modelDescription>CGA4131COM</modelDescription>\n\t\t<modelName>CGA4131COM</modelName>\n\t\t' \
                     b'<modelNumber>CGA4131COM</modelNumber>\n\t\t<modelURL>http://www.cisco.com</modelURL>\n\t\t\t' \
                     b'<serialNumber></serialNumber>\n\t\t<UDN>uuid:11111111-2222-3333-4444-555555555555</UDN>\n\t\t' \
                     b'<UPC>CGA4131COM</UPC>\n\t\t<serviceList>\n\t\t<service>\n\t\t\t' \
                     b'<serviceType>urn:schemas-upnp-org:service:WANIPConnection:1</serviceType>\n\t\t\t' \
                     b'<serviceId>urn:upnp-org:serviceId:WANIPConn1</serviceId>\n\t\t\t' \
                     b'<SCPDURL>/WANIPConnectionServiceSCPD.xml</SCPDURL>\n\t\t\t' \
                     b'<controlURL>/upnp/control/WANIPConnection0</controlURL>\n\t\t' \
                     b'<eventSubURL>/upnp/event/WANIPConnection0</eventSubURL>\n\t\t</service>\n\t\t</serviceList>\n\t\t' \
                     b'</device>\n</deviceList>\n</device>\n</deviceList>\n<presentationURL>http://10.1.10.1' \
                     b'/</presentationURL></device>\n/root>\n'

    bad_response: bytes = b'HTTP/1.1 200 OK\r\n' \
                          b'CONTENT-LENGTH: 2971\r\n' \
                          b'CONTENT-TYPE: text/xml\r\n' \
                          b'DATE: Thu, 18 Oct 2018 01:20:23 GMT\r\n' \
                          b'LAST-MODIFIED: Fri, 28 Sep 2018 18:35:48 GMT\r\n' \
                          b'SERVER: Linux/3.14.28-Prod_17.2, UPnP/1.0, Portable SDK for UPnP devices/1.6.22\r\n' \
                          b'X-User-Agent: redsonic\r\n' \
                          b'CONNECTION: close\r\n' \
                          b'\r\n' \
                          b'%s' % bad_xml

    expected_parsed: Mapping[str, Union[dict, str]] = {
        "specVersion": {"major": '1', "minor": '0'},
        "device": {
            "deviceType": 'urn:schemas-upnp-org:device:InternetGatewayDevice:1',
            "friendlyName": 'CGA4131COM',
            "manufacturer": 'Cisco',
            "manufacturerURL": 'http://www.cisco.com/',
            "modelDescription": 'CGA4131COM',
            "modelName": 'CGA4131COM',
            "modelNumber": 'CGA4131COM',
            "modelURL": 'http://www.cisco.com',
            "UDN": 'uuid:11111111-2222-3333-4444-555555555556',
            "UPC": 'CGA4131COM',
            "serviceList": {
                "service": {
                    "serviceType": 'urn:schemas-upnp-org:service:Layer3Forwarding:1',
                    "serviceId": 'urn:upnp-org:serviceId:L3Forwarding1',
                    "SCPDURL": '/Layer3ForwardingSCPD.xml',
                    "controlURL": '/upnp/control/Layer3Forwarding',
                    "eventSubURL": '/upnp/event/Layer3Forwarding'
                }
            },
            "deviceList": {
                "device": {
                    "deviceType": 'urn:schemas-upnp-org:device:WANDevice:1',
                    "friendlyName": 'WANDevice:1',
                    "manufacturer": 'Cisco',
                    "manufacturerURL": 'http://www.cisco.com/',
                    "modelDescription": 'CGA4131COM',
                    "modelName": 'CGA4131COM',
                    "modelNumber": 'CGA4131COM',
                    "modelURL": 'http://www.cisco.com',
                    "UDN": 'uuid:ebf5a0a0-1dd1-11b2-a92f-603d266f9915',
                    "UPC": 'CGA4131COM',
                    "serviceList": {
                        "service": {
                            "serviceType": 'urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1',
                            "serviceId": 'urn:upnp-org:serviceId:WANCommonIFC1',
                            "SCPDURL": '/WANCommonInterfaceConfigSCPD.xml',
                            "controlURL": '/upnp/control/WANCommonInterfaceConfig0',
                            "eventSubURL": '/upnp/event/WANCommonInterfaceConfig0'
                        }
                    },
                    "deviceList": {
                        "device": {
                            "deviceType": 'urn:schemas-upnp-org:device:WANConnectionDevice:1',
                            "friendlyName": 'WANConnectionDevice:1',
                            "manufacturer": 'Cisco',
                            "manufacturerURL": 'http://www.cisco.com/',
                            "modelDescription": 'CGA4131COM',
                            "modelName": 'CGA4131COM',
                            "modelNumber": 'CGA4131COM',
                            "modelURL": 'http://www.cisco.com',
                            "UDN": 'uuid:11111111-2222-3333-4444-555555555555',
                            "UPC": 'CGA4131COM',
                            "serviceList": {
                                "service": {
                                    "serviceType": 'urn:schemas-upnp-org:service:WANIPConnection:1',
                                    "serviceId": 'urn:upnp-org:serviceId:WANIPConn1',
                                    "SCPDURL": '/WANIPConnectionServiceSCPD.xml',
                                    "controlURL": '/upnp/control/WANIPConnection0',
                                    "eventSubURL": '/upnp/event/WANIPConnection0'
                                }
                            }
                        }
                    }
                }
            },
            "presentationURL": 'http://10.1.10.1/'
        }
    }

    async def test_scpd_get(self) -> None:
        sent: list = []
        replies: dict = {self.get_request: self.response}
        with mock_tcp_and_udp(self.loop, tcp_replies=replies, sent_tcp_packets=sent):
            result, raw, err = await scpd_get(self.path, self.lan_addr, self.port, self.loop)
            self.assertEqual(None, err)
            self.assertDictEqual(self.expected_parsed, result)

    async def test_scpd_get_timeout(self):
        sent: list = []
        replies: dict = {}
        with mock_tcp_and_udp(self.loop, tcp_replies=replies, sent_tcp_packets=sent):
            result, raw, err = await scpd_get(self.path, self.lan_addr, self.port, self.loop)
            self.assertTrue(isinstance(err, UPnPError))
            self.assertDictEqual({}, result)
            self.assertEqual(b'', raw)

    async def test_scpd_get_bad_xml(self):
        sent: list = []
        replies: dict = {self.get_request: self.bad_response}
        with mock_tcp_and_udp(self.loop, tcp_replies=replies, sent_tcp_packets=sent):
            result, raw, err = await scpd_get(self.path, self.lan_addr, self.port, self.loop)
            self.assertDictEqual({}, result)
            self.assertEqual(self.bad_xml, raw)
            self.assertTrue(isinstance(err, UPnPError))
            self.assertTrue(str(err).startswith('No element found'))

    async def test_scpd_get_overrun_content_length(self):
        sent: list = []
        replies: dict = {self.get_request: self.bad_response + b'\r\n'}
        with mock_tcp_and_udp(self.loop, tcp_replies=replies, sent_tcp_packets=sent):
            result, raw, err = await scpd_get(self.path, self.lan_address, self.port, self.loop)
            self.assertDictEqual({}, result)
            self.assertEqual(self.bad_response + b'\r\n', raw)
            self.assertTrue(isinstance(err, UPnPError))
            self.assertTrue(str(err).startswith('Too many bytes written'))


class TestSCPDPost(TestBase):
    param_names: list = []
    kwargs: dict = {}
    method: str = "GetExternalIPAddress"
    gateway_addr: str = "10.0.0.1"
    port: int = 49152
    st, lan_addr, path = b'urn:schemas-upnp-org:service:WANIPConnection:1', '10.0.0.2', b'/soap.cgi?service=WANIPConn1'
    post_bytes: bytes = b'POST /soap.cgi?service=WANIPConn1 HTTP/1.1\r\n' \
                        b'Host: 10.0.0.1\r\nUser-Agent: python3/aioupnp, UPnP/1.0, MiniUPnPc/1.9\r\n' \
                        b'Content-Length: 285\r\nContent-Type: text/xml\r\n' \
                        b'SOAPAction: "urn:schemas-upnp-org:service:WANIPConnection:1#GetExternalIPAddress"\r\n' \
                        b'Connection: Close\r\nCache-Control: no-cache\r\nPragma: no-cache\r\n\r\n' \
                        b'<?xml version="1.0"?>\r\n<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" ' \
                        b's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">' \
                        b'<s:Body><u:GetExternalIPAddress xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1">' \
                        b'</u:GetExternalIPAddress></s:Body></s:Envelope>\r\n'

    bad_envelope: bytes = b"s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"><s:Body>\n<u:GetExternalIPAddressResponse xmlns:u=\"urn:schemas-upnp-org:service:WANIPConnection:1\">\r\n<NewExternalIPAddress>11.22.33.44</NewExternalIPAddress>\r\n</u:GetExternalIPAddressResponse>\r\n</s:Body> </s:Envelope>"
    envelope: bytes = b"<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"><s:Body>\n<u:GetExternalIPAddressResponse xmlns:u=\"urn:schemas-upnp-org:service:WANIPConnection:1\">\r\n<NewExternalIPAddress>11.22.33.44</NewExternalIPAddress>\r\n</u:GetExternalIPAddressResponse>\r\n</s:Body> </s:Envelope>"

    post_response: bytes = b"HTTP/1.1 200 OK\r\n" \
                           b"CONTENT-LENGTH: 340\r\n" \
                           b"CONTENT-TYPE: text/xml; charset=\"utf-8\"\r\n" \
                           b"DATE: Thu, 18 Oct 2018 01:20:23 GMT\r\n" \
                           b"EXT:\r\n" \
                           b"SERVER: Linux/3.14.28-Prod_17.2, UPnP/1.0, Portable SDK for UPnP devices/1.6.22\r\n" \
                           b"X-User-Agent: redsonic\r\n" \
                           b"\r\n" \
                           b"%s" % envelope

    bad_envelope_response: bytes = b"HTTP/1.1 200 OK\r\n" \
                                   b"CONTENT-LENGTH: 339\r\n" \
                                   b"CONTENT-TYPE: text/xml; charset=\"utf-8\"\r\n" \
                                   b"DATE: Thu, 18 Oct 2018 01:20:23 GMT\r\n" \
                                   b"EXT:\r\n" \
                                   b"SERVER: Linux/3.14.28-Prod_17.2, UPnP/1.0, Portable SDK for UPnP devices/1.6.22\r\n" \
                                   b"X-User-Agent: redsonic\r\n" \
                                   b"\r\n" \
                                   b"%s" % bad_envelope

    async def test_scpd_post(self) -> Optional[AssertionError]:
        sent: list = []
        replies: dict = {self.post_bytes: self.post_response}
        with mock_tcp_and_udp(self.loop, tcp_replies=replies, sent_tcp_packets=sent):
            result, raw, err = await scpd_post(
                self.path, self.gateway_addr, self.port, self.method, self.param_names, self.st, self.loop
            )
            self.assertEqual(None, err)
            self.assertEqual(self.envelope, raw)
            self.assertDictEqual({'NewExternalIPAddress': '11.22.33.44'}, result)

    async def test_scpd_post_timeout(self):
        sent: list = []
        replies: dict = {}
        with mock_tcp_and_udp(self.loop, tcp_replies=replies, sent_tcp_packets=sent):
            result, raw, err = await scpd_post(
                self.path, self.gateway_address, self.port, self.method, self.param_names, self.st, self.loop
            )
            self.assertTrue(isinstance(err, UPnPError))
            self.assertTrue(str(err).startswith('Timeout'))
            self.assertEqual(b'', raw)
            self.assertDictEqual({}, result)

    async def test_scpd_post_bad_xml_response(self):
        sent = []
        replies = {self.post_bytes: self.bad_envelope_response}
        with mock_tcp_and_udp(self.loop, tcp_replies=replies, sent_tcp_packets=sent):
            result, raw, err = await scpd_post(
                self.path, self.gateway_address, self.port, self.method, self.param_names, self.st, self.loop
            )
            self.assertTrue(isinstance(err, UPnPError))
            self.assertTrue(str(err).startswith('no element found'))
            self.assertEqual(self.bad_envelope, raw)
            self.assertDictEqual({}, result)

    async def test_scpd_post_overrun_response(self):
        sent = []
        replies = {self.post_bytes: self.post_response + b'\r\n'}
        with mock_tcp_and_udp(self.loop, tcp_replies=replies, sent_tcp_packets=sent):
            result, raw, err = await scpd_post(
                self.path, self.gateway_address, self.port, self.method, self.param_names, self.st, self.loop
            )
            self.assertTrue(isinstance(err, UPnPError))
            self.assertTrue(str(err).startswith('too many bytes written'))
            self.assertEqual(self.post_response + b'\r\n', raw)
            self.assertDictEqual({}, result)
