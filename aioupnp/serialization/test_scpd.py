import unittest
from aioupnp.serialization.scpd import serialize_scpd_get


class TestSCPDSerialization(unittest.TestCase):
    path, lan_address = '/InternetGatewayDevice.xml', '10.0.0.1'
    expected_result = b'GET /InternetGatewayDevice.xml HTTP/1.1\r\n' \
                      b'Accept-Encoding: gzip\r\nHost: 10.0.0.1\r\nConnection: Close\r\n\r\n'

    def test_serialize_get(self):
        self.assertEqual(serialize_scpd_get(self.path, self.lan_address), self.expected_result)
