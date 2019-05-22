import asyncio
import time
import typing
import logging
from typing import Tuple
from aioupnp.protocols.scpd import scpd_post
from aioupnp.device import Service

log = logging.getLogger(__name__)


def soap_optional_str(x: typing.Optional[str]) -> typing.Optional[str]:
    return x if x is not None and str(x).lower() not in ['none', 'nil'] else None


def soap_bool(x: typing.Optional[str]) -> bool:
    return False if not x or str(x).lower() in ['false', 'False'] else True


def recast_single_result(t: type, result: typing.Any) -> typing.Optional[typing.Union[str, int, float, bool]]:
    if t is bool:
        return soap_bool(result)
    if t is str:
        return soap_optional_str(result)
    return t(result)


def recast_return(return_annotation, result: typing.Dict[str, typing.Union[int, str]],
                  result_keys: typing.List[str]) -> typing.Tuple:
    if return_annotation is None or len(result_keys) == 0:
        return ()
    if len(result_keys) == 1:
        assert len(result_keys) == 1
        single_result = result[result_keys[0]]
        return (recast_single_result(return_annotation, single_result), )
    annotated_args: typing.List[type] = list(return_annotation.__args__)
    assert len(annotated_args) == len(result_keys)
    recast_results: typing.List[typing.Optional[typing.Union[str, int, float, bool]]] = []
    for type_annotation, result_key in zip(annotated_args, result_keys):
        recast_results.append(recast_single_result(type_annotation, result.get(result_key, None)))
    return tuple(recast_results)


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
        'GetGenericPortMappingEntry',
        'GetSpecificPortMappingEntry',
        'DeletePortMapping',
        'GetExternalIPAddress',
        # 'SetConnectionType',
        # 'GetNATRSIPStatus',
        # 'GetConnectionTypeInfo',
        # 'GetStatusInfo',
        # 'ForceTermination',
        # 'RequestConnection',
        # 'GetCommonLinkProperties',
        # 'GetTotalBytesSent',
        # 'GetTotalBytesReceived',
        # 'GetTotalPacketsSent',
        # 'GetTotalPacketsReceived',
        # 'X_GetICSStatistics',
        # 'GetDefaultConnectionService',
        # 'SetDefaultConnectionService',
        # 'SetEnabledForInternet',
        # 'GetEnabledForInternet',
        # 'GetMaximumActiveConnections',
        # 'GetActiveConnections'
    ]

    def __init__(self, loop: asyncio.AbstractEventLoop, base_address: bytes, port: int) -> None:
        self._loop = loop
        self._registered: typing.Dict[Service,
                                      typing.Dict[str, typing.Tuple[typing.List[str], typing.List[str]]]] = {}
        self._wrappers_no_args: typing.Dict[str, typing.Callable[[], typing.Awaitable[typing.Any]]] = {}
        self._wrappers_kwargs: typing.Dict[str, typing.Callable[..., typing.Awaitable[typing.Any]]] = {}

        self._base_address = base_address
        self._port = port
        self._requests: typing.List[typing.Tuple[str, typing.Dict[str, typing.Any], bytes,
                                                 typing.Tuple, typing.Optional[Exception], float]] = []

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

    def _register_soap_wrapper(self, name: str) -> None:
        annotations: typing.Dict[str, typing.Any] = typing.get_type_hints(getattr(self, name))
        service = self.get_service(name)
        input_names: typing.List[str] = self._registered[service][name][0]
        output_names: typing.List[str] = self._registered[service][name][1]

        async def wrapper(**kwargs: typing.Any) -> typing.Tuple:

            assert service.controlURL is not None
            assert service.serviceType is not None
            response, xml_bytes, err = await scpd_post(
                service.controlURL, self._base_address.decode(), self._port, name, input_names,
                service.serviceType.encode(), self._loop, **kwargs
            )
            if err is not None:
                assert isinstance(xml_bytes, bytes)
                self._requests.append((name, kwargs, xml_bytes, (), err, time.time()))
                raise err
            assert 'return' in annotations
            result = recast_return(annotations['return'], response, output_names)

            self._requests.append((name, kwargs, xml_bytes, result, None, time.time()))
            return result

        if not len(list(k for k in annotations if k != 'return')):
            self._wrappers_no_args[name] = wrapper
        else:
            self._wrappers_kwargs[name] = wrapper
        return None

    def register(self, name: str, service: Service, inputs: typing.List[str], outputs: typing.List[str]) -> None:
        if name not in self.SOAP_COMMANDS:
            raise AttributeError(name)
        if self.is_registered(name):
            raise AttributeError(f"{name} is already a registered SOAP command")
        if service not in self._registered:
            self._registered[service] = {}
        self._registered[service][name] = inputs, outputs
        self._register_soap_wrapper(name)

    async def AddPortMapping(self, NewRemoteHost: str, NewExternalPort: int, NewProtocol: str, NewInternalPort: int,
                             NewInternalClient: str, NewEnabled: int, NewPortMappingDescription: str,
                             NewLeaseDuration: str) -> None:
        """Returns None"""
        name = "AddPortMapping"
        if not self.is_registered(name):
            raise NotImplementedError()
        assert name in self._wrappers_kwargs
        await self._wrappers_kwargs[name](
            NewRemoteHost=NewRemoteHost, NewExternalPort=NewExternalPort, NewProtocol=NewProtocol,
            NewInternalPort=NewInternalPort, NewInternalClient=NewInternalClient, NewEnabled=NewEnabled,
            NewPortMappingDescription=NewPortMappingDescription, NewLeaseDuration=NewLeaseDuration
        )
        return None

    async def GetGenericPortMappingEntry(self, NewPortMappingIndex: int) -> Tuple[str, int, str, int, str,
                                                                            bool, str, int]:
        """
        Returns (NewRemoteHost, NewExternalPort, NewProtocol, NewInternalPort, NewInternalClient, NewEnabled,
                 NewPortMappingDescription, NewLeaseDuration)
        """
        name = "GetGenericPortMappingEntry"
        if not self.is_registered(name):
            raise NotImplementedError()
        assert name in self._wrappers_kwargs
        result: Tuple[str, int, str, int, str, bool, str, int] = await self._wrappers_kwargs[name](
            NewPortMappingIndex=NewPortMappingIndex
        )
        return result

    async def GetSpecificPortMappingEntry(self, NewRemoteHost: str, NewExternalPort: int,
                                          NewProtocol: str) -> Tuple[int, str, bool, str, int]:
        """Returns (NewInternalPort, NewInternalClient, NewEnabled, NewPortMappingDescription, NewLeaseDuration)"""
        name = "GetSpecificPortMappingEntry"
        if not self.is_registered(name):
            raise NotImplementedError()
        assert name in self._wrappers_kwargs
        result: Tuple[int, str, bool, str, int] = await self._wrappers_kwargs[name](
            NewRemoteHost=NewRemoteHost, NewExternalPort=NewExternalPort, NewProtocol=NewProtocol
        )
        return result

    async def DeletePortMapping(self, NewRemoteHost: str, NewExternalPort: int, NewProtocol: str) -> None:
        """Returns None"""
        name = "DeletePortMapping"
        if not self.is_registered(name):
            raise NotImplementedError()
        assert name in self._wrappers_kwargs
        await self._wrappers_kwargs[name](
            NewRemoteHost=NewRemoteHost, NewExternalPort=NewExternalPort, NewProtocol=NewProtocol
        )
        return None

    async def GetExternalIPAddress(self) -> str:
        """Returns (NewExternalIPAddress)"""
        name = "GetExternalIPAddress"
        if not self.is_registered(name):
            raise NotImplementedError()
        assert name in self._wrappers_no_args
        result: Tuple[str] = await self._wrappers_no_args[name]()
        return result[0]

    # async def GetNATRSIPStatus(self) -> Tuple[bool, bool]:
    #     """Returns (NewRSIPAvailable, NewNATEnabled)"""
    #     name = "GetNATRSIPStatus"
    #     if not self.is_registered(name):
    #         raise NotImplementedError()
    #     assert name in self._wrappers_no_args
    #     result: Tuple[bool, bool] = await self._wrappers_no_args[name]()
    #     return result[0], result[1]
    #
    # async def SetConnectionType(self, NewConnectionType: str) -> None:
    #     """Returns None"""
    #     name = "SetConnectionType"
    #     if not self.is_registered(name):
    #         raise NotImplementedError()
    #     assert name in self._wrappers_kwargs
    #     await self._wrappers_kwargs[name](NewConnectionType=NewConnectionType)
    #     return None
    #
    # async def GetConnectionTypeInfo(self) -> Tuple[str, str]:
    #     """Returns (NewConnectionType, NewPossibleConnectionTypes)"""
    #     name = "GetConnectionTypeInfo"
    #     if not self.is_registered(name):
    #         raise NotImplementedError()
    #     assert name in self._wrappers_no_args
    #     result: Tuple[str, str] = await self._wrappers_no_args[name]()
    #     return result
    #
    # async def GetStatusInfo(self) -> Tuple[str, str, int]:
    #     """Returns (NewConnectionStatus, NewLastConnectionError, NewUptime)"""
    #     name = "GetStatusInfo"
    #     if not self.is_registered(name):
    #         raise NotImplementedError()
    #     assert name in self._wrappers_no_args
    #     result: Tuple[str, str, int] = await self._wrappers_no_args[name]()
    #     return result
    #
    # async def ForceTermination(self) -> None:
    #     """Returns None"""
    #     name = "ForceTermination"
    #     if not self.is_registered(name):
    #         raise NotImplementedError()
    #     assert name in self._wrappers_no_args
    #     await self._wrappers_no_args[name]()
    #     return None
    #
    # async def RequestConnection(self) -> None:
    #     """Returns None"""
    #     name = "RequestConnection"
    #     if not self.is_registered(name):
    #         raise NotImplementedError()
    #     assert name in self._wrappers_no_args
    #     await self._wrappers_no_args[name]()
    #     return None
    #
    # async def GetCommonLinkProperties(self) -> Tuple[str, int, int, str]:
    #     """Returns (NewWANAccessType, NewLayer1UpstreamMaxBitRate, NewLayer1DownstreamMaxBitRate,
    #      NewPhysicalLinkStatus)"""
    #     name = "GetCommonLinkProperties"
    #     if not self.is_registered(name):
    #         raise NotImplementedError()
    #     assert name in self._wrappers_no_args
    #     result: Tuple[str, int, int, str] = await self._wrappers_no_args[name]()
    #     return result
    #
    # async def GetTotalBytesSent(self) -> int:
    #     """Returns (NewTotalBytesSent)"""
    #     name = "GetTotalBytesSent"
    #     if not self.is_registered(name):
    #         raise NotImplementedError()
    #     assert name in self._wrappers_no_args
    #     result: Tuple[int] = await self._wrappers_no_args[name]()
    #     return result[0]
    #
    # async def GetTotalBytesReceived(self) -> int:
    #     """Returns (NewTotalBytesReceived)"""
    #     name = "GetTotalBytesReceived"
    #     if not self.is_registered(name):
    #         raise NotImplementedError()
    #     assert name in self._wrappers_no_args
    #     result: Tuple[int] = await self._wrappers_no_args[name]()
    #     return result[0]
    #
    # async def GetTotalPacketsSent(self) -> int:
    #     """Returns (NewTotalPacketsSent)"""
    #     name = "GetTotalPacketsSent"
    #     if not self.is_registered(name):
    #         raise NotImplementedError()
    #     assert name in self._wrappers_no_args
    #     result: Tuple[int] = await self._wrappers_no_args[name]()
    #     return result[0]
    #
    # async def GetTotalPacketsReceived(self) -> int:
    #     """Returns (NewTotalPacketsReceived)"""
    #     name = "GetTotalPacketsReceived"
    #     if not self.is_registered(name):
    #         raise NotImplementedError()
    #     assert name in self._wrappers_no_args
    #     result: Tuple[int] = await self._wrappers_no_args[name]()
    #     return result[0]
    #
    # async def X_GetICSStatistics(self) -> Tuple[int, int, int, int, str, str]:
    #     """Returns (TotalBytesSent, TotalBytesReceived, TotalPacketsSent, TotalPacketsReceived,
    #     Layer1DownstreamMaxBitRate, Uptime)"""
    #     name = "X_GetICSStatistics"
    #     if not self.is_registered(name):
    #         raise NotImplementedError()
    #     assert name in self._wrappers_no_args
    #     result: Tuple[int, int, int, int, str, str] = await self._wrappers_no_args[name]()
    #     return result
    #
    # async def GetDefaultConnectionService(self) -> str:
    #     """Returns (NewDefaultConnectionService)"""
    #     name = "GetDefaultConnectionService"
    #     if not self.is_registered(name):
    #         raise NotImplementedError()
    #     assert name in self._wrappers_no_args
    #     result: Tuple[str] = await self._wrappers_no_args[name]()
    #     return result[0]
    #
    # async def SetDefaultConnectionService(self, NewDefaultConnectionService: str) -> None:
    #     """Returns (None)"""
    #     name = "SetDefaultConnectionService"
    #     if not self.is_registered(name):
    #         raise NotImplementedError()
    #     assert name in self._wrappers_kwargs
    #     await self._wrappers_kwargs[name](NewDefaultConnectionService=NewDefaultConnectionService)
    #     return None
    #
    # async def SetEnabledForInternet(self, NewEnabledForInternet: bool) -> None:
    #     name = "SetEnabledForInternet"
    #     if not self.is_registered(name):
    #         raise NotImplementedError()
    #     assert name in self._wrappers_kwargs
    #     await self._wrappers_kwargs[name](NewEnabledForInternet=NewEnabledForInternet)
    #     return None
    #
    # async def GetEnabledForInternet(self) -> bool:
    #     name = "GetEnabledForInternet"
    #     if not self.is_registered(name):
    #         raise NotImplementedError()
    #     assert name in self._wrappers_no_args
    #     result: Tuple[bool] = await self._wrappers_no_args[name]()
    #     return result[0]
    #
    # async def GetMaximumActiveConnections(self, NewActiveConnectionIndex: int) -> None:
    #     name = "GetMaximumActiveConnections"
    #     if not self.is_registered(name):
    #         raise NotImplementedError()
    #     assert name in self._wrappers_kwargs
    #     await self._wrappers_kwargs[name](NewActiveConnectionIndex=NewActiveConnectionIndex)
    #     return None
    #
    # async def GetActiveConnections(self) -> Tuple[str, str]:
    #     """Returns (NewActiveConnDeviceContainer, NewActiveConnectionServiceID"""
    #     name = "GetActiveConnections"
    #     if not self.is_registered(name):
    #         raise NotImplementedError()
    #     assert name in self._wrappers_no_args
    #     result: Tuple[str, str] = await self._wrappers_no_args[name]()
    #     return result
