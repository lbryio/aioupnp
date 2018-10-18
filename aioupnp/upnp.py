import os
import socket
import logging
import json
import asyncio
import zlib
import base64
from collections import OrderedDict
from typing import Tuple, Dict, List, Union
from aioupnp.fault import UPnPError
from aioupnp.gateway import Gateway
from aioupnp.util import get_gateway_and_lan_addresses
from aioupnp.protocols.ssdp import m_search, fuzzy_m_search
from aioupnp.protocols.soap import SOAPCommand
from aioupnp.serialization.ssdp import SSDPDatagram

log = logging.getLogger(__name__)


def cli(fn):
    fn._cli = True
    return fn


def _encode(x):
    if isinstance(x, bytes):
        return x.decode()
    elif isinstance(x, Exception):
        return str(x)
    return x


class UPnP:
    def __init__(self, lan_address: str, gateway_address: str, gateway: Gateway) -> None:
        self.lan_address = lan_address
        self.gateway_address = gateway_address
        self.gateway = gateway

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
                       igd_args: OrderedDict = None, interface_name: str = 'default',
                       ssdp_socket: socket.socket = None, soap_socket: socket.socket = None):
        try:
            lan_address, gateway_address = cls.get_lan_and_gateway(lan_address, gateway_address, interface_name)
        except Exception as err:
            raise UPnPError("failed to get lan and gateway addresses: %s" % str(err))
        gateway = await Gateway.discover_gateway(
            lan_address, gateway_address, timeout, igd_args, ssdp_socket, soap_socket
        )
        return cls(lan_address, gateway_address, gateway)

    @classmethod
    @cli
    async def m_search(cls, lan_address: str = '', gateway_address: str = '', timeout: int = 1,
                       igd_args: OrderedDict = None, interface_name: str = 'default',
                       ssdp_socket: socket.socket = None) -> Dict:
        try:
            lan_address, gateway_address = cls.get_lan_and_gateway(lan_address, gateway_address, interface_name)
            assert gateway_address and lan_address
        except Exception as err:
            raise UPnPError("failed to get lan and gateway addresses for interface \"%s\": %s" % (interface_name,
                                                                                                  str(err)))
        if not igd_args:
            igd_args, datagram = await fuzzy_m_search(lan_address, gateway_address, timeout, ssdp_socket)
        else:
            igd_args = OrderedDict(igd_args)
            datagram = await m_search(lan_address, gateway_address, igd_args, timeout, ssdp_socket)
        return {
            'lan_address': lan_address,
            'gateway_address': gateway_address,
            'm_search_kwargs': SSDPDatagram("M-SEARCH", igd_args).get_cli_igd_kwargs(),
            'discover_reply': datagram.as_dict()
        }

    @cli
    async def get_external_ip(self) -> str:
        return await self.gateway.commands.GetExternalIPAddress()

    @cli
    async def add_port_mapping(self, external_port: int, protocol: str, internal_port: int, lan_address: str,
                               description: str) -> None:
        return await self.gateway.commands.AddPortMapping(
            NewRemoteHost='', NewExternalPort=external_port, NewProtocol=protocol,
            NewInternalPort=internal_port, NewInternalClient=lan_address,
            NewEnabled=1, NewPortMappingDescription=description, NewLeaseDuration='0'
        )

    @cli
    async def get_port_mapping_by_index(self, index: int) -> Dict:
        result = await self._get_port_mapping_by_index(index)
        if result:
            if isinstance(self.gateway.commands.GetGenericPortMappingEntry, SOAPCommand):
                return {
                    k: v for k, v in zip(self.gateway.commands.GetGenericPortMappingEntry.return_order, result)
                }
        return {}

    async def _get_port_mapping_by_index(self, index: int) -> Union[None, Tuple[Union[None, str], int, str,
                                                                                int, str, bool, str, int]]:
        try:
            redirect = await self.gateway.commands.GetGenericPortMappingEntry(NewPortMappingIndex=index)
            return redirect
        except UPnPError:
            return None

    @cli
    async def get_redirects(self) -> List[Dict]:
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
    async def delete_port_mapping(self, external_port: int, protocol: str) -> None:
        """
        :param external_port: (int) external port to listen on
        :param protocol:      (str) 'UDP' | 'TCP'
        :return: None
        """
        return await self.gateway.commands.DeletePortMapping(
            NewRemoteHost="", NewExternalPort=external_port, NewProtocol=protocol
        )

    @cli
    async def get_next_mapping(self, port: int, protocol: str, description: str, internal_port: int=None) -> int:
        if protocol not in ["UDP", "TCP"]:
            raise UPnPError("unsupported protocol: {}".format(protocol))
        internal_port = internal_port or port
        redirect_tups = []
        cnt = 0
        port = int(port)
        internal_port = int(internal_port)
        redirect = await self._get_port_mapping_by_index(cnt)
        while redirect:
            redirect_tups.append(redirect)
            cnt += 1
            redirect = await self._get_port_mapping_by_index(cnt)

        redirects = {
            "%i:%s" % (ext_port, proto): (int_host, int_port, desc)
            for (ext_host, ext_port, proto, int_port, int_host, enabled, desc, _) in redirect_tups
        }
        while ("%i:%s" % (port, protocol)) in redirects:
            int_host, int_port, _ = redirects["%i:%s" % (port, protocol)]
            if int_host == self.lan_address and int_port == internal_port:
                break
            port += 1

        await self.add_port_mapping(  # set one up
                port, protocol, internal_port, self.lan_address, description
        )
        return port

    @cli
    async def debug_gateway(self) -> str:
        return json.dumps({
            "gateway": self.gateway.debug_gateway(),
            "client_address": self.lan_address,
        }, default=_encode, indent=2)

    @property
    def zipped_debugging_info(self) -> str:
        return base64.b64encode(zlib.compress(
            json.dumps({
                "gateway": self.gateway.debug_gateway(),
                "client_address": self.lan_address,
            }, default=_encode, indent=2).encode()
        )).decode()

    @cli
    async def generate_test_data(self):
        print("found gateway via M-SEARCH")
        try:
            external_ip = await self.get_external_ip()
            print("got external ip: %s" % external_ip)
        except (UPnPError, NotImplementedError):
            print("failed to get the external ip")
        try:
            await self.get_redirects()
            print("got redirects")
        except (UPnPError, NotImplementedError):
            print("failed to get redirects")
        try:
            await self.get_specific_port_mapping(4567, "UDP")
            print("got specific mapping")
        except (UPnPError, NotImplementedError):
            print("failed to get specific mapping")
        try:
            ext_port = await self.get_next_mapping(4567, "UDP", "aioupnp test mapping")
            print("set up external mapping to port %i" % ext_port)
            try:
                await self.get_specific_port_mapping(4567, "UDP")
                print("got specific mapping")
            except (UPnPError, NotImplementedError):
                print("failed to get specific mapping")
            try:
                await self.get_redirects()
                print("got redirects")
            except (UPnPError, NotImplementedError):
                print("failed to get redirects")
            await self.delete_port_mapping(ext_port, "UDP")
            print("deleted mapping")
        except (UPnPError, NotImplementedError):
            print("failed to add and remove a mapping")
        try:
            await self.get_redirects()
            print("got redirects")
        except (UPnPError, NotImplementedError):
            print("failed to get redirects")
        try:
            await self.get_specific_port_mapping(4567, "UDP")
            print("got specific mapping")
        except (UPnPError, NotImplementedError):
            print("failed to get specific mapping")
        if self.gateway.devices:
            device = list(self.gateway.devices.values())[0]
            assert device.manufacturer and device.modelName
            device_path = os.path.join(os.getcwd(), self.gateway.manufacturer_string)
        else:
            device_path = os.path.join(os.getcwd(), "UNKNOWN GATEWAY")
        with open(device_path, "w") as f:
            f.write(await self.debug_gateway())
        return "Generated test data! -> %s" % device_path

    @cli
    async def get_natrsip_status(self) -> Tuple[bool, bool]:
        """Returns (NewRSIPAvailable, NewNATEnabled)"""
        return await self.gateway.commands.GetNATRSIPStatus()

    @cli
    async def set_connection_type(self, NewConnectionType: str) -> None:
        """Returns None"""
        return await self.gateway.commands.SetConnectionType(NewConnectionType)

    @cli
    async def get_connection_type_info(self) -> Tuple[str, str]:
        """Returns (NewConnectionType, NewPossibleConnectionTypes)"""
        return await self.gateway.commands.GetConnectionTypeInfo()

    @cli
    async def get_status_info(self) -> Tuple[str, str, int]:
        """Returns (NewConnectionStatus, NewLastConnectionError, NewUptime)"""
        return await self.gateway.commands.GetStatusInfo()

    @cli
    async def force_termination(self) -> None:
        """Returns None"""
        return await self.gateway.commands.ForceTermination()

    @cli
    async def request_connection(self) -> None:
        """Returns None"""
        return await self.gateway.commands.RequestConnection()

    @cli
    async def get_common_link_properties(self):
        """Returns (NewWANAccessType, NewLayer1UpstreamMaxBitRate, NewLayer1DownstreamMaxBitRate, NewPhysicalLinkStatus)"""
        return await self.gateway.commands.GetCommonLinkProperties()

    @cli
    async def get_total_bytes_sent(self):
        """Returns (NewTotalBytesSent)"""
        return await self.gateway.commands.GetTotalBytesSent()

    @cli
    async def get_total_bytes_received(self):
        """Returns (NewTotalBytesReceived)"""
        return await self.gateway.commands.GetTotalBytesReceived()

    @cli
    async def get_total_packets_sent(self):
        """Returns (NewTotalPacketsSent)"""
        return await self.gateway.commands.GetTotalPacketsSent()

    @cli
    async def get_total_packets_received(self):
        """Returns (NewTotalPacketsReceived)"""
        return await self.gateway.commands.GetTotalPacketsReceived()

    @cli
    async def x_get_ics_statistics(self) -> Tuple[int, int, int, int, str, str]:
        """Returns (TotalBytesSent, TotalBytesReceived, TotalPacketsSent, TotalPacketsReceived, Layer1DownstreamMaxBitRate, Uptime)"""
        return await self.gateway.commands.X_GetICSStatistics()

    @cli
    async def get_default_connection_service(self):
        """Returns (NewDefaultConnectionService)"""
        return await self.gateway.commands.GetDefaultConnectionService()

    @cli
    async def set_default_connection_service(self, NewDefaultConnectionService: str) -> None:
        """Returns (None)"""
        return await self.gateway.commands.SetDefaultConnectionService(NewDefaultConnectionService)

    @cli
    async def set_enabled_for_internet(self, NewEnabledForInternet: bool) -> None:
        return await self.gateway.commands.SetEnabledForInternet(NewEnabledForInternet)

    @cli
    async def get_enabled_for_internet(self) -> bool:
        return await self.gateway.commands.GetEnabledForInternet()

    @cli
    async def get_maximum_active_connections(self, NewActiveConnectionIndex: int):
        return await self.gateway.commands.GetMaximumActiveConnections(NewActiveConnectionIndex)

    @cli
    async def get_active_connections(self) -> Tuple[str, str]:
        """Returns (NewActiveConnDeviceContainer, NewActiveConnectionServiceID"""
        return await self.gateway.commands.GetActiveConnections()

    @classmethod
    def run_cli(cls, method, igd_args: OrderedDict, lan_address: str = '', gateway_address: str = '', timeout: int = 30,
                interface_name: str = 'default', kwargs: dict = None) -> None:
        kwargs = kwargs or {}
        igd_args = igd_args
        timeout = int(timeout)
        close_loop = False
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            close_loop = True
        if not loop and not close_loop:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            close_loop = True

        fut: asyncio.Future = asyncio.Future()

        async def wrapper():
            if method == 'm_search':
                fn = lambda *_a, **_kw: cls.m_search(
                    lan_address, gateway_address, timeout, igd_args, interface_name
                )
            else:
                try:
                    u = await cls.discover(
                        lan_address, gateway_address, timeout, igd_args, interface_name
                    )
                except UPnPError as err:
                    fut.set_exception(err)
                    return
                if hasattr(u, method) and hasattr(getattr(u, method), "_cli"):
                    fn = getattr(u, method)
                else:
                    fut.set_exception(UPnPError("\"%s\" is not a recognized command" % method))
                    return
            try:
                result = await fn(**{k: fn.__annotations__[k](v) for k, v in kwargs.items()})
                fut.set_result(result)
            except UPnPError as err:
                fut.set_exception(err)

            except Exception as err:
                log.exception("uncaught error")
                fut.set_exception(UPnPError("uncaught error: %s" % str(err)))

        if not hasattr(UPnP, method) or not hasattr(getattr(UPnP, method), "_cli"):
            fut.set_exception(UPnPError("\"%s\" is not a recognized command" % method))
            wrapper = lambda : None

        loop.run_until_complete(wrapper())
        if close_loop:
            loop.close()
        try:
            result = fut.result()
        except UPnPError as err:
            print("aioupnp encountered an error:\n%s" % str(err))
            return

        if isinstance(result, (list, tuple, dict)):
            print(json.dumps(result, indent=2, default=_encode))
        else:
            print(result)
