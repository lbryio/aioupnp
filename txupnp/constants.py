POST = "POST"
XML_VERSION = "<?xml version=\"1.0\"?>"
FAULT = "{http://schemas.xmlsoap.org/soap/envelope/}Fault"
ENVELOPE = "{http://schemas.xmlsoap.org/soap/envelope/}Envelope"
BODY = "{http://schemas.xmlsoap.org/soap/envelope/}Body"
SOAP_ENCODING = "http://schemas.xmlsoap.org/soap/encoding/"
SOAP_ENVELOPE = "http://schemas.xmlsoap.org/soap/envelope"
CONTROL_KEY = 'urn:schemas-upnp-org:control-1-0'
SERVICE_KEY = 'urn:schemas-upnp-org:service-1-0'
GATEWAY_SCHEMA = 'urn:schemas-upnp-org:device:InternetGatewayDevice:1'
WAN_INTERFACE_KEY = 'urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1'
LAYER_FORWARD_KEY = 'urn:schemas-upnp-org:service:Layer3Forwarding:1'
WAN_IP_KEY = 'urn:schemas-upnp-org:service:WANIPConnection:1'

SSDP_IP_ADDRESS = '239.255.255.250'
SSDP_PORT = 1900
SSDP_DISCOVER = "ssdp:discover"
M_SEARCH_TEMPLATE = "\r\n".join([
    "M-SEARCH * HTTP/1.1",
    "HOST: {}:{}",
    "ST: {}",
    "MAN: \"{}\"",
    "MX: {}\r\n\r\n",
])
