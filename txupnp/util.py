import re
import functools
from collections import defaultdict
from xml.etree import ElementTree

BASE_ADDRESS_REGEX = re.compile("^(http:\/\/\d*\.\d*\.\d*\.\d*:\d*)\/.*$".encode())
BASE_PORT_REGEX = re.compile("^http:\/\/\d*\.\d*\.\d*\.\d*:(\d*)\/.*$".encode())


def etree_to_dict(t: ElementTree) -> dict:
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d


def flatten_keys(d, strip):
    if not isinstance(d, (list, dict)):
        return d
    if isinstance(d, list):
        return [flatten_keys(i, strip) for i in d]
    t = {}
    for k, v in d.items():
        if strip in k and strip != k:
            t[k.split(strip)[1]] = flatten_keys(v, strip)
        else:
            t[k] = flatten_keys(v, strip)
    return t


def get_dict_val_case_insensitive(d, k):
    match = list(filter(lambda x: x.lower() == k.lower(), d.keys()))
    if not match:
        return
    if len(match) > 1:
        raise KeyError("overlapping keys")
    return d[match[0]]


def verify_return_types(*types):
    """
    Attempt to recast results to expected result types
    """

    def _verify_return_types(fn):
        @functools.wraps(fn)
        def _inner(*result):
            r = fn(*tuple(t(r) for t, r in zip(types, result)))
            if isinstance(r, tuple) and len(r) == 1:
                return r[0]
            return r
        return _inner
    return _verify_return_types


def return_types(*types):
    """
    Decorator to set the expected return types of a SOAP function call
    """

    def return_types_wrapper(fn):
        fn._return_types = types
        return fn

    return return_types_wrapper


none_or_str = lambda x: None if not x or x == 'None' else str(x)

none = lambda _: None
