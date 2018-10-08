import unittest
from aioupnp.serialization.soap import serialize_soap_post


class TestSOAPSerialization(unittest.TestCase):
    param_names: list = []
    kwargs: dict = {}
    method, gateway_address = "GetExternalIPAddress", b'10.0.0.1'
    st, lan_address, path = b'urn:schemas-upnp-org:service:WANIPConnection:1', '10.0.0.1', b'/soap.cgi?service=WANIPConn1'
    expected_result = b'POST /soap.cgi?service=WANIPConn1 HTTP/1.1\r\n' \
                      b'Host: 10.0.0.1\r\nUser-Agent: python3/aioupnp, UPnP/1.0, MiniUPnPc/1.9\r\n' \
                      b'Content-Length: 285\r\nContent-Type: text/xml\r\n' \
                      b'SOAPAction: "urn:schemas-upnp-org:service:WANIPConnection:1#GetExternalIPAddress"\r\n' \
                      b'Connection: Close\r\nCache-Control: no-cache\r\nPragma: no-cache\r\n\r\n' \
                      b'<?xml version="1.0"?>\r\n<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"' \
                      b' s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">' \
                      b'<s:Body><u:GetExternalIPAddress xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1">' \
                      b'</u:GetExternalIPAddress></s:Body></s:Envelope>\r\n'

    def test_serialize_get(self):
        self.assertEqual(serialize_soap_post(
            self.method, self.param_names, self.st, self.gateway_address, self.path, **self.kwargs
        ), self.expected_result)
