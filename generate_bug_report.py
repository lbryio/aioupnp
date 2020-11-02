import os
import sys
import socket
import ctypes
import contextlib
import struct
import binascii
import enum
import re
import time
import base64
import ssl
import asyncio
import codecs
import typing
import json
from ctypes import c_char, c_short
from typing import Tuple
import aioupnp
from aioupnp.upnp import UPnP, UPnPError, get_gateway_and_lan_addresses
from aioupnp.constants import SSDP_IP_ADDRESS
import certifi
import aiohttp
import miniupnpc



_IFF_PROMISC  = 0x0100
_SIOCGIFFLAGS = 0x8913  # get the active flags
_SIOCSIFFLAGS = 0x8914  # set the active flags
_ETH_P_ALL    = 0x0003  # all protocols
ETHER_HEADER_LEN = 6 + 6 + 2
VLAN_HEADER_LEN = 2

printable = re.compile(b"([a-z0-9!\"#$%&'()*+,.\/:;<=>?@\[\] ^_`{|}~-]*)")


class PacketTypes(enum.Enum):  # if_packet.h
    HOST = 0
    BROADCAST = 1
    MULTICAST = 2
    OTHERHOST = 3
    OUTGOING = 4
    LOOPBACK = 5
    FASTROUTE = 6


class Layer2(enum.Enum):  # https://www.iana.org/assignments/ieee-802-numbers/ieee-802-numbers.xhtml
    IPv4 = 0x0800
    ARP =  0x0806
    VLAN = 0x8100
    MVRP = 0x88f5
    MMRP = 0x88f6
    IPv6 = 0x86dd
    GRE  = 0xb7ea


class Layer3(enum.Enum):  # https://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml
    ICMP = 1
    IGMP = 2
    TCP = 6
    UDP = 17


class _ifreq(ctypes.Structure):
    _fields_ = [("ifr_ifrn", c_char * 16),
                ("ifr_flags", c_short)]


@contextlib.contextmanager
def _promiscuous_posix_socket_context(interface: str):
    import fcntl  # posix-only
    sock = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.htons(_ETH_P_ALL))
    ifr = _ifreq()
    ifr.ifr_ifrn = interface.encode()[:16]
    fcntl.ioctl(sock, _SIOCGIFFLAGS, ifr)  # get the flags
    ifr.ifr_flags |= _IFF_PROMISC  # add the promiscuous flag
    fcntl.ioctl(sock, _SIOCSIFFLAGS, ifr)  # update
    sock.setblocking(False)
    try:
        yield sock
    finally:
        ifr.ifr_flags ^= _IFF_PROMISC  # mask it off (remove)
        fcntl.ioctl(sock, _SIOCSIFFLAGS, ifr)  # update
        print("closed posix promiscuous socket")


@contextlib.contextmanager
def _promiscuous_non_posix_socket_context():
    # the public network interface
    HOST = socket.gethostbyname(socket.gethostname())
    # create a raw socket and bind it to the public interface
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
    # prevent socket from being left in TIME_WAIT state, enabling reuse
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, 0))
    # Include IP headers
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    # receive all packages
    sock.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
    sock.setblocking(False)
    try:
        yield sock
    finally:
        # disable promiscuous mode
        sock.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
        print("closed non-posix promiscuous socket")


def promiscuous(interface: typing.Optional[str] = None) -> typing.ContextManager[socket.socket]:
    if os.name == 'posix':
        return _promiscuous_posix_socket_context(interface)
    return _promiscuous_non_posix_socket_context()


def ipv4_to_str(addr: bytes) -> str:
    return ".".join((str(b) for b in addr))


def pretty_mac(mac: bytes) -> str:
    return ":".join((('0' if b < 16 else '') + hex(b)[2:] for b in mac))


def split_byte(b: int, bit=4) -> Tuple[bytes, bytes]:
    return chr(((b >> (8-bit)) % 256) << (8-bit) >> (8-bit)).encode(), chr(((b << bit) % 256) >> bit).encode()


