import struct
import socket
from asyncio.protocols import DatagramProtocol
from asyncio.transports import DatagramTransport


class MulticastProtocol(DatagramProtocol):
    @property
    def socket(self) -> socket.socket:
        return self.transport.get_extra_info('socket')

    def get_ttl(self) -> int:
        return self.socket.getsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL)

    def set_ttl(self, ttl: int = 1) -> None:
        self.socket.setsockopt(
            socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', ttl)
        )

    def join_group(self, addr: str, interface: str) -> None:
        addr = socket.inet_aton(addr)
        interface = socket.inet_aton(interface)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, addr + interface)

    def leave_group(self, addr: str, interface: str) -> None:
        addr = socket.inet_aton(addr)
        interface = socket.inet_aton(interface)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, addr + interface)

    def connection_made(self, transport: DatagramTransport) -> None:
        self.transport = transport
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    @classmethod
    def create_socket(cls, bind_address: str, multicast_address: str):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind_address, 0))
        sock.setsockopt(
            socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
            socket.inet_aton(multicast_address) + socket.inet_aton(bind_address)
        )
        sock.setblocking(False)
        return sock


