import logging
import binascii
from twisted.internet import defer
from twisted.internet.protocol import DatagramProtocol
from txupnp.constants import UPNP_ORG_IGD, SSDP_DISCOVER, SSDP_IP_ADDRESS, SSDP_PORT, service_types
from txupnp.constants import SSDP_HOST
from txupnp.fault import UPnPError
from txupnp.ssdp_datagram import SSDPDatagram

log = logging.getLogger(__name__)


class SSDPProtocol(DatagramProtocol):
    def __init__(self, reactor, iface, router, ssdp_address=SSDP_IP_ADDRESS,
                 ssdp_port=SSDP_PORT, ttl=1, max_devices=None):
        self._reactor = reactor
        self._sem = defer.DeferredSemaphore(1)
        self.discover_callbacks = {}
        self.iface = iface
        self.router = router
        self.ssdp_address = ssdp_address
        self.ssdp_port = ssdp_port
        self.ttl = ttl
        self._start = None
        self.max_devices = max_devices
        self.devices = []

    def _send_m_search(self, service=UPNP_ORG_IGD):
        packet = SSDPDatagram(SSDPDatagram._M_SEARCH, host=SSDP_HOST, st=service, man=SSDP_DISCOVER, mx=1)
        log.debug("sending packet to %s:\n%s", SSDP_HOST, packet.encode())
        try:
            self.transport.write(packet.encode().encode(), (self.ssdp_address, self.ssdp_port))
        except Exception as err:
            log.exception("failed to write %s to %s:%i", binascii.hexlify(packet.encode()), self.ssdp_address, self.ssdp_port)
            raise err

    @staticmethod
    def _gather(finished_deferred, max_results):
        results = []

        def discover_cb(packet):
            if not finished_deferred.called:
                results.append(packet.as_dict())
                if len(results) >= max_results:
                    finished_deferred.callback(results)

        return discover_cb

    def m_search(self, address=None, timeout=1, max_devices=1):
        address = address or self.iface

        # return deferred for a pending call if we have one
        if address in self.discover_callbacks:
            d = self.protocol.discover_callbacks[address][1]
            if not d.called:  # the existing deferred has already fired, make a new one
                return d

        def _trap_timeout_and_return_results(err):
            if err.check(defer.TimeoutError):
                return self.devices
            raise err

        d = defer.Deferred()
        d.addTimeout(timeout, self._reactor)
        d.addErrback(_trap_timeout_and_return_results)
        found_cb = self._gather(d, max_devices)
        self.discover_callbacks[address] = found_cb, d
        for st in service_types:
            self._send_m_search(service=st)
        return d

    def startProtocol(self):
        self._start = self._reactor.seconds()
        self.transport.setTTL(self.ttl)
        self.transport.joinGroup(self.ssdp_address, interface=self.iface)
        self.m_search()

    def datagramReceived(self, datagram, address):
        if address[0] == self.iface:
            return
        try:
            packet = SSDPDatagram.decode(datagram)
            log.debug("decoded %s from %s:%i:\n%s", packet.get_friendly_name(), address[0], address[1], packet.encode())
        except UPnPError as err:
            log.error("failed to decode SSDP packet from %s:%i: %s\npacket: %s", address[0], address[1], err,
                      binascii.hexlify(datagram))
            return
        except Exception:
            log.exception("failed to decode: %s", binascii.hexlify(datagram))
            return
        if packet._packet_type == packet._OK:
            log.debug("%s:%i replied to our m-search with new xml url: %s", address[0], address[1], packet.location)
            if packet.st not in map(lambda p: p['st'], self.devices):
                self.devices.append(packet.as_dict())
                log.debug("%i device%s so far", len(self.devices), "" if len(self.devices) < 2 else "s")
                if address[0] in self.discover_callbacks:
                    self._sem.run(self.discover_callbacks[address[0]][0], packet)
        elif packet._packet_type == packet._NOTIFY:
            log.debug("%s:%i sent us a notification (type: %s), url: %s", address[0], address[1], packet.nts,
                      packet.location)


class SSDPFactory(object):
    def __init__(self, reactor, lan_address, router_address):
        self.lan_address = lan_address
        self.router_address = router_address
        self._reactor = reactor
        self.protocol = None
        self.port = None

    def disconnect(self):
        if not self.port:
            return
        self.protocol.transport.leaveGroup(SSDP_IP_ADDRESS, interface=self.lan_address)
        self.port.stopListening()
        self.port = None
        self.protocol = None

    def connect(self):
        if not self.protocol:
            self.protocol = SSDPProtocol(self._reactor, self.lan_address, self.router_address)
        if not self.port:
            self._reactor.addSystemEventTrigger("before", "shutdown", self.disconnect)
            self.port = self._reactor.listenMulticast(self.protocol.ssdp_port, self.protocol, listenMultiple=True)

    @defer.inlineCallbacks
    def m_search(self, address, timeout=1, max_devices=1):
        """
        Perform a M-SEARCH (HTTP over UDP) and gather the results

        :param address: (str) address to listen for responses from
        :param timeout: (int) timeout for the query
        :param max_devices: (int) block until timeout or at least this many devices are found
        :param service_types: (list) M-SEARCH "ST" arguments to try, if None use the defaults
        :return: (list) [ (dict) {
            'server: (str) gateway os and version
            'location': (str) upnp gateway url,
            'cache-control': (str) max age,
            'date': (int) server time,
            'usn': (str) usn
        }, ...]
        """

        self.connect()
        server_infos = yield self.protocol.m_search(address, timeout, max_devices)
        defer.returnValue(server_infos)
