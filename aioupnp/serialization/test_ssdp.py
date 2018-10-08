import unittest
from aioupnp.serialization.ssdp import SSDPDatagram
from aioupnp.fault import UPnPError


class TestParseMSearchRequest(unittest.TestCase):
    datagram = b'M-SEARCH * HTTP/1.1\r\n' \
               b'HOST: 239.255.255.250:1900\r\n' \
               b'ST: urn:schemas-upnp-org:device:InternetGatewayDevice:1\r\n' \
               b'MAN: "ssdp:discover"\r\n' \
               b'MX: 1\r\n' \
               b'\r\n'

    def test_parse_m_search_response(self):
        packet = SSDPDatagram.decode(self.datagram)
        self.assertTrue(packet._packet_type, packet._M_SEARCH)
        self.assertEqual(packet.host, '239.255.255.250:1900')
        self.assertEqual(packet.st, 'urn:schemas-upnp-org:device:InternetGatewayDevice:1')
        self.assertEqual(packet.man, 'ssdp:discover')
        self.assertEqual(packet.mx, 1)

    def test_serialize_m_search(self):
        packet = SSDPDatagram.decode(self.datagram)
        self.assertEqual(packet.encode().encode(), self.datagram)


class TestParseMSearchResponse(unittest.TestCase):
    datagram = "\r\n".join([
        'HTTP/1.1 200 OK',
        'CACHE_CONTROL: max-age=1800',
        'LOCATION: http://10.0.0.1:49152/InternetGatewayDevice.xml',
        'SERVER: Linux, UPnP/1.0, DIR-890L Ver 1.20',
        'ST: urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1',
        'USN: uuid:00000000-0000-0000-0000-000000000000::urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1'
    ]).encode()

    def test_parse_m_search_response(self):
        packet = SSDPDatagram.decode(self.datagram)
        self.assertTrue(packet._packet_type, packet._OK)
        self.assertEqual(packet.cache_control, 'max-age=1800')
        self.assertEqual(packet.location, 'http://10.0.0.1:49152/InternetGatewayDevice.xml')
        self.assertEqual(packet.server, 'Linux, UPnP/1.0, DIR-890L Ver 1.20')
        self.assertEqual(packet.st, 'urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1')
        self.assertEqual(packet.usn, 'uuid:00000000-0000-0000-0000-000000000000::urn:'
                                     'schemas-upnp-org:service:WANCommonInterfaceConfig:1'
)


class TestParseMSearchResponseDashCacheControl(TestParseMSearchResponse):
    datagram = "\r\n".join([
        'HTTP/1.1 200 OK',
        'CACHE-CONTROL: max-age=1800',
        'LOCATION: http://10.0.0.1:49152/InternetGatewayDevice.xml',
        'SERVER: Linux, UPnP/1.0, DIR-890L Ver 1.20',
        'ST: urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1',
        'USN: uuid:00000000-0000-0000-0000-000000000000::urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1'
    ]).encode()


class TestParseMSearchResponseCaseInsensitive(TestParseMSearchResponse):
    datagram = "\r\n".join([
        'HTTP/1.1 200 OK',
        'cache-CONTROL: max-age=1800',
        'LOCATION: http://10.0.0.1:49152/InternetGatewayDevice.xml',
        'Server: Linux, UPnP/1.0, DIR-890L Ver 1.20',
        'st: urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1',
        'USN: uuid:00000000-0000-0000-0000-000000000000::urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1'
    ]).encode()

    def test_get_case_insensitive(self):
        packet = SSDPDatagram.decode(self.datagram)
        self.assertEqual('max-age=1800', packet['Cache_Control'])

    def test_key_error(self):
        packet = SSDPDatagram.decode(self.datagram)
        self.assertRaises(KeyError, lambda : packet['Cache Control'])


class TestFailToParseMSearchResponseNoST(unittest.TestCase):
    datagram = "\r\n".join([
        'HTTP/1.1 200 OK',
        'CACHE_CONTROL: max-age=1800',
        'LOCATION: http://10.0.0.1:49152/InternetGatewayDevice.xml',
        'SERVER: Linux, UPnP/1.0, DIR-890L Ver 1.20',
        'USN: uuid:00000000-0000-0000-0000-000000000000::urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1'
    ]).encode()

    def test_fail_to_parse_m_search_response(self):
        self.assertRaises(UPnPError, SSDPDatagram.decode, self.datagram)


class TestFailToParseMSearchResponseNoOK(TestFailToParseMSearchResponseNoST):
    datagram = "\r\n".join([
        'cache-CONTROL: max-age=1800',
        'LOCATION: http://10.0.0.1:49152/InternetGatewayDevice.xml',
        'Server: Linux, UPnP/1.0, DIR-890L Ver 1.20',
        'st: urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1',
        'USN: uuid:00000000-0000-0000-0000-000000000000::urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1'
    ]).encode()


class TestFailToParseMSearchResponseNoLocation(TestFailToParseMSearchResponseNoST):
    datagram = "\r\n".join([
        'HTTP/1.1 200 OK',
        'cache-CONTROL: max-age=1800',
        'Server: Linux, UPnP/1.0, DIR-890L Ver 1.20',
        'st: urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1',
        'USN: uuid:00000000-0000-0000-0000-000000000000::urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1'
    ]).encode()


class TestParseNotify(unittest.TestCase):
    datagram = \
        b'NOTIFY * HTTP/1.1 \r\n' \
        b'Host: 239.255.255.250:1900\r\n' \
        b'Cache-Control: max-age=180\r\n' \
        b'Location: http://192.168.1.1:5431/dyndev/uuid:000c-29ea-247500c00068\r\n' \
        b'NT: upnp:rootdevice\r\n' \
        b'NTS: ssdp:alive\r\n' \
        b'SERVER: LINUX/2.4 UPnP/1.0 BRCM400/1.0\r\n' \
        b'USN: uuid:000c-29ea-247500c00068::upnp:rootdevice\r\n' \
        b'\r\n'

    def test_parse_notify(self):
        packet = SSDPDatagram.decode(self.datagram)
        self.assertTrue(packet._packet_type, packet._NOTIFY)
        self.assertEqual(packet.host, '239.255.255.250:1900')
        self.assertEqual(packet.cache_control, 'max-age=180')
        self.assertEqual(packet.location, 'http://192.168.1.1:5431/dyndev/uuid:000c-29ea-247500c00068')
        self.assertEqual(packet.nt, 'upnp:rootdevice')
        self.assertEqual(packet.nts, 'ssdp:alive')
        self.assertEqual(packet.server, 'LINUX/2.4 UPnP/1.0 BRCM400/1.0')
        self.assertEqual(packet.usn, 'uuid:000c-29ea-247500c00068::upnp:rootdevice')
