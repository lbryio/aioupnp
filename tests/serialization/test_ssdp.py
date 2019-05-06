import unittest
from collections import OrderedDict
from aioupnp.serialization.ssdp import SSDPDatagram
from aioupnp.fault import UPnPError
from aioupnp.constants import UPNP_ORG_IGD


class TestSSDPDatagram(unittest.TestCase):
    def test_fail_to_init(self):
        datagram_args = OrderedDict([
            ("Host", '{}:{}'.format("239.255.255.250", 1900)),
            ("Man", "\"ssdp:discover\""),
            ("ST", "ssdp:all"),
            ("MX", 5),
        ])

        with self.assertRaises(UPnPError):
            SSDPDatagram("?", **datagram_args)

    def test_fail_to_decode_missing_required(self):
        packet = '\r\n'.join([
            "M-SEARCH * HTTP/1.1",
            "Host: 239.255.255.250:1900",
            "ST: ssdp:all",
            "MX: 5",
        ]).encode()

        with self.assertRaises(UPnPError):
            SSDPDatagram.decode(packet)

    def test_fail_to_decode_blank(self):
        packet = '\r\n'.join([]).encode()

        with self.assertRaises(UPnPError):
            SSDPDatagram.decode(packet)

    def test_fail_to_decode_one_line(self):
        packet = '\r\n'.join([
            "M-SEARCH * HTTP/1.1"
        ]).encode()

        with self.assertRaises(UPnPError):
            SSDPDatagram.decode(packet)

    def test_cli_args(self):
        datagram_args = OrderedDict([
            ("Host", '{}:{}'.format("239.255.255.250", 1900)),
            ("Man", "\"ssdp:discover\""),
            ("ST", "ssdp:all"),
            ("MX", 5),
        ])
        packet = SSDPDatagram("M-SEARCH", **datagram_args)
        self.assertEqual(
            packet.get_cli_igd_kwargs(),
            "--Host={} --Man={} --ST={} --MX={}".format(
                "239.255.255.250:1900",
                "\"ssdp:discover\"",
                "ssdp:all",
                str(5),
            )
        )

    def test_as_dict(self):
        datagram_args = OrderedDict([
            ("Host", '{}:{}'.format("239.255.255.250", 1900)),
            ("Man", "\"ssdp:discover\""),
            ("ST", "ssdp:all"),
            ("MX", 5),
        ])
        packet = SSDPDatagram("M-SEARCH", **datagram_args)
        self.assertDictEqual(
            packet.as_dict(),
            {
                'Host': "239.255.255.250:1900",
                'Man': "\"ssdp:discover\"",
                'ST': "ssdp:all",
                'MX': 5
            }
        )


class TestMSearchDatagramSerialization(unittest.TestCase):
    packet = '\r\n'.join([
        "M-SEARCH * HTTP/1.1",
        "Host: 239.255.255.250:1900"
        "Man: \"ssdp:discover\"",
        "ST: ssdp:all",
        "MX: 5",
    ]).encode()

    datagram_args = OrderedDict([
        ('Host', "{}:{}".format('239.255.255.250', 1900)),
        ('Man', '"ssdp:discover"'),
        ('ST', 'ssdp:all'),
        ('MX', 5),
    ])

    def test_deserialize_and_reserialize(self):
        packet1 = SSDPDatagram.decode(self.packet)
        packet2 = SSDPDatagram("M-SEARCH", **self.datagram_args)
        self.assertEqual(packet2.encode(), packet1.encode())


class TestSerializationOrder(TestMSearchDatagramSerialization):
    packet = '\r\n'.join([
        "M-SEARCH * HTTP/1.1",
        "Host: 239.255.255.250:1900",
        "ST: ssdp:all",
        "Man: \"ssdp:discover\"",
        "MX: 5",
    ]).encode()

    datagram_args = OrderedDict([
        ("Host", '{}:{}'.format("239.255.255.250", 1900)),
        ("ST", "ssdp:all"),
        ("Man", "\"ssdp:discover\""),
        ("MX", 5),
    ])


class TestSerializationPreserveCase(TestMSearchDatagramSerialization):
    packet = '\r\n'.join([
        "M-SEARCH * HTTP/1.1",
        "HOST: 239.255.255.250:1900",
        "ST: ssdp:all",
        "Man: \"ssdp:discover\"",
        "mx: 5",
    ]).encode()

    datagram_args = OrderedDict([
        ("HOST", '{}:{}'.format("239.255.255.250", 1900)),
        ("ST", 'ssdp:all'),
        ("Man", "\"ssdp:discover\""),
        ("mx", 5),
    ])


