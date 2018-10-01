import os
import json
import logging
from twisted.internet import task, defer
from twisted.internet.error import ConnectionDone
from twisted.internet.protocol import DatagramProtocol
from twisted.python.failure import Failure
from twisted.test.proto_helpers import _FakePort
from txupnp.ssdp_datagram import SSDPDatagram

log = logging.getLogger()


class MockResponse:
    def __init__(self, content):
        self._content = content
        self.headers = {}

    def content(self):
        return defer.succeed(self._content)


class MockDevice:
    def __init__(self, manufacturer, model):
        self.manufacturer = manufacturer
        self.model = model
        device_path = os.path.join(
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "devices"), "{} {}".format(manufacturer, model)
        )
        assert os.path.isfile(device_path)
        with open(device_path, "r") as f:
            self.device_dict = json.loads(f.read())

    def __repr__(self):
        return "MockDevice(manufacturer={}, model={})".format(self.manufacturer, self.model)


def get_mock_devices():
    return [
        MockDevice(path.split(" ")[0], path.split(" ")[1])
        for path in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "devices"))
        if ".py" not in path and "pycache" not in path
    ]


def get_device_test_case(manufacturer: str, model: str) -> MockDevice:
    r = [
        MockDevice(path.split(" ")[0], path.split(" ")[1])
        for path in os.listdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "devices"))
        if ".py" not in path and "pycache" not in path and path.split(" ") == [manufacturer, model]
    ]
    return r[0]


class MockMulticastTransport:
    def __init__(self, address, port, max_packet_size, network, protocol):
        self.address = address
        self.port = port
        self.max_packet_size = max_packet_size
        self._network = network
        self._protocol = protocol

    def write(self, data, address):
        if address[0] in self._network.group:
            destinations = self._network.group[address[0]]
        else:
            destinations = address[0]
        for address, dest in self._network.peers.items():
            if address[0] in destinations and dest.address != self.address:
                dest._protocol.datagramReceived(data, (self.address, self.port))

    def setTTL(self, ttl):
        pass

    def joinGroup(self, address, interface=None):
        group = self._network.group.get(address, [])
        group.append(interface)
        self._network.group[address] = group

    def leaveGroup(self, address, interface=None):
        group = self._network.group.get(address, [])
        if interface in group:
            group.remove(interface)
            self._network.group[address] = group


class MockTCPTransport(_FakePort):
    def __init__(self, address, port, callback, mock_requests):
        super().__init__((address, port))
        self._callback = callback
        self._mock_requests = mock_requests

    def write(self, data):
        if data.startswith(b"POST"):
            for url, packets in self._mock_requests['POST'].items():
                for request_response in packets:
                    if data.decode() == request_response['request']:
                        self._callback(request_response['response'].encode())
                        return
        elif data.startswith(b"GET"):
            for url, packets in self._mock_requests['GET'].items():
                if data.decode() == packets['request']:
                    self._callback(packets['response'].encode())
                    return


class MockMulticastPort(_FakePort):
    def __init__(self, protocol, remover, address, transport):
        super().__init__((address, 1900))
        self.protocol = protocol
        self._remover = remover
        self.transport = transport

    def startListening(self, reason=None):
        self.protocol.transport = self.transport
        return self.protocol.startProtocol()

    def stopListening(self, reason=None):
        result = self.protocol.stopProtocol()
        self._remover()
        return result


class MockNetwork:
    def __init__(self):
        self.peers = {}
        self.group = {}

    def add_peer(self, port, protocol, interface, maxPacketSize):
        transport = MockMulticastTransport(interface, port, maxPacketSize, self, protocol)
        self.peers[(interface, port)] = transport

        def remove_peer():
            if self.peers.get((interface, port)):
                del self.peers[(interface, port)]
        return transport, remove_peer


class MockReactor(task.Clock):
    def __init__(self, client_addr, mock_scpd_requests):
        super().__init__()
        self.client_addr = client_addr
        self._mock_scpd_requests = mock_scpd_requests
        self.network = MockNetwork()

    def listenMulticast(self, port, protocol, interface=None, maxPacketSize=8192, listenMultiple=True):
        interface = interface or self.client_addr
        transport, remover = self.network.add_peer(port, protocol, interface, maxPacketSize)
        port = MockMulticastPort(protocol, remover, interface, transport)
        port.startListening()
        return port

    def connectTCP(self, host, port, factory, timeout=30, bindAddress=None):
        protocol = factory.buildProtocol(host)

        def _write_and_close(data):
            protocol.dataReceived(data)
            protocol.connectionLost(Failure(ConnectionDone()))

        protocol.transport = MockTCPTransport(host, port, _write_and_close, self._mock_scpd_requests)
        protocol.connectionMade()


class MockSSDPServiceGatewayProtocol(DatagramProtocol):
    def __init__(self, client_addr: int, iface: str, packets_rx: list, packets_tx: list):
        self.client_addr = client_addr
        self.iface = iface
        self.packets_tx = [SSDPDatagram.decode(packet.encode()) for packet in packets_tx] # sent by client
        self.packets_rx = [((addr, port), SSDPDatagram.decode(packet.encode())) for (addr, port), packet in packets_rx] # rx by client

    def datagramReceived(self, datagram, address):
        packet = SSDPDatagram.decode(datagram)
        if packet.st in map(lambda p: p[1].st, self.packets_rx):  # this contains one of the service types the server replied to
            reply = list(filter(lambda p: p[1].st == packet.st, self.packets_rx))[0][1]
            self.transport.write(reply.encode().encode(), (self.client_addr, 1900))
        else:
            pass
