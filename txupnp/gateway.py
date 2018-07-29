import json
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

    def get_info(self):
        return {
            "service_type": self.service_type,
            "service_id": self.service_id,
            "control_path": self.control_path,
            "subscribe_path": self.subscribe_path,
            "scpd_path": self.scpd_path
        }


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

    def get_info(self):
        return {
            'device_type': self.device_type,
            'friendly_name': self.friendly_name,
            'manufacturers': self.manufacturer,
            'model_name': self.model_name,
            'model_number': self.model_number,
            'serial_number': self.serial_number,
            'udn': self.udn
        }


class RootDevice(object):
    def __init__(self, xml_string):
        try:
            root = flatten_keys(etree_to_dict(ElementTree.fromstring(xml_string)), "{%s}" % DEVICE)[ROOT]
        except Exception as err:
            if xml_string:
                log.exception("failed to decode xml: %s\n%s", err, xml_string)
            root = {}
        self.spec_version = root.get(SPEC_VERSION)
        self.url_base = root.get("URLBase")
        self.devices = []
        self.services = []
        if root:
            root_device = Device(self, **(root["device"]))
            self.devices.append(root_device)
            log.info("finished setting up root gateway. %i devices and %i services", len(self.devices), len(self.services))


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

    def debug_device(self):
        def default_byte(x):
            if isinstance(x, bytes):
                return x.decode()
            return x

        devices = []
        for device in self._device.devices:
            info = device.get_info()
            devices.append(info)
        services = []
        for service in self._device.services:
            info = service.get_info()
            services.append(info)
        return json.dumps({
            'root_url': self.base_address,
            'gateway_xml_url': self.location,
            'usn': self.usn,
            'devices': devices,
            'services': services
        }, indent=2, default=default_byte)

    @defer.inlineCallbacks
    def discover_services(self):
        log.info("querying %s", self.location)
        response = yield treq.get(self.location)
        response_xml = yield response.content()
        if not response_xml:
            log.error("service sent an empty reply\n%s", self.debug_device())
        try:
            self._device = RootDevice(response_xml)
        except Exception as err:
            log.error("error parsing gateway: %s\n%s\n\n%s", err, self.debug_device(), response_xml)
            self._device = RootDevice("")
        log.debug("finished setting up gateway:\n%s", self.debug_device())

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
