import logging
from collections import namedtuple, OrderedDict
from twisted.internet import defer
from twisted.web.client import Agent, HTTPConnectionPool
import treq
from treq.client import HTTPClient
from xml.etree import ElementTree
from txupnp.util import etree_to_dict, flatten_keys, return_types, _return_types, none_or_str
from txupnp.fault import handle_fault
from txupnp.constants import POST, ENVELOPE, BODY, XML_VERSION, WAN_IP_KEY, SERVICE_KEY, SSDP_IP_ADDRESS

log = logging.getLogger(__name__)


class StringProducer(object):
    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return defer.succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass


def xml_arg(name, arg):
    return "<%s>%s</%s>" % (name, arg, name)


def get_soap_body(service_name, method, param_names, **kwargs):
    args = "".join(xml_arg(n, kwargs.get(n)) for n in param_names)
    return '\n%s\n<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body><u:%s xmlns:u="%s">%s</u:%s></s:Body></s:Envelope>' % (XML_VERSION, method, service_name, args, method)


class _SCPDCommand(object):
    def __init__(self, gateway_address, service_port, control_url, service_id, method, param_names, returns,
                 reactor=None):
        if not reactor:
            from twisted.internet import reactor
        self._reactor = reactor
        self._pool = HTTPConnectionPool(reactor)
        self.agent = Agent(reactor, connectTimeout=1)
        self._http_client = HTTPClient(self.agent, data_to_body_producer=StringProducer)
        self.gateway_address = gateway_address
        self.service_port = service_port
        self.control_url = control_url
        self.service_id = service_id
        self.method = method
        self.param_names = param_names
        self.returns = returns

    def extract_body(self, xml_response, service_key=WAN_IP_KEY):
        content_dict = etree_to_dict(ElementTree.fromstring(xml_response))
        envelope = content_dict[ENVELOPE]
        return flatten_keys(envelope[BODY], "{%s}" % service_key)

    def extract_response(self, body):
        body = handle_fault(body)  # raises UPnPError if there is a fault
        if '%sResponse' % self.method in body:
            response_key = '%sResponse' % self.method
        else:
            1/0
            return

        response = body[response_key]
        extracted_response = tuple([response[n] for n in self.returns])
        if len(extracted_response) == 1:
            return extracted_response[0]
        return extracted_response

    @defer.inlineCallbacks
    def send_upnp_soap(self, **kwargs):
        soap_body = get_soap_body(self.service_id, self.method, self.param_names, **kwargs).encode()
        headers = OrderedDict((
            ('SOAPAction', '%s#%s' % (self.service_id, self.method)),
            ('Host', ('%s:%i' % (SSDP_IP_ADDRESS, self.service_port))),
            ('Content-Type', 'text/xml'),
            ('Content-Length', len(soap_body))
        )
        )
        response = yield self._http_client.request(
            POST, url=self.control_url, data=soap_body, headers=headers
        )
        xml_response = yield response.content()
        response = self.extract_response(self.extract_body(xml_response))
        defer.returnValue(response)

    @staticmethod
    def _process_result(results):
        """
        this method gets decorated automatically with a function that maps result types to the types
        defined in the @return_types decorator
        """
        return results

    @defer.inlineCallbacks
    def __call__(self, **kwargs):
        if set(kwargs.keys()) != set(self.param_names):
            raise Exception("argument mismatch")
        response = yield self.send_upnp_soap(**kwargs)
        result = self._process_result(response)
        defer.returnValue(result)


class SCPDCommandManager(object):
    def __init__(self, upnp):
        self._upnp = upnp

    @defer.inlineCallbacks
    def discover_commands(self):
        response = yield treq.get(self._upnp.wan_ip.scpd_url)
        content = yield response.content()
        tree = ElementTree.fromstring(content)
        actions = flatten_keys(etree_to_dict(tree), "{%s}" % SERVICE_KEY)["scpd"]["actionList"]["action"]
        for action_dict in actions:
            self._register_command(action_dict)
        log.info("registered %i commands", len(actions))
        defer.returnValue(None)

    @staticmethod
    def _soap_function_info(action_dict):
        if not action_dict.get('argumentList'):
            return (
                action_dict['name'],
                [],
                []
            )
        arg_dicts = action_dict['argumentList']['argument']
        if not isinstance(arg_dicts, list):  # when there is one arg, ew
            arg_dicts = [arg_dicts]
        return (
            action_dict['name'],
            [i['name'] for i in arg_dicts if i['direction'] == 'in'],
            [i['name'] for i in arg_dicts if i['direction'] == 'out']
        )

    def _register_command(self, action_info):
        command = _SCPDCommand(self._upnp.gateway_ip, self._upnp.gateway_port, self._upnp.wan_ip.control_url,
                               self._upnp.wan_ip.service_id, *self._soap_function_info(action_info))
        if not hasattr(self, command.method):
            raise NotImplementedError(command.method)
        current = getattr(self, command.method)
        if hasattr(current, "_return_types"):
            command._process_result = _return_types(*current._return_types)(command._process_result)
        setattr(command, "__doc__", current.__doc__)
        setattr(self, command.method, command)

    @staticmethod
    def AddPortMapping(NewRemoteHost, NewExternalPort, NewProtocol, NewInternalPort, NewInternalClient,
                       NewEnabled, NewPortMappingDescription, NewLeaseDuration):
        """Returns None"""
        raise NotImplementedError()

    @staticmethod
    def GetNATRSIPStatus():
        """Returns (NewRSIPAvailable, NewNATEnabled)"""
        raise NotImplementedError()

    @staticmethod
    @return_types(none_or_str, int, str, int, str, bool, str, int)
    def GetGenericPortMappingEntry(NewPortMappingIndex):
        """
        Returns (NewRemoteHost, NewExternalPort, NewProtocol, NewInternalPort, NewInternalClient, NewEnabled,
                 NewPortMappingDescription, NewLeaseDuration)
        """
        raise NotImplementedError()

    @staticmethod
    @return_types(int, str, bool, str, int)
    def GetSpecificPortMappingEntry(NewRemoteHost, NewExternalPort, NewProtocol):
        """Returns (NewInternalPort, NewInternalClient, NewEnabled, NewPortMappingDescription, NewLeaseDuration)"""
        raise NotImplementedError()

    @staticmethod
    def SetConnectionType(NewConnectionType):
        """Returns None"""
        raise NotImplementedError()

    @staticmethod
    def GetExternalIPAddress():
        """Returns (NewExternalIPAddress)"""
        raise NotImplementedError()

    @staticmethod
    def GetConnectionTypeInfo():
        """Returns (NewConnectionType, NewPossibleConnectionTypes)"""
        raise NotImplementedError()

    @staticmethod
    def GetStatusInfo():
        """Returns (NewConnectionStatus, NewLastConnectionError, NewUptime)"""
        raise NotImplementedError()

    @staticmethod
    def ForceTermination():
        """Returns None"""
        raise NotImplementedError()

    @staticmethod
    def DeletePortMapping(NewRemoteHost, NewExternalPort, NewProtocol):
        """Returns None"""
        raise NotImplementedError()

    @staticmethod
    def RequestConnection():
        """Returns None"""
        raise NotImplementedError()
