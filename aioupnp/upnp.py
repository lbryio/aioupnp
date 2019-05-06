import os
import logging
import json
import asyncio
from asyncio import AbstractEventLoop
import zlib
import base64
from collections import OrderedDict
from typing import Tuple, Dict, List, Union, Optional, Any, Awaitable, Mapping
from aioupnp.fault import UPnPError
from aioupnp.gateway import Gateway
from aioupnp.util import get_gateway_and_lan_addresses
from aioupnp.protocols.ssdp import m_search, fuzzy_m_search
from aioupnp.commands import SOAPCommand
from aioupnp.serialization.ssdp import SSDPDatagram

log = logging.getLogger(__name__)


def cli(fn: Any[object]) -> object:
    """CLI wrapper.

    :param fn:
    :return:
    """
    fn._cli = True
    return fn


def _encode(x: Union[bytes, Exception, str]) -> Union[str, TypeError]:
    """Convenience function used internally to encode data."""
    if isinstance(x, bytes):
        return x.decode()
    elif isinstance(x, Exception):
        return str(x)
    assert isinstance(x, str), TypeError(f'{x} should be str. Got: {type(x)}.')
    return x


class UPnP:
    """Universal Plug N' Play protocol."""

    def __init__(self, lan_address: str, gateway_address: str, gateway: Gateway) -> None:
        self.lan_address = lan_address
        self.gateway_address = gateway_address
        self.gateway = gateway

    @classmethod
    def get_lan_and_gateway(cls, lan_address: Optional[str] = "", gateway_address: Optional[str] = "",
                            interface_name: Optional[str] = "default") -> Tuple[str, str]:
        """Return LAN address and Gateway address respectively."""
        if not lan_address or not gateway_address:
            gateway_addr, lan_addr = get_gateway_and_lan_addresses(interface_name)
            lan_address = lan_address or lan_addr
            gateway_address = gateway_address or gateway_addr
        return lan_address, gateway_address

    @classmethod
    async def discover(cls, lan_address: str = "", gateway_address: str = "", timeout: int = 30,
                       igd_args: Optional[Mapping] = None, interface_name: Optional[str] = "default",
                       loop: Optional[AbstractEventLoop] = None) -> __class__:
        """Discovery."""
        try:
            lan_address, gateway_address = cls.get_lan_and_gateway(lan_address, gateway_address, interface_name)
        except Exception as err:
            raise UPnPError("Failed to get LAN and Gateway addresses: %s." % str(err))
        gateway = await Gateway.discover_gateway(
            lan_address, gateway_address, timeout, igd_args, loop
        )
        return cls(lan_address, gateway_address, gateway)

    @classmethod
    @cli
    async def m_search(cls, lan_address: Optional[str] = "", gateway_address: Optional[str] = "",
                       timeout: Optional[int] = 1, igd_args: Optional[Mapping] = None,
                       unicast: Optional[bool] = True, interface_name: Optional[str] = "default",
                       loop: Optional[AbstractEventLoop] = None) -> Dict:
        """M-Search."""
        if not lan_address or not gateway_address:
            try:
                lan_address, gateway_address = cls.get_lan_and_gateway(lan_address, gateway_address, interface_name)
                assert gateway_address and lan_address
            except Exception as err:
                raise UPnPError("failed to get lan and gateway addresses for interface \"%s\": %s" % (interface_name,
                                                                                                      str(err)))
        if not igd_args:
            igd_args, datagram = await fuzzy_m_search(
                lan_address, gateway_address, timeout, loop, unicast=unicast, ignored=None
            )
        else:
            igd_args = OrderedDict(igd_args)
            datagram = await m_search(
                lan_address, gateway_address, igd_args, timeout, loop, unicast=unicast, ignored=None
            )
        return {
            'lan_address': lan_address,
            'gateway_address': gateway_address,
            'm_search_kwargs': SSDPDatagram("M-SEARCH", **igd_args).get_cli_igd_kwargs(),
            'discover_reply': datagram.as_dict()
        }

    @cli
    async def get_external_ip(self) -> Awaitable[str]:
        """Returns external IP address."""
        return await self.gateway.commands.GetExternalIPAddress()

    @cli
    async def add_port_mapping(self, external_port: int, protocol: str, internal_port: int, lan_address: str,
                               description: str) -> Awaitable[None]:
        """Adds port mapping."""
        return await self.gateway.commands.AddPortMapping(
            NewRemoteHost='', NewExternalPort=external_port, NewProtocol=protocol,
            NewInternalPort=internal_port, NewInternalClient=lan_address,
            NewEnabled=1, NewPortMappingDescription=description, NewLeaseDuration='0'
        )

    @cli
    async def get_port_mapping_by_index(self, index: int) -> Dict:
        """Get port mapping by index."""
        result = await self._get_port_mapping_by_index(index)
        if result:
            if isinstance(self.gateway.commands.GetGenericPortMappingEntry, SOAPCommand):
                return {
                    k: v for k, v in zip(self.gateway.commands.GetGenericPortMappingEntry.return_order, result)
                }
        return {}

    async def _get_port_mapping_by_index(self, index: int) -> Optional[Tuple[Optional[str], int, str, int, str, bool,
                                                                             str, int]]:
        """Internal coroutine to get port mapping by index."""
        try:
            redirect = await self.gateway.commands.GetGenericPortMappingEntry(NewPortMappingIndex=index)
            return redirect
        except UPnPError as err:
            print(err)
            return None

    @cli
    async def get_redirects(self) -> List:
        """Returns redirected responses."""
        redirects = []
        cnt = 0
        redirect = await self.get_port_mapping_by_index(cnt)
        while redirect:
            redirects.append(redirect)
            cnt += 1
            redirect = await self.get_port_mapping_by_index(cnt)
        return redirects

    @cli
    async def get_specific_port_mapping(self, external_port: int, protocol: str) -> Dict:
        """
        :param external_port: (int) external port to listen on
        :param protocol:      (str) 'UDP' | 'TCP'
        :return: (int) <internal port>, (str) <lan ip>, (bool) <enabled>, (str) <description>, (int) <lease time>
        """

        try:
            result = await self.gateway.commands.GetSpecificPortMappingEntry(
                NewRemoteHost='', NewExternalPort=external_port, NewProtocol=protocol
            )
            if result and isinstance(self.gateway.commands.GetSpecificPortMappingEntry, SOAPCommand):
                return {k: v for k, v in zip(self.gateway.commands.GetSpecificPortMappingEntry.return_order, result)}
        except UPnPError:
            pass
        return {}

    @cli
    async def delete_port_mapping(self, external_port: int, protocol: str) -> Awaitable[None]:
        """
        :param external_port: (int) external port to listen on
        :param protocol:      (str) 'UDP' | 'TCP'
        :return: None
        """
        return await self.gateway.commands.DeletePortMapping(
            NewRemoteHost="", NewExternalPort=external_port, NewProtocol=protocol
        )

    @cli
    async def get_next_mapping(self, port: int, protocol: str, description: str,
                               internal_port: Optional[int] = None) -> Union[int, UPnPError]:
        """Get next mapping."""
        assert protocol in ["UDP", "TCP"], UPnPError("Unsupported protocol: {}.".format(protocol))
        internal_port = int(internal_port or port)
        requested_port = int(internal_port)
        redirect_tups = []
        cnt = 0
        port = int(port)
        redirect = await self._get_port_mapping_by_index(cnt)
        while redirect:
            redirect_tups.append(redirect)
            cnt += 1
            redirect = await self._get_port_mapping_by_index(cnt)
        redirects = {
            (ext_port, proto): (int_host, int_port, desc)
            for (ext_host, ext_port, proto, int_port, int_host, enabled, desc, _) in redirect_tups
        }
        while (port, protocol) in redirects:
            int_host, int_port, desc = redirects[(port, protocol)]
            if int_host == self.lan_address and int_port == requested_port and desc == description:
                return port
            port += 1
        await self.add_port_mapping(  # set one up
                port, protocol, internal_port, self.lan_address, description
        )
        return port

    @cli
    async def debug_gateway(self) -> bytes:
        """"Return gateway information in JSON format."""
        return json.dumps({
            "gateway": self.gateway.debug_gateway(),
            "client_address": self.lan_address,
        }, default=_encode, indent=2)

    @property
    def zipped_debugging_info(self) -> str:
        """Returns zipped debugging information."""
        return base64.b64encode(zlib.compress(
            json.dumps({
                "gateway": self.gateway.debug_gateway(),
                "client_address": self.lan_address,
            }, default=_encode, indent=2).encode()
        )).decode()

    @cli
    async def generate_test_data(self) -> str:
        """Generates test data."""
        print("Found gateway via M-SEARCH.")
        try:
            external_ip = await self.get_external_ip()
            print("Got external IP Address: %s." % external_ip)
        except (UPnPError, NotImplementedError):
            print("Failed to get the external IP address.")
        try:
            await self.get_redirects()
            print("Got redirects.")
        except (UPnPError, NotImplementedError):
            print("Failed to get redirects.")
        try:
            await self.get_specific_port_mapping(4567, "UDP")
            print("Got specific mapping.")
        except (UPnPError, NotImplementedError):
            print("Failed to get specific mapping.")
        try:
            ext_port = await self.get_next_mapping(4567, "UDP", "aioupnp test mapping")
            print("Set up external mapping to port %i." % ext_port)
            try:
                await self.get_specific_port_mapping(4567, "UDP")
                print("Got specific mapping.")
            except (UPnPError, NotImplementedError):
                print("Failed to get specific mapping.")
            try:
                await self.get_redirects()
                print("Got redirects.")
            except (UPnPError, NotImplementedError):
                print("Failed to get redirects.")
            await self.delete_port_mapping(ext_port, "UDP")
            print("Deleted mapping.")
        except (UPnPError, NotImplementedError):
            print("Failed to add and remove a mapping.")
        try:
            await self.get_redirects()
            print("Got redirects.")
        except (UPnPError, NotImplementedError):
            print("Failed to get redirects.")
        try:
            await self.get_specific_port_mapping(4567, "UDP")
            print("Got specific mapping.")
        except (UPnPError, NotImplementedError):
            print("Failed to get specific mapping.")
        if self.gateway.devices:
            device = list((await self.gateway.devices).values())[0]
            assert device.manufacturer and device.modelName
            device_path = os.path.join(os.getcwd(), await self.gateway.manufacturer_string)
        else:
            device_path = os.path.join(os.getcwd(), "UNKNOWN GATEWAY")
        with open(device_path, "w") as f:
            f.write((await self.debug_gateway()).decode())
        return "Generated test data! -> %s." % device_path

    @cli
    async def get_natrsip_status(self) -> Tuple[bool, bool]:
        """Returns (NewRSIPAvailable, NewNATEnabled)."""
        return await self.gateway.commands.GetNATRSIPStatus()

    @cli
    async def set_connection_type(self, new_connection_type: str) -> Awaitable[None]:
        """Returns None."""
        return await self.gateway.commands.SetConnectionType(new_connection_type)

    @cli
    async def get_connection_type_info(self) -> Tuple[str, str]:
        """Returns (NewConnectionType, NewPossibleConnectionTypes)."""
        return await self.gateway.commands.GetConnectionTypeInfo()

    @cli
    async def get_status_info(self) -> Awaitable[Tuple[str, str, int]]:
        """Returns (NewConnectionStatus, NewLastConnectionError, NewUptime)."""
        return await self.gateway.commands.GetStatusInfo()

    @cli
    async def force_termination(self) -> Awaitable[None]:
        """Returns None."""
        return await self.gateway.commands.ForceTermination()

    @cli
    async def request_connection(self) -> Awaitable[None]:
        """Returns None."""
        return await self.gateway.commands.RequestConnection()

    @cli
    async def get_common_link_properties(self) -> Dict:
        """Returns (    NewWANAccessType, NewLayer1UpstreamMaxBitRate,
                        NewLayer1DownstreamMaxBitRate, NewPhysicalLinkStatus    )."""
        return await self.gateway.commands.GetCommonLinkProperties()

    @cli
    async def get_total_bytes_sent(self) -> Awaitable[int]:
        """Returns NewTotalBytesSent."""
        return await self.gateway.commands.GetTotalBytesSent()

    @cli
    async def get_total_bytes_received(self) -> Awaitable[int]:
        """Returns NewTotalBytesReceived."""
        return await self.gateway.commands.GetTotalBytesReceived()

    @cli
    async def get_total_packets_sent(self) -> Awaitable[int]:
        """Returns NewTotalPacketsSent."""
        return await self.gateway.commands.GetTotalPacketsSent()

    @cli
    async def get_total_packets_received(self) -> Awaitable[int]:
        """Returns NewTotalPacketsReceived."""
        return await self.gateway.commands.GetTotalPacketsReceived()

    @cli
    async def x_get_ics_statistics(self) -> Awaitable[Tuple[int, int, int, int, str, str]]:
        """Returns (    TotalBytesSent, TotalBytesReceived, TotalPacketsSent,
                        TotalPacketsReceived, Layer1DownstreamMaxBitRate, Uptime    )."""
        return await self.gateway.commands.X_GetICSStatistics()

    @cli
    async def get_default_connection_service(self) -> Awaitable[str]:
        """Returns NewDefaultConnectionService."""
        return await self.gateway.commands.GetDefaultConnectionService()

    @cli
    async def set_default_connection_service(self, new_default_connection_service: str) -> Awaitable[None]:
        """Returns None."""
        return await self.gateway.commands.SetDefaultConnectionService(new_default_connection_service)

    @cli
    async def set_enabled_for_internet(self, new_enabled_for_internet: bool) -> Awaitable[None]:
        """
        :param new_enabled_for_internet:
        :return: bool
        """
        return await self.gateway.commands.SetEnabledForInternet(new_enabled_for_internet)

    @cli
    async def get_enabled_for_internet(self) -> Awaitable[bool]:
        """Get the value for the internet connectivity configuration."""
        return await self.gateway.commands.GetEnabledForInternet()

    @cli
    async def get_maximum_active_connections(self, new_active_connection_index: int) -> Awaitable[int]:
        """Get MAX active connections the gateway is configured to support."""
        return await self.gateway.commands.GetMaximumActiveConnections(new_active_connection_index)

    @cli
    async def get_active_connections(self) -> Awaitable[Tuple[str, str]]:
        """Returns (NewActiveConnDeviceContainer, NewActiveConnectionServiceID)."""
        return await self.gateway.commands.GetActiveConnections()

    @classmethod
    def run_cli(cls, method: str, igd_args: Mapping[str, Any], lan_address: Optional[str] = "",
                gateway_address: Optional[str] = "", timeout: Optional[int] = 30,
                interface_name: Optional[str] = "default", unicast: Optional[bool] = True,
                loop: Optional[AbstractEventLoop] = None, **kwargs) -> Optional[asyncio.Future]:
        """
        :param method: the command name
        :param igd_args: ordered case sensitive M-SEARCH headers, if provided all headers to be used must be provided
        :param lan_address: the ip address of the local interface
        :param gateway_address: the ip address of the gateway
        :param timeout: timeout, in seconds
        :param interface_name: name of the network interface, the default is aliased to 'default'
        :param unicast: Unicast
        :param kwargs: keyword arguments for the command
        :param loop: EventLoop, used for testing
        """
        kwargs = kwargs or {}
        timeout = int(timeout)
        loop = loop or asyncio.get_event_loop_policy().get_event_loop()
        fut: asyncio.Future = asyncio.Future()

        async def wrapper():  # wrap the upnp setup and call of the command in a coroutine

            if method == 'm_search':  # if we're only m_searching don't do any device discovery
                fn = lambda *_a, **_kw: cls.m_search(
                    lan_address, gateway_address, timeout, igd_args, unicast, interface_name, loop
                )
            else:  # automatically discover the gateway
                try:
                    u = await cls.discover(
                        lan_address, gateway_address, timeout, igd_args, interface_name, loop=loop
                    )
                except UPnPError as err:
                    fut.set_exception(err)
                    return
                if hasattr(u, method) and hasattr(getattr(u, method), "_cli"):
                    fn = getattr(u, method)
                else:
                    fut.set_exception(UPnPError("\"%s\" is not a recognized command" % method))
                    return
            try:  # call the command
                result = await fn(**{k: fn.__annotations__[k](v) for k, v in kwargs.items()})
                fut.set_result(result)
            except UPnPError as err:
                fut.set_exception(err)
            except Exception as err:
                log.exception("Uncaught error.")
                fut.set_exception(UPnPError("Uncaught error: %s." % str(err)))

        if not hasattr(UPnP, method) or not hasattr(getattr(UPnP, method), "_cli"):
            fut.set_exception(UPnPError("\"%s\" is not a recognized command." % method))
        else:
            loop.run_until_complete(wrapper())
        try:
            result = fut.result()
        except UPnPError as err:
            print("aioupnp encountered an error: %s." % str(err))
            return

        if isinstance(result, (list, tuple, dict)):
            print(json.dumps(result, indent=2, default=_encode))
        else:
            print(result)
