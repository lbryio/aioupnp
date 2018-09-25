from twisted.internet import reactor, defer
from twisted.trial import unittest
from txupnp.constants import SSDP_PORT
from txupnp import mocks
from txupnp.ssdp import SSDPFactory


class TestDiscoverGateway(unittest.TestCase):
    router_address = '10.0.0.1'
    client_address = '10.0.0.10'
    service_name = 'WANCommonInterfaceConfig:1'
    st = 'urn:schemas-upnp-org:service:%s' % service_name
    port = 49152
    location = 'InternetGatewayDevice.xml'
    usn = 'uuid:00000000-0000-0000-0000-000000000000::%s' % st
    version = 'Linux, UPnP/1.0, DIR-890L Ver 1.20'

    expected_devices = [
        {
            'cache_control': 'max-age=1800',
            'location': 'http://%s:%i/%s' % (router_address, port, location),
            'server': version,
            'st': st,
            'usn': usn
         }
    ]

    def setUp(self):
        fake_reactor = mocks.MockReactor()
        reactor.listenMulticast = fake_reactor.listenMulticast
        self.reactor = reactor
        server_protocol = mocks.MockSSDPServiceGatewayProtocol(
            self.router_address, self.service_name, self.st, self.port, self.location, self.usn, self.version
        )
        self.server_port = self.reactor.listenMulticast(SSDP_PORT, server_protocol)

    def tearDown(self):
        self.server_port.stopListening()

    @defer.inlineCallbacks
    def test_discover(self):
        client_factory = SSDPFactory(self.reactor, self.client_address, self.router_address)
        result = yield client_factory.m_search(self.router_address)
        self.assertListEqual(self.expected_devices, result)
        client_factory.disconnect()
