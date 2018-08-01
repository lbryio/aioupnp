import re
import logging
from txupnp.fault import UPnPError
from txupnp.constants import line_separator

log = logging.getLogger(__name__)


_ssdp_datagram_patterns = {
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

_vendor_pattern = re.compile("^([\w|\d]*)\.([\w|\d]*\.com):([ \"|\w|\d\:]*)$")


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

    _vendor_field_pattern = _vendor_pattern

    _patterns = _ssdp_datagram_patterns

    _required_fields = {
        _M_SEARCH: [
            'host',
            'st',
            'man',
            'mx',
        ],
        _NOTIFY: [
            'host',
            'location',
            'nt',
            'nts',
            'server',
            'usn',
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
