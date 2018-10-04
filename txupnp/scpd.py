import re
import logging
from xml.etree import ElementTree
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import defer, error
from txupnp.constants import XML_VERSION, DEVICE, ROOT, SERVICE, ENVELOPE, BODY
from txupnp.util import etree_to_dict, flatten_keys
from txupnp.fault import handle_fault, UPnPError

log = logging.getLogger(__name__)

CONTENT_PATTERN = re.compile(
    "(\<\?xml version=\"1\.0\"\?\>(\s*.)*|\>)".encode()
)
CONTENT_NO_XML_VERSION_PATTERN = re.compile(
    "(\<s\:Envelope xmlns\:s=\"http\:\/\/schemas\.xmlsoap\.org\/soap\/envelope\/\"(\s*.)*\>)".encode()
)

XML_ROOT_SANITY_PATTERN = re.compile(
    "(?i)(\{|(urn:schemas-[\w|\d]*-(com|org|net))[:|-](device|service)[:|-]([\w|\d|\:|\-|\_]*)|\}([\w|\d|\:|\-|\_]*))"
)


def parse_service_description(content: bytes):
    if not content:
        return []
    element_dict = etree_to_dict(ElementTree.fromstring(content.decode()))
    service_info = flatten_keys(element_dict, "{%s}" % SERVICE)
    if "scpd" not in service_info:
        return []
    action_list = service_info["scpd"]["actionList"]
    if not len(action_list):  # it could be an empty string
        return []
    result = []
    if isinstance(action_list["action"], dict):
        arg_dicts = action_list["action"]['argumentList']['argument']
        if not isinstance(arg_dicts, list):  # when there is one arg, ew
            arg_dicts = [arg_dicts]
        return [[
            action_list["action"]['name'],
            [i['name'] for i in arg_dicts if i['direction'] == 'in'],
            [i['name'] for i in arg_dicts if i['direction'] == 'out']
        ]]
    for action in action_list["action"]:
        if not action.get('argumentList'):
            result.append((action['name'], [], []))
        else:
            arg_dicts = action['argumentList']['argument']
            if not isinstance(arg_dicts, list):  # when there is one arg, ew
                arg_dicts = [arg_dicts]
            result.append((
                action['name'],
                [i['name'] for i in arg_dicts if i['direction'] == 'in'],
                [i['name'] for i in arg_dicts if i['direction'] == 'out']
            ))
    return result


class SCPDHTTPClientProtocol(Protocol):
    def connectionMade(self):
        self.response_buff = b""
        log.debug("Sending HTTP:\n%s", self.factory.packet.decode())
        self.factory.reactor.callLater(0, self.transport.write, self.factory.packet)

    def dataReceived(self, data):
        self.response_buff += data

    def connectionLost(self, reason):
        if reason.trap(error.ConnectionDone):
            log.debug("Received HTTP:\n%s", self.response_buff.decode())
            if XML_VERSION.encode() in self.response_buff:
                parsed = CONTENT_PATTERN.findall(self.response_buff)
                result = b'' if not parsed else parsed[0][0]
                self.factory.finished_deferred.callback(result)
            else:
                parsed = CONTENT_NO_XML_VERSION_PATTERN.findall(self.response_buff)
                result = b'' if not parsed else XML_VERSION.encode() + b'\r\n' + parsed[0][0]
                self.factory.finished_deferred.callback(result)


class SCPDHTTPClientFactory(ClientFactory):
    protocol = SCPDHTTPClientProtocol

    def __init__(self, reactor, packet):
        self.reactor = reactor
        self.finished_deferred = defer.Deferred()
        self.packet = packet

    def buildProtocol(self, addr):
        p = self.protocol()
        p.factory = self
        return p

    @classmethod
    def post(cls, reactor, command, **kwargs):
        args = "".join("<%s>%s</%s>" % (n, kwargs.get(n), n) for n in command.param_names)
        soap_body = ('\r\n%s\r\n<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
                     's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body>'
                     '<u:%s xmlns:u="%s">%s</u:%s></s:Body></s:Envelope>' % (
                     XML_VERSION, command.method, command.service_id.decode(),
                     args, command.method))
        if "http://" in command.gateway_address.decode():
            host = command.gateway_address.decode().split("http://")[1]
        else:
            host = command.gateway_address.decode()
        data = (
                (
                    'POST %s HTTP/1.1\r\n'
                    'Host: %s\r\n'
                    'User-Agent: python3/txupnp, UPnP/1.0, MiniUPnPc/1.9\r\n'
                    'Content-Length: %i\r\n'
                    'Content-Type: text/xml\r\n'
                    'SOAPAction: \"%s#%s\"\r\n'
                    'Connection: Close\r\n'
                    'Cache-Control: no-cache\r\n'
                    'Pragma: no-cache\r\n'
                    '%s'
                    '\r\n'
                ) % (
                    command.control_url.decode(),  # could be just / even if it shouldn't be
                    host,
                    len(soap_body),
                    command.service_id.decode(),  # maybe no quotes
                    command.method,
                    soap_body
                )
        ).encode()
        return cls(reactor, data)

    @classmethod
    def get(cls, reactor, control_url: str, address: str):
        if "http://" in address:
            host = address.split("http://")[1]
        else:
            host = address
        if ":" in host:
            host = host.split(":")[0]
        if not control_url.startswith("/"):
            control_url = "/" + control_url
        data = (
                (
                    'GET %s HTTP/1.1\r\n'
                    'Accept-Encoding: gzip\r\n'
                    'Host: %s\r\n'
                    '\r\n'
                ) % (control_url, host)
        ).encode()
        return cls(reactor, data)


