import asyncio
import time
import typing
import functools
import logging
from typing import Tuple
from aioupnp.protocols.scpd import scpd_post
from aioupnp.device import Service

log = logging.getLogger(__name__)


def soap_optional_str(x: typing.Optional[str]) -> typing.Optional[str]:
    return x if x is not None and str(x).lower() not in ['none', 'nil'] else None


def soap_bool(x: typing.Optional[str]) -> bool:
    return False if not x or str(x).lower() in ['false', 'False'] else True


def recast_single_result(t, result):
    if t is bool:
        return soap_bool(result)
    if t is str:
        return soap_optional_str(result)
    return t(result)


def recast_return(return_annotation, result, result_keys: typing.List[str]):
    if return_annotation is None:
        return None
    if len(result_keys) == 1:
        assert len(result_keys) == 1
        single_result = result[result_keys[0]]
        return recast_single_result(return_annotation, single_result)

    annotated_args: typing.List[type] = list(return_annotation.__args__)
    assert len(annotated_args) == len(result_keys)
    recast_results: typing.List[typing.Optional[typing.Union[str, int, bool, bytes]]] = []
    for type_annotation, result_key in zip(annotated_args, result_keys):
        recast_results.append(recast_single_result(type_annotation, result[result_key]))
    return tuple(recast_results)


def soap_command(fn):
    @functools.wraps(fn)
    async def wrapper(self: 'SOAPCommands', **kwargs):
        if not self.is_registered(fn.__name__):
            return fn(self, **kwargs)
        service = self.get_service(fn.__name__)
        assert service.controlURL is not None
        assert service.serviceType is not None
        response, xml_bytes, err = await scpd_post(
            service.controlURL, self._base_address.decode(), self._port, fn.__name__, self._registered[service][fn.__name__][0],
            service.serviceType.encode(), self._loop, **kwargs
        )
        if err is not None:

            self._requests.append((fn.__name__, kwargs, xml_bytes, None, err, time.time()))
            raise err
        result = recast_return(fn.__annotations__.get('return'), response, self._registered[service][fn.__name__][1])
        self._requests.append((fn.__name__, kwargs, xml_bytes, result, None, time.time()))
        return result
    return wrapper


