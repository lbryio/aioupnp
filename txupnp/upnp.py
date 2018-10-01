import netifaces
import logging
from twisted.internet import defer
from txupnp.fault import UPnPError
from txupnp.ssdp import SSDPFactory
from txupnp.gateway import Gateway

log = logging.getLogger(__name__)


class UPnP:
    def __init__(self, reactor, try_miniupnpc_fallback=False, debug_ssdp=False, router_ip=None,
                 lan_ip=None, iface_name=None):
        self._reactor = reactor
        if router_ip and lan_ip and iface_name:
            self.router_ip, self.lan_address, self.iface_name = router_ip, lan_ip, iface_name
        else:
            self.router_ip, self.iface_name = netifaces.gateways()['default'][netifaces.AF_INET]
            self.lan_address = netifaces.ifaddresses(self.iface_name)[netifaces.AF_INET][0]['addr']
        self.sspd_factory = SSDPFactory(self._reactor, self.lan_address, self.router_ip, debug_packets=debug_ssdp)
        self.try_miniupnpc_fallback = try_miniupnpc_fallback
        self.miniupnpc_runner = None
        self.miniupnpc_igd_url = None
        self.gateway = None

    def m_search(self, address, timeout=1, max_devices=1):
        """
        Perform a HTTP over UDP M-SEARCH query

        returns (list) [{
            'server: <gateway os and version string>
            'location': <upnp gateway url>,
            'cache-control': <max age>,
            'date': <server time>,
            'usn': <usn>
        }, ...]
        """
        return self.sspd_factory.m_search(address, timeout=timeout, max_devices=max_devices)

    @defer.inlineCallbacks
    def _discover(self, timeout=1, max_devices=1):
        server_infos = yield self.sspd_factory.m_search(
            self.router_ip, timeout=timeout, max_devices=max_devices
        )
        server_info = server_infos[0]
        if 'st' in server_info:
            gateway = Gateway(reactor=self._reactor, **server_info)
            yield gateway.discover_commands()
            self.gateway = gateway
            defer.returnValue(True)
        elif 'st' not in server_info:
            log.error("don't know how to handle gateway: %s", server_info)
        defer.returnValue(False)

    @defer.inlineCallbacks
    def discover(self, timeout=1, max_devices=1):
        try:
            found = yield self._discover(timeout=timeout, max_devices=max_devices)
        except defer.TimeoutError:
            found = False
        finally:
            self.sspd_factory.disconnect()
        if found:
            log.debug("found upnp device")
        else:
            log.debug("failed to find upnp device")
        defer.returnValue(found)

    def get_external_ip(self) -> str:
        return self.gateway.commands.GetExternalIPAddress()

    def add_port_mapping(self, external_port: int, protocol: str, internal_port, lan_address: str,
                         description: str) -> None:
        return self.gateway.commands.AddPortMapping(
            NewRemoteHost="", NewExternalPort=external_port, NewProtocol=protocol,
            NewInternalPort=internal_port, NewInternalClient=lan_address,
            NewEnabled=1, NewPortMappingDescription=description, NewLeaseDuration=""
        )

    @defer.inlineCallbacks
    def get_port_mapping_by_index(self, index: int) -> (str, int, str, int, str, bool, str, int):
        try:
            redirect = yield self.gateway.commands.GetGenericPortMappingEntry(NewPortMappingIndex=index)
            defer.returnValue(redirect)
        except UPnPError:
            defer.returnValue(None)

    @defer.inlineCallbacks
    def get_redirects(self):
        redirects = []
        cnt = 0
        redirect = yield self.get_port_mapping_by_index(cnt)
        while redirect:
            redirects.append(redirect)
            cnt += 1
            redirect = yield self.get_port_mapping_by_index(cnt)
        defer.returnValue(redirects)

    @defer.inlineCallbacks
    def get_specific_port_mapping(self, external_port: int, protocol: str) -> (int, str, bool, str, int):
        """
        :param external_port: (int) external port to listen on
        :param protocol:      (str) 'UDP' | 'TCP'
        :return: (int) <internal port>, (str) <lan ip>, (bool) <enabled>, (str) <description>, (int) <lease time>
        """

        try:
            result = yield self.gateway.commands.GetSpecificPortMappingEntry(
                NewRemoteHost=None, NewExternalPort=external_port, NewProtocol=protocol
            )
            defer.returnValue(result)
        except UPnPError:
            defer.returnValue(None)

    def delete_port_mapping(self, external_port: int, protocol: str) -> None:
        """
        :param external_port: (int) external port to listen on
        :param protocol:      (str) 'UDP' | 'TCP'
        :return: None
        """
        return self.gateway.commands.DeletePortMapping(
            NewRemoteHost="", NewExternalPort=external_port, NewProtocol=protocol
        )

    @defer.inlineCallbacks
    def get_next_mapping(self, port, protocol, description, internal_port=None):
        if protocol not in ["UDP", "TCP"]:
            raise UPnPError("unsupported protocol: {}".format(protocol))
        internal_port = internal_port or port
        redirect_tups = yield self.get_redirects()
        redirects = {
            "%i:%s" % (ext_port, proto): (int_host, int_port, desc)
            for (ext_host, ext_port, proto, int_port, int_host, enabled, desc, lease) in redirect_tups
        }
        while ("%i:%s" % (port, protocol)) in redirects:
            int_host, int_port, _ = redirects["%i:%s" % (port, protocol)]
            if int_host == self.lan_address and int_port == internal_port:
                break
            port += 1

        yield self.add_port_mapping(  # set one up
                port, protocol, internal_port, self.lan_address, description
        )
        defer.returnValue(port)
