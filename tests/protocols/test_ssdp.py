import json
from collections import OrderedDict
from aioupnp.fault import UPnPError
from aioupnp.protocols.m_search_patterns import packet_generator
from aioupnp.serialization.ssdp import SSDPDatagram
from aioupnp.constants import SSDP_IP_ADDRESS
from aioupnp.protocols.ssdp import m_search, SSDPProtocol
from tests import AsyncioTestCase, mock_tcp_and_udp


class TestSSDP(AsyncioTestCase):
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

    async def test_socket_setup_error(self):
        with mock_tcp_and_udp(self.loop, raise_oserror_on_bind=True):
            with self.assertRaises(UPnPError):
                await m_search("10.0.0.2", "10.0.0.1", self.successful_args, timeout=1, loop=self.loop)

    async def test_transport_not_connected_error(self):
        try:
            await SSDPProtocol('', '').m_search('1.2.3.4', 2,  [self.query_packet.as_dict()])
            self.assertTrue(False)
        except UPnPError as err:
            self.assertEqual(str(err), "SSDP transport not connected")

    async def test_deadbeef_response(self):
        replies = {
            (self.query_packet.encode().encode(), ("10.0.0.1", 1900)): b'\xde\xad\xbe\xef'
        }
        sent = []

        with mock_tcp_and_udp(self.loop, udp_replies=replies, udp_expected_addr="10.0.0.1", sent_udp_packets=sent):
            with self.assertRaises(UPnPError):
                await m_search("10.0.0.2", "10.0.0.1", self.successful_args, timeout=1, loop=self.loop)

    async def test_ssdp_pretty_print(self):
        self.assertEqual(
            json.dumps({
                "HOST": "239.255.255.250:1900",
                "MAN": "ssdp:discover",
                "MX": 1,
                "ST": "urn:schemas-upnp-org:device:WANDevice:1"
            }, indent=2), str(self.query_packet)
        )

    async def test_m_search_reply_unicast(self):
        replies = {
            (self.query_packet.encode().encode(), ("10.0.0.1", 1900)): self.reply_packet.encode().encode()
        }
        sent = []

        with mock_tcp_and_udp(self.loop, udp_replies=replies, udp_expected_addr="10.0.0.1", sent_udp_packets=sent):
            reply = await m_search("10.0.0.2", "10.0.0.1", self.successful_args, timeout=1, loop=self.loop)

        self.assertEqual(reply.encode(), self.reply_packet.encode())
        self.assertIn(self.query_packet.encode().encode(), sent)

        with self.assertRaises(UPnPError):
            with mock_tcp_and_udp(self.loop, udp_expected_addr="10.0.0.10", udp_replies=replies):
                await m_search("10.0.0.2", "10.0.0.1", self.successful_args, timeout=1, loop=self.loop)

    async def test_m_search_reply_multicast(self):
        replies = {
            (self.query_packet.encode().encode(), (SSDP_IP_ADDRESS, 1900)): self.reply_packet.encode().encode()
        }
        sent = []

        with mock_tcp_and_udp(self.loop, udp_replies=replies, udp_expected_addr="10.0.0.1", sent_udp_packets=sent):
            reply = await m_search("10.0.0.2", "10.0.0.1", self.successful_args, timeout=1, loop=self.loop)

        self.assertEqual(reply.encode(), self.reply_packet.encode())
        self.assertIn(self.query_packet.encode().encode(), sent)

        with self.assertRaises(UPnPError):
            with mock_tcp_and_udp(self.loop, udp_replies=replies, udp_expected_addr="10.0.0.10"):
                await m_search("10.0.0.2", "10.0.0.1", self.successful_args, timeout=1, loop=self.loop)

    # async def test_packets_sent_fuzzy_m_search(self):
    #     sent = []
    #
    #     with self.assertRaises(UPnPError):
    #         with mock_tcp_and_udp(self.loop, udp_expected_addr="10.0.0.1", sent_udp_packets=sent):
    #             await fuzzy_m_search("10.0.0.2", "10.0.0.1", 1, self.loop)
    #     for packet in self.byte_packets:
    #         self.assertIn(packet, sent)
    #
    # async def test_packets_fuzzy_m_search(self):
    #     replies = {
    #         (self.query_packet.encode().encode(), (SSDP_IP_ADDRESS, 1900)): self.reply_packet.encode().encode()
    #     }
    #     sent = []
    #
    #     with mock_tcp_and_udp(self.loop, udp_expected_addr="10.0.0.1", udp_replies=replies, sent_udp_packets=sent):
    #         args, reply = await fuzzy_m_search("10.0.0.2", "10.0.0.1", 1, self.loop)
    #
    #     self.assertEqual(reply.encode(), self.reply_packet.encode())
    #     self.assertEqual(args, self.successful_args)
    #
    # async def test_packets_sent_fuzzy_m_search_ignore_invalid_datagram_replies(self):
    #     sent = []
    #
    #     with self.assertRaises(UPnPError):
    #         with mock_tcp_and_udp(self.loop, udp_expected_addr="10.0.0.1", sent_udp_packets=sent,
    #                               add_potato_datagrams=True):
    #             await fuzzy_m_search("10.0.0.2", "10.0.0.1", 1, self.loop)
    #
    #     for packet in self.byte_packets:
    #         self.assertIn(packet, sent)