import unittest
from aioupnp.fault import UPnPError
from aioupnp.serialization.soap import serialize_soap_post, deserialize_soap_post_response


class TestSOAPSerialization(unittest.TestCase):
    param_names = []
    kwargs = {}
    method = "GetExternalIPAddress"
    gateway_address = "10.0.0.1".encode()
    st = "urn:schemas-upnp-org:service:WANIPConnection:1".encode()
    lan_address = "10.0.0.1".encode()
    path = "/soap.cgi?service=WANIPConn1".encode()

    post_request = '\r\n'.join([
        "POST /soap.cgi?service=WANIPConn1 HTTP/1.1",
        "Host: 10.0.0.1",
        "User-Agent: python3/aioupnp, UPnP/1.0, MiniUPnPc/1.9",
        "Content-Length: 285",
        "Content-Type: text/xml",
        "SOAPAction: \"urn:schemas-upnp-org:service:WANIPConnection:1#GetExternalIPAddress\"",
        "Connection: Close",
        "Cache-Control: no-cache",
        "Pragma: no-cache",
        "<?xml version=\"1.0\"?>",
        "<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\"",
        "s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">",
        "<s:Body><u:GetExternalIPAddress xmlns:u=\"urn:schemas-upnp-org:service:WANIPConnection:1\">",
        "</u:GetExternalIPAddress></s:Body></s:Envelope>",
    ]).encode()

    post_response = '\r\n'.join([
        "HTTP/1.1 200 OK",
        "CONTENT-LENGTH: 340",
        "CONTENT-TYPE: text/xml; charset=\"utf-8\"",
        "DATE: Thu, 18 Oct 2018 01:20:23 GMT",
        "EXT:",
        "SERVER: Linux/3.14.28-Prod_17.2, UPnP/1.0, Portable SDK for UPnP devices/1.6.22",
        "X-User-Agent: redsonic",
        ("<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\""
         "s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">"),
        "<s:Body>",
        "<u:GetExternalIPAddressResponse xmlns:u=\"urn:schemas-upnp-org:service:WANIPConnection:1\">",
        "<NewExternalIPAddress>11.22.33.44</NewExternalIPAddress>",
        "</u:GetExternalIPAddressResponse>",
        "</s:Body></s:Envelope>",
    ]).encode()

    error_response = '\r\n'.join([
        "HTTP/1.1 500 Internal Server Error",
        "Server: WebServer",
        "Date: Thu, 11 Oct 2018 22:16:17 GMT",
        "Connection: close"
        "CONTENT-TYPE: text/xml; charset=\"utf-8\"",
        "CONTENT-LENGTH: 482",
        "EXT:",
        ("<?xml version=\"1.0\"?>\n<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\""
         "s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">\n\t<s:Body>\n\t\t<s:Fault>\n\t\t\t"
         "<faultcode>s:Client</faultcode>\n\t\t\t<faultstring>UPnPError</faultstring>\n\t\t\t"
         "<detail>\n\t\t\t\t<UPnPError xmlns=\"urn:schemas-upnp-org:control-1-0\">\n\t\t\t\t\t"
         "<errorCode>713</errorCode>\n\t\t\t\t\t<errorDescription>SpecifiedArrayIndexInvalid"
         "</errorDescription>\n\t\t\t\t</UPnPError>\n\t\t\t</detail>\n\t\t</s:Fault>\n\t</s:Body>\n</s:Envelope>\n")
    ]).encode()

    def test_serialize_post(self):
        self.assertEqual(serialize_soap_post(
            self.method, self.param_names, self.st, self.gateway_address, self.path, **self.kwargs
        ), self.post_request)

    def test_deserialize_post_response(self):
        self.assertDictEqual(deserialize_soap_post_response(
            self.post_response, self.method.encode(), service_id=self.st),
            {'NewExternalIPAddress': "11.22.33.44"}
        )

    def test_raise_from_error_response(self):
        raised = False
        try:
            deserialize_soap_post_response(self.error_response, self.method.encode(), service_id=self.st)
        except UPnPError as err:
            raised = True
            self.assertTrue(f"{err}" is "SpecifiedArrayIndexInvalid")
        self.assertTrue(raised)
