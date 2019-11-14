import unittest
from aioupnp.fault import UPnPError
from aioupnp.serialization.soap import serialize_soap_post, deserialize_soap_post_response


class TestSOAPSerialization(unittest.TestCase):
    param_names: list = []
    kwargs: dict = {}
    method, gateway_address = "GetExternalIPAddress", b'10.0.0.1'
    st, lan_address, path = b'urn:schemas-upnp-org:service:WANIPConnection:1', '10.0.0.1', b'/soap.cgi?service=WANIPConn1'
    post_bytes = b'POST /soap.cgi?service=WANIPConn1 HTTP/1.1\r\n' \
                 b'Host: 10.0.0.1\r\nUser-Agent: python3/aioupnp, UPnP/1.0, MiniUPnPc/1.9\r\n' \
                 b'Content-Length: 285\r\nContent-Type: text/xml\r\n' \
                 b'SOAPAction: "urn:schemas-upnp-org:service:WANIPConnection:1#GetExternalIPAddress"\r\n' \
                 b'Connection: Close\r\nCache-Control: no-cache\r\nPragma: no-cache\r\n\r\n' \
                 b'<?xml version="1.0"?>\r\n<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"' \
                 b' s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">' \
                 b'<s:Body><u:GetExternalIPAddress xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1">' \
                 b'</u:GetExternalIPAddress></s:Body></s:Envelope>\r\n'

    post_response = b"HTTP/1.1 200 OK\r\n" \
                    b"CONTENT-LENGTH: 340\r\n" \
                    b"CONTENT-TYPE: text/xml; charset=\"utf-8\"\r\n" \
                    b"DATE: Thu, 18 Oct 2018 01:20:23 GMT\r\n" \
                    b"EXT:\r\n" \
                    b"SERVER: Linux/3.14.28-Prod_17.2, UPnP/1.0, Portable SDK for UPnP devices/1.6.22\r\n" \
                    b"X-User-Agent: redsonic\r\n" \
                    b"\r\n" \
                    b"<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"><s:Body>\n<u:GetExternalIPAddressResponse xmlns:u=\"urn:schemas-upnp-org:service:WANIPConnection:1\">\r\n<NewExternalIPAddress>11.22.33.44</NewExternalIPAddress>\r\n</u:GetExternalIPAddressResponse>\r\n</s:Body> </s:Envelope>"

    blank_response = b"HTTP/1.1 200 OK\r\n" \
                    b"CONTENT-LENGTH: 148\r\n" \
                    b"CONTENT-TYPE: text/xml; charset=\"utf-8\"\r\n" \
                    b"DATE: Thu, 18 Oct 2018 01:20:23 GMT\r\n" \
                    b"EXT:\r\n" \
                    b"SERVER: Linux/3.14.28-Prod_17.2, UPnP/1.0, Portable SDK for UPnP devices/1.6.22\r\n" \
                    b"X-User-Agent: redsonic\r\n" \
                    b"\r\n" \
                    b"<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"><s:Body>\n</s:Body> </s:Envelope>"

    blank_response_body = b"HTTP/1.1 200 OK\r\n" \
                    b"CONTENT-LENGTH: 280\r\n" \
                    b"CONTENT-TYPE: text/xml; charset=\"utf-8\"\r\n" \
                    b"DATE: Thu, 18 Oct 2018 01:20:23 GMT\r\n" \
                    b"EXT:\r\n" \
                    b"SERVER: Linux/3.14.28-Prod_17.2, UPnP/1.0, Portable SDK for UPnP devices/1.6.22\r\n" \
                    b"X-User-Agent: redsonic\r\n" \
                    b"\r\n" \
                    b"<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"><s:Body>\n<u:GetExternalIPAddressResponse xmlns:u=\"urn:schemas-upnp-org:service:WANIPConnection:1\"></u:GetExternalIPAddressResponse>\r\n</s:Body> </s:Envelope>"

    error_response = b"HTTP/1.1 500 Internal Server Error\r\n" \
                     b"Server: WebServer\r\n" \
                     b"Date: Thu, 11 Oct 2018 22:16:17 GMT\r\n" \
                     b"Connection: close\r\n" \
                     b"CONTENT-TYPE: text/xml; charset=\"utf-8\"\r\n" \
                     b"CONTENT-LENGTH: 482 \r\n" \
                     b"EXT:\r\n" \
                     b"\r\n" \
                     b"<?xml version=\"1.0\"?>\n<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">\n\t<s:Body>\n\t\t<s:Fault>\n\t\t\t<faultcode>s:Client</faultcode>\n\t\t\t<faultstring>UPnPError</faultstring>\n\t\t\t<detail>\n\t\t\t\t<UPnPError xmlns=\"urn:schemas-upnp-org:control-1-0\">\n\t\t\t\t\t<errorCode>713</errorCode>\n\t\t\t\t\t<errorDescription>SpecifiedArrayIndexInvalid</errorDescription>\n\t\t\t\t</UPnPError>\n\t\t\t</detail>\n\t\t</s:Fault>\n\t</s:Body>\n</s:Envelope>\n"

    error_response_no_description = b"HTTP/1.1 500 Internal Server Error\r\n" \
                                    b"Server: WebServer\r\n" \
                                    b"Date: Thu, 11 Oct 2018 22:16:17 GMT\r\n" \
                                    b"Connection: close\r\n" \
                                    b"CONTENT-TYPE: text/xml; charset=\"utf-8\"\r\n" \
                                    b"CONTENT-LENGTH: 429 \r\n" \
                                    b"EXT:\r\n" \
                                    b"\r\n" \
                                    b"<?xml version=\"1.0\"?>\n<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">\n\t<s:Body>\n\t\t<s:Fault>\n\t\t\t<faultcode>s:Client</faultcode>\n\t\t\t<faultstring>UPnPError</faultstring>\n\t\t\t<detail>\n\t\t\t\t<UPnPError xmlns=\"urn:schemas-upnp-org:control-1-0\">\n\t\t\t\t\t<errorCode>713</errorCode>\n\t\t\t\t\t\n\t\t\t\t</UPnPError>\n\t\t\t</detail>\n\t\t</s:Fault>\n\t</s:Body>\n</s:Envelope>\n"

    def test_serialize_post(self):
        self.assertEqual(serialize_soap_post(
            self.method, self.param_names, self.st, self.gateway_address, self.path, **self.kwargs
        ), self.post_bytes)

    def test_serialize_post_http_host(self):
        self.assertEqual(serialize_soap_post(
            self.method, self.param_names, self.st, b'http://' + self.gateway_address, self.path, **self.kwargs
        ), self.post_bytes)

    def test_deserialize_post_response(self):
        self.assertDictEqual(
            deserialize_soap_post_response(self.post_response, self.method, service_id=self.st.decode()),
            {'NewExternalIPAddress': '11.22.33.44'}
        )

    def test_deserialize_error_response_field_not_found(self):
        with self.assertRaises(UPnPError) as e:
            deserialize_soap_post_response(self.post_response, self.method + 'derp', service_id=self.st.decode())
        self.assertTrue(str(e.exception).startswith('unknown response fields for GetExternalIPAddressderp'))

    def test_deserialize_blank_response(self):
        # TODO: these seem like they should error... this test will break and have to be updated
        self.assertDictEqual({}, deserialize_soap_post_response(self.blank_response, self.method,
                                                                service_id=self.st.decode()))
        self.assertDictEqual({}, deserialize_soap_post_response(self.blank_response_body, self.method,
                                                                service_id=self.st.decode()))

    def test_raise_from_error_response(self):
        raised = False
        try:
            deserialize_soap_post_response(self.error_response, self.method, service_id=self.st.decode())
        except UPnPError as err:
            raised = True
            self.assertEqual(str(err), 'SpecifiedArrayIndexInvalid')
        self.assertTrue(raised)

    def test_raise_from_error_response_without_error_description(self):
        raised = False
        expected = 'Failed to decode error response: {"faultcode": "s:Client", "faultstring": "UPnPError", "detail": {"UPnPError": {"errorCode": "713"}}}'
        try:
            deserialize_soap_post_response(self.error_response_no_description, self.method, service_id=self.st.decode())
        except UPnPError as err:
            raised = True
            self.assertEqual(str(err), expected)
        self.assertTrue(raised)

    def test_soap_env_namespace_response(self):
        # tp link devices use `SOAP-ENV` namespace rather than the normal `s`
        response = b'HTTP/1.1 200 OK\r\nCONNECTION: close\r\nSERVER: ipos/7.0 UPnP/1.0 TL-WR940N/TL-WR941ND/3.0\r\nCONTENT-LENGTH: 404\r\nCONTENT-TYPE: text/xml; charset="utf-8"\r\n\r\n<?xml version="1.0"?>\n<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">\n<SOAP-ENV:Body>\n<u:GetExternalIPAddressResponse xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1"><NewExternalIPAddress>100.100.100.100</NewExternalIPAddress></u:GetExternalIPAddressResponse></SOAP-ENV:Body>\n</SOAP-ENV:Envelope>\n'
        self.assertDictEqual(
            deserialize_soap_post_response(response, 'GetExternalIPAddress', self.st.decode()),
            {'NewExternalIPAddress': '100.100.100.100'}
        )
