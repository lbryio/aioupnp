from aioupnp.util import flatten_keys
from aioupnp.constants import FAULT, CONTROL
from collections import OrderedDict
from typing import Any, Mapping, Optional


class UPnPError(Exception):
    """UPnPError."""
    ...


def handle_fault(response: OrderedDict) -> Any[Mapping, Optional[UPnPError]]:
    """Handle Fault.

    :param dict response: Response
    """
    if FAULT in response:
        fault = flatten_keys(response[FAULT], "{%s}" % CONTROL)
        error_description = fault['detail'][0]['UPnPError']['errorDescription']
        raise UPnPError(error_description)
    return response
