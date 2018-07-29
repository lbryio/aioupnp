from txupnp.util import flatten_keys
from txupnp.constants import FAULT, CONTROL


class UPnPError(Exception):
    pass


def handle_fault(response):
    if FAULT in response:
        fault = flatten_keys(response[FAULT], "{%s}" % CONTROL)
        raise UPnPError(fault['detail']['UPnPError']['errorDescription'])
    return response