class TestSerializationPreserveAllLowerCase(TestMSearchDatagramSerialization):
    packet = '\r\n'.join([
        "M-SEARCH * HTTP/1.1",
        "host: 239.255.255.250:1900",
        "st: ssdp:all",
        "man: \"ssdp:discover\"",
        "mx: 5",
    ]).encode()

    datagram_args = OrderedDict([
        ("host", '{}:{}'.format("239.255.255.250", 1900)),
        ("st", "ssdp:all"),
        ("man", "\"ssdp:discover\""),
        ("mx", 5),
    ])


class TestParseMSearchRequestWithQuotes(unittest.TestCase):
    datagram = '\r\n'.join([
        "M-SEARCH * HTTP/1.1",
        "HOST: 239.255.255.250:1900",
        "ST: urn:schemas-upnp-org:device:InternetGatewayDevice:1",
        "MAN: \"ssdp:discover\"",
        "MX: 1",
    ]).encode()

    def test_parse_m_search(self):
        packet = SSDPDatagram.decode(self.datagram)
        self.assertTrue(packet._packet_type, packet._M_SEARCH)
        self.assertEqual(packet.host, "239.255.255.250:1900")
        self.assertEqual(packet.st, "urn:schemas-upnp-org:device:InternetGatewayDevice:1")
        self.assertEqual(packet.man, "\"ssdp:discover\"")
        self.assertEqual(packet.mx, 1)


class TestParseMSearchRequestWithoutQuotes(unittest.TestCase):
    datagram = '\r\n'.join([
        "M-SEARCH * HTTP/1.1",
        "HOST: 239.255.255.250:1900",
        "ST: urn:schemas-upnp-org:device:InternetGatewayDevice:1"
        "MAN: ssdp:discover"
        "MX: 1",
    ]).encode()

    def test_parse_m_search(self):
        packet = SSDPDatagram.decode(self.datagram)
        self.assertTrue(packet._packet_type, packet._M_SEARCH)
        self.assertEqual(packet.host, "239.255.255.250:1900")
        self.assertEqual(packet.st, "urn:schemas-upnp-org:device:InternetGatewayDevice:1")
        self.assertEqual(packet.man, "ssdp:discover")
        self.assertEqual(packet.mx, 1)

    def test_serialize_m_search(self):
        packet = SSDPDatagram.decode(self.datagram)
        self.assertEqual(packet.encode().encode(), self.datagram)


class TestParseMSearchResponse(unittest.TestCase):
    datagram = '\r\n'.join([
        "HTTP/1.1 200 OK",
        "CACHE_CONTROL: max-age=1800",
        "LOCATION: http://10.0.0.1:49152/InternetGatewayDevice.xml",
        "SERVER: Linux, UPnP/1.0, DIR-890L Ver 1.20",
        "ST: urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1",
        "USN: uuid:00000000-0000-0000-0000-000000000000::urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1"
    ]).encode()

    def test_parse_m_search_response(self):
        packet = SSDPDatagram.decode(self.datagram)
        self.assertTrue(packet._packet_type, packet._OK)
        self.assertEqual(packet.cache_control, "max-age=1800")
        self.assertEqual(packet.location, "http://10.0.0.1:49152/InternetGatewayDevice.xml")
        self.assertEqual(packet.server, "Linux, UPnP/1.0, DIR-890L Ver 1.20")
        self.assertEqual(packet.st, "urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1")
        self.assertEqual(packet.usn, "uuid:00000000-0000-0000-0000-000000000000::urn:"
                                     "schemas-upnp-org:service:WANCommonInterfaceConfig:1")


class TestParseMSearchResponseRedSonic(TestParseMSearchResponse):
    datagram = '\r\n'.join([
        "HTTP/1.1 200 OK",
        "CACHE-CONTROL: max-age=1800",
        "DATE: Thu, 04 Oct 2018 22:59:40 GMT",
        "EXT:",
        "LOCATION: http://10.1.10.1:49152/IGDdevicedesc_brlan0.xml",
        "OPT: \"http://schemas.upnp.org/upnp/1/0/\"; ns=01",
        "01-NLS: 00000000-0000-0000-0000-000000000000",
        "SERVER: Linux/3.14.28-Prod_17.2, UPnP/1.0, Portable SDK for UPnP devices/1.6.22",
        "X-User-Agent: redsonic",
        "ST: urn:schemas-upnp-org:device:InternetGatewayDevice:1",
        "USN: uuid:00000000-0000-0000-0000-000000000000::urn:schemas-upnp-org:device:InternetGatewayDevice:1",
    ]).encode()

    def test_parse_m_search_response(self):
        packet = SSDPDatagram.decode(self.datagram)
        self.assertTrue(packet._packet_type, packet._OK)
        self.assertEqual(packet.cache_control, "max-age=1800")
        self.assertEqual(packet.location, "http://10.1.10.1:49152/IGDdevicedesc_brlan0.xml")
        self.assertEqual(packet.server, "Linux/3.14.28-Prod_17.2, UPnP/1.0, Portable SDK for UPnP devices/1.6.22")
        self.assertEqual(packet.st, UPNP_ORG_IGD)


