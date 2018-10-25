from collections import OrderedDict
from aioupnp.fault import UPnPError
from aioupnp.protocols.m_search_patterns import packet_generator
from aioupnp.serialization.ssdp import SSDPDatagram
from aioupnp.constants import SSDP_IP_ADDRESS
from aioupnp.protocols.ssdp import fuzzy_m_search, m_search
from tests import TestBase
from tests.mocks import mock_datagram_endpoint_factory


class TestSSDP(TestBase):
    packet_args = list(packet_generator())
    byte_packets = [SSDPDatagram("M-SEARCH", p).encode().encode() for p in packet_args]

    successful_args = OrderedDict([
        ("HOST", "239.255.255.250:1900"),
        ("MAN", "ssdp:discover"),
        ("MX", 1),
        ("ST", "urn:schemas-upnp-org:device:WANDevice:1")
    ])
    query_packet = SSDPDatagram("M-SEARCH", successful_args)

    reply_args = OrderedDict([
        ("CACHE_CONTROL", "max-age=1800"),
        ("LOCATION", "http://10.0.0.1:49152/InternetGatewayDevice.xml"),
        ("SERVER", "Linux, UPnP/1.0, DIR-890L Ver 1.20"),
        ("ST", "urn:schemas-upnp-org:device:WANDevice:1"),
        ("USN", "uuid:22222222-3333-4444-5555-666666666666::urn:schemas-upnp-org:device:WANDevice:1")
    ])
    reply_packet = SSDPDatagram("OK", reply_args)

    async def test_m_search_reply_unicast(self):
        replies = {
            (self.query_packet.encode().encode(), ("10.0.0.1", 1900)): self.reply_packet.encode().encode()
        }
        sent = []

        with mock_datagram_endpoint_factory(self.loop, "10.0.0.1", replies=replies, sent_packets=sent):
            reply = await m_search("10.0.0.2", "10.0.0.1", self.successful_args, timeout=1, loop=self.loop, unicast=True)

        self.assertEqual(reply.encode(), self.reply_packet.encode())
        self.assertListEqual(sent, [self.query_packet.encode().encode()])

        with self.assertRaises(UPnPError):
            with mock_datagram_endpoint_factory(self.loop, "10.0.0.1", replies=replies):
                await m_search("10.0.0.2", "10.0.0.1", self.successful_args, timeout=1, loop=self.loop, unicast=False)

    async def test_m_search_reply_multicast(self):
        replies = {
            (self.query_packet.encode().encode(), (SSDP_IP_ADDRESS, 1900)): self.reply_packet.encode().encode()
        }
        sent = []

        with mock_datagram_endpoint_factory(self.loop, "10.0.0.1", replies=replies, sent_packets=sent):
            reply = await m_search("10.0.0.2", "10.0.0.1", self.successful_args, timeout=1, loop=self.loop)

        self.assertEqual(reply.encode(), self.reply_packet.encode())
        self.assertListEqual(sent, [self.query_packet.encode().encode()])

        with self.assertRaises(UPnPError):
            with mock_datagram_endpoint_factory(self.loop, "10.0.0.1", replies=replies):
                await m_search("10.0.0.2", "10.0.0.1", self.successful_args, timeout=1, loop=self.loop, unicast=True)

    async def test_packets_sent_fuzzy_m_search(self):
        sent = []

        with self.assertRaises(UPnPError):
            with mock_datagram_endpoint_factory(self.loop, "10.0.0.1", sent_packets=sent):
                await fuzzy_m_search("10.0.0.2", "10.0.0.1", 1, self.loop)

        self.assertListEqual(sent, self.byte_packets)

    async def test_packets_fuzzy_m_search(self):
        replies = {
            (self.query_packet.encode().encode(), (SSDP_IP_ADDRESS, 1900)): self.reply_packet.encode().encode()
        }
        sent = []

        with mock_datagram_endpoint_factory(self.loop, "10.0.0.1", replies=replies, sent_packets=sent):
            args, reply = await fuzzy_m_search("10.0.0.2", "10.0.0.1", 1, self.loop)

        self.assertEqual(reply.encode(), self.reply_packet.encode())
        self.assertEqual(args, self.successful_args)
