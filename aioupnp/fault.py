from aioupnp.util import flatten_keys
from aioupnp.constants import FAULT, CONTROL
from typing import Dict, Union


class UPnPError(Exception):
    """UPnPError."""
    pass


def handle_fault(response: Dict) -> Union[Dict, UPnPError]:
    """Handle Fault.

    :param dict response: Response
    """
    if FAULT in response:
        fault = flatten_keys(response[FAULT], "{%s}" % CONTROL)
        error_description = fault['detail'][0]['UPnPError']['errorDescription']
        raise UPnPError(error_description)
    return response
