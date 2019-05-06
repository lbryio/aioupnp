import logging
from typing import Dict, List, Union, Type, Any, Optional, Set, Tuple, TYPE_CHECKING, NoReturn, Awaitable, Mapping
import asyncio
if TYPE_CHECKING:
    from asyncio import AbstractEventLoop, TimeoutError
    from collections import OrderedDict

from aioupnp.util import get_dict_val_case_insensitive, BASE_PORT_REGEX, BASE_ADDRESS_REGEX
from aioupnp.constants import SPEC_VERSION, SERVICE
from aioupnp.commands import SOAPCommands
from aioupnp.device import Device, Service
from aioupnp.protocols.ssdp import fuzzy_m_search, m_search
from aioupnp.protocols.scpd import scpd_get
from aioupnp.serialization.ssdp import SSDPDatagram
from aioupnp.util import flatten_keys
from aioupnp.fault import UPnPError

log = logging.getLogger(__name__)

return_type_lambas: Mapping[Type, str] = {
    Union[None, str]: lambda x: x if x is not None and str(x).lower() not in ["none", "nil"] else None
}


def get_action_list(element_dict: OrderedDict) -> List:
    """Get Action List.

    :param element_dict:
    :return:
    """
    # [(<method>, [<input1>, ...], [<output1, ...]), ...]
    service_info = flatten_keys(element_dict[0], "{%s}" % SERVICE)
    if "actionList" in service_info:
        action_list = service_info["actionList"]
    else:
        return []
    if not len(action_list):  # it could be an empty string
        return []

    result: list = []
    if isinstance(action_list[0]["action"], Dict):
        arg_dicts = action_list[0]["action"]['argumentList']['argument']
        if not isinstance(arg_dicts, List):  # when there is one arg
            arg_dicts = [arg_dicts]
        return [[
            action_list[0]["action"]['name'],
            [i[0]['name'] for i in arg_dicts if i[0]['direction'] == 'in'],
            [i[0]['name'] for i in arg_dicts if i[0]['direction'] == 'out']
        ]]
    for action in action_list[0]["action"]:
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
    """Gateway."""

    def __init__(self, ok_packet: SSDPDatagram, m_search_args: OrderedDict,
                 lan_address: str, gateway_address: str) -> None:
        """Gateway object.

        :param ok_packet:
        :param m_search_args:
        :param lan_address:
        :param gateway_address:
        """
        self._ok_packet: SSDPDatagram = ok_packet
        self._m_search_args: OrderedDict = m_search_args
        self._lan_address: str = lan_address
        self.usn: bytes = (ok_packet.usn or '').encode()
        self.ext: bytes = (ok_packet.ext or '').encode()
        self.server: bytes = (ok_packet.server or '').encode()
        self.location: bytes = (ok_packet.location or '').encode()
        self.cache_control: bytes = (ok_packet.cache_control or '').encode()
        self.date: bytes = (ok_packet.date or '').encode()
        self.urn: bytes = (ok_packet.st or '').encode()

        self._xml_response: bytes = b''
        self._service_descriptors: Mapping[str, Any] = {}
        self.base_address: bytes = BASE_ADDRESS_REGEX.findall(self.location)[0]
        self.port: int = int(BASE_PORT_REGEX.findall(self.location)[0])
        self.base_ip: bytes = self.base_address.lstrip(b'http://').split(b':')[0]
        assert self.base_ip == gateway_address.encode(), print(f'base ip = {self.base_ip} = {gateway_address.encode()}')
        self.path: bytes = self.location.split(b'%s:%i/' % (self.base_ip, self.port))[1]

        self.spec_version: Optional[str] = None
        self.url_base: Optional[str] = None

        self._device: Optional[Device] = None
        self._devices: List[Device] = []
        self._services: List[Service] = []

        self._unsupported_actions: Mapping[str, Any] = {}
        self._registered_commands: Mapping[str, Any] = {}
        self.commands = SOAPCommands()

    def gateway_descriptor(self) -> Mapping[str, str]:
        """Gateway Descriptor.

        :return: dict
        """
        return {
            'server': self.server.decode(),
            'urlBase': self.url_base,
            'location': self.location.decode(),
            'specVersion': self.spec_version,
            'usn': self.usn.decode(),
            'urn': self.urn.decode(),
        }

    @property
    async def manufacturer_string(self) -> str:
        """Manufacturer string.

        :return str: Manufacturer string.
        """
        if not self.devices:
            return "UNKNOWN GATEWAY"
        device = await asyncio.gather(getattr(self.devices, "values")[0])
        return "%s %s" % (device.manufacturer, device.modelName)

    @property
    def services(self) -> Mapping[Type[Service], Service]:
        """Services.

        :return dict: Services.
        """
        if not self._device:
            return {}
        return {service.serviceType: service for service in self._services}

    @property
    async def devices(self) -> Mapping[Type[Device], Device]:
        """Devices

        :return dict: Devices.
        """
        if not self._device:
            return {}
        return {device.udn: device for device in self._devices}

    def get_service(self, service_type: str) -> Union[Service, None]:
        for service in self._services:
            if service.serviceType.lower() is service_type.lower():
                return service
        return None

    @property
    async def soap_requests(self) -> Awaitable[List]:
        soap_call_infos = []
        for name in self._registered_commands.keys():
            if not hasattr(getattr(self.commands, name), "_requests"):
                continue
            soap_call_infos.extend([
                (name, request_args, raw_response, decoded_response, soap_error, ts)
                for (
                    request_args, raw_response, decoded_response, soap_error, ts
                ) in getattr((self.commands, name), "_requests")
            ])
        return await soap_call_infos.sort(key=lambda x: x[5])

    def debug_gateway(self) -> Dict[str, Union[int, str, OrderedDict, List]]:
        return {
            'manufacturer_string': self.manufacturer_string,
            'gateway_address': self.base_ip,
            'gateway_descriptor': self.gateway_descriptor(),
            'gateway_xml': self._xml_response,
            'services_xml': self._service_descriptors,
            'services': {service.SCPDURL: service.as_dict() for service in self._services},
            'm_search_args': [(k, v) for (k, v) in self._m_search_args.items()],
            'reply': self._ok_packet.as_dict(),
            'soap_port': self.port,
            'registered_soap_commands': self._registered_commands,
            'unsupported_soap_commands': self._unsupported_actions,
            'soap_requests': self.soap_requests
        }

    @classmethod
    async def _discover_gateway(cls, lan_address: str, gateway_address: str, timeout: Optional[float] = 30.0,
                                igd_args: Optional[OrderedDict] = None, loop: Optional[AbstractEventLoop] = None,
                                unicast: Optional[bool] = False) -> Optional[__class__]:
        ignored: Set[Any] = set()
        required_commands: List[str] = ["AddPortMapping", "DeletePortMapping", "GetExternalIPAddress"]
        while True:
            if not igd_args:
                m_search_args, datagram = await fuzzy_m_search(
                    lan_address, gateway_address, timeout, loop,  ignored, unicast
                )
            else:
                m_search_args = OrderedDict(igd_args)
                datagram = await m_search(lan_address, gateway_address, igd_args, timeout, loop, ignored, unicast)
            try:
                gateway = cls(datagram, m_search_args, lan_address, gateway_address)
                log.debug("Got gateway descriptor: %s.", datagram.location)
                await gateway.discover_commands(loop)
                requirements_met = all([required in gateway._registered_commands for required in required_commands])
                if not requirements_met:
                    not_met = [
                        req for req in required_commands if req not in getattr(gateway, '_registered_commands')
                    ]
                    log.debug("Found gateway %s at: %s, however it does not implement required soap commands: %s.",
                              gateway.manufacturer_string, gateway.location, not_met)
                    ignored.add(datagram.location)
                    continue
                else:
                    log.debug("Found gateway device: %s.", datagram.location)
                    return gateway
            except (TimeoutError, UPnPError) as err:
                log.debug("Get %s failed: (%s), looking for other devices.", datagram.location, str(err))
                ignored.add(datagram.location)
                continue

    @classmethod
    async def discover_gateway(cls, lan_address: str, gateway_address: str, timeout: Optional[float] = 30.0,
                               igd_args: Optional[OrderedDict] = None, loop: Optional[AbstractEventLoop] = None,
                               unicast: Optional[bool] = None) -> Union[__class__, Awaitable[__class__]]:
        if unicast is not None:
            return await cls._discover_gateway(lan_address, gateway_address, timeout, igd_args, loop, unicast)

        done, pending = await asyncio.wait([
            cls._discover_gateway(
                lan_address, gateway_address, timeout, igd_args, loop, unicast=True
            ),
            cls._discover_gateway(
                lan_address, gateway_address, timeout, igd_args, loop, unicast=False
            )
        ], return_when=asyncio.tasks.FIRST_COMPLETED)

        for task in pending:
            task.cancel()
        for task in done:
            try:
                task.exception()
            except asyncio.CancelledError:
                pass
        return list(done)[0].result()

    async def discover_commands(self, loop: Optional[AbstractEventLoop] = None) -> NoReturn[Optional[UPnPError]]:
        response, xml_bytes, get_err = await scpd_get(self.path.decode(), self.base_ip.decode(), self.port, loop=loop)
        self._xml_response = xml_bytes
        if get_err is not None:
            raise get_err
        self.spec_version = get_dict_val_case_insensitive(response, SPEC_VERSION)
        self.url_base = get_dict_val_case_insensitive(response, "urlbase")
        if not self.url_base:
            self.url_base = self.base_address.decode()
        if response:
            device_dict = get_dict_val_case_insensitive(response, "device")
            self._device = Device(self._devices, self._services, **device_dict)
        else:
            self._device = Device(self._devices, self._services)
        for service_type in self.services.keys():
            await self.register_commands(self.services[service_type], loop)

    async def register_commands(self, service: Service,
                                loop: Optional[AbstractEventLoop] = None) -> NoReturn[Optional[UPnPError]]:
        if not service.SCPDURL:
            raise UPnPError("No SCPD URL.")
        log.debug("Grabbing file descriptor for %s from: %s.", service.serviceType, service.SCPDURL)
        service_dict, xml_bytes, get_err = await scpd_get(service.SCPDURL, self.base_ip.decode(), self.port)
        setattr(self._service_descriptors, service.SCPDURL, xml_bytes)
        if get_err is not None:
            log.debug("Failed to fetch file descriptor for %s from: %s.", service.serviceType, service.SCPDURL)
            if xml_bytes:
                log.debug("Response: %s.", xml_bytes)
            return
        if not service_dict:
            return

        action_list: List[OrderedDict] = get_action_list(service_dict)

        for name, inputs, outputs in action_list:
            try:
                self.commands.register(self.base_ip, self.port, name, service.controlURL, service.serviceType.encode(),
                                       inputs, outputs, loop)
                setattr(self._registered_commands, 'name', service.serviceType)
                log.debug("Registered %s::%s.", service.serviceType, name)
            except AttributeError:
                s = self._unsupported_actions.get(service.serviceType, [])
                s.append(name)
                setattr(self._unsupported_actions, service.serviceType, s)
                log.debug("Available command for %s does not have a wrapper implemented: %s %s %s.",
                          service.serviceType, name, inputs, outputs)
            log.debug("Registered service: %s.", service.serviceType)
