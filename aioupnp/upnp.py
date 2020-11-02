import zlib
import base64
import logging
import json
import asyncio
from typing import Tuple, Dict, List, Union, Optional, Any
from aioupnp.fault import UPnPError
from aioupnp.gateway import Gateway
from aioupnp.interfaces import get_gateway_and_lan_addresses
from aioupnp.commands import GetGenericPortMappingEntryResponse, GetSpecificPortMappingEntryResponse


log = logging.getLogger(__name__)


class UPnP:
    def __init__(self, lan_address: str, gateway_address: str, gateway: Gateway) -> None:
        self.lan_address = lan_address
        self.gateway_address = gateway_address
        self.gateway = gateway

    @classmethod
    def get_annotations(cls, command: str) -> Tuple[Dict[str, Any], Optional[str]]:
        if command == "m_search":
            return cls.m_search.__annotations__, cls.m_search.__doc__
        if command == "get_external_ip":
            return cls.get_external_ip.__annotations__, cls.get_external_ip.__doc__
        if command == "add_port_mapping":
            return cls.add_port_mapping.__annotations__, cls.add_port_mapping.__doc__
        if command == "get_port_mapping_by_index":
            return cls.get_port_mapping_by_index.__annotations__, cls.get_port_mapping_by_index.__doc__
        if command == "get_redirects":
            return cls.get_redirects.__annotations__, cls.get_redirects.__doc__
        if command == "get_specific_port_mapping":
            return cls.get_specific_port_mapping.__annotations__, cls.get_specific_port_mapping.__doc__
        if command == "delete_port_mapping":
            return cls.delete_port_mapping.__annotations__, cls.delete_port_mapping.__doc__
        if command == "get_next_mapping":
            return cls.get_next_mapping.__annotations__, cls.get_next_mapping.__doc__
        raise AttributeError(command)  # pragma: no cover

    @staticmethod
    def get_lan_and_gateway(lan_address: str = '', gateway_address: str = '',
                            interface_name: str = 'default') -> Tuple[str, str]:
        if not lan_address or not gateway_address:
            gateway_addr, lan_addr = get_gateway_and_lan_addresses(interface_name)
            lan_address = lan_address or lan_addr
            gateway_address = gateway_address or gateway_addr
        return lan_address, gateway_address

    @classmethod
    async def discover(cls, lan_address: str = '', gateway_address: str = '', timeout: int = 3,
                       igd_args: Optional[Dict[str, Union[str, int]]] = None, interface_name: str = 'default',
                       loop: Optional[asyncio.AbstractEventLoop] = None) -> 'UPnP':
        lan_address, gateway_address = cls.get_lan_and_gateway(lan_address, gateway_address, interface_name)
        gateway = await Gateway.discover_gateway(
            lan_address, gateway_address, timeout, igd_args, loop
        )
        return cls(lan_address, gateway_address, gateway)

    @classmethod
    async def m_search(cls, lan_address: str = '', gateway_address: str = '', timeout: int = 1,
                       interface_name: str = 'default',
                       igd_args: Optional[Dict[str, Union[str, int]]] = None,
                       loop: Optional[asyncio.AbstractEventLoop] = None
                       ) -> Dict[str, Union[str, Dict[str, Union[str, int]]]]:
        """
        Perform a M-SEARCH for a upnp gateway.

        :param lan_address: (str) the local interface ipv4 address
        :param gateway_address: (str) the gateway ipv4 address
        :param timeout: (int) m search timeout
        :param interface_name: (str) name of the network interface
        :param igd_args: (dict) case sensitive M-SEARCH headers. if used all headers to be used must be provided.

        :return: {
            'lan_address': (str) lan address,
            'gateway_address': (str) gateway address,
            'm_search_kwargs': (str) equivalent igd_args ,
            'discover_reply': (dict) SSDP response datagram
        }
        """

        if not lan_address or not gateway_address:
            try:
                lan_address, gateway_address = cls.get_lan_and_gateway(lan_address, gateway_address, interface_name)
                assert gateway_address and lan_address
            except Exception as err:
                raise UPnPError("failed to get lan and gateway addresses for interface \"%s\": %s" % (interface_name,
                                                                                                      str(err)))
        gateway = await Gateway.discover_gateway(
            lan_address, gateway_address, timeout, igd_args, loop
        )
        return {
            'lan_address': lan_address,
            'gateway_address': gateway_address,
            # 'm_search_kwargs': SSDPDatagram("M-SEARCH", igd_args).get_cli_igd_kwargs(),
            'discover_reply': gateway._ok_packet.as_dict()
        }

    async def get_external_ip(self) -> str:
        """
        Get the external ip address from the gateway

        :return: (str) external ip
        """
        return await self.gateway.commands.GetExternalIPAddress()

    async def add_port_mapping(self, external_port: int, protocol: str, internal_port: int, lan_address: str,
                               description: str) -> None:
        """
        Add a new port mapping

        :param external_port: (int) external port to map
        :param protocol: (str) UDP | TCP
        :param internal_port: (int) internal port
        :param lan_address: (str) internal lan address
        :param description: (str) mapping description
        :return: None
        """
        await self.gateway.commands.AddPortMapping(
            NewRemoteHost='', NewExternalPort=external_port, NewProtocol=protocol,
            NewInternalPort=internal_port, NewInternalClient=lan_address,
            NewEnabled=1, NewPortMappingDescription=description, NewLeaseDuration='0'
        )
        return None

    async def get_port_mapping_by_index(self, index: int) -> GetGenericPortMappingEntryResponse:
        """
        Get information about a port mapping by index number

        :param index: (int) mapping index number
        :return: NamedTuple[
            gateway_address: str
            external_port: int
            protocol: str
            internal_port: int
            lan_address: str
            enabled: bool
            description: str
            lease_time: int
        ]
        """
        return await self.gateway.commands.GetGenericPortMappingEntry(NewPortMappingIndex=index)

    async def get_redirects(self) -> List[GetGenericPortMappingEntryResponse]:
        """
        Get information about all mapped ports

        :return: List[
            NamedTuple[
                gateway_address: str
                external_port: int
                protocol: str
                internal_port: int
                lan_address: str
                enabled: bool
                description: str
                lease_time: int
            ]
        ]
        """
        redirects: List[GetGenericPortMappingEntryResponse] = []
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

    async def get_specific_port_mapping(self, external_port: int, protocol: str) -> GetSpecificPortMappingEntryResponse:
        """
        Get information about a port mapping by port number and protocol

        :param external_port: (int) port number
        :param protocol: (str) UDP | TCP
        :return: NamedTuple[
            internal_port: int
            lan_address: str
            enabled: bool
            description: str
            lease_time: int
        ]
        """
        return await self.gateway.commands.GetSpecificPortMappingEntry(
            NewRemoteHost='', NewExternalPort=external_port, NewProtocol=protocol
        )

    async def delete_port_mapping(self, external_port: int, protocol: str) -> None:
        """
        Delete a port mapping

        :param external_port: (int) port number of mapping
        :param protocol: (str) TCP | UDP
        :return: None
        """
        await self.gateway.commands.DeletePortMapping(
            NewRemoteHost="", NewExternalPort=external_port, NewProtocol=protocol
        )

        return None

    async def get_next_mapping(self, port: int, protocol: str, description: str,
                               internal_port: Optional[int] = None) -> int:
        """
        Get a new port mapping. If the requested port is not available, increment until the next free port is mapped

        :param port: (int) external port
        :param protocol: (str) UDP | TCP
        :param description: (str) mapping description
        :param internal_port: (int) internal port

        :return: (int) mapped port
        """

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

    async def gather_debug_info(self) -> str:  # pragma: no cover
        """
        Gather debugging information for this gateway, used for generating test cases for devices with errors.

        :return: (str) compressed debugging information
        """

        def _encode(x):
            if isinstance(x, bytes):
                return x.decode()
            elif isinstance(x, Exception):
                return str(x)
            return x

        try:
            await self.get_external_ip()
        except UPnPError:
            pass
        try:
            await self.get_redirects()
        except UPnPError:
            pass
        external_port = 0
        made_mapping = False
        try:
            external_port = await self.get_next_mapping(1234, 'TCP', 'aioupnp testing')
            made_mapping = True
        except UPnPError:
            pass
        try:
            await self.get_redirects()
        except UPnPError:
            pass
        if made_mapping:
            try:
                await self.delete_port_mapping(external_port, 'TCP')
            except UPnPError:
                pass
            try:
                await self.get_redirects()
            except UPnPError:
                pass
        return base64.b64encode(zlib.compress(
            json.dumps({
                "gateway": self.gateway.debug_gateway(),
                "client_address": self.lan_address,
            }, default=_encode, indent=2).encode()
        )).decode()

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


