# import os
# import zlib
# import base64
import logging
import json
import asyncio
from collections import OrderedDict
from typing import Tuple, Dict, List, Union, Optional
from aioupnp.fault import UPnPError
from aioupnp.gateway import Gateway
from aioupnp.interfaces import get_gateway_and_lan_addresses
from aioupnp.protocols.ssdp import m_search, fuzzy_m_search
from aioupnp.serialization.ssdp import SSDPDatagram
from aioupnp.commands import SOAPCommands

log = logging.getLogger(__name__)


# def _encode(x):
#     if isinstance(x, bytes):
#         return x.decode()
#     elif isinstance(x, Exception):
#         return str(x)
#     return x


class UPnP:
    def __init__(self, lan_address: str, gateway_address: str, gateway: Gateway) -> None:
        self.lan_address = lan_address
        self.gateway_address = gateway_address
        self.gateway = gateway

    @classmethod
    def get_annotations(cls, command: str) -> Dict[str, type]:
        return getattr(SOAPCommands, command).__annotations__

    @classmethod
    def get_lan_and_gateway(cls, lan_address: str = '', gateway_address: str = '',
                            interface_name: str = 'default') -> Tuple[str, str]:
        if not lan_address or not gateway_address:
            gateway_addr, lan_addr = get_gateway_and_lan_addresses(interface_name)
            lan_address = lan_address or lan_addr
            gateway_address = gateway_address or gateway_addr
        return lan_address, gateway_address

    @classmethod
    async def discover(cls, lan_address: str = '', gateway_address: str = '', timeout: int = 30,
                       igd_args: Optional[Dict[str, Union[str, int]]] = None, interface_name: str = 'default',
                       loop: Optional[asyncio.AbstractEventLoop] = None) -> 'UPnP':
        try:
            lan_address, gateway_address = cls.get_lan_and_gateway(lan_address, gateway_address, interface_name)
        except Exception as err:
            raise UPnPError("failed to get lan and gateway addresses: %s" % str(err))
        gateway = await Gateway.discover_gateway(
            lan_address, gateway_address, timeout, igd_args, loop
        )
        return cls(lan_address, gateway_address, gateway)

    @classmethod
    async def m_search(cls, lan_address: str = '', gateway_address: str = '', timeout: int = 1,
                       igd_args: Optional[Dict[str, Union[int, str]]] = None,
                       unicast: bool = True, interface_name: str = 'default',
                       loop: Optional[asyncio.AbstractEventLoop] = None
                       ) -> Dict[str, Union[str, Dict[str, Union[int, str]]]]:
        if not lan_address or not gateway_address:
            try:
                lan_address, gateway_address = cls.get_lan_and_gateway(lan_address, gateway_address, interface_name)
                assert gateway_address and lan_address
            except Exception as err:
                raise UPnPError("failed to get lan and gateway addresses for interface \"%s\": %s" % (interface_name,
                                                                                                      str(err)))
        if not igd_args:
            igd_args, datagram = await fuzzy_m_search(lan_address, gateway_address, timeout, loop, unicast=unicast)
        else:
            igd_args = OrderedDict(igd_args)
            datagram = await m_search(lan_address, gateway_address, igd_args, timeout, loop, unicast=unicast)
        return {
            'lan_address': lan_address,
            'gateway_address': gateway_address,
            'm_search_kwargs': SSDPDatagram("M-SEARCH", igd_args).get_cli_igd_kwargs(),
            'discover_reply': datagram.as_dict()
        }

    async def get_external_ip(self) -> str:
        return await self.gateway.commands.GetExternalIPAddress()

    async def add_port_mapping(self, external_port: int, protocol: str, internal_port: int, lan_address: str,
                               description: str) -> None:
        await self.gateway.commands.AddPortMapping(
            NewRemoteHost='', NewExternalPort=external_port, NewProtocol=protocol,
            NewInternalPort=internal_port, NewInternalClient=lan_address,
            NewEnabled=1, NewPortMappingDescription=description, NewLeaseDuration='0'
        )
        return None

    async def get_port_mapping_by_index(self, index: int) -> Tuple[str, int, str, int, str, bool, str, int]:
        return await self.gateway.commands.GetGenericPortMappingEntry(NewPortMappingIndex=index)

    async def get_redirects(self) -> List[Tuple[str, int, str, int, str, bool, str, int]]:
        redirects: List[Tuple[str, int, str, int, str, bool, str, int]] = []
        cnt = 0
        try:
            redirect = await self.get_port_mapping_by_index(cnt)
        except UPnPError:
            return redirects
        while redirect is not None:
            redirects.append(redirect)
            cnt += 1
            try:
                redirect = await self.get_port_mapping_by_index(cnt)
            except UPnPError:
                break
        return redirects

    async def get_specific_port_mapping(self, external_port: int, protocol: str) -> Tuple[int, str, bool, str, int]:
        """
        :param external_port: (int) external port to listen on
        :param protocol:      (str) 'UDP' | 'TCP'
        :return: (int) <internal port>, (str) <lan ip>, (bool) <enabled>, (str) <description>, (int) <lease time>
        """
        return await self.gateway.commands.GetSpecificPortMappingEntry(
            NewRemoteHost='', NewExternalPort=external_port, NewProtocol=protocol
        )

    async def delete_port_mapping(self, external_port: int, protocol: str) -> None:
        """
        :param external_port: (int) external port to listen on
        :param protocol:      (str) 'UDP' | 'TCP'
        :return: None
        """
        await self.gateway.commands.DeletePortMapping(
            NewRemoteHost="", NewExternalPort=external_port, NewProtocol=protocol
        )
        return None

    async def get_next_mapping(self, port: int, protocol: str, description: str,
                               internal_port: Optional[int] = None) -> int:
        if protocol not in ["UDP", "TCP"]:
            raise UPnPError("unsupported protocol: {}".format(protocol))
        _internal_port = int(internal_port or port)
        requested_port = int(_internal_port)
        port = int(port)
        redirect_tups = await self.get_redirects()

        redirects: Dict[Tuple[int, str], Tuple[str, int, str]] = {
            (ext_port, proto): (int_host, int_port, desc)
            for (ext_host, ext_port, proto, int_port, int_host, enabled, desc, _) in redirect_tups
        }

        while (port, protocol) in redirects:
            int_host, int_port, desc = redirects[(port, protocol)]
            if int_host == self.lan_address and int_port == requested_port and desc == description:
                return port
            port += 1
        await self.add_port_mapping(port, protocol, _internal_port, self.lan_address, description)
        return port

    # @cli
    # async def debug_gateway(self) -> str:
    #     return json.dumps({
    #         "gateway": self.gateway.debug_gateway(),
    #         "client_address": self.lan_address,
    #     }, default=_encode, indent=2)
    #
    # @property
    # def zipped_debugging_info(self) -> str:
    #     return base64.b64encode(zlib.compress(
    #         json.dumps({
    #             "gateway": self.gateway.debug_gateway(),
    #             "client_address": self.lan_address,
    #         }, default=_encode, indent=2).encode()
    #     )).decode()
    #
    # @cli
    # async def get_natrsip_status(self) -> Tuple[bool, bool]:
    #     """Returns (NewRSIPAvailable, NewNATEnabled)"""
    #     return await self.gateway.commands.GetNATRSIPStatus()
    #
    # @cli
    # async def set_connection_type(self, NewConnectionType: str) -> None:
    #     """Returns None"""
    #     return await self.gateway.commands.SetConnectionType(NewConnectionType)
    #
    # @cli
    # async def get_connection_type_info(self) -> Tuple[str, str]:
    #     """Returns (NewConnectionType, NewPossibleConnectionTypes)"""
    #     return await self.gateway.commands.GetConnectionTypeInfo()
    #
    # @cli
    # async def get_status_info(self) -> Tuple[str, str, int]:
    #     """Returns (NewConnectionStatus, NewLastConnectionError, NewUptime)"""
    #     return await self.gateway.commands.GetStatusInfo()
    #
    # @cli
    # async def force_termination(self) -> None:
    #     """Returns None"""
    #     return await self.gateway.commands.ForceTermination()
    #
    # @cli
    # async def request_connection(self) -> None:
    #     """Returns None"""
    #     return await self.gateway.commands.RequestConnection()
    #
    # @cli
    # async def get_common_link_properties(self):
    #     """Returns (NewWANAccessType, NewLayer1UpstreamMaxBitRate, NewLayer1DownstreamMaxBitRate,
    #      NewPhysicalLinkStatus)"""
    #     return await self.gateway.commands.GetCommonLinkProperties()
    #
    # @cli
    # async def get_total_bytes_sent(self) -> int:
    #     """Returns (NewTotalBytesSent)"""
    #     return await self.gateway.commands.GetTotalBytesSent()
    #
    # @cli
    # async def get_total_bytes_received(self):
    #     """Returns (NewTotalBytesReceived)"""
    #     return await self.gateway.commands.GetTotalBytesReceived()
    #
    # @cli
    # async def get_total_packets_sent(self):
    #     """Returns (NewTotalPacketsSent)"""
    #     return await self.gateway.commands.GetTotalPacketsSent()
    #
    # @cli
    # async def get_total_packets_received(self):
    #     """Returns (NewTotalPacketsReceived)"""
    #     return await self.gateway.commands.GetTotalPacketsReceived()
    #
    # @cli
    # async def x_get_ics_statistics(self) -> Tuple[int, int, int, int, str, str]:
    #     """Returns (TotalBytesSent, TotalBytesReceived, TotalPacketsSent, TotalPacketsReceived,
    #      Layer1DownstreamMaxBitRate, Uptime)"""
    #     return await self.gateway.commands.X_GetICSStatistics()
    #
    # @cli
    # async def get_default_connection_service(self):
    #     """Returns (NewDefaultConnectionService)"""
    #     return await self.gateway.commands.GetDefaultConnectionService()
    #
    # @cli
    # async def set_default_connection_service(self, NewDefaultConnectionService: str) -> None:
    #     """Returns (None)"""
    #     return await self.gateway.commands.SetDefaultConnectionService(NewDefaultConnectionService)
    #
    # @cli
    # async def set_enabled_for_internet(self, NewEnabledForInternet: bool) -> None:
    #     return await self.gateway.commands.SetEnabledForInternet(NewEnabledForInternet)
    #
    # @cli
    # async def get_enabled_for_internet(self) -> bool:
    #     return await self.gateway.commands.GetEnabledForInternet()
    #
    # @cli
    # async def get_maximum_active_connections(self, NewActiveConnectionIndex: int):
    #     return await self.gateway.commands.GetMaximumActiveConnections(NewActiveConnectionIndex)
    #
    # @cli
    # async def get_active_connections(self) -> Tuple[str, str]:
    #     """Returns (NewActiveConnDeviceContainer, NewActiveConnectionServiceID"""
    #     return await self.gateway.commands.GetActiveConnections()


