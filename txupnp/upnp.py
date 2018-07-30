import logging
import json
from twisted.internet import defer
from txupnp.fault import UPnPError
from txupnp.soap import SOAPServiceManager
from txupnp.util import DeferredDict

log = logging.getLogger(__name__)


class UPnP(object):
    def __init__(self, reactor):
        self._reactor = reactor
        self.soap_manager = SOAPServiceManager(reactor)

    @property
    def lan_address(self):
        return self.soap_manager.lan_address

    @property
    def commands(self):
        try:
            return self.soap_manager.get_runner()
        except UPnPError as err:
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
    def discover(self, timeout=1, max_devices=1, keep_listening=False):
        try:
            yield self.soap_manager.discover_services(timeout=timeout, max_devices=max_devices)
            found = True
        except defer.TimeoutError:
            log.warning("failed to find upnp gateway")
            found = False
        finally:
            if not keep_listening:
                self.soap_manager.sspd_factory.disconnect()
        defer.returnValue(found)

    def get_external_ip(self):
        return self.commands.GetExternalIPAddress()

    def add_port_mapping(self, external_port, protocol, internal_port, lan_address, description, lease_duration):
        return self.commands.AddPortMapping(
            NewRemoteHost=None, NewExternalPort=external_port, NewProtocol=protocol,
            NewInternalPort=internal_port, NewInternalClient=lan_address,
            NewEnabled=1, NewPortMappingDescription=description,
            NewLeaseDuration=lease_duration
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
            raise err

    def delete_port_mapping(self, external_port, protocol):
        """
        :param external_port: (int) external port to listen on
        :param protocol:      (str) 'UDP' | 'TCP'
        :return: None
        """
        return self.commands.DeletePortMapping(
            NewRemoteHost=None, NewExternalPort=external_port, NewProtocol=protocol
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
    def get_next_mapping(self, port, protocol, description):
        if protocol not in ["UDP", "TCP"]:
            raise UPnPError("unsupported protocol: {}".format(protocol))
        mappings = yield DeferredDict({p: self.get_specific_port_mapping(port, p)
                                       for p in ["UDP", "TCP"]})
        if not any((m is not None for m in mappings.values())):  # there are no redirects for this port
            yield self.add_port_mapping(  # set one up
                port, protocol, port, self.lan_address, description, 0
            )
            defer.returnValue(port)
        if mappings[protocol]:
            mapped_port = mappings[protocol][0]
            mapped_address = mappings[protocol][1]
            if mapped_port == port and mapped_address == self.lan_address:  # reuse redirect to us
                defer.returnValue(port)
        port = yield self.get_next_mapping(  # try the next port
            port + 1, protocol, description
        )
        defer.returnValue(port)

    def get_debug_info(self):
        def default_byte(x):
            if isinstance(x, bytes):
                return x.decode()
            return x
        return json.dumps(self.soap_manager.debug(), indent=2, default=default_byte)
