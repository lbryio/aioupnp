import sys
import struct
import socket
import typing
from asyncio.protocols import DatagramProtocol
from asyncio.transports import DatagramTransport
from unittest import mock


SOCKET_TYPES = (socket.SocketType, mock.MagicMock)
if sys.version_info >= (3, 8):  # pragma: no cover
    from asyncio.trsock import TransportSocket
    SOCKET_TYPES = (socket.SocketType, TransportSocket, mock.MagicMock)


def _get_sock(transport: typing.Optional[DatagramTransport]) -> typing.Optional[socket.socket]:
    if transport is None or not hasattr(transport, "_extra"):
        return None
    sock: typing.Optional[socket.socket] = transport.get_extra_info('socket', None)
    assert sock is None or isinstance(sock, SOCKET_TYPES)
    return sock


class MulticastProtocol(DatagramProtocol):
    def __init__(self, multicast_address: str, bind_address: str) -> None:
        self.multicast_address = multicast_address
        self.bind_address = bind_address
        self.transport: typing.Optional[DatagramTransport] = None

    @property
    def sock(self) -> typing.Optional[socket.socket]:
        return _get_sock(self.transport)

    def get_ttl(self) -> int:
        sock = self.sock
        if sock:
            return sock.getsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL)
        return 0

    def set_ttl(self, ttl: int = 1) -> None:
        sock = self.sock
        if sock:
            sock.setsockopt(
                socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', ttl)
            )
        return None

    def join_group(self, multicast_address: str, bind_address: str) -> None:
        sock = self.sock
        if sock:
            sock.setsockopt(
                socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                socket.inet_aton(multicast_address) + socket.inet_aton(bind_address)
            )
        return None

    def leave_group(self, multicast_address: str, bind_address: str) -> None:
        sock = self.sock
        if sock:
            sock.setsockopt(
                socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP,
                socket.inet_aton(multicast_address) + socket.inet_aton(bind_address)
            )
        return None

    def connection_made(self, transport: DatagramTransport) -> None:  # type: ignore
        self.transport = transport
        return None

    @classmethod
    def create_multicast_socket(cls, bind_address: str) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind_address, 0))
        sock.setblocking(False)
        return sock
