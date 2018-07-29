import logging
import binascii
from twisted.internet import defer
from twisted.internet.protocol import DatagramProtocol
from txupnp.fault import UPnPError
from txupnp.constants import GATEWAY_SCHEMA, M_SEARCH_TEMPLATE, SSDP_DISCOVER, SSDP_IP_ADDRESS, SSDP_PORT

log = logging.getLogger(__name__)


def parse_http_fields(content_lines):
    return {
        (k.lower().rstrip(":".encode()).replace("-".encode(), "_".encode())).decode(): v.decode()
        for k, v in {
            l.split(": ".encode())[0]: "".encode().join(l.split(": ".encode())[1:])
            for l in content_lines
        }.items() if k
    }


def parse_ssdp_request(operation, port, protocol, content_lines):
    if operation != "NOTIFY".encode():
        log.warning("unsupported operation: %s", operation)
        raise UPnPError("unsupported operation: %s" % operation)
    if port != "*".encode():
        log.warning("unexpected port: %s", port)
        raise UPnPError("unexpected port: %s" % port)
    return parse_http_fields(content_lines)


def parse_ssdp_response(code, response, content_lines):
    try:
        if int(code) != 200:
            raise UPnPError("unexpected http response code: %i" % int(code))
    except ValueError:
        log.error(response)
        raise UPnPError("unexpected http response code: %s" % code)
    if response != "OK".encode():
        raise UPnPError("unexpected response: %s" % response)
    return parse_http_fields(content_lines)


class SSDPProtocol(DatagramProtocol):
    def __init__(self, reactor, finished_deferred, iface, router, ssdp_address=SSDP_IP_ADDRESS,
                 ssdp_port=SSDP_PORT, ttl=1, max_devices=None):
        self._reactor = reactor
        self._sem = defer.DeferredSemaphore(1)
        self.finished_deferred = finished_deferred
        self.iface = iface
        self.router = router
        self.ssdp_address = ssdp_address
        self.ssdp_port = ssdp_port
        self.ttl = ttl
        self._start = None
        self.max_devices = max_devices
        self.devices = []

    def startProtocol(self):
        return self._sem.run(self.do_start)

    def send_m_search(self):
        data = M_SEARCH_TEMPLATE.format(self.ssdp_address, self.ssdp_port, GATEWAY_SCHEMA, SSDP_DISCOVER, self.ttl)
        try:
            log.info("sending m-search (%i bytes) to %s:%i", len(data), self.ssdp_address, self.ssdp_port)
            self.transport.write(data.encode(), (self.ssdp_address, self.ssdp_port))
        except Exception as err:
            log.exception("failed to write %s to %s:%i", binascii.hexlify(data), self.ssdp_address, self.ssdp_port)
            raise err

    def parse_ssdp_datagram(self, datagram):
        lines = datagram.split("\r\n".encode())
        header_pieces = lines[0].split(" ".encode())
        protocols = {
            "HTTP/1.1".encode()
        }
        operations = {
            "M-SEARCH".encode(),
            "NOTIFY".encode()
        }
        if header_pieces[0] in operations:
            if header_pieces[2] not in protocols:
                raise UPnPError("unknown protocol: %s" % header_pieces[2])
            return parse_ssdp_request(header_pieces[0], header_pieces[1], header_pieces[2], lines[1:])
        if header_pieces[0] in protocols:
            parsed = parse_ssdp_response(header_pieces[1], header_pieces[2], lines[1:])
            log.info("received reply (%i bytes) to SSDP request (%f) (%s) %s", len(datagram),
                     self._reactor.seconds() - self._start, parsed['location'], parsed['server'])
            return parsed
        raise UPnPError("don't know how to decode datagram: %s" % binascii.hexlify(datagram))

    def do_start(self):
        self._start = self._reactor.seconds()
        self.finished_deferred.addTimeout(self.ttl, self._reactor)
        self.transport.setTTL(self.ttl)
        self.transport.joinGroup(self.ssdp_address, interface=self.iface)
        self.send_m_search()

    def leave_group(self):
        self.transport.leaveGroup(self.ssdp_address, interface=self.iface)

    def datagramReceived(self, datagram, addr):
        self._sem.run(self.handle_datagram, datagram, addr)

    def handle_datagram(self, datagram, address):
        if address[0] == self.router:
            try:
                parsed = self.parse_ssdp_datagram(datagram)
                self.devices.append(parsed)
                log.info("found %i/%s so far", len(self.devices), self.max_devices)
                if not self.finished_deferred.called:
                    if not self.max_devices or (self.max_devices and len(self.devices) >= self.max_devices):
                        self._sem.run(self.finished_deferred.callback, self.devices)
            except UPnPError as err:
                log.error("error decoding SSDP response from %s:%s (error: %s)\n%s", address[0], address[1], str(err), binascii.hexlify(datagram))
                raise err
        elif address[0] != self.iface:
            log.info("received %i bytes from %s:%i\n%s", len(datagram), address[0], address[1], binascii.hexlify(datagram))
        else:
            pass  # loopback


class SSDPFactory(object):
    def __init__(self, lan_address, reactor):
        self.lan_address = lan_address
        self._reactor = reactor
        self.protocol = None
        self.port = None
        self.finished_deferred = defer.Deferred()

    def stop(self):
        try:
            self.protocol.leave_group()
            self.port.stopListening()
        except:
            pass

    def connect(self, address, ttl, max_devices=1):
        self.protocol = SSDPProtocol(self._reactor, self.finished_deferred, self.lan_address, address, ttl=ttl,
                                     max_devices=max_devices)
        self.port = self._reactor.listenMulticast(self.protocol.ssdp_port, self.protocol, listenMultiple=True)
        self._reactor.addSystemEventTrigger("before", "shutdown", self.stop)
        return self.finished_deferred

    @defer.inlineCallbacks
    def m_search(self, address, ttl=30, max_devices=2):
        """
        Perform a HTTP over UDP M-SEARCH query

        returns (list) [{
            'server: <gateway os and version string>
            'location': <upnp gateway url>,
            'cache-control': <max age>,
            'date': <server time>,
            'usn': <usn>
        }, ...]
        """
        d = self.connect(address, ttl, max_devices=max_devices)
        try:
            server_infos = yield d
        except defer.TimeoutError:
            server_infos = self.protocol.devices
        log.info("found %i devices", len(server_infos))
        self.stop()
        defer.returnValue(server_infos)
