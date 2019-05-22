import unittest

from asyncio import DatagramTransport
from aioupnp.protocols.multicast import MulticastProtocol


class TestMulticast(unittest.TestCase):
    def test_it(self):
        class none_socket:
            sock = None

            def get(self, name, default=None):
                return default

        protocol = MulticastProtocol('1.2.3.4', '1.2.3.4')
        transport = DatagramTransport(none_socket())
        protocol.set_ttl(1)
        with self.assertRaises(ValueError):
            _ = protocol.get_ttl()
        protocol.connection_made(transport)
        protocol.set_ttl(1)
        with self.assertRaises(ValueError):
            _ = protocol.get_ttl()
