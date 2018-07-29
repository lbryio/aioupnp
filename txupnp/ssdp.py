import logging
import binascii
import re
from twisted.internet import defer
from twisted.internet.protocol import DatagramProtocol
from txupnp.fault import UPnPError
from txupnp.constants import GATEWAY_SCHEMA, SSDP_DISCOVER, SSDP_IP_ADDRESS, SSDP_PORT, SSDP_ALL

log = logging.getLogger(__name__)


SSDP_HOST = "%s:%i" % (SSDP_IP_ADDRESS, SSDP_PORT)
SSDP_BYEBYE = "ssdp:byebye"
SSDP_UPDATE = "ssdp:update"
SSDP_ROOT_DEVICE = "upnp:rootdevice"
line_separator = "\r\n"


class SSDPDatagram(object):
    _M_SEARCH = "M-SEARCH"
    _NOTIFY = "NOTIFY"
    _OK = "OK"

    _start_lines = {
        _M_SEARCH: "M-SEARCH * HTTP/1.1",
        _NOTIFY: "NOTIFY * HTTP/1.1",
        _OK: "HTTP/1.1 200 OK"
    }

    _friendly_names = {
        _M_SEARCH: "m-search",
        _NOTIFY: "notify",
        _OK: "m-search response"
    }

    _vendor_field_pattern = re.compile("^([\w|\d]*)\.([\w|\d]*\.com):([ \"|\w|\d\:]*)$")

    _patterns = {
        'host': (re.compile("^(?i)(host):(.*)$"), str),
        'st': (re.compile("^(?i)(st):(.*)$"), str),
        'man': (re.compile("^(?i)(man):|(\"(.*)\")$"), str),
        'mx': (re.compile("^(?i)(mx):(.*)$"), int),
        'nt': (re.compile("^(?i)(nt):(.*)$"), str),
        'nts': (re.compile("^(?i)(nts):(.*)$"), str),
        'usn': (re.compile("^(?i)(usn):(.*)$"), str),
        'location': (re.compile("^(?i)(location):(.*)$"), str),
        'cache_control': (re.compile("^(?i)(cache-control):(.*)$"), str),
        'server': (re.compile("^(?i)(server):(.*)$"), str),
    }

    _required_fields = {
        _M_SEARCH: [
            'host',
            'st',
            'man',
            'mx',
        ],
        _OK: [
            'cache_control',
            # 'date',
            # 'ext',
            'location',
            'server',
            'st',
            'usn'
        ]
    }

    _marshallers = {
        'mx': str,
        'man': lambda x: ("\"%s\"" % x)
    }

    def __init__(self, packet_type, host=None, st=None, man=None, mx=None, nt=None, nts=None, usn=None, location=None,
                 cache_control=None, server=None, date=None, ext=None, **kwargs):
        if packet_type not in [self._M_SEARCH, self._NOTIFY, self._OK]:
            raise UPnPError("unknown packet type: {}".format(packet_type))
        self._packet_type = packet_type
        self.host = host
        self.st = st
        self.man = man
        self.mx = mx
        self.nt = nt
        self.nts = nts
        self.usn = usn
        self.location = location
        self.cache_control = cache_control
        self.server = server
        self.date = date
        self.ext = ext
        for k, v in kwargs.items():
            if not k.startswith("_") and hasattr(self, k.lower()) and getattr(self, k.lower()) is None:
                setattr(self, k.lower(), v)

    def __getitem__(self, item):
        for i in self._required_fields[self._packet_type]:
            if i.lower() == item.lower():
                return getattr(self, i)
        raise KeyError(item)

    def get_friendly_name(self):
        return self._friendly_names[self._packet_type]

    def encode(self, trailing_newlines=2):
        lines = [self._start_lines[self._packet_type]]
        for attr_name in self._required_fields[self._packet_type]:
            attr = getattr(self, attr_name)
            if attr is None:
                raise UPnPError("required field for {} is missing: {}".format(self._packet_type, attr_name))
            if attr_name in self._marshallers:
                value = self._marshallers[attr_name](attr)
            else:
                value = attr
            lines.append("{}: {}".format(attr_name.upper(), value))
        serialized = line_separator.join(lines)
        for _ in range(trailing_newlines):
            serialized += line_separator
        return serialized

    def as_dict(self):
        return self._lines_to_content_dict(self.encode().split(line_separator))

    @classmethod
    def decode(cls, datagram):
        packet = cls._from_string(datagram.decode())
        for attr_name in packet._required_fields[packet._packet_type]:
            attr = getattr(packet, attr_name)
            if attr is None:
                raise UPnPError(
                    "required field for {} is missing from m-search response: {}".format(packet._packet_type, attr_name)
                )
        return packet

    @classmethod
    def _lines_to_content_dict(cls, lines):
        result = {}
        for line in lines:
            if not line:
                continue
            matched = False
            for name, (pattern, field_type) in cls._patterns.items():
                if name not in result and pattern.findall(line):
                    match = pattern.findall(line)[-1][-1]
                    result[name] = field_type(match.lstrip(" ").rstrip(" "))
                    matched = True
                    break
            if not matched:
                if cls._vendor_field_pattern.findall(line):
                    match = cls._vendor_field_pattern.findall(line)[-1]
                    vendor_key = match[0].lstrip(" ").rstrip(" ")
                    # vendor_domain = match[1].lstrip(" ").rstrip(" ")
                    value = match[2].lstrip(" ").rstrip(" ")
                    if vendor_key not in result:
                        result[vendor_key] = value
        return result

    @classmethod
    def _from_string(cls, datagram):
        lines = [l for l in datagram.split(line_separator) if l]
        if lines[0] == cls._start_lines[cls._M_SEARCH]:
            return cls._from_request(lines[1:])
        if lines[0] == cls._start_lines[cls._NOTIFY]:
            return cls._from_notify(lines[1:])
        if lines[0] == cls._start_lines[cls._OK]:
            return cls._from_response(lines[1:])

    @classmethod
    def _from_response(cls, lines):
        return cls(cls._OK, **cls._lines_to_content_dict(lines))

    @classmethod
    def _from_notify(cls, lines):
        return cls(cls._NOTIFY, **cls._lines_to_content_dict(lines))

    @classmethod
    def _from_request(cls, lines):
        return cls(cls._M_SEARCH, **cls._lines_to_content_dict(lines))


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

    def startProtocol(self):
        self._start = self._reactor.seconds()
        self.transport.setTTL(self.ttl)
        self.transport.joinGroup(self.ssdp_address, interface=self.iface)

        for st in [SSDP_ALL, SSDP_ROOT_DEVICE, GATEWAY_SCHEMA, GATEWAY_SCHEMA.lower()]:
            self.send_m_search(service=st)

    def send_m_search(self, service=GATEWAY_SCHEMA):
        packet = SSDPDatagram(SSDPDatagram._M_SEARCH, host=SSDP_HOST, st=service, man=SSDP_DISCOVER, mx=1)
        log.debug("writing packet:\n%s", packet.encode())
        log.info("sending m-search (%i bytes) to %s:%i", len(packet.encode()), self.ssdp_address, self.ssdp_port)
        try:
            self.transport.write(packet.encode().encode(), (self.ssdp_address, self.ssdp_port))
        except Exception as err:
            log.exception("failed to write %s to %s:%i", binascii.hexlify(packet.encode()), self.ssdp_address, self.ssdp_port)
            raise err

    def leave_group(self):
        self.transport.leaveGroup(self.ssdp_address, interface=self.iface)

    def datagramReceived(self, datagram, address):
        if address[0] == self.iface:
            return
        try:
            packet = SSDPDatagram.decode(datagram)
            log.debug("decoded %s from %s:%i:\n%s", packet.get_friendly_name(), address[0], address[1], packet.encode())
        except Exception:
            log.exception("failed to decode: %s", binascii.hexlify(datagram))
            return
        if packet._packet_type == packet._OK:
            log.info("%s:%i replied to our m-search with new xml url: %s", address[0], address[1], packet.location)
        else:
            log.info("%s:%i notified us of a service type: %s", address[0], address[1], packet.st)
        if packet.st not in map(lambda p: p['st'], self.devices):
            self.devices.append(packet.as_dict())
            log.info("%i device%s so far", len(self.devices), "" if len(self.devices) < 2 else "s")
            if address[0] in self.discover_callbacks:
                self._sem.run(self.discover_callbacks[address[0]][0], packet)


