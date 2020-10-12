import re
import logging
import typing
import asyncio
from typing import Dict, List, Optional
from aioupnp.util import get_dict_val_case_insensitive
from aioupnp.constants import SPEC_VERSION, SERVICE
from aioupnp.commands import SOAPCommands
from aioupnp.device import Device, Service
from aioupnp.protocols.ssdp import m_search, multi_m_search
from aioupnp.protocols.scpd import scpd_get
from aioupnp.serialization.ssdp import SSDPDatagram
from aioupnp.util import flatten_keys
from aioupnp.fault import UPnPError

log = logging.getLogger(__name__)

BASE_ADDRESS_REGEX = re.compile("^(http:\/\/\d*\.\d*\.\d*\.\d*:\d*)\/.*$".encode())
BASE_PORT_REGEX = re.compile("^http:\/\/\d*\.\d*\.\d*\.\d*:(\d*)\/.*$".encode())


def get_action_list(element_dict: typing.Dict[str, typing.Union[str, typing.Dict[str, str],
                                                                typing.List[typing.Dict[str, typing.Dict[str, str]]]]]
                    ) -> typing.List[typing.Tuple[str, typing.List[str], typing.List[str]]]:
    service_info = flatten_keys(element_dict, "{%s}" % SERVICE)
    result: typing.List[typing.Tuple[str, typing.List[str], typing.List[str]]] = []
    if "actionList" in service_info:
        action_list = service_info["actionList"]
    else:
        return result
    if not len(action_list):  # it could be an empty string
        return result

    action = action_list["action"]
    if isinstance(action, dict):
        arg_dicts: typing.List[typing.Dict[str, str]] = []
        if not isinstance(action['argumentList']['argument'], list):  # when there is one arg
            arg_dicts.extend([action['argumentList']['argument']])
        else:
            arg_dicts.extend(action['argumentList']['argument'])

        result.append((action_list["action"]['name'], [i['name'] for i in arg_dicts if i['direction'] == 'in'],
                       [i['name'] for i in arg_dicts if i['direction'] == 'out']))
        return result
    assert isinstance(action, list)
    for _action in action:
        if not _action.get('argumentList'):
            result.append((_action['name'], [], []))
        else:
            if not isinstance(_action['argumentList']['argument'], list):  # when there is one arg
                arg_dicts = [_action['argumentList']['argument']]
            else:
                arg_dicts = _action['argumentList']['argument']
            result.append((
                _action['name'],
                [i['name'] for i in arg_dicts if i['direction'] == 'in'],
                [i['name'] for i in arg_dicts if i['direction'] == 'out']
            ))
    return result


def parse_location(location: bytes) -> typing.Tuple[bytes, int]:
    base_address_result: typing.List[bytes] = BASE_ADDRESS_REGEX.findall(location)
    base_address = base_address_result[0]
    port_result: typing.List[bytes] = BASE_PORT_REGEX.findall(location)
    port = int(port_result[0])
    return base_address, port


