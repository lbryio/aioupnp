import struct
import socket
from asyncio.protocols import DatagramProtocol
from asyncio.transports import DatagramTransport


class MulticastProtocol(DatagramProtocol):
    def __init__(self, multicast_address: str, bind_address: str) -> None:
        self.multicast_address = multicast_address
        self.bind_address = bind_address
        self.transport: DatagramTransport

    @property
    def sock(self) -> socket.socket:
        s: socket.socket = self.transport.get_extra_info(name='socket')
        return s

    def get_ttl(self) -> int:
        return self.sock.getsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL)

    def set_ttl(self, ttl: int = 1) -> None:
        self.sock.setsockopt(
            socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', ttl)
        )

    def join_group(self, multicast_address: str, bind_address: str) -> None:
        self.sock.setsockopt(
            socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
            socket.inet_aton(multicast_address) + socket.inet_aton(bind_address)
        )

    def leave_group(self, multicast_address: str, bind_address: str) -> None:
        self.sock.setsockopt(
            socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP,
            socket.inet_aton(multicast_address) + socket.inet_aton(bind_address)
        )

    def connection_made(self, transport) -> None:
        self.transport = transport

    @classmethod
    def create_multicast_socket(cls, bind_address: str):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind_address, 0))
        sock.setblocking(False)
        return sock
