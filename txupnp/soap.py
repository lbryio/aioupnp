import logging
from twisted.internet import defer
from txupnp.util import get_lan_info
from txupnp.ssdp import SSDPFactory
from txupnp.scpd import SCPDCommandRunner
from txupnp.gateway import Gateway
from txupnp.fault import UPnPError
from txupnp.constants import GATEWAY_SCHEMA

log = logging.getLogger(__name__)


class SOAPServiceManager(object):
    def __init__(self, reactor):
        self._reactor = reactor
        self.iface_name, self.router_ip, self.lan_address = get_lan_info()
        self.sspd_factory = SSDPFactory(self._reactor, self.lan_address, self.router_ip)
        self._command_runners = {}
        self._selected_runner = GATEWAY_SCHEMA

    @defer.inlineCallbacks
    def discover_services(self, address=None, timeout=30, max_devices=1):
        server_infos = yield self.sspd_factory.m_search(
            address or self.router_ip, timeout=timeout, max_devices=max_devices
        )
        locations = []
        for server_info in server_infos:
            if 'st' in server_info and server_info['st'] not in self._command_runners:
                locations.append(server_info['location'])
                gateway = Gateway(**server_info)
                yield gateway.discover_services()
                command_runner = SCPDCommandRunner(gateway)
                yield command_runner.discover_commands()
                self._command_runners[gateway.urn.decode()] = command_runner
            elif 'st' not in server_info:
                log.error("don't know how to handle gateway: %s", server_info)
                continue
        defer.returnValue(len(self._command_runners))

    def set_runner(self, urn):
        if urn not in self._command_runners:
            raise IndexError(urn)
        self._command_runners = urn

    def get_runner(self):
        if self._command_runners and not self._selected_runner in self._command_runners:
            self._selected_runner = list(self._command_runners.keys())[0]
        if not self._command_runners:
            raise UPnPError("no devices found")
        return self._command_runners[self._selected_runner]

    def get_available_runners(self):
        return self._command_runners.keys()
