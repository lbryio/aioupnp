import logging
import time
import typing
from typing import Tuple, Union, List
from aioupnp.protocols.scpd import scpd_post

log = logging.getLogger(__name__)
none_or_str = Union[None, str]
return_type_lambas = {
    Union[None, str]: lambda x: x if x is not None and str(x).lower() not in ['none', 'nil'] else None
}


def safe_type(t):
    if t is typing.Tuple:
        return tuple
    if t is typing.List:
        return list
    if t is typing.Dict:
        return dict
    if t is typing.Set:
        return set
    return t


class SOAPCommand:
    def __init__(self, gateway_address: str, service_port: int, control_url: str, service_id: bytes, method: str,
                 param_types: dict, return_types: dict, param_order: list, return_order: list, loop=None) -> None:
        self.gateway_address = gateway_address
        self.service_port = service_port
        self.control_url = control_url
        self.service_id = service_id
        self.method = method
        self.param_types = param_types
        self.param_order = param_order
        self.return_types = return_types
        self.return_order = return_order
        self.loop = loop
        self._requests: typing.List = []

    async def __call__(self, **kwargs) -> typing.Union[None, typing.Dict, typing.List, typing.Tuple]:
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

    SOAP_COMMANDS = [
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
        self._registered = set()

    def register(self, base_ip: bytes, port: int, name: str, control_url: str,
                 service_type: bytes, inputs: List, outputs: List, loop=None) -> None:
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
    async def AddPortMapping(NewRemoteHost: str, NewExternalPort: int, NewProtocol: str, NewInternalPort: int,
                       NewInternalClient: str, NewEnabled: int, NewPortMappingDescription: str,
                       NewLeaseDuration: str) -> None:
        """Returns None"""
        raise NotImplementedError()

    @staticmethod
    async def GetNATRSIPStatus() -> Tuple[bool, bool]:
        """Returns (NewRSIPAvailable, NewNATEnabled)"""
        raise NotImplementedError()

    @staticmethod
    async def GetGenericPortMappingEntry(NewPortMappingIndex: int) -> Tuple[str, int, str, int, str,
                                                                            bool, str, int]:
        """
        Returns (NewRemoteHost, NewExternalPort, NewProtocol, NewInternalPort, NewInternalClient, NewEnabled,
                 NewPortMappingDescription, NewLeaseDuration)
        """
        raise NotImplementedError()

    @staticmethod
    async def GetSpecificPortMappingEntry(NewRemoteHost: str, NewExternalPort: int,
                                          NewProtocol: str) -> Tuple[int, str, bool, str, int]:
        """Returns (NewInternalPort, NewInternalClient, NewEnabled, NewPortMappingDescription, NewLeaseDuration)"""
        raise NotImplementedError()

    @staticmethod
    async def SetConnectionType(NewConnectionType: str) -> None:
        """Returns None"""
        raise NotImplementedError()

    @staticmethod
    async def GetExternalIPAddress() -> str:
        """Returns (NewExternalIPAddress)"""
        raise NotImplementedError()

    @staticmethod
    async def GetConnectionTypeInfo() -> Tuple[str, str]:
        """Returns (NewConnectionType, NewPossibleConnectionTypes)"""
        raise NotImplementedError()

    @staticmethod
    async def GetStatusInfo() -> Tuple[str, str, int]:
        """Returns (NewConnectionStatus, NewLastConnectionError, NewUptime)"""
        raise NotImplementedError()

    @staticmethod
    async def ForceTermination() -> None:
        """Returns None"""
        raise NotImplementedError()

    @staticmethod
    async def DeletePortMapping(NewRemoteHost: str, NewExternalPort: int, NewProtocol: str) -> None:
        """Returns None"""
        raise NotImplementedError()

    @staticmethod
    async def RequestConnection() -> None:
        """Returns None"""
        raise NotImplementedError()

    @staticmethod
    async def GetCommonLinkProperties():
        """Returns (NewWANAccessType, NewLayer1UpstreamMaxBitRate, NewLayer1DownstreamMaxBitRate, NewPhysicalLinkStatus)"""
        raise NotImplementedError()

    @staticmethod
    async def GetTotalBytesSent():
        """Returns (NewTotalBytesSent)"""
        raise NotImplementedError()

    @staticmethod
    async def GetTotalBytesReceived():
        """Returns (NewTotalBytesReceived)"""
        raise NotImplementedError()

    @staticmethod
    async def GetTotalPacketsSent():
        """Returns (NewTotalPacketsSent)"""
        raise NotImplementedError()

    @staticmethod
    def GetTotalPacketsReceived():
        """Returns (NewTotalPacketsReceived)"""
        raise NotImplementedError()

    @staticmethod
    async def X_GetICSStatistics() -> Tuple[int, int, int, int, str, str]:
        """Returns (TotalBytesSent, TotalBytesReceived, TotalPacketsSent, TotalPacketsReceived, Layer1DownstreamMaxBitRate, Uptime)"""
        raise NotImplementedError()

    @staticmethod
    async def GetDefaultConnectionService():
        """Returns (NewDefaultConnectionService)"""
        raise NotImplementedError()

    @staticmethod
    async def SetDefaultConnectionService(NewDefaultConnectionService: str) -> None:
        """Returns (None)"""
        raise NotImplementedError()

    @staticmethod
    async def SetEnabledForInternet(NewEnabledForInternet: bool) -> None:
        raise NotImplementedError()

    @staticmethod
    async def GetEnabledForInternet() -> bool:
        raise NotImplementedError()

    @staticmethod
    async def GetMaximumActiveConnections(NewActiveConnectionIndex: int):
        raise NotImplementedError()

    @staticmethod
    async def GetActiveConnections() -> Tuple[str, str]:
        """Returns (NewActiveConnDeviceContainer, NewActiveConnectionServiceID"""
        raise NotImplementedError()