def run_cli(method, igd_args: Dict[str, Union[bool, str, int]], lan_address: str = '',
            gateway_address: str = '', timeout: int = 30, interface_name: str = 'default',
            unicast: bool = True, kwargs: Optional[Dict] = None,
            loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
    """
    :param method: the command name
    :param igd_args: ordered case sensitive M-SEARCH headers, if provided all headers to be used must be provided
    :param lan_address: the ip address of the local interface
    :param gateway_address: the ip address of the gateway
    :param timeout: timeout, in seconds
    :param interface_name: name of the network interface, the default is aliased to 'default'
    :param kwargs: keyword arguments for the command
    :param loop: EventLoop, used for testing
    """


    kwargs = kwargs or {}
    igd_args = igd_args
    timeout = int(timeout)
    loop = loop or asyncio.get_event_loop()
    fut: 'asyncio.Future' = asyncio.Future(loop=loop)

    async def wrapper():  # wrap the upnp setup and call of the command in a coroutine
        cli_commands = [
            'm_search',
            'get_external_ip',
            'add_port_mapping',
            'get_port_mapping_by_index',
            'get_redirects',
            'get_specific_port_mapping',
            'delete_port_mapping',
            'get_next_mapping'
        ]

        if method == 'm_search':  # if we're only m_searching don't do any device discovery
            fn = lambda *_a, **_kw: UPnP.m_search(
                lan_address, gateway_address, timeout, igd_args, unicast, interface_name, loop
            )
        else:  # automatically discover the gateway
            try:
                u = await UPnP.discover(
                    lan_address, gateway_address, timeout, igd_args, interface_name, loop=loop
                )
            except UPnPError as err:
                fut.set_exception(err)
                return
            if method not in cli_commands:
                fut.set_exception(UPnPError("\"%s\" is not a recognized command" % method))
                return
            else:
                fn = getattr(u, method)

        try:  # call the command
            result = await fn(**{k: fn.__annotations__[k](v) for k, v in kwargs.items()})
            fut.set_result(result)
        except UPnPError as err:
            fut.set_exception(err)

        except Exception as err:
            log.exception("uncaught error")
            fut.set_exception(UPnPError("uncaught error: %s" % str(err)))

    if not hasattr(UPnP, method):
        fut.set_exception(UPnPError("\"%s\" is not a recognized command" % method))
    else:
        loop.run_until_complete(wrapper())
    try:
        result = fut.result()
    except UPnPError as err:
        print("aioupnp encountered an error: %s" % str(err))
        return

    if isinstance(result, (list, tuple, dict)):
        print(json.dumps(result, indent=2))
    else:
        print(result)
    return
