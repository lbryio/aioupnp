POST: str = "POST"
ROOT: str = "root"
SPEC_VERSION: str = "specVersion"
XML_VERSION: str = "<?xml version=\"1.0\"?>"
FAULT: str = "{http://schemas.xmlsoap.org/soap/envelope/}Fault"
ENVELOPE: str = "{http://schemas.xmlsoap.org/soap/envelope/}Envelope"
BODY: str = "{http://schemas.xmlsoap.org/soap/envelope/}Body"

CONTROL: str = "urn:schemas-upnp-org:control-1-0"
SERVICE: str = "urn:schemas-upnp-org:service-1-0"
DEVICE: str = "urn:schemas-upnp-org:device-1-0"

WIFI_ALLIANCE_ORG_IGD: str = "urn:schemas-wifialliance-org:device:WFADevice:1"
UPNP_ORG_IGD: str = "urn:schemas-upnp-org:device:InternetGatewayDevice:1"

WAN_SCHEMA: str = "urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1"
LAYER_SCHEMA: str = "urn:schemas-upnp-org:service:Layer3Forwarding:1"
IP_SCHEMA: str = "urn:schemas-upnp-org:service:WANIPConnection:1"

SSDP_IP_ADDRESS: str = "239.255.255.250"
SSDP_PORT: int = 1900
SSDP_HOST: str = "%s:%i" % (SSDP_IP_ADDRESS, SSDP_PORT)
SSDP_DISCOVER: str = "ssdp:discover"
line_separator: str = "\r\n"