class EtherFrame:
    __slots__ = [
        'source_mac',
        'target_mac',
        'ether_type',
        'vlan_id',
        'tpid'
    ]

    def __init__(self, source_mac: bytes, target_mac: bytes, ether_type: int,
                 vlan_id: typing.Optional[int] = None, tpid: typing.Optional[int] = None):
        self.source_mac = source_mac
        self.target_mac = target_mac
        self.ether_type = ether_type
        self.vlan_id = vlan_id
        self.tpid = tpid

    def encode(self) -> bytes:
        if self.vlan_id is None:
            return struct.pack("6s6sH", *(getattr(self, slot) for slot in self.__slots__[:-2]))
        return struct.pack("6s6sHHH", *(getattr(self, slot) for slot in self.__slots__))

    @classmethod
    def decode(cls, packet: bytes) -> Tuple['EtherFrame', bytes]:
        vlan_id = None
        tpid = None
        if struct.unpack(f'!H', packet[12:14])[0] == Layer2.VLAN.value:
            target_mac, source_mac, tpid, vlan_id, ether_type, data = struct.unpack(f'!6s6sHHH{len(packet) - ETHER_HEADER_LEN - VLAN_HEADER_LEN}s', packet)
        else:
            target_mac, source_mac, ether_type, data = struct.unpack(f'!6s6sH{len(packet) - ETHER_HEADER_LEN}s', packet)
        return cls(source_mac, target_mac, ether_type, vlan_id, tpid), data

    def debug(self) -> str:
        if self.vlan_id is None:
            return f"EtherFrame(source={pretty_mac(self.source_mac)}, target={pretty_mac(self.target_mac)}, " \
                f"ether_type={Layer2(self.ether_type).name})"
        return f"EtherFrame(source={pretty_mac(self.source_mac)}, target={pretty_mac(self.target_mac)}, " \
               f"ether_type={Layer2(self.ether_type).name}, vlan={self.vlan_id})"


class IPv4Packet:
    __slots__ = [
        'ether_frame',
        'version',
        'header_length',
        'dscp',
        'ecn',
        'total_length',
        'identification',
        'df',
        'mf',
        'flag',
        'fragment_offset',
        'ttl',
        'protocol',
        'header_checksum',
        '_source_address',
        '_destination_address',
        'data',
        'packet_type',
        'interface'
    ]

    ETHER_TYPE = Layer2.IPv4

    def __init__(self, ether_frame: EtherFrame, version: int, header_length: int, dscp: int, ecn: int,
                 total_length: int, identification: int, mf: bool, df: bool, flag: bool, fragment_offset: int, ttl: int,
                 protocol: int, header_checksum: int, source_address: bytes, destination_address: bytes, data: bytes,
                 packet_type: int, interface: str):
        self.ether_frame = ether_frame
        self.version = version
        self.header_length = header_length
        self.dscp = dscp
        self.ecn = ecn
        self.total_length = total_length
        self.identification = identification
        self.mf = mf
        self.df = df
        self.flag = flag
        self.fragment_offset = fragment_offset
        self.ttl = ttl
        self.protocol = Layer3(protocol)
        self.header_checksum = header_checksum
        self._source_address = source_address
        self._destination_address = destination_address
        self.data = data
        self.packet_type = PacketTypes(packet_type)
        self.interface = interface

    @property
    def source(self) -> str:
        return ipv4_to_str(self._source_address)

    @property
    def destination(self) -> str:
        return ipv4_to_str(self._destination_address)

    @staticmethod
    def checksum(header: bytes) -> int:
        c = 0
        for i in range(0, len(header), 2):
            c += int.from_bytes(header[i:i + 2], 'big')
            while c > 0xffff:
                c %= 0xffff
        while c > 0xffff:
            c %= 0xffff
        return c ^ 0xffff

    def get_header(self) -> bytes:
        version_and_hlen = (self.version << 4) + self.header_length
        dscp_and_ecn = (self.dscp << 2) + self.ecn
        flags = (4 if self.flag else 0) + (2 if self.df else 0) + (1 if self.mf else 0)
        df_mf_and_fragment = (flags << 12) + self.fragment_offset
        return struct.pack(
            '!BBHHHBBH4s4s', version_and_hlen, dscp_and_ecn, self.total_length,
            self.identification, df_mf_and_fragment, self.ttl, self.protocol.value,
            self.header_checksum, self._source_address, self._destination_address
        )

    @classmethod
    def decode(cls, ether_frame: EtherFrame, packet: bytes, packet_type: int, interface: str) -> 'IPv4Packet':
        if cls.checksum(packet[:20]):
            raise ValueError(f'\nipv4 checksum failed, frame: {ether_frame.debug()}\n'
                             f'packet: {binascii.hexlify(packet).decode()}, checksum: {hex(cls.checksum(packet[:20]))}')
        data_len = len(packet) - 20
        version_and_hlen, dscp_and_ecn, tlen, ident, df_mf_and_fragment, ttl, proto, checksum, source, dest = \
            struct.unpack(
                f'!BBHHHBBH4s4s', packet[:20]
            )
        version, hlen = split_byte(version_and_hlen)
        flags = df_mf_and_fragment >> 13
        mask = (flags << 13) | df_mf_and_fragment
        fragment = mask ^ df_mf_and_fragment
        flag, df, mf = False, False, False
        if flags % 2:
            mf = True
            flags -= 1
        if flags % 2:
            df = True
            flags -= 2
        if flags % 4:
            flag = True
            flags -= 4
        dscp, ecn = split_byte(dscp_and_ecn, 6)
        return cls(
            ether_frame, ord(version), ord(hlen), ord(dscp), ord(ecn), tlen, ident, mf, df, flag, fragment, ttl,
            proto, checksum, source, dest, packet[20:], packet_type, interface
        )

    def encode(self) -> bytes:
        return self.ether_frame.encode() + self.get_header() + self.data

    @property
    def printable_data(self) -> str:
        return b".".join(printable.findall(self.data)).decode()

    def __repr__(self) -> str:
        return f"IPv4(protocol={self.protocol.name}, " \
               f"iface={self.interface}, " \
               f"type={self.packet_type.name}, " \
               f"source={ipv4_to_str(self._source_address)}, " \
               f"destination={ipv4_to_str(self._destination_address)}, " \
               f"data_len={len(self.data)})"