class Gateway:
    def __init__(self, ok_packet: SSDPDatagram, lan_address: str, gateway_address: str,
                 loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self._loop = loop or asyncio.get_event_loop()
        self._ok_packet = ok_packet
        self._lan_address = lan_address
        self.usn: bytes = (ok_packet.usn or '').encode()
        self.ext: bytes = (ok_packet.ext or '').encode()
        self.server: bytes = (ok_packet.server or '').encode()
        self.location: bytes = (ok_packet.location or '').encode()
        self.cache_control: bytes = (ok_packet.cache_control or '').encode()
        self.date: bytes = (ok_packet.date or '').encode()
        self.urn: bytes = (ok_packet.st or '').encode()

        self._xml_response: bytes = b""
        self._service_descriptors: Dict[str, str] = {}

        self.base_address, self.port = parse_location(self.location)
        self.base_ip = self.base_address.lstrip(b"http://").split(b":")[0]
        assert self.base_ip == gateway_address.encode()
        self.path = self.location.split(b"%s:%i/" % (self.base_ip, self.port))[1]

        self.spec_version: Optional[str] = None
        self.url_base: Optional[str] = None

        self._device: Optional[Device] = None
        self._devices: List[Device] = []
        self._services: List[Service] = []

        self._unsupported_actions: Dict[str, typing.List[str]] = {}
        self._registered_commands: Dict[str, str] = {}
        self.commands = SOAPCommands(self._loop, self.base_ip, self.port)

    @property
    def manufacturer_string(self) -> str:
        manufacturer_string = "UNKNOWN GATEWAY"
        if self.devices:
            devices: typing.List[Device] = list(self.devices.values())
            device = devices[0]
            manufacturer_string = f"{device.manufacturer} {device.modelName}"
        return manufacturer_string

    @property
    def services(self) -> Dict[str, Service]:
        services: Dict[str, Service] = {}
        if self._services:
            for service in self._services:
                if service.serviceType is not None:
                    services[service.serviceType] = service
        return services

    @property
    def devices(self) -> Dict[str, Device]:
        devices: Dict[str, Device] = {}
        if self._device:
            for device in self._devices:
                if device.udn is not None:
                    devices[device.udn] = device
        return devices

    # def get_service(self, service_type: str) -> Optional[Service]:
    #     for service in self._services:
    #         if service.serviceType and service.serviceType.lower() == service_type.lower():
    #             return service
    #     return None

    def debug_gateway(self) -> Dict[str, typing.Union[str, bytes, int, Dict, List]]:
        return {
            'manufacturer_string': self.manufacturer_string,
            'gateway_address': self.base_ip.decode(),
            'server': self.server.decode(),
            'urlBase': self.url_base or '',
            'location': self.location.decode(),
            "specVersion": self.spec_version or '',
            'usn': self.usn.decode(),
            'urn': self.urn.decode(),
            'gateway_xml': self._xml_response.decode(),
            'services_xml': self._service_descriptors,
            'services': {service.SCPDURL: service.as_dict() for service in self._services},
            'reply': self._ok_packet.as_dict(),
            'soap_port': self.port,
            'registered_soap_commands': self._registered_commands,
            'unsupported_soap_commands': self._unsupported_actions,
            'soap_requests': list(self.commands._request_debug_infos)
        }

    @classmethod
    async def _try_gateway_from_ssdp(cls, datagram: SSDPDatagram, lan_address: str,
                                     gateway_address: str,
                                     loop: Optional[asyncio.AbstractEventLoop] = None) -> Optional['Gateway']:
        required_commands: typing.List[str] = [
            'AddPortMapping',
            'DeletePortMapping',
            'GetExternalIPAddress'
        ]
        try:
            gateway = cls(datagram, lan_address, gateway_address, loop=loop)
            log.debug('get gateway descriptor %s', datagram.location)
            await gateway.discover_commands()
            requirements_met = all([gateway.commands.is_registered(required) for required in required_commands])
            if not requirements_met:
                not_met = [
                    required for required in required_commands if not gateway.commands.is_registered(required)
                ]
                assert datagram.location is not None
                log.debug("found gateway %s at %s, but it does not implement required soap commands: %s",
                          gateway.manufacturer_string, gateway.location, not_met)
                return None
            else:
                log.debug('found gateway %s at %s', gateway.manufacturer_string or "device", datagram.location)
                return gateway
        except (asyncio.TimeoutError, UPnPError) as err:
            assert datagram.location is not None
            log.debug("get %s failed (%s), looking for other devices", datagram.location, str(err))
            return None

    @classmethod
    async def _gateway_from_igd_args(cls, lan_address: str, gateway_address: str,
                                     igd_args: typing.Dict[str, typing.Union[int, str]],
                                     timeout: int = 30,
                                     loop: Optional[asyncio.AbstractEventLoop] = None) -> 'Gateway':
        datagram = await m_search(lan_address, gateway_address, igd_args, timeout, loop)
        gateway = await cls._try_gateway_from_ssdp(datagram, lan_address, gateway_address, loop)
        if not gateway:
            raise UPnPError("no gateway found for given args")
        return gateway

    @classmethod
    async def _discover_gateway(cls, lan_address: str, gateway_address: str, timeout: int = 3,
                                loop: Optional[asyncio.AbstractEventLoop] = None) -> 'Gateway':
        ignored: typing.Set[str] = set()
        ssdp_proto = await multi_m_search(
            lan_address, gateway_address, timeout, loop
        )
        try:
            while True:
                datagram = await ssdp_proto.devices.get()
                if datagram.location in ignored:
                    continue
                gateway = await cls._try_gateway_from_ssdp(datagram, lan_address, gateway_address, loop)
                if gateway:
                    return gateway
                elif datagram.location:
                    ignored.add(datagram.location)
        finally:
            ssdp_proto.disconnect()

    @classmethod
    async def discover_gateway(cls, lan_address: str, gateway_address: str, timeout: int = 3,
                               igd_args: Optional[typing.Dict[str, typing.Union[int, str]]] = None,
                               loop: Optional[asyncio.AbstractEventLoop] = None) -> 'Gateway':
        loop = loop or asyncio.get_event_loop()
        if igd_args:
            return await cls._gateway_from_igd_args(lan_address, gateway_address, igd_args, timeout, loop)
        try:
            return await asyncio.wait_for(loop.create_task(
                cls._discover_gateway(lan_address, gateway_address, timeout, loop)
            ), timeout, loop=loop)
        except asyncio.TimeoutError:
            raise UPnPError(f"M-SEARCH for {gateway_address}:1900 timed out")

    async def discover_commands(self) -> None:
        response, xml_bytes, get_err = await scpd_get(
            self.path.decode(), self.base_ip.decode(), self.port, loop=self._loop
        )
        self._xml_response = xml_bytes
        if get_err is not None:
            raise get_err
        spec_version = get_dict_val_case_insensitive(response, SPEC_VERSION)
        if isinstance(spec_version, bytes):
            self.spec_version = spec_version.decode()
        else:
            self.spec_version = spec_version
        url_base = get_dict_val_case_insensitive(response, "urlbase")
        if isinstance(url_base, bytes):
            self.url_base = url_base.decode()
        else:
            self.url_base = url_base
        if not self.url_base:
            self.url_base = self.base_address.decode()
        if response:
            source_keys: typing.List[str] = list(response.keys())
            matches: typing.List[str] = list(filter(lambda x: x.lower() == "device", source_keys))
            match_key = matches[0]
            match: dict = response[match_key]
            # if not len(match):
            #     return None
            # if len(match) > 1:
            #     raise KeyError("overlapping keys")
            # if len(match) == 1:
            #     matched_key: typing.AnyStr = match[0]
            #     return source[matched_key]
            # raise KeyError("overlapping keys")

            self._device = Device(
                self._devices, self._services, **match
            )
        else:
            self._device = Device(self._devices, self._services)
        for service_type in self.services.keys():
            await self.register_commands(self.services[service_type], self._loop)
        return None

    async def register_commands(self, service: Service,
                                loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        if not service.SCPDURL:
            raise UPnPError("no scpd url")
        if not service.serviceType:
            raise UPnPError("no service type")

        log.debug("get descriptor for %s from %s", service.serviceType, service.SCPDURL)
        service_dict, xml_bytes, get_err = await scpd_get(service.SCPDURL, self.base_ip.decode(), self.port, loop=loop)
        self._service_descriptors[service.SCPDURL] = xml_bytes.decode()

        if get_err is not None:
            log.debug("failed to get descriptor for %s from %s", service.serviceType, service.SCPDURL)
            if xml_bytes:
                log.debug("response: %s", xml_bytes.decode())
            return None
        if not service_dict:
            return None

        action_list = get_action_list(service_dict)
        for name, inputs, outputs in action_list:
            try:
                self.commands.register(name, service, inputs, outputs)
                self._registered_commands[name] = service.serviceType
                log.debug("registered %s::%s", service.serviceType, name)
            except AttributeError:
                self._unsupported_actions.setdefault(service.serviceType, [])
                self._unsupported_actions[service.serviceType].append(name)
                log.debug("available command for %s does not have a wrapper implemented: %s %s %s",
                          service.serviceType, name, inputs, outputs)
            log.debug("registered service %s", service.serviceType)
        return None
