import logging
from twisted.internet import defer
import treq
import re
from xml.etree import ElementTree
from txupnp.util import etree_to_dict, flatten_keys, get_dict_val_case_insensitive
from txupnp.util import BASE_PORT_REGEX, BASE_ADDRESS_REGEX
from txupnp.constants import DEVICE, ROOT
from txupnp.constants import SPEC_VERSION

log = logging.getLogger(__name__)

service_type_pattern = re.compile(
    "(?i)(\{|(urn:schemas-[\w|\d]*-(com|org|net))[:|-](device|service)[:|-]([\w|\d|\:|\-|\_]*)|\})"
)

xml_root_sanity_pattern = re.compile(
    "(?i)(\{|(urn:schemas-[\w|\d]*-(com|org|net))[:|-](device|service)[:|-]([\w|\d|\:|\-|\_]*)|\}([\w|\d|\:|\-|\_]*))"
)


class CaseInsensitive(object):
    def __init__(self, **kwargs):
        not_evaluated = {}
        for k, v in kwargs.items():
            if k.startswith("_"):
                not_evaluated[k] = v
                continue
            try:
                getattr(self, k)
                setattr(self, k, v)
            except AttributeError as err:
                not_evaluated[k] = v
        if not_evaluated:
            log.debug("%s did not apply kwargs: %s", self.__class__.__name__, not_evaluated)

    def _get_attr_name(self, case_insensitive):
        for k, v in self.__dict__.items():
            if k.lower() == case_insensitive.lower():
                return k

    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        for k, v in self.__class__.__dict__.items():
            if k.lower() == item.lower():
                if k not in self.__dict__:
                    self.__dict__[k] = v
                return v
        raise AttributeError(item)

    def __setattr__(self, item, value):
        if item in self.__dict__:
            self.__dict__[item] = value
            return
        to_update = None
        for k, v in self.__dict__.items():
            if k.lower() == item.lower():
                to_update = k
                break
        self.__dict__[to_update or item] = value

    def as_dict(self):
        return {
            k: v for k, v in self.__dict__.items() if not k.startswith("_") and not callable(v)
        }


class Service(CaseInsensitive):
    serviceType = None
    serviceId = None
    controlURL = None
    eventSubURL = None
    SCPDURL = None


class Device(CaseInsensitive):
    serviceList = None
    deviceList = None
    deviceType = None
    friendlyName = None
    manufacturer = None
    manufacturerURL = None
    modelDescription = None
    modelName = None
    modelNumber = None
    modelURL = None
    serialNumber = None
    udn = None
    upc = None
    presentationURL = None
    iconList = None

    def __init__(self, devices, services, **kwargs):
        super(Device, self).__init__(**kwargs)
        if self.serviceList and "service" in self.serviceList:
            new_services = self.serviceList["service"]
            if isinstance(new_services, dict):
                new_services = [new_services]
            services.extend([Service(**service) for service in new_services])
        if self.deviceList:
            for kw in self.deviceList.values():
                if isinstance(kw, dict):
                    d = Device(devices, services, **kw)
                    devices.append(d)
                elif isinstance(kw, list):
                    for _inner_kw in kw:
                        d = Device(devices, services, **_inner_kw)
                        devices.append(d)
                else:
                    log.warning("failed to parse device:\n%s", kw)


class Gateway(object):
    def __init__(self, **kwargs):
        flattened = {
            k.lower(): v for k, v in kwargs.items()
        }
        usn = flattened["usn"]
        server = flattened["server"]
        location = flattened["location"]
        st = flattened["st"]

        cache_control = flattened.get("cache_control") or flattened.get("cache-control") or ""
        date = flattened.get("date", "")
        ext = flattened.get("ext", "")

        self.usn = usn.encode()
        self.ext = ext.encode()
        self.server = server.encode()
        self.location = location.encode()
        self.cache_control = cache_control.encode()
        self.date = date.encode()
        self.urn = st.encode()

        self.base_address = BASE_ADDRESS_REGEX.findall(self.location)[0]
        self.port = int(BASE_PORT_REGEX.findall(self.location)[0])
        self.xml_response = None
        self.spec_version = None
        self.url_base = None

        self._device = None
        self._devices = []
        self._services = []

    def debug_device(self, include_xml=False, include_services=True):
        r = {
            'server': self.server,
            'urlBase': self.url_base,
            'location': self.location,
            "specVersion": self.spec_version,
            'usn': self.usn,
            'urn': self.urn,
            'devices': [device.as_dict() for device in self._devices]
        }
        if include_xml:
            r['xml_response'] = self.xml_response
        if include_services:
            r['services'] = [service.as_dict() for service in self._services]

        return r

    @defer.inlineCallbacks
    def discover_services(self):
        log.debug("querying %s", self.location)
        response = yield treq.get(self.location)
        self.xml_response = yield response.content()
        if not self.xml_response:
            log.warning("service sent an empty reply\n%s", self.debug_device())
        xml_dict = etree_to_dict(ElementTree.fromstring(self.xml_response))
        schema_key = DEVICE
        root = ROOT
        if len(xml_dict) > 1:
            log.warning(xml_dict.keys())
        for k in xml_dict.keys():
            m = xml_root_sanity_pattern.findall(k)
            if len(m) == 3 and m[1][0] and m[2][5]:
                schema_key = m[1][0]
                root = m[2][5]
                break

        flattened_xml = flatten_keys(xml_dict, "{%s}" % schema_key)[root]
        self.spec_version = get_dict_val_case_insensitive(flattened_xml, SPEC_VERSION)
        self.url_base = get_dict_val_case_insensitive(flattened_xml, "urlbase")

        if flattened_xml:
            self._device = Device(
                self._devices, self._services, **get_dict_val_case_insensitive(flattened_xml, "device")
            )
            log.debug("finished setting up root gateway. %i devices and %i services", len(self.devices),
                          len(self.services))
        else:
            self._device = Device(self._devices, self._services)
        log.debug("finished setting up gateway:\n%s", self.debug_device())

    @property
    def services(self):
        if not self._device:
            return {}
        return {service.serviceType: service for service in self._services}

    @property
    def devices(self):
        if not self._device:
            return {}
        return {device.udn: device for device in self._devices}

    def get_service(self, service_type):
        for service in self._services:
            if service.serviceType.lower() == service_type.lower():
                return service
