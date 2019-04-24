import logging
import time
from typing import Any, Optional
from typing import Tuple, Union, List
from aioupnp.protocols.scpd import scpd_post
from asyncio import AbstractEventLoop

log = logging.getLogger(__name__)
none_or_str = Union[None, str]
return_type_lambas = {
    Union[None, str]: lambda x: x if x is not None and str(x).lower() not in ['none', 'nil'] else None
}


def safe_type(t: Any[tuple, list, dict, set]) -> Any[type, list, dict, set]:
    """Return input if type safe.

    :param t:
    :return:
    """
    if isinstance(t, Tuple):
        return tuple
    if isinstance(t, List):
        return list
    if isinstance(t, dict):
        return dict
    if isinstance(t, set):
        return set
    return t


class SOAPCommand:
    """SOAP Command."""

    def __init__(self, gateway_address: str, service_port: int, control_url: str, service_id: bytes, method: str,
                 param_types: dict, return_types: dict, param_order: list, return_order: list,
                 loop: Any[Optional[AbstractEventLoop], None] = None) -> None:
        """

        :param gateway_address:
        :param service_port:
        :param control_url:
        :param service_id:
        :param method:
        :param param_types:
        :param return_types:
        :param param_order:
        :param return_order:
        :param loop:
        """
        self.gateway_address: str = gateway_address
        self.service_port: int = service_port
        self.control_url: str = control_url
        self.service_id: bytes = service_id
        self.method: str = method
        self.param_types = param_types
        self.param_order = param_order
        self.return_types = return_types
        self.return_order = return_order
        self.loop: Any[AbstractEventLoop, None] = loop
        self._requests: list = []

    async def __call__(self, **kwargs) -> Union[None, dict, list, tuple]:
        """Supports Call.

        :param kwargs:
        :return:
        """
        if set(kwargs.keys()) != set(self.param_types.keys()):
            raise Exception("argument mismatch: %s vs %s" % (kwargs.keys(), self.param_types.keys()))
        soap_kwargs = {n: safe_type(self.param_types[n])(kwargs[n]) for n in self.param_types.keys()}
        response, xml_bytes, err = await scpd_post(
            self.control_url, self.gateway_address, self.service_port, self.method, self.param_order,
            self.service_id, self.loop, **soap_kwargs
        )
        if err is not None:
            self._requests.append((soap_kwargs, xml_bytes, None, err, time.time()))
            raise err
        if not response:
            result = None
        else:
            recast_result = tuple([safe_type(self.return_types[n])(response.get(n)) for n in self.return_order])
            if len(recast_result) == 1:
                result = recast_result[0]
            else:
                result = recast_result
        self._requests.append((soap_kwargs, xml_bytes, result, None, time.time()))
        return result


