import logging
from twisted.internet import defer
from txupnp.scpd import SCPDCommand, SCPDRequester
from txupnp.util import get_dict_val_case_insensitive, verify_return_types, BASE_PORT_REGEX, BASE_ADDRESS_REGEX
from txupnp.constants import SPEC_VERSION
from txupnp.commands import SCPDCommands

log = logging.getLogger(__name__)


class CaseInsensitive:
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

    def _get_attr_name(self, case_insensitive: str) -> str:
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

    def as_dict(self) -> dict:
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


class Gateway:
    def __init__(self, reactor, **kwargs):
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

        self._xml_response = ""
        self._service_descriptors = {}
        self.base_address = BASE_ADDRESS_REGEX.findall(self.location)[0]
        self.port = int(BASE_PORT_REGEX.findall(self.location)[0])
        self.spec_version = None
        self.url_base = None

        self._device = None
        self._devices = []
        self._services = []

        self._reactor = reactor
        self._unsupported_actions = {}
        self._registered_commands = {}
        self.commands = SCPDCommands()
        self.requester = SCPDRequester(self._reactor)

    def as_dict(self) -> dict:
        r = {
            'server': self.server.decode(),
            'urlBase': self.url_base,
            'location': self.location.decode(),
            "specVersion": self.spec_version,
            'usn': self.usn.decode(),
            'urn': self.urn.decode(),
        }
        return r

    @defer.inlineCallbacks
    def discover_commands(self):
        response = yield self.requester.scpd_get(self.location.decode().split(self.base_address.decode())[1], self.base_address.decode(), self.port)
        self.spec_version = get_dict_val_case_insensitive(response, SPEC_VERSION)
        self.url_base = get_dict_val_case_insensitive(response, "urlbase")
        if not self.url_base:
            self.url_base = self.base_address.decode()
        if response:
            self._device = Device(
                self._devices, self._services, **get_dict_val_case_insensitive(response, "device")
            )
        else:
            self._device = Device(self._devices, self._services)
        for service_type in self.services.keys():
            service = self.services[service_type]
            yield self.register_commands(service)

    @defer.inlineCallbacks
    def register_commands(self, service: Service):
        try:
            action_list = yield self.requester.scpd_get_supported_actions(service, self.base_address.decode(), self.port)
        except Exception as err:
            log.exception("failed to register service %s: %s", service.serviceType, str(err))
            return
        for name, inputs, outputs in action_list:
            try:
                command = SCPDCommand(self.requester, self.base_address, self.port,
                                      service.controlURL.encode(),
                                      service.serviceType.encode(), name, inputs, outputs)
                current = getattr(self.commands, command.method)
                if hasattr(current, "_return_types"):
                    command._process_result = verify_return_types(*current._return_types)(command._process_result)
                setattr(command, "__doc__", current.__doc__)
                setattr(self.commands, command.method, command)
                self._registered_commands[command.method] = service.serviceType
                log.debug("registered %s::%s", service.serviceType, command.method)
            except AttributeError:
                s = self._unsupported_actions.get(service.serviceType, [])
                s.append(name)
                self._unsupported_actions[service.serviceType] = s
                log.debug("available command for %s does not have a wrapper implemented: %s %s %s",
                          service.serviceType, name, inputs, outputs)

    @property
    def services(self) -> dict:
        if not self._device:
            return {}
        return {service.serviceType: service for service in self._services}

    @property
    def devices(self) -> dict:
        if not self._device:
            return {}
        return {device.udn: device for device in self._devices}

    def get_service(self, service_type: str) -> Service:
        for service in self._services:
            if service.serviceType.lower() == service_type.lower():
                return service

    def debug_commands(self):
        return {
            'available': self._registered_commands,
            'failed': self._unsupported_actions
        }
