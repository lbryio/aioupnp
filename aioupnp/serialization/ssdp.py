import re
import logging
import binascii
import json
from collections import OrderedDict
from typing import List
from aioupnp.fault import UPnPError
from aioupnp.constants import line_separator

log = logging.getLogger(__name__)

_template = "^(?i)(%s):[ ]*(.*)$"


ssdp_datagram_patterns = {
    'host': (re.compile("^(?i)(host):(.*)$"), str),
    'st': (re.compile(_template % 'st'), str),
    'man': (re.compile(_template % 'man'), str),
    'mx': (re.compile(_template % 'mx'), int),
    'nt': (re.compile(_template % 'nt'), str),
    'nts': (re.compile(_template % 'nts'), str),
    'usn': (re.compile(_template % 'usn'), str),
    'location': (re.compile(_template % 'location'), str),
    'cache_control': (re.compile(_template % 'cache[-|_]control'), str),
    'server': (re.compile(_template % 'server'), str),
}

vendor_pattern = re.compile("^([\w|\d]*)\.([\w|\d]*\.com):([ \"|\w|\d\:]*)$")


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

    _vendor_field_pattern = vendor_pattern

    _patterns = ssdp_datagram_patterns

    _required_fields = {
        _M_SEARCH: [
            'host',
            'man',
            'mx',
            'st',
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

    def __init__(self, packet_type, kwargs: OrderedDict = None) -> None:
        if packet_type not in [self._M_SEARCH, self._NOTIFY, self._OK]:
            raise UPnPError("unknown packet type: {}".format(packet_type))
        self._packet_type = packet_type
        kwargs = kwargs or OrderedDict()
        self._field_order: list = [
            k.lower().replace("-", "_") for k in kwargs.keys()
        ]
        self.host = None
        self.man = None
        self.mx = None
        self.st = None
        self.nt = None
        self.nts = None
        self.usn = None
        self.location = None
        self.cache_control = None
        self.server = None
        self.date = None
        self.ext = None
        for k, v in kwargs.items():
            normalized = k.lower().replace("-", "_")
            if not normalized.startswith("_") and hasattr(self, normalized) and getattr(self,normalized) is None:
                setattr(self, normalized, v)
        self._case_mappings: dict = {k.lower(): k for k in kwargs.keys()}
        for k in self._required_fields[self._packet_type]:
            if getattr(self, k) is None:
                raise UPnPError("missing required field %s" % k)

    def get_cli_igd_kwargs(self) -> str:
        fields = []
        for field in self._field_order:
            v = getattr(self, field)
            fields.append("--%s=%s" % (self._case_mappings.get(field, field), v))
        return " ".join(fields)

    def __repr__(self) -> str:
        return self.as_json()

    def __getitem__(self, item):
        for i in self._required_fields[self._packet_type]:
            if i.lower() == item.lower():
                return getattr(self, i)
        raise KeyError(item)

    def get_friendly_name(self) -> str:
        return self._friendly_names[self._packet_type]

    def encode(self, trailing_newlines: int = 2) -> str:
        lines = [self._start_lines[self._packet_type]]
        for attr_name in self._field_order:
            if attr_name not in self._required_fields[self._packet_type]:
                continue
            attr = getattr(self, attr_name)
            if attr is None:
                raise UPnPError("required field for {} is missing: {}".format(self._packet_type, attr_name))
            if attr_name == 'mx':
                value = str(attr)
            else:
                value = attr
            lines.append("{}: {}".format(self._case_mappings.get(attr_name.lower(), attr_name.upper()), value))
        serialized = line_separator.join(lines)
        for _ in range(trailing_newlines):
            serialized += line_separator
        return serialized

    def as_dict(self) -> OrderedDict:
        return self._lines_to_content_dict(self.encode().split(line_separator))

    def as_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2)

    @classmethod
    def decode(cls, datagram: bytes):
        packet = cls._from_string(datagram.decode())
        if packet is None:
            raise UPnPError(
                "failed to decode datagram: {}".format(binascii.hexlify(datagram))
            )
        for attr_name in packet._required_fields[packet._packet_type]:
            attr = getattr(packet, attr_name)
            if attr is None:
                raise UPnPError(
                    "required field for {} is missing from m-search response: {}".format(packet._packet_type, attr_name)
                )
        return packet

    @classmethod
    def _lines_to_content_dict(cls, lines: list) -> OrderedDict:
        result: OrderedDict = OrderedDict()
        for line in lines:
            if not line:
                continue
            matched = False
            for name, (pattern, field_type) in cls._patterns.items():
                if name not in result and pattern.findall(line):
                    match = pattern.findall(line)[-1][-1]
                    result[line[:len(name)]] = field_type(match.lstrip(" ").rstrip(" "))
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
    def _from_string(cls, datagram: str):
        lines = [l for l in datagram.split(line_separator) if l]
        if lines[0] == cls._start_lines[cls._M_SEARCH]:
            return cls._from_request(lines[1:])
        if lines[0] in [cls._start_lines[cls._NOTIFY], cls._start_lines[cls._NOTIFY] + " "]:
            return cls._from_notify(lines[1:])
        if lines[0] == cls._start_lines[cls._OK]:
            return cls._from_response(lines[1:])

    @classmethod
    def _from_response(cls, lines: List):
        return cls(cls._OK, cls._lines_to_content_dict(lines))

    @classmethod
    def _from_notify(cls, lines: List):
        return cls(cls._NOTIFY, cls._lines_to_content_dict(lines))

    @classmethod
    def _from_request(cls, lines: List):
        return cls(cls._M_SEARCH, cls._lines_to_content_dict(lines))
