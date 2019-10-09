import unittest
from unittest import mock
import socket
import struct
from asyncio import DatagramTransport
from aioupnp.protocols.multicast import MulticastProtocol


class TestMulticast(unittest.TestCase):
    def test_multicast(self):
        _ttl = None
        mock_socket = mock.MagicMock(spec=socket.socket)
        def getsockopt(*_):
            return _ttl

        def setsockopt(a, b, ttl: bytes):
            nonlocal _ttl
            _ttl, = struct.unpack('b', ttl)

        mock_socket.getsockopt = getsockopt
        mock_socket.setsockopt = setsockopt

        protocol = MulticastProtocol('1.2.3.4', '1.2.3.4')
        transport = DatagramTransport()
        transport._extra = {'socket': mock_socket}
        self.assertIsNone(protocol.set_ttl(1))
        self.assertEqual(0, protocol.get_ttl())
        protocol.connection_made(transport)
        self.assertIsNone(protocol.set_ttl(1))
        self.assertEqual(1, protocol.get_ttl())
