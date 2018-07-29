import binascii
import logging
from twisted.internet import defer
import treq
from xml.etree import ElementTree
from txupnp.util import etree_to_dict, flatten_keys
from txupnp.util import BASE_PORT_REGEX, BASE_ADDRESS_REGEX
from txupnp.constants import DEVICE, ROOT
from txupnp.constants import SPEC_VERSION

log = logging.getLogger(__name__)


class Service(object):
    def __init__(self, serviceType, serviceId, SCPDURL, eventSubURL, controlURL):
        self.service_type = serviceType
        self.service_id = serviceId
        self.control_path = controlURL
        self.subscribe_path = eventSubURL
        self.scpd_path = SCPDURL


class Device(object):
    def __init__(self, _root_device, deviceType=None, friendlyName=None, manufacturer=None, manufacturerURL=None,
                 modelDescription=None, modelName=None, modelNumber=None, modelURL=None, serialNumber=None,
                 UDN=None, serviceList=None, deviceList=None, **kwargs):
        serviceList = serviceList or {}
        deviceList = deviceList or {}
        self._root_device = _root_device
        self.device_type = deviceType
        self.friendly_name = friendlyName
        self.manufacturer = manufacturer
        self.manufacturer_url = manufacturerURL
        self.model_description = modelDescription
        self.model_name = modelName
        self.model_number = modelNumber
        self.model_url = modelURL
        self.serial_number = serialNumber
        self.udn = UDN
        services = serviceList["service"]
        if isinstance(services, dict):
            services = [services]
        services = [Service(**service) for service in services]
        self._root_device.services.extend(services)
        devices = [Device(self._root_device, **deviceList[k]) for k in deviceList]
        self._root_device.devices.extend(devices)


class RootDevice(object):
    def __init__(self, xml_string):
        try:
            root = flatten_keys(etree_to_dict(ElementTree.fromstring(xml_string)), "{%s}" % DEVICE)[ROOT]
        except Exception as err:
            log.exception("failed to decode xml: %s\n%s", err, xml_string)
            root = {}
        self.spec_version = root.get(SPEC_VERSION)
        self.url_base = root.get("URLBase")
        self.devices = []
        self.services = []
        if root:
            root_device = Device(self, **(root["device"]))
            self.devices.append(root_device)
            log.info("finished setting up root device. %i devices and %i services", len(self.devices), len(self.services))


class Gateway(object):
    def __init__(self, usn, server, location, st, cache_control="", date="", ext=""):
        self.usn = usn.encode()
        self.ext = ext.encode()
        self.server = server.encode()
        self.location = location.encode()
        self.cache_control = cache_control.encode()
        self.date = date.encode()
        self.urn = st.encode()
        self.base_address = BASE_ADDRESS_REGEX.findall(self.location)[0]
        self.port = int(BASE_PORT_REGEX.findall(self.location)[0])
        self._device = None

    @defer.inlineCallbacks
    def discover_services(self):
        log.info("querying %s", self.location)
        response = yield treq.get(self.location)
        response_xml = yield response.content()
        self._device = RootDevice(response_xml)
        if not self._device.devices or not self._device.services:
            log.error("failed to parse device: \n%s", response_xml)

    @property
    def services(self):
        if not self._device:
            return {}
        return {service.service_type: service for service in self._device.services}

    @property
    def devices(self):
        if not self._device:
            return {}
        return {device.udn: device for device in self._device.devices}

    def get_service(self, service_type):
        for service in self._device.services:
            if service.service_type.lower() == service_type.lower():
                return service
