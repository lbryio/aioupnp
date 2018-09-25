import logging
import binascii
from twisted.internet import task
from txupnp.constants import SSDP_IP_ADDRESS
from txupnp.fault import UPnPError
from txupnp.ssdp_datagram import SSDPDatagram
from twisted.internet.protocol import DatagramProtocol

log = logging.getLogger()


class MockMulticastTransport:
    def __init__(self, address, port, max_packet_size, network):
        self.address = address
        self.port = port
        self.max_packet_size = max_packet_size
        self._network = network

    def write(self, data, address):
        if address in self._network.peers:
            for dest in self._network.peers[address]:
                dest.datagramReceived(data, (self.address, self.port))
        else:  # the node is sending to an address that doesnt currently exist, act like it never arrived
            pass

    def setTTL(self, ttl):
        pass

    def joinGroup(self, address, interface=None):
        pass

    def leaveGroup(self, address, interface=None):
        pass


class MockMulticastPort(object):
    def __init__(self, protocol, remover):
        self.protocol = protocol
        self._remover = remover

    def startListening(self, reason=None):
        return self.protocol.startProtocol()

    def stopListening(self, reason=None):
        result = self.protocol.stopProtocol()
        self._remover()
        return result


class MockNetwork:
    def __init__(self):
        self.peers = {}  # (interface, port): (protocol, max_packet_size)

    def add_peer(self, port, protocol, interface, maxPacketSize):
        protocol.transport = MockMulticastTransport(interface, port, maxPacketSize, self)
        peers = self.peers.get((interface, port), [])
        peers.append(protocol)
        self.peers[(interface, port)] = peers

        def remove_peer():
            if self.peers.get((interface, port)):
                self.peers[(interface, port)].remove(protocol)
            if not self.peers.get((interface, port)):
                del self.peers[(interface, port)]
            del protocol.transport
        return remove_peer


class MockReactor(task.Clock):
    def __init__(self):
        super().__init__()
        self.network = MockNetwork()

    def listenMulticast(self, port, protocol, interface=SSDP_IP_ADDRESS, maxPacketSize=8192, listenMultiple=True):
        remover = self.network.add_peer(port, protocol, interface, maxPacketSize)
        port = MockMulticastPort(protocol, remover)
        port.startListening()
        return port


class MockSSDPServiceGatewayProtocol(DatagramProtocol):
    def __init__(self, iface, service_name, st, port, location, usn, version):
        self.iface = iface
        self.service_name = service_name
        self.gateway_st = st
        self.gateway_location = location
        self.gateway_usn = usn
        self.gateway_version = version
        self.gateway_port = port

    def datagramReceived(self, datagram, address):
        try:
            packet = SSDPDatagram.decode(datagram)
        except UPnPError as err:
            log.error("failed to decode SSDP packet from %s:%i: %s\npacket: %s", address[0], address[1], err,
                      binascii.hexlify(datagram))
            return

        if packet._packet_type == packet._M_SEARCH:
            if packet.man == "ssdp:discover" and packet.st == self.gateway_st:
                location = 'http://{}:{}/{}'.format(self.iface, self.gateway_port, self.gateway_location)
                response = SSDPDatagram(SSDPDatagram._OK, st=self.gateway_st, cache_control='max-age=1800',
                                        location=location, server=self.gateway_version, usn=self.gateway_usn)
                self.transport.write(response.encode().encode(), address)

