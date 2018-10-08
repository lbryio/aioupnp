from aioupnp.util import flatten_keys
from aioupnp.constants import FAULT, CONTROL


class UPnPError(Exception):
    pass


def handle_fault(response: dict) -> dict:
    if FAULT in response:
        fault = flatten_keys(response[FAULT], "{%s}" % CONTROL)
        error_description = fault['detail']['UPnPError']['errorDescription']
        raise UPnPError(error_description)
    return response
