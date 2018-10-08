import logging
from aioupnp.util import get_dict_val_case_insensitive, BASE_PORT_REGEX, BASE_ADDRESS_REGEX
from aioupnp.constants import SPEC_VERSION, UPNP_ORG_IGD, SERVICE
from aioupnp.commands import SCPDCommands
from aioupnp.device import Device, Service
from aioupnp.protocols.ssdp import m_search
from aioupnp.protocols.scpd import scpd_get
from aioupnp.protocols.soap import SCPDCommand
from aioupnp.util import flatten_keys

log = logging.getLogger(__name__)


def get_action_list(element_dict: dict) -> list:  # [(<method>, [<input1>, ...], [<output1, ...]), ...]
    service_info = flatten_keys(element_dict, "{%s}" % SERVICE)
    if "actionList" in service_info:
        action_list = service_info["actionList"]
    else:
        return []
    if not len(action_list):  # it could be an empty string
        return []

    result = []
    if isinstance(action_list["action"], dict):
        arg_dicts = action_list["action"]['argumentList']['argument']
        if not isinstance(arg_dicts, list):  # when there is one arg
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
            if not isinstance(arg_dicts, list):  # when there is one arg
                arg_dicts = [arg_dicts]
            result.append((
                action['name'],
                [i['name'] for i in arg_dicts if i['direction'] == 'in'],
                [i['name'] for i in arg_dicts if i['direction'] == 'out']
            ))
    return result


class Gateway:
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

        self._xml_response = ""
        self._service_descriptors = {}
        self.base_address = BASE_ADDRESS_REGEX.findall(self.location)[0]
        self.port = int(BASE_PORT_REGEX.findall(self.location)[0])
        self.base_ip = self.base_address.lstrip(b"http://").split(b":")[0]
        self.path = self.location.split(b"%s:%i/" % (self.base_ip, self.port))[1]

        self.spec_version = None
        self.url_base = None

        self._device = None
        self._devices = []
        self._services = []

        self._unsupported_actions = {}
        self._registered_commands = {}
        self.commands = SCPDCommands()

    def gateway_descriptor(self) -> dict:
        r = {
            'server': self.server.decode(),
            'urlBase': self.url_base,
            'location': self.location.decode(),
            "specVersion": self.spec_version,
            'usn': self.usn.decode(),
            'urn': self.urn.decode(),
        }
        return r

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

    @classmethod
    async def discover_gateway(cls, lan_address: str, gateway_address: str, timeout: int = 1,
                               service: str = UPNP_ORG_IGD):
        datagram = await m_search(lan_address, gateway_address, timeout, service)
        gateway = cls(**datagram.as_dict())
        await gateway.discover_commands()
        return gateway

    async def discover_commands(self):
        response = await scpd_get("/" + self.path.decode(), self.base_ip.decode(), self.port)

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
            await self.register_commands(self.services[service_type])

    async def register_commands(self, service: Service):
        service_dict = await scpd_get(("" if service.SCPDURL.startswith("/") else "/") + service.SCPDURL,
                                      self.base_ip.decode(), self.port)
        if not service_dict:
            return

        action_list = get_action_list(service_dict)

        for name, inputs, outputs in action_list:
            try:
                current = getattr(self.commands, name)
                annotations = current.__annotations__
                return_types = annotations.get('return', None)
                if return_types:
                    if not isinstance(return_types, tuple):
                        return_types = (return_types, )
                    return_types = {r: t for r, t in zip(outputs, return_types)}
                param_types = {}
                for param_name, param_type in annotations.items():
                    if param_name == "return":
                        continue
                    param_types[param_name] = param_type
                command = SCPDCommand(
                    self.base_ip.decode(), self.port, service.controlURL, service.serviceType.encode(),
                    name, param_types, return_types, inputs, outputs)
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