class SOAPCommands:
    """
    Type annotated wrappers for common UPnP SOAP functions

    A SOAPCommands object has its command attributes overridden during device discovery with SOAPCommand objects
    for the commands implemented by the gateway.

    SOAPCommand will use the typing annotations provided here to properly cast the types of arguments and results
    to their expected types.
    """

    SOAP_COMMANDS: typing.List[str] = [
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
        'SetDefaultConnectionService',
        'SetEnabledForInternet',
        'GetEnabledForInternet',
        'GetMaximumActiveConnections',
        'GetActiveConnections'
    ]

    def __init__(self, loop: asyncio.AbstractEventLoop, base_address: bytes, port: int) -> None:
        self._loop = loop
        self._registered: typing.Dict[Service,
                                      typing.Dict[str, typing.Tuple[typing.List[str], typing.List[str]]]] = {}
        self._base_address = base_address
        self._port = port
        self._requests: typing.List[typing.Tuple[str, typing.Dict[str, typing.Any], bytes,
                                                 typing.Optional[typing.Dict[str, typing.Any]],
                                                 typing.Optional[Exception], float]] = []

    def is_registered(self, name: str) -> bool:
        if name not in self.SOAP_COMMANDS:
            raise ValueError("unknown command")
        for service in self._registered.values():
            if name in service:
                return True
        return False

    def get_service(self, name: str) -> Service:
        if name not in self.SOAP_COMMANDS:
            raise ValueError("unknown command")
        for service, commands in self._registered.items():
            if name in commands:
                return service
        raise ValueError(name)

    def register(self, name: str, service: Service, inputs: typing.List[str], outputs: typing.List[str]) -> None:
        # control_url: str, service_type: bytes,
        if name not in self.SOAP_COMMANDS:
            raise AttributeError(name)
        if self.is_registered(name):
            raise AttributeError(f"{name} is already a registered SOAP command")
        if service not in self._registered:
            self._registered[service] = {}
        self._registered[service][name] = inputs, outputs

    @soap_command
    async def AddPortMapping(self, NewRemoteHost: str, NewExternalPort: int, NewProtocol: str, NewInternalPort: int,
                             NewInternalClient: str, NewEnabled: int, NewPortMappingDescription: str,
                             NewLeaseDuration: str) -> None:
        """Returns None"""
        raise NotImplementedError()

    @soap_command
    async def GetNATRSIPStatus(self) -> Tuple[bool, bool]:
        """Returns (NewRSIPAvailable, NewNATEnabled)"""
        raise NotImplementedError()

    @soap_command
    async def GetGenericPortMappingEntry(self, NewPortMappingIndex: int) -> Tuple[str, int, str, int, str,
                                                                            bool, str, int]:
        """
        Returns (NewRemoteHost, NewExternalPort, NewProtocol, NewInternalPort, NewInternalClient, NewEnabled,
                 NewPortMappingDescription, NewLeaseDuration)
        """
        raise NotImplementedError()

    @soap_command
    async def GetSpecificPortMappingEntry(self, NewRemoteHost: str, NewExternalPort: int,
                                          NewProtocol: str) -> Tuple[int, str, bool, str, int]:
        """Returns (NewInternalPort, NewInternalClient, NewEnabled, NewPortMappingDescription, NewLeaseDuration)"""
        raise NotImplementedError()

    @soap_command
    async def SetConnectionType(self, NewConnectionType: str) -> None:
        """Returns None"""
        raise NotImplementedError()

    @soap_command
    async def GetExternalIPAddress(self) -> str:
        """Returns (NewExternalIPAddress)"""
        raise NotImplementedError()

    @soap_command
    async def GetConnectionTypeInfo(self) -> Tuple[str, str]:
        """Returns (NewConnectionType, NewPossibleConnectionTypes)"""
        raise NotImplementedError()

    @soap_command
    async def GetStatusInfo(self) -> Tuple[str, str, int]:
        """Returns (NewConnectionStatus, NewLastConnectionError, NewUptime)"""
        raise NotImplementedError()

    @soap_command
    async def ForceTermination(self) -> None:
        """Returns None"""
        raise NotImplementedError()

    @soap_command
    async def DeletePortMapping(self, NewRemoteHost: str, NewExternalPort: int, NewProtocol: str) -> None:
        """Returns None"""
        raise NotImplementedError()

    @soap_command
    async def RequestConnection(self) -> None:
        """Returns None"""
        raise NotImplementedError()

    @soap_command
    async def GetCommonLinkProperties(self) -> Tuple[str, int, int, str]:
        """Returns (NewWANAccessType, NewLayer1UpstreamMaxBitRate, NewLayer1DownstreamMaxBitRate, NewPhysicalLinkStatus)"""
        raise NotImplementedError()

    @soap_command
    async def GetTotalBytesSent(self) -> int:
        """Returns (NewTotalBytesSent)"""
        raise NotImplementedError()

    @soap_command
    async def GetTotalBytesReceived(self) -> int:
        """Returns (NewTotalBytesReceived)"""
        raise NotImplementedError()

    @soap_command
    async def GetTotalPacketsSent(self) -> int:
        """Returns (NewTotalPacketsSent)"""
        raise NotImplementedError()

    @soap_command
    async def GetTotalPacketsReceived(self) -> int:
        """Returns (NewTotalPacketsReceived)"""
        raise NotImplementedError()

    @soap_command
    async def X_GetICSStatistics(self) -> Tuple[int, int, int, int, str, str]:
        """Returns (TotalBytesSent, TotalBytesReceived, TotalPacketsSent, TotalPacketsReceived, Layer1DownstreamMaxBitRate, Uptime)"""
        raise NotImplementedError()

    @soap_command
    async def GetDefaultConnectionService(self) -> str:
        """Returns (NewDefaultConnectionService)"""
        raise NotImplementedError()

    @soap_command
    async def SetDefaultConnectionService(self, NewDefaultConnectionService: str) -> None:
        """Returns (None)"""
        raise NotImplementedError()

    @soap_command
    async def SetEnabledForInternet(self, NewEnabledForInternet: bool) -> None:
        raise NotImplementedError()

    @soap_command
    async def GetEnabledForInternet(self) -> bool:
        raise NotImplementedError()

    @soap_command
    async def GetMaximumActiveConnections(self, NewActiveConnectionIndex: int):
        raise NotImplementedError()

    @soap_command
    async def GetActiveConnections(self) -> Tuple[str, str]:
        """Returns (NewActiveConnDeviceContainer, NewActiveConnectionServiceID"""
        raise NotImplementedError()
