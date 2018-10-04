from twisted.internet import reactor, defer
from twisted.trial import unittest
from txupnp.constants import SSDP_PORT, SSDP_IP_ADDRESS
from txupnp.upnp import UPnP
from txupnp.mocks import MockReactor, MockSSDPServiceGatewayProtocol, get_device_test_case


class TestDevice(unittest.TestCase):
    manufacturer, model = "Cisco", "CGA4131COM"

    device = get_device_test_case(manufacturer, model)
    router_address = device.device_dict['router_address']
    client_address = device.device_dict['client_address']
    expected_devices = device.device_dict['expected_devices']
    packets_rx = device.device_dict['ssdp']['received']
    packets_tx = device.device_dict['ssdp']['sent']
    expected_available_commands = device.device_dict['commands']['available']
    scdp_packets = device.device_dict['scpd']

    def setUp(self):
        fake_reactor = MockReactor(self.client_address, self.scdp_packets)
        reactor.listenMulticast = fake_reactor.listenMulticast
        self.reactor = reactor
        server_protocol = MockSSDPServiceGatewayProtocol(
            self.client_address, self.router_address, self.packets_rx, self.packets_tx
        )
        self.server_port = self.reactor.listenMulticast(SSDP_PORT, server_protocol, interface=self.router_address)
        self.server_port.transport.joinGroup(SSDP_IP_ADDRESS, interface=self.router_address)

        self.upnp = UPnP(
            self.reactor, debug_ssdp=True, router_ip=self.router_address,
            lan_ip=self.client_address, iface_name='mock'
        )

    def tearDown(self):
        self.upnp.sspd_factory.disconnect()
        self.server_port.stopListening()


class TestSSDP(TestDevice):
    @defer.inlineCallbacks
    def test_discover_device(self):
        result = yield self.upnp.m_search(self.router_address, timeout=1)
        self.assertEqual(len(self.expected_devices), len(result))
        self.assertEqual(len(result), 1)
        self.assertDictEqual(self.expected_devices[0], result[0])


class TestSCPD(TestDevice):
    @defer.inlineCallbacks
    def setUp(self):
        fake_reactor = MockReactor(self.client_address, self.scdp_packets)
        reactor.listenMulticast = fake_reactor.listenMulticast
        reactor.connectTCP = fake_reactor.connectTCP
        self.reactor = reactor
        server_protocol = MockSSDPServiceGatewayProtocol(
            self.client_address, self.router_address, self.packets_rx, self.packets_tx
        )
        self.server_port = self.reactor.listenMulticast(SSDP_PORT, server_protocol, interface=self.router_address)
        self.server_port.transport.joinGroup(SSDP_IP_ADDRESS, interface=self.router_address)

        self.upnp = UPnP(
            self.reactor, debug_ssdp=True, router_ip=self.router_address,
            lan_ip=self.client_address, iface_name='mock'
        )
        yield self.upnp.discover()

    def test_parse_available_commands(self):
        self.assertDictEqual(self.expected_available_commands, self.upnp.gateway.debug_commands()['available'])

    def test_parse_gateway(self):
        self.assertDictEqual(self.device.device_dict['gateway_dict'], self.upnp.gateway.as_dict())

    @defer.inlineCallbacks
    def test_commands(self):
        method, args, expected = self.device.device_dict['soap'][0]
        command1 = getattr(self.upnp, method)
        result = yield command1(*tuple(args))
        self.assertEqual(result, expected)

        method, args, expected = self.device.device_dict['soap'][1]
        command2 = getattr(self.upnp, method)
        result = yield command2(*tuple(args))
        result = [[i for i in r] for r in result]
        self.assertListEqual(result, expected)

        method, args, expected = self.device.device_dict['soap'][2]
        command3 = getattr(self.upnp, method)
        result = yield command3(*tuple(args))
        self.assertEqual(result, expected)

        method, args, expected = self.device.device_dict['soap'][3]
        command4 = getattr(self.upnp, method)
        result = yield command4(*tuple(args))
        result = [r for r in result]
        self.assertEqual(result, expected)

        method, args, expected = self.device.device_dict['soap'][4]
        command5 = getattr(self.upnp, method)
        result = yield command5(*tuple(args))
        self.assertEqual(result, expected)


class TestDDWRTSSDP(TestSSDP):
    manufacturer, model = "DD-WRT", "router"


class TestDDWRTSCPD(TestSCPD):
    manufacturer, model = "DD-WRT", "router"


class TestMiniUPnPMiniUPnPd(TestSSDP):
    manufacturer, model = "MiniUPnP", "MiniUPnPd"


class TestMiniUPnPMiniUPnPdSCPD(TestSCPD):
    manufacturer, model = "MiniUPnP", "MiniUPnPd"