def make_filter(l3_protocol=None, src=None, dst=None, invert=False):
    def filter_packet(packet: IPv4Packet):
        if l3_protocol and not Layer3(packet.protocol) == l3_protocol:
            return False
        if src and not packet.source == src:
            return False
        if dst and not packet.destination == dst:
            return False
        return True
    if invert:
        return lambda packet: not filter_packet(packet)
    return filter_packet


async def sniff_ipv4(filters=None, kill=None):
    start = time.perf_counter()
    loop = asyncio.get_event_loop()

    async def sock_recv(sock, n):
        """Receive data from the socket.

        The return value is a bytes object representing the data received.
        The maximum amount of data to be received at once is specified by
        nbytes.
        """
        if loop._debug and sock.gettimeout() != 0:
            raise ValueError("the socket must be non-blocking")
        fut = loop.create_future()
        _sock_recv(fut, None, sock, n)
        return await fut

    def _sock_recv(fut, registered_fd, sock, n):
        # _sock_recv() can add itself as an I/O callback if the operation can't
        # be done immediately. Don't use it directly, call sock_recv().
        if registered_fd is not None:
            # Remove the callback early.  It should be rare that the
            # selector says the fd is ready but the call still returns
            # EAGAIN, and I am willing to take a hit in that case in
            # order to simplify the common case.
            loop.remove_reader(registered_fd)
        if fut.cancelled():
            return
        try:
            data, flags = sock.recvfrom(n)
        except (BlockingIOError, InterruptedError):
            fd = sock.fileno()
            loop.add_reader(fd, _sock_recv, fut, fd, sock, n)
        except Exception as exc:
            fut.set_exception(exc)
        else:
            fut.set_result((data, flags))

    with promiscuous('lo') as sock:
        while True:
            if not kill:
                data, flags = await sock_recv(sock, 9000)
            else:
                t = asyncio.create_task(sock_recv(sock, 9000))
                await asyncio.wait([t, kill.wait()], return_when=asyncio.FIRST_COMPLETED)
                if kill.is_set():
                    break
                data, flags = await t
            # https://stackoverflow.com/questions/42821309/how-to-interpret-result-of-recvfrom-raw-socket/45215859#45215859
            if data:
                try:
                    ether_frame, packet = EtherFrame.decode(data)
                    if ether_frame.ether_type == Layer2.IPv4.value:
                        interface, _, packet_type, _, _ = flags
                        ipv4 = IPv4Packet.decode(ether_frame, packet, packet_type, interface)
                        if not filters or any((f(ipv4) for f in filters)):
                            yield time.perf_counter() - start, ipv4
                except ValueError:
                    pass


