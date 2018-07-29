import logging
from twisted.internet import defer
from txupnp.fault import UPnPError
from txupnp.soap import SOAPServiceManager

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
        return self.soap_manager.get_runner()

    def m_search(self, address, ttl=30, max_devices=2):
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
        return self.soap_manager.sspd_factory.m_search(address, ttl=ttl, max_devices=max_devices)

    @defer.inlineCallbacks
    def discover(self, ttl=30, max_devices=2):
        try:
            yield self.soap_manager.discover_services(ttl=ttl, max_devices=max_devices)
        except defer.TimeoutError:
            log.warning("failed to find upnp gateway")
            defer.returnValue(False)
        defer.returnValue(True)

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

    def get_specific_port_mapping(self, external_port, protocol):
        """
        :param external_port: (int) external port to listen on
        :param protocol:      (str) 'UDP' | 'TCP'
        :return: (int) <internal port>, (str) <lan ip>, (bool) <enabled>, (str) <description>, (int) <lease time>
        """
        return self.commands.GetSpecificPortMappingEntry(
            NewRemoteHost=None, NewExternalPort=external_port, NewProtocol=protocol
        )

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