cli_commands = [
    'm_search',
    'get_external_ip',
    'add_port_mapping',
    'get_port_mapping_by_index',
    'get_redirects',
    'get_specific_port_mapping',
    'delete_port_mapping',
    'get_next_mapping',
    'gather_debug_info'
]


def run_cli(method: str, igd_args: Dict[str, Union[bool, str, int]], lan_address: str = '',
            gateway_address: str = '', timeout: int = 3, interface_name: str = 'default',
            kwargs: Optional[Dict[str, str]] = None,
            loop: Optional[asyncio.AbstractEventLoop] = None) -> None:

    kwargs = kwargs or {}
    timeout = int(timeout)
    loop = loop or asyncio.get_event_loop()
    fut: 'asyncio.Future' = loop.create_future()

    async def wrapper():  # wrap the upnp setup and call of the command in a coroutine
        if method == 'm_search':  # if we're only m_searching don't do any device discovery
            fn = lambda *_a, **_kw: UPnP.m_search(
                lan_address, gateway_address, timeout, interface_name, igd_args, loop
            )
        else:  # automatically discover the gateway
            try:
                u = await UPnP.discover(
                    lan_address, gateway_address, timeout, igd_args, interface_name, loop=loop
                )
            except UPnPError as err:  # pragma: no cover
                fut.set_exception(err)
                return
            if method not in cli_commands:
                fut.set_exception(UPnPError("\"%s\" is not a recognized command" % method))  # pragma: no cover
                return  # pragma: no cover
            else:
                fn = getattr(u, method)

        try:  # call the command
            result = await fn(**{k: fn.__annotations__[k](v) for k, v in kwargs.items()})
            fut.set_result(result)
        except UPnPError as err:
            fut.set_exception(err)
        except Exception as err:  # pragma: no cover
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