class TestParseMSearchResponseDashCacheControl(TestParseMSearchResponse):
    datagram = '\r\n'.join([
        "HTTP/1.1 200 OK",
        "CACHE-CONTROL: max-age=1800",
        "LOCATION: http://10.0.0.1:49152/InternetGatewayDevice.xml",
        "SERVER: Linux, UPnP/1.0, DIR-890L Ver 1.20",
        "ST: urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1",
        "USN: uuid:00000000-0000-0000-0000-000000000000::urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1"
    ]).encode()


class TestParseMSearchResponseCaseInsensitive(TestParseMSearchResponse):
    datagram = '\r\n'.join([
        "HTTP/1.1 200 OK",
        "cache-CONTROL: max-age=1800",
        "LOCATION: http://10.0.0.1:49152/InternetGatewayDevice.xml",
        "Server: Linux, UPnP/1.0, DIR-890L Ver 1.20",
        "st: urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1",
        "USN: uuid:00000000-0000-0000-0000-000000000000::urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1"
    ]).encode()

    def test_get_case_insensitive(self):
        packet = SSDPDatagram.decode(self.datagram)
        self.assertEqual("max-age=1800", packet['Cache_Control'])

    def test_key_error(self):
        packet = SSDPDatagram.decode(self.datagram)
        self.assertRaises(KeyError, lambda: packet['Cache Control'])


class TestFailToParseMSearchResponseNoST(unittest.TestCase):
    datagram = '\r\n'.join([
        "HTTP/1.1 200 OK",
        "CACHE_CONTROL: max-age=1800",
        "LOCATION: http://10.0.0.1:49152/InternetGatewayDevice.xml",
        "SERVER: Linux, UPnP/1.0, DIR-890L Ver 1.20",
        "USN: uuid:00000000-0000-0000-0000-000000000000::urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1"
    ]).encode()

    def test_fail_to_parse_m_search_response(self):
        self.assertRaises(UPnPError, SSDPDatagram.decode, self.datagram)


class TestFailToParseMSearchResponseNoOK(TestFailToParseMSearchResponseNoST):
    datagram = '\r\n'.join([
        "cache-CONTROL: max-age=1800",
        "LOCATION: http://10.0.0.1:49152/InternetGatewayDevice.xml",
        "Server: Linux, UPnP/1.0, DIR-890L Ver 1.20",
        "st: urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1",
        "USN: uuid:00000000-0000-0000-0000-000000000000::urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1"
    ]).encode()


class TestFailToParseMSearchResponseNoLocation(TestFailToParseMSearchResponseNoST):
    datagram = '\r\n'.join([
        "HTTP/1.1 200 OK",
        "cache-CONTROL: max-age=1800",
        "Server: Linux, UPnP/1.0, DIR-890L Ver 1.20",
        "st: urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1",
        "USN: uuid:00000000-0000-0000-0000-000000000000::urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1"
    ]).encode()


class TestParseNotify(unittest.TestCase):
    datagram = '\r\n'.join([
        "NOTIFY * HTTP/1.1",
        "Host: 239.255.255.250:1900",
        "Cache-Control: max-age=180",
        "Location: http://192.168.1.1:5431/dyndev/uuid:000c-29ea-247500c00068",
        "NT: upnp:rootdevice",
        "NTS: ssdp:alive",
        "SERVER: LINUX/2.4 UPnP/1.0 BRCM400/1.0",
        "USN: uuid:000c-29ea-247500c00068::upnp:rootdevice",
    ]).encode()

    def test_parse_notify(self):
        packet = SSDPDatagram.decode(self.datagram)
        self.assertTrue(packet._packet_type, packet._NOTIFY)
        self.assertEqual(packet.host, "239.255.255.250:1900")
        self.assertEqual(packet.cache_control, "max-age=180")  # this is an optional field
        self.assertEqual(packet.location, "http://192.168.1.1:5431/dyndev/uuid:000c-29ea-247500c00068")
        self.assertEqual(packet.nt, "upnp:rootdevice")
        self.assertEqual(packet.nts, "ssdp:alive")
        self.assertEqual(packet.server, "LINUX/2.4 UPnP/1.0 BRCM400/1.0")
        self.assertEqual(packet.usn, "uuid:000c-29ea-247500c00068::upnp:rootdevice")
