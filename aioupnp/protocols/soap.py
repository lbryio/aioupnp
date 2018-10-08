import logging
from aioupnp.protocols.scpd import scpd_post

log = logging.getLogger(__name__)


class SCPDCommand:
    def __init__(self, gateway_address: str, service_port: int, control_url: str, service_id: bytes, method: str,
                 param_types: dict, return_types: dict, param_order: list, return_order: list):
        self.gateway_address = gateway_address
        self.service_port = service_port
        self.control_url = control_url
        self.service_id = service_id
        self.method = method
        self.param_types = param_types
        self.param_order = param_order
        self.return_types = return_types
        self.return_order = return_order

    async def __call__(self, **kwargs):
        if set(kwargs.keys()) != set(self.param_types.keys()):
            raise Exception("argument mismatch: %s vs %s" % (kwargs.keys(), self.param_types.keys()))
        close_after_send = not self.return_types or self.return_types == [None]
        response = await scpd_post(
            self.control_url, self.gateway_address, self.service_port, self.method, self.param_order, self.service_id,
            close_after_send, **{n: self.param_types[n](kwargs[n]) for n in self.param_types.keys()}
        )
        extracted_response = tuple([None if self.return_types[n] is None else self.return_types[n](response[n])
                                    for n in self.return_order]) or (None, )
        if len(extracted_response) == 1:
            return extracted_response[0]
        return extracted_response
