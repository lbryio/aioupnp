POST = "POST"
ROOT = "root"
SPEC_VERSION = "specVersion"
XML_VERSION = "<?xml version=\"1.0\"?>"
FAULT = "{http://schemas.xmlsoap.org/soap/envelope/}Fault"
ENVELOPE = "{http://schemas.xmlsoap.org/soap/envelope/}Envelope"
BODY = "{http://schemas.xmlsoap.org/soap/envelope/}Body"


CONTROL = 'urn:schemas-upnp-org:control-1-0'
SERVICE = 'urn:schemas-upnp-org:service-1-0'
DEVICE = 'urn:schemas-upnp-org:device-1-0'

WIFI_ALLIANCE_ORG_IGD = "urn:schemas-wifialliance-org:device:WFADevice:1"
UPNP_ORG_IGD = 'urn:schemas-upnp-org:device:InternetGatewayDevice:1'

WAN_SCHEMA = 'urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1'
LAYER_SCHEMA = 'urn:schemas-upnp-org:service:Layer3Forwarding:1'
IP_SCHEMA = 'urn:schemas-upnp-org:service:WANIPConnection:1'

SSDP_IP_ADDRESS = '239.255.255.250'
SSDP_PORT = 1900
SSDP_HOST = "%s:%i" % (SSDP_IP_ADDRESS, SSDP_PORT)
SSDP_DISCOVER = "ssdp:discover"
line_separator = "\r\n"