class SCPDRequester:
    client_factory = SCPDHTTPClientFactory

    def __init__(self, reactor):
        self._reactor = reactor
        self._get_requests = {}
        self._post_requests = {}

    def _save_get(self, request: bytes, response: bytes, destination: str) -> None:
        self._get_requests[destination.lstrip("/")] = {
            'request': request,
            'response': response
        }

    def _save_post(self, request: bytes, response: bytes, destination: str) -> None:
        p = self._post_requests.get(destination.lstrip("/"), [])
        p.append({
            'request': request,
            'response': response,
        })
        self._post_requests[destination.lstrip("/")] = p

    @defer.inlineCallbacks
    def _scpd_get_soap_xml(self, control_url: str, address: str, service_port: int) -> bytes:
        factory = self.client_factory.get(self._reactor, control_url, address)
        url = address.split("http://")[1].split(":")[0]
        self._reactor.connectTCP(url, service_port, factory)
        xml_response_bytes = yield factory.finished_deferred
        self._save_get(factory.packet, xml_response_bytes, control_url)
        return xml_response_bytes

    @defer.inlineCallbacks
    def scpd_post_soap(self, command, **kwargs) -> tuple:
        factory = self.client_factory.post(self._reactor, command, **kwargs)
        url = command.gateway_address.split(b"http://")[1].split(b":")[0]
        self._reactor.connectTCP(url.decode(), command.service_port, factory)
        xml_response_bytes = yield factory.finished_deferred
        self._save_post(
            factory.packet, xml_response_bytes, command.gateway_address.decode() + command.control_url.decode()
        )
        content_dict = etree_to_dict(ElementTree.fromstring(xml_response_bytes.decode()))
        envelope = content_dict[ENVELOPE]
        response_body = flatten_keys(envelope[BODY], "{%s}" % command.service_id)
        body = handle_fault(response_body)  # raises UPnPError if there is a fault
        response_key = None
        for key in body:
            if command.method in key:
                response_key = key
                break
        if not response_key:
            raise UPnPError("unknown response fields for %s")
        response = body[response_key]
        extracted_response = tuple([response[n] for n in command.returns])
        return extracted_response

    @defer.inlineCallbacks
    def scpd_get_supported_actions(self, service, address: str, port: int) -> list:
        xml_bytes = yield self._scpd_get_soap_xml(service.SCPDURL, address, port)
        return parse_service_description(xml_bytes)

    @defer.inlineCallbacks
    def scpd_get(self, control_url: str, service_address: str, service_port: int) -> dict:
        xml_bytes = yield self._scpd_get_soap_xml(control_url, service_address, service_port)
        xml_dict = etree_to_dict(ElementTree.fromstring(xml_bytes.decode()))
        schema_key = DEVICE
        root = ROOT
        for k in xml_dict.keys():
            m = XML_ROOT_SANITY_PATTERN.findall(k)
            if len(m) == 3 and m[1][0] and m[2][5]:
                schema_key = m[1][0]
                root = m[2][5]
                break
        flattened_xml = flatten_keys(xml_dict, "{%s}" % schema_key)[root]
        return flattened_xml

    def dump_packets(self) -> dict:
        return {
            'GET': self._get_requests,
            'POST': self._post_requests
        }


class SCPDCommand:
    def __init__(self, scpd_requester: SCPDRequester, gateway_address, service_port, control_url, service_id, method,
                 param_names,
                 returns):
        self.scpd_requester = scpd_requester
        self.gateway_address = gateway_address
        self.service_port = service_port
        self.control_url = control_url
        self.service_id = service_id
        self.method = method
        self.param_names = param_names
        self.returns = returns

    @staticmethod
    def _process_result(*results):
        """
        this method gets decorated automatically with a function that maps result types to the types
        defined in the @return_types decorator
        """
        return results

    @defer.inlineCallbacks
    def __call__(self, **kwargs):
        if set(kwargs.keys()) != set(self.param_names):
            raise Exception("argument mismatch: %s vs %s" % (kwargs.keys(), self.param_names))
        response = yield self.scpd_requester.scpd_post_soap(self, **kwargs)
        try:
            result = self._process_result(*response)
        except Exception as err:
            log.error("error formatting response (%s):\n%s", err, response)
            raise err
        defer.returnValue(result)
