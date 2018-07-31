import re
import functools
from collections import defaultdict
import netifaces
from twisted.internet import defer

BASE_ADDRESS_REGEX = re.compile("^(http:\/\/\d*\.\d*\.\d*\.\d*:\d*)\/.*$".encode())
BASE_PORT_REGEX = re.compile("^http:\/\/\d*\.\d*\.\d*\.\d*:(\d*)\/.*$".encode())


def etree_to_dict(t):
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


def get_lan_info():
    gateway_address, iface_name = netifaces.gateways()['default'][netifaces.AF_INET]
    lan_addr = netifaces.ifaddresses(iface_name)[netifaces.AF_INET][0]['addr']
    return iface_name, gateway_address, lan_addr


def _return_types(*types):
    def _return_types_wrapper(fn):
        @functools.wraps(fn)
        def _inner(response):
            if isinstance(response, (list, tuple)):
                r = tuple(t(r) for t, r in zip(types, response))
                if len(r) == 1:
                    return fn(r[0])
                return fn(r)
            return fn(types[0](response))
        return _inner
    return _return_types_wrapper


def return_types(*types):
    def return_types_wrapper(fn):
        fn._return_types = types
        return fn

    return return_types_wrapper


none_or_str = lambda x: None if not x or x == 'None' else str(x)

none = lambda _: None


@defer.inlineCallbacks
def DeferredDict(d, consumeErrors=False):
    keys = []
    dl = []
    response = {}
    for k, v in d.items():
        keys.append(k)
        dl.append(v)
    results = yield defer.DeferredList(dl, consumeErrors=consumeErrors)
    for k, (success, result) in zip(keys, results):
        if success:
            response[k] = result
    defer.returnValue(response)
