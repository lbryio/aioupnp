import re
import logging
import binascii
import json
from collections import OrderedDict
from typing import List, Optional, Dict, Union, Callable
from aioupnp.fault import UPnPError
from aioupnp.constants import line_separator

log = logging.getLogger(__name__)

_template = "(?i)^(%s):[ ]*(.*)$"


def compile_find(pattern: str) -> Callable[[str], Optional[str]]:
    p = re.compile(pattern)

    def find(line: str) -> Optional[str]:
        result: List[List[str]] = []
        for outer in p.findall(line):
            result.append([])
            for inner in outer:
                result[-1].append(inner)
        if result:
            return result[-1][-1].lstrip(" ").rstrip(" ")
        return None

    return find


ssdp_datagram_patterns: Dict[str, Callable[[str], Optional[str]]] = {
    'host': compile_find("(?i)^(host):(.*)$"),
    'st': compile_find(_template % 'st'),
    'man': compile_find(_template % 'man'),
    'mx': compile_find(_template % 'mx'),
    'nt': compile_find(_template % 'nt'),
    'nts': compile_find(_template % 'nts'),
    'usn': compile_find(_template % 'usn'),
    'location': compile_find(_template % 'location'),
    'cache_control': compile_find(_template % 'cache[-|_]control'),
    'server': compile_find(_template % 'server'),
}


class SSDPDatagram:
    _M_SEARCH = "M-SEARCH"
    _NOTIFY = "NOTIFY"
    _OK = "OK"

    _start_lines: Dict[str, str] = {
        _M_SEARCH: "M-SEARCH * HTTP/1.1",
        _NOTIFY: "NOTIFY * HTTP/1.1",
        _OK: "HTTP/1.1 200 OK"
    }

    _friendly_names: Dict[str, str] = {
        _M_SEARCH: "m-search",
        _NOTIFY: "notify",
        _OK: "m-search response"
    }

    _required_fields: Dict[str, List[str]] = {
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

    def __init__(self, packet_type: str, kwargs: Optional[Dict[str, Union[str, int]]] = None) -> None:
        if packet_type not in [self._M_SEARCH, self._NOTIFY, self._OK]:
            raise UPnPError("unknown packet type: {}".format(packet_type))
        self._packet_type = packet_type
        kw: Dict[str, Union[str, int]] = kwargs or OrderedDict()
        self._field_order: List[str] = [
            k.lower().replace("-", "_") for k in kw.keys()
        ]
        self.host: Optional[str] = None
        self.man: Optional[str] = None
        self.mx: Optional[Union[str, int]] = None
        self.st: Optional[str] = None
        self.nt: Optional[str] = None
        self.nts: Optional[str] = None
        self.usn: Optional[str] = None
        self.location: Optional[str] = None
        self.cache_control: Optional[str] = None
        self.server: Optional[str] = None
        self.date: Optional[str] = None
        self.ext: Optional[str] = None
        for k, v in kw.items():
            normalized = k.lower().replace("-", "_")
            if not normalized.startswith("_") and hasattr(self, normalized):
                if getattr(self, normalized, None) is None:
                    setattr(self, normalized, v)
        self._case_mappings: Dict[str, str] = {k.lower(): k for k in kw.keys()}
        for k in self._required_fields[self._packet_type]:
            if getattr(self, k, None) is None:
                raise UPnPError("missing required field %s" % k)

    def get_cli_igd_kwargs(self) -> str:
        fields = []
        for field in self._field_order:
            fields.append("--%s=%s" % (self._case_mappings.get(field, field), getattr(self, field, None)))
        return " ".join(fields)

    def __repr__(self) -> str:
        return self.as_json()

    def __getitem__(self, item: str) -> Union[str, int]:
        for i in self._required_fields[self._packet_type]:
            if i.lower() == item.lower():
                return getattr(self, i)
        raise KeyError(item)

    def encode(self, trailing_newlines: int = 2) -> str:
        lines = [self._start_lines[self._packet_type]]
        lines.extend(
            f"{self._case_mappings.get(attr_name.lower(), attr_name.upper())}: {str(getattr(self, attr_name))}"
            for attr_name in self._field_order if attr_name in self._required_fields[self._packet_type]
        )
        serialized = line_separator.join(lines)
        for _ in range(trailing_newlines):
            serialized += line_separator
        return serialized

    def as_dict(self) -> Dict[str, Union[str, int]]:
        return self._lines_to_content_dict(self.encode().split(line_separator))

    def as_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2)

    @classmethod
    def decode(cls, datagram: bytes) -> 'SSDPDatagram':
        try:
            packet = cls._from_string(datagram.decode())
        except UnicodeDecodeError:
            raise UPnPError(
                f"failed to decode datagram: {binascii.hexlify(datagram).decode()}"
            )
        if packet is None:
            raise UPnPError(
                f"failed to decode datagram: {binascii.hexlify(datagram).decode()}"
            )
        return packet

    @classmethod
    def _lines_to_content_dict(cls, lines: List[str]) -> Dict[str, Union[str, int]]:
        result: Dict[str, Union[str, int]] = OrderedDict()
        matched_keys: List[str] = []
        for line in lines:
            if not line:
                continue
            matched = False
            for name, pattern in ssdp_datagram_patterns.items():
                if name not in matched_keys:
                    if name.lower() == 'mx':
                        _matched_int = pattern(line)
                        if _matched_int is not None:
                            match_int = int(_matched_int)
                            result[line[:len(name)]] = match_int
                            matched = True
                            matched_keys.append(name)
                            break
                    else:
                        match = pattern(line)
                        if match is not None:
                            result[line[:len(name)]] = match
                            matched = True
                            matched_keys.append(name)
                            break
        return result

    @classmethod
    def _from_string(cls, datagram: str) -> Optional['SSDPDatagram']:
        lines = [l for l in datagram.split(line_separator) if l]
        if not lines:
            return None
        if lines[0] == cls._start_lines[cls._M_SEARCH]:
            return cls._from_request(lines[1:])
        if lines[0] in [cls._start_lines[cls._NOTIFY], cls._start_lines[cls._NOTIFY] + " "]:
            return cls._from_notify(lines[1:])
        if lines[0] == cls._start_lines[cls._OK]:
            return cls._from_response(lines[1:])
        return None

    @classmethod
    def _from_response(cls, lines: List) -> 'SSDPDatagram':
        return cls(cls._OK, cls._lines_to_content_dict(lines))

    @classmethod
    def _from_notify(cls, lines: List) -> 'SSDPDatagram':
        return cls(cls._NOTIFY, cls._lines_to_content_dict(lines))

    @classmethod
    def _from_request(cls, lines: List) -> 'SSDPDatagram':
        return cls(cls._M_SEARCH, cls._lines_to_content_dict(lines))
