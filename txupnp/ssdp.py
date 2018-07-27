import logging
from twisted.internet import defer
from twisted.internet.protocol import DatagramProtocol
from txupnp.util import get_lan_info
from txupnp.constants import GATEWAY_SCHEMA, M_SEARCH_TEMPLATE, SSDP_DISCOVER, SSDP_IP_ADDRESS, SSDP_PORT

log = logging.getLogger(__name__)


class SSDPProtocol(DatagramProtocol):
    def __init__(self, reactor, finished_deferred, iface, router, ssdp_address=SSDP_IP_ADDRESS,
                 ssdp_port=SSDP_PORT, ttl=1):
        self._reactor = reactor
        self._sem = defer.DeferredSemaphore(1)
        self.finished_deferred = finished_deferred
        self.iface = iface
        self.router = router
        self.ssdp_address = ssdp_address
        self.ssdp_port = ssdp_port
        self.ttl = ttl
        self._start = None

    @staticmethod
    def parse_ssdp_response(datagram):
        lines = datagram.split("\r\n".encode())
        if not lines:
            return
        protocol, code, response = lines[0].split(" ".encode())
        if int(code) != 200:
            raise Exception("unexpected http response code")
        if response != "OK".encode():
            raise Exception("unexpected response")
        fields = {
            k.lower(): v
            for k, v in {
                l.split(": ".encode())[0]: "".encode().join(l.split(": ".encode())[1:])
                for l in lines[1:]
            }.items() if k
        }
        return fields

    def startProtocol(self):
        return self._sem.run(self.do_start)

    def do_start(self):
        self._start = self._reactor.seconds()
        self.finished_deferred.addTimeout(self.ttl, self._reactor)
        self.transport.setTTL(self.ttl)
        self.transport.joinGroup(self.ssdp_address, interface=self.iface)
        data = M_SEARCH_TEMPLATE.format(self.ssdp_address, self.ssdp_port, GATEWAY_SCHEMA, SSDP_DISCOVER, self.ttl)
        self.transport.write(data.encode(), (self.ssdp_address, self.ssdp_port))

    def do_stop(self, gateway_xml_location):
        self.transport.leaveGroup(self.ssdp_address, interface=self.iface)
        if not self.finished_deferred.called:
            self.finished_deferred.callback(gateway_xml_location)

    def datagramReceived(self, datagram, addr):
        self._sem.run(self.handle_datagram, datagram, addr)

    def handle_datagram(self, datagram, address):
        if address[0] == self.router:
            try:
                server_info = self.parse_ssdp_response(datagram)
            except:
                log.exception("error parsing response: %s", datagram.encode('hex'))
                raise
            if server_info:
                log.info("received reply (%i bytes) to SSDP request (%fs)", len(datagram),
                         self._reactor.seconds() - self._start)
                self._sem.run(self.do_stop, server_info)
        elif address[0] != get_lan_info()[2]:
            log.info("received %i bytes from %s:%i", len(datagram), address[0], address[1])


class SSDPFactory(object):
    def __init__(self, lan_address, reactor):
        self.lan_address = lan_address
        self._reactor = reactor

    @defer.inlineCallbacks
    def m_search(self, address):
        finished_d = defer.Deferred()
        ssdp_protocol = SSDPProtocol(self._reactor, finished_d, self.lan_address, address, ttl=30)
        port = ssdp_protocol._reactor.listenMulticast(ssdp_protocol.ssdp_port, ssdp_protocol, listenMultiple=True)
        server_info = yield finished_d
        port.stopListening()
        defer.returnValue(server_info)