class SOAPCommands:
    """
    Type annotated wrappers for common UPnP SOAP functions

    A SOAPCommands object has its command attributes overridden during device discovery with SOAPCommand objects
    for the commands implemented by the gateway.

    SOAPCommand will use the typing annotations provided here to properly cast the types of arguments and results
    to their expected types.
    """

    SOAP_COMMANDS: List[str] = [
        'AddPortMapping',
        'GetNATRSIPStatus',
        'GetGenericPortMappingEntry',
        'GetSpecificPortMappingEntry',
        'SetConnectionType',
        'GetExternalIPAddress',
        'GetConnectionTypeInfo',
        'GetStatusInfo',
        'ForceTermination',
        'DeletePortMapping',
        'RequestConnection',
        'GetCommonLinkProperties',
        'GetTotalBytesSent',
        'GetTotalBytesReceived',
        'GetTotalPacketsSent',
        'GetTotalPacketsReceived',
        'X_GetICSStatistics',
        'GetDefaultConnectionService',
        'NewDefaultConnectionService',
        'NewEnabledForInternet',
        'SetDefaultConnectionService',
        'SetEnabledForInternet',
        'GetEnabledForInternet',
        'NewActiveConnectionIndex',
        'GetMaximumActiveConnections',
        'GetActiveConnections'
    ]

    def __init__(self):
        """SOAPCommand."""
        self._registered: set = set()

    def register(self, base_ip: bytes, port: int, name: str, control_url: str,
                 service_type: bytes, inputs: List, outputs: List,
                 loop: Any[Optional[AbstractEventLoop], None] = None) -> None:
        """Register Service.

        :param base_ip:
        :param port:
        :param name:
        :param control_url:
        :param service_type:
        :param inputs:
        :param outputs:
        :param loop:
        :return:
        """
        if name not in self.SOAP_COMMANDS or name in self._registered:
            raise AttributeError(name)
        current = getattr(self, name)
        annotations = current.__annotations__
        return_types = annotations.get('return', None)
        if return_types:
            if hasattr(return_types, '__args__'):
                return_types = tuple([return_type_lambas.get(a, a) for a in return_types.__args__])
            elif isinstance(return_types, type):
                return_types = (return_types,)
            return_types = {r: t for r, t in zip(outputs, return_types)}
        param_types = {}
        for param_name, param_type in annotations.items():
            if param_name == "return":
                continue
            param_types[param_name] = param_type
        command = SOAPCommand(
            base_ip.decode(), port, control_url, service_type,
            name, param_types, return_types, inputs, outputs, loop=loop
        )
        setattr(command, "__doc__", current.__doc__)
        setattr(self, command.method, command)
        self._registered.add(command.method)

    @staticmethod
    async def add_port_mapping(new_remote_host: str, new_external_port: int, new_protocol: str, new_internal_port: int,
                       new_internal_client: str, new_enabled: int, new_port_mapping_description: str,
                       new_lease_duration: str) -> Any:
        """Returns None"""
        raise NotImplementedError()

    AddPortMapping = add_port_mapping

    @staticmethod
    async def get_NATRSIP_status() -> Any:
        """Returns (NewRSIPAvailable, NewNATEnabled)"""
        raise NotImplementedError()

    GetNATRSIPStatus = get_NATRSIP_status

    @staticmethod
    async def get_generic_port_mapping_entry(new_port_mapping_index: int) -> Any:
        """
        Returns (NewRemoteHost, NewExternalPort, NewProtocol, NewInternalPort, NewInternalClient, NewEnabled,
                 NewPortMappingDescription, NewLeaseDuration)
        """
        raise NotImplementedError()

    GetGenericPortMappingEntry = get_generic_port_mapping_entry

    @staticmethod
    async def get_specific_port_mapping_entry(new_remote_host: str, new_external_port: int, new_protocol: str) -> Any:
        """Returns (NewInternalPort, NewInternalClient, NewEnabled, NewPortMappingDescription, NewLeaseDuration)"""
        raise NotImplementedError()

    GetSpecificPortMappingEntry = get_specific_port_mapping_entry

    @staticmethod
    async def set_connection_type(new_conn_type: str) -> Any:
        """Returns None"""
        raise NotImplementedError()

    SetConnectionType = set_connection_type

    @staticmethod
    async def get_external_ip_address() -> Any:
        """Returns (NewExternalIPAddress)"""
        raise NotImplementedError()

    GetExternalIPAddress = get_external_ip_address

    @staticmethod
    async def get_connection_type_info() -> Any:
        """Returns (NewConnectionType, NewPossibleConnectionTypes)"""
        raise NotImplementedError()

    GetConnectionTypeInfo = get_connection_type_info

    @staticmethod
    async def get_status_info() -> Any:
        """Returns (NewConnectionStatus, NewLastConnectionError, NewUptime)"""
        raise NotImplementedError()

    GetStatusInfo = get_status_info

    @staticmethod
    async def force_termination() -> Any:
        """Returns None"""
        raise NotImplementedError()

    @staticmethod
    async def delete_port_mapping(new_remote_host: str, new_external_port: int, new_protocol: str) -> Any:
        """Returns None"""
        raise NotImplementedError()

    DeletePortMapping = delete_port_mapping

    @staticmethod
    async def request_connection() -> Any:
        """Returns None"""
        raise NotImplementedError()

    RequestConnection = request_connection

    @staticmethod
    async def get_common_link_properties() -> Any:
        """Returns (NewWANAccessType, NewLayer1UpstreamMaxBitRate, NewLayer1DownstreamMaxBitRate, NewPhysicalLinkStatus)"""
        raise NotImplementedError()

    GetCommonLinkProperties = get_common_link_properties

    @staticmethod
    async def get_total_bytes_sent() -> Any:
        """Returns (NewTotalBytesSent)"""
        raise NotImplementedError()

    GetTotalBytesSent = get_total_bytes_sent

    @staticmethod
    async def get_total_bytes_received() -> Any:
        """Returns (NewTotalBytesReceived)"""
        raise NotImplementedError()

    GetTotalBytesRecieved = get_total_bytes_received

    @staticmethod
    async def get_total_packets_sent() -> Any:
        """Returns (NewTotalPacketsSent)"""
        raise NotImplementedError()

    GetTotalPacketsSent = get_total_packets_sent

    @staticmethod
    def get_total_packets_received() -> Any:
        """Returns (NewTotalPacketsReceived)"""
        raise NotImplementedError()

    GetTotalPacketsReceived = get_total_packets_received

    @staticmethod
    async def x_get_ICS_statistics() -> Any:
        """Returns (TotalBytesSent, TotalBytesReceived, TotalPacketsSent, TotalPacketsReceived, Layer1DownstreamMaxBitRate, Uptime)"""
        raise NotImplementedError()

    X_GetICSStatistics = x_get_ICS_statistics

    @staticmethod
    async def get_default_connection_service() -> Any:
        """Returns (NewDefaultConnectionService)"""
        raise NotImplementedError()

    GetDefaultConnectionService = get_default_connection_service

    @staticmethod
    async def set_default_connection_service(new_default_connection_service: str) -> Any:
        """Returns (None)"""
        raise NotImplementedError()

    SetDefaultConnectionService = set_default_connection_service

    @staticmethod
    async def set_enabled_for_internet(new_enabled_for_internet: bool) -> Any:
        """

        :param new_enabled_for_internet:
        :return:
        """
        raise NotImplementedError()

    SetEnabledForInternet = set_enabled_for_internet

    @staticmethod
    async def get_enabled_for_internet() -> Any:
        """

        :return bool?:
        """
        raise NotImplementedError()

    GetEnabledForInternet = get_enabled_for_internet

    @staticmethod
    async def get_maximum_active_connections(new_active_connection_index: int) -> Any:
        """

        :param new_active_connection_index:
        :return:
        """
        raise NotImplementedError()

    GetMaximumActiveConnections = get_maximum_active_connections

    @staticmethod
    async def get_active_connections() -> Any:
        """Returns (NewActiveConnDeviceContainer, NewActiveConnectionServiceID"""
        raise NotImplementedError()

    GetActiveConnections = get_active_connections
