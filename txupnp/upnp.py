import logging
from xml.etree import ElementTree
from twisted.internet import defer
import treq
from txupnp.fault import UPnPError
from txupnp.ssdp import SSDPFactory
from txupnp.scpd import SCPDCommandManager
from txupnp.util import get_lan_info, BASE_ADDRESS_REGEX, flatten_keys, etree_to_dict, DEVICE_ELEMENT_REGEX
from txupnp.util import find_inner_service_info, BASE_PORT_REGEX
from txupnp.constants import LAYER_FORWARD_KEY, WAN_INTERFACE_KEY, WAN_IP_KEY

log = logging.getLogger(__name__)


class Service(object):
    def __init__(self, base_address, serviceId=None, SCPDURL=None, eventSubURL=None, controlURL=None, **kwargs):
        self.base_address = base_address
        self.service_id = serviceId
        self._control_path = controlURL
        self._subscribe_path = eventSubURL
        self._scpd_path = SCPDURL

    @property
    def scpd_url(self):
        return self.base_address.decode() + self._scpd_path

    @property
    def control_url(self):
        return self.base_address.decode() + self._control_path


class UPnP(object):
    def __init__(self, reactor):
        self._reactor = reactor
        self.iface_name, self.gateway_ip, self.lan_address = get_lan_info()
        self._m_search_factory = SSDPFactory(self.lan_address, self._reactor)
        self.gateway_url = ""
        self.gateway_base = ""
        self.gateway_port = None
        self.layer_3_forwarding = None
        self.wan_ip = None
        self.wan_interface = None
        self.commands = SCPDCommandManager(self)

    def m_search(self, address):
        """
        Perform a HTTP over UDP M-SEARCH query

        returns (dict) {
            'location': <upnp gateway url>,
            'cache-control': <max age>,
            'date': <server time>,
            'usn': <usn>
        }
        """
        return self._m_search_factory.m_search(address)

    @defer.inlineCallbacks
    def _discover_gateway(self):
        server_info = yield self.m_search(self.gateway_ip)
        if 'server'.encode() in server_info:
            log.info("gateway version: %s", server_info['server'.encode()])
        else:
            log.info("discovered gateway")
        self.gateway_url = server_info['location'.encode()]
        self.gateway_base = BASE_ADDRESS_REGEX.findall(self.gateway_url)[0]
        self.gateway_port = int(BASE_PORT_REGEX.findall(self.gateway_url)[0])  # the tcp port
        response = yield treq.get(self.gateway_url)
        response_xml = yield response.text()
        elements = ElementTree.fromstring(response_xml)
        for element in elements:
            if DEVICE_ELEMENT_REGEX.findall(element.tag):
                tag = DEVICE_ELEMENT_REGEX.findall(element.tag)[0]
                prefix = tag[:-6]
                device_info = flatten_keys(etree_to_dict(elements.find(tag)), prefix)
                self.layer_3_forwarding = Service(self.gateway_base, **find_inner_service_info(
                    device_info['device']['serviceList']['service'], LAYER_FORWARD_KEY
                    )
                                                  )
                self.wan_interface = Service(self.gateway_base, **find_inner_service_info(
                    device_info['device']['deviceList']['device']['serviceList']['service'], WAN_INTERFACE_KEY
                    )
                                             )
                self.wan_ip = Service(self.gateway_base, **find_inner_service_info(
                    device_info['device']['deviceList']['device']['deviceList']['device']['serviceList']['service'],
                    WAN_IP_KEY
                    )
                                      )
                defer.returnValue(None)

    @defer.inlineCallbacks
    def discover(self):
        try:
            yield self._discover_gateway()
        except defer.TimeoutError:
            log.warning("failed to find gateway")
            defer.returnValue(False)
        yield self.commands.discover_commands()
        defer.returnValue(True)

    def get_external_ip(self):
        return self.commands.GetExternalIPAddress()
    #
    # def GetStatusInfo(self):
    #     return self._commands['GetStatusInfo']()
    #
    # def GetConnectionTypeInfo(self):
    #     return self._commands['GetConnectionTypeInfo']()

    def add_port_mapping(self, external_port, protocol, internal_port, lan_address, description, lease_duration):
        return self.commands.AddPortMapping(
            NewRemoteHost=None, NewExternalPort=external_port, NewProtocol=protocol,
            NewInternalPort=internal_port, NewInternalClient=lan_address,
            NewEnabled=1, NewPortMappingDescription=description,
            NewLeaseDuration=lease_duration
        )

    # def GetNATRSIPStatus(self):
    #     return self._commands['GetNATRSIPStatus']()

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
        return self.commands.GetSpecificPortMappingEntry(
            NewRemoteHost=None, NewExternalPort=external_port, NewProtocol=protocol
        )

    # def ForceTermination(self):
    #     return self._commands['ForceTermination']()

    def delete_port_mapping(self, external_port, protocol):
        return self.commands.DeletePortMapping(
            NewRemoteHost=None, NewExternalPort=external_port, NewProtocol=protocol
        )
