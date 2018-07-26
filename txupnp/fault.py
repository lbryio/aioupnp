from txupnp.util import flatten_keys
from txupnp.constants import FAULT, CONTROL_KEY


class UPnPError(Exception):
    pass


def handle_fault(response):
    if FAULT in response:
        fault = flatten_keys(response[FAULT], "{%s}" % CONTROL_KEY)
        raise UPnPError(fault['detail']['UPnPError']['errorDescription'])
    return response
