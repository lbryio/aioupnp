import logging
import json
from twisted.internet import defer
from txupnp.fault import UPnPError
from txupnp.soap import SOAPServiceManager
from txupnp.scpd import UPnPFallback

log = logging.getLogger(__name__)


class UPnP(object):
    def __init__(self, reactor, try_miniupnpc_fallback=True):
        self._reactor = reactor
        self.try_miniupnpc_fallback = try_miniupnpc_fallback
        self.soap_manager = SOAPServiceManager(reactor)
        self.miniupnpc_runner = None
        self.miniupnpc_igd_url = None

    @property
    def lan_address(self):
        return self.soap_manager.lan_address

    @property
    def commands(self):
        try:
            runner = self.soap_manager.get_runner()
            required_commands = [
                "GetExternalIPAddress",
                "AddPortMapping",
                "GetSpecificPortMappingEntry",
                "GetGenericPortMappingEntry",
                "DeletePortMapping"
            ]
            if all((command in runner._registered_commands for command in required_commands)):
                return runner
            raise UPnPError("required commands not found")
        except UPnPError as err:
            if self.try_miniupnpc_fallback and self.miniupnpc_runner:
                return self.miniupnpc_runner
            log.warning("upnp is not available: %s", err)

    def m_search(self, address, timeout=30, max_devices=2):
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
        return self.soap_manager.sspd_factory.m_search(address, timeout=timeout, max_devices=max_devices)

    @defer.inlineCallbacks
    def discover(self, timeout=1, max_devices=1, keep_listening=False, try_txupnp=True):
        found = False
        if not try_txupnp and not self.try_miniupnpc_fallback:
            log.warning("nothing left to try")
        if try_txupnp:
            try:
                found = yield self.soap_manager.discover_services(timeout=timeout, max_devices=max_devices)
            except defer.TimeoutError:
                found = False
            finally:
                if not keep_listening:
                    self.soap_manager.sspd_factory.disconnect()
        if found:
            try:
                runner = self.soap_manager.get_runner()
                required_commands = [
                    "GetExternalIPAddress",
                    "AddPortMapping",
                    "GetSpecificPortMappingEntry",
                    "GetGenericPortMappingEntry",
                    "DeletePortMapping"
                ]
                found = all((command in runner._registered_commands for command in required_commands))
            except UPnPError:
                found = False
        if not found and self.try_miniupnpc_fallback:
            found = yield self.start_miniupnpc_fallback()
        defer.returnValue(found)

    @defer.inlineCallbacks
    def start_miniupnpc_fallback(self):
        found = False
        if not self.miniupnpc_runner:
            log.debug("trying miniupnpc fallback")
            fallback = UPnPFallback()
            success = yield fallback.discover()
            self.miniupnpc_igd_url = fallback.device_url
            if success:
                log.info("successfully started miniupnpc fallback")
                self.miniupnpc_runner = fallback
                found = True
        if not found:
            log.warning("failed to find upnp gateway using miniupnpc fallback")
        defer.returnValue(found)

    def get_external_ip(self):
        return self.commands.GetExternalIPAddress()

    def add_port_mapping(self, external_port, protocol, internal_port, lan_address, description):
        return self.commands.AddPortMapping(
            NewRemoteHost="", NewExternalPort=external_port, NewProtocol=protocol,
            NewInternalPort=internal_port, NewInternalClient=lan_address,
            NewEnabled=1, NewPortMappingDescription=description, NewLeaseDuration=""
        )

    def get_port_mapping_by_index(self, index):
        return self.commands.GetGenericPortMappingEntry(NewPortMappingIndex=index)

    @defer.inlineCallbacks
    def get_redirects(self):
        redirects = []
        cnt = 0
        while True:
            try:
                redirect = yield self.get_port_mapping_by_index(cnt)
                redirects.append(redirect)
                cnt += 1
            except UPnPError:
                break
        defer.returnValue(redirects)

    @defer.inlineCallbacks
    def get_specific_port_mapping(self, external_port, protocol):
        """
        :param external_port: (int) external port to listen on
        :param protocol:      (str) 'UDP' | 'TCP'
        :return: (int) <internal port>, (str) <lan ip>, (bool) <enabled>, (str) <description>, (int) <lease time>
        """

        try:
            result = yield self.commands.GetSpecificPortMappingEntry(
                NewRemoteHost=None, NewExternalPort=external_port, NewProtocol=protocol
            )
            defer.returnValue(result)
        except UPnPError as err:
            if 'NoSuchEntryInArray' in str(err):
                defer.returnValue(None)
            else:
                raise err

    def delete_port_mapping(self, external_port, protocol, new_remote_host=""):
        """
        :param external_port: (int) external port to listen on
        :param protocol:      (str) 'UDP' | 'TCP'
        :return: None
        """
        return self.commands.DeletePortMapping(
            NewRemoteHost=new_remote_host, NewExternalPort=external_port, NewProtocol=protocol
        )

    def get_rsip_nat_status(self):
        """
        :return: (bool) NewRSIPAvailable, (bool) NewNATEnabled
        """
        return self.commands.GetNATRSIPStatus()

    def get_status_info(self):
        """
        :return: (str) NewConnectionStatus, (str) NewLastConnectionError, (int) NewUptime
        """
        return self.commands.GetStatusInfo()

    def get_connection_type_info(self):
        """
        :return: (str) NewConnectionType (str), NewPossibleConnectionTypes (str)
        """
        return self.commands.GetConnectionTypeInfo()

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

    def get_debug_info(self, include_gateway_xml=False):
        def default_byte(x):
            if isinstance(x, bytes):
                return x.decode()
            return x
        return json.dumps({
            'txupnp': self.soap_manager.debug(include_gateway_xml=include_gateway_xml),
            'miniupnpc_igd_url': self.miniupnpc_igd_url
            },
            indent=2, default=default_byte
        )