async def main():
    loop = asyncio.get_event_loop()
    gateway, lan = get_gateway_and_lan_addresses('default')

    done = asyncio.Event()

    def discover_aioupnp():
        async def _discover():
            print("testing aioupnp")
            try:
                u = await UPnP.discover()
                print("successfully detected router with aioupnp")
                try:
                    await u.get_external_ip()
                    print("successfully detected external ip with aioupnp")
                except UPnPError:
                    print("failed to detect external ip with aioupnp")
                try:
                    await u.get_redirects()
                    print("successfully detected redirects with aioupnp")
                except UPnPError:
                    print("failed to get redirects with aioupnp")
                try:
                    external_port = await u.get_next_mapping(1234, 'TCP', 'aioupnp testing')
                    print("successfully set redirect with aioupnp")
                except UPnPError:
                    print("failed to set redirect with aioupnp")
                    external_port = None
                try:
                    await u.get_redirects()
                    print("successfully detected redirects with aioupnp")
                except UPnPError:
                    print("failed to get redirects with aioupnp")
                if external_port:
                    try:
                        print("successfully removed redirect with aioupnp")
                        await u.delete_port_mapping(external_port, 'TCP')
                    except UPnPError:
                        print("failed to delete redirect with aioupnp")
                    try:
                        await u.get_redirects()
                        print("successfully detected redirects with aioupnp")
                    except UPnPError:
                        print("failed to get redirects with aioupnp")
            except UPnPError:
                print("failed to discover router with aioupnp")
            finally:
                print("done with aioupnp test")
        asyncio.create_task(_discover())

    def discover_miniupnpc():
        def _miniupnpc_discover():
            try:
                u = miniupnpc.UPnP()
            except:
                print("failed to create upnp object with miniupnpc")
                return
            try:
                u.discover()
            except:
                print("failed to detect router with miniupnpc")
                return
            try:
                u.selectigd()
                print("successfully detected router with miniupnpc")
            except:
                print("failed to detect router with miniupnpc")
                return
            try:
                u.externalipaddress()
                print("successfully detected external ip with miniupnpc")
            except:
                print("failed to detect external ip with miniupnpc")
                return

        async def _discover():
            print("testing miniupnpc")
            try:
                await loop.run_in_executor(None, _miniupnpc_discover)
            finally:
                done.set()
                print("done with miniupnpc test")

        asyncio.create_task(_discover())

    loop.call_later(0, discover_aioupnp)
    loop.call_later(8, discover_miniupnpc)
    start = time.perf_counter()
    packets = []
    try:
        async for (ts, ipv4_packet) in sniff_ipv4([
                make_filter(l3_protocol=Layer3.UDP, src=SSDP_IP_ADDRESS),
                make_filter(l3_protocol=Layer3.UDP, dst=SSDP_IP_ADDRESS),
                make_filter(l3_protocol=Layer3.UDP, src=lan, dst=gateway),
                make_filter(l3_protocol=Layer3.UDP, src=gateway, dst=lan),
                make_filter(l3_protocol=Layer3.TCP, src=lan, dst=gateway),
                make_filter(l3_protocol=Layer3.TCP, src=gateway, dst=lan)], done):
            packets.append(
                (time.perf_counter() - start, ipv4_packet.packet_type.name,
                 ipv4_packet.source, ipv4_packet.destination, base64.b64encode(ipv4_packet.data).decode())
            )
    except KeyboardInterrupt:
        print("stopping")
    finally:
        with open("aioupnp-bug-report.json", "w") as cap_file:
            cap_file.write(json.dumps(packets))
        print(f"Wrote bug report: {os.path.abspath('aioupnp-bug-report.json')}")
        print("Sending bug report")
        ssl_ctx = ssl.create_default_context(
            purpose=ssl.Purpose.CLIENT_AUTH, capath=certifi.where()
        )
        auth = aiohttp.BasicAuth(
            base64.b64decode(codecs.encode('Ax5LZzR1o3q3Z3WjATASDwR5rKyHH0qOIRIbLmMXn2H=', 'rot_13')).decode(), ''
        )
        report_id = base64.b64encode(os.urandom(16)).decode()
        async with aiohttp.ClientSession() as session:
            for i, (ts, direction, source, destination, packet) in enumerate(packets):
                post = {
                    'userId': report_id,
                    'event': 'aioupnp bug report',
                    'context': {
                        'library': {
                            'name': 'aioupnp',
                            'version': aioupnp.__version__
                        }
                    },
                    'properties': {
                        'sequence': i,
                        'ts': ts,
                        'direction': direction,
                        'source': source,
                        'destination': destination,
                        'packet': packet
                    },
                }
                async with session.request(method='POST', url='https://api.segment.io/v1/track',
                                           headers={'Connection': 'Close'}, auth=auth, json=post, ssl=ssl_ctx):
                    sys.stdout.write(f"\r{'.' * i}")
        sys.stdout.write("\n")
        print("Successfully sent bug report, thanks for your contribution!")


if __name__ == "__main__":
    asyncio.run(main())