def gather(finished_deferred, max_results):
    results = []

    def discover_cb(packet):
        if not finished_deferred.called:
            results.append(packet.as_dict())
            if len(results) >= max_results:
                finished_deferred.callback(results)

    return discover_cb


class SSDPFactory(object):
    def __init__(self, reactor, lan_address, router_address):
        self.lan_address = lan_address
        self.router_address = router_address
        self._reactor = reactor
        self.protocol = SSDPProtocol(self._reactor, self.lan_address, self.router_address)
        self.port = None

    def disconnect(self):
        if self.protocol:
            self.protocol.leave_group()
            self.protocol = None
        if not self.port:
            return
        self.port.stopListening()
        self.port = None

    def connect(self):
        self._reactor.addSystemEventTrigger("before", "shutdown", self.disconnect)
        self.port = self._reactor.listenMulticast(self.protocol.ssdp_port, self.protocol, listenMultiple=True)

    @defer.inlineCallbacks
    def m_search(self, address, timeout=30, max_devices=1):
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

        self.connect()

        if address in self.protocol.discover_callbacks:
            d = self.protocol.discover_callbacks[address][1]
        else:
            d = defer.Deferred()
            d.addTimeout(timeout, self._reactor)
            found_cb = gather(d, max_devices)
            self.protocol.discover_callbacks[address] = found_cb, d
            for st in [SSDP_ALL, SSDP_ROOT_DEVICE, GATEWAY_SCHEMA, GATEWAY_SCHEMA.lower()]:
                self.protocol.send_m_search(service=st)
        try:
            server_infos = yield d
        except defer.TimeoutError:
            server_infos = self.protocol.devices
        defer.returnValue(server_infos)
