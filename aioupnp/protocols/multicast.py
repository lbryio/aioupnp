import asyncio
import socket
import struct


class MulticastProtocol(asyncio.DatagramProtocol):
    def __init__(self, multicast_address, bind_address) -> None:
        self.multicast_address = multicast_address
        self.bind_address = bind_address
        self.transport = None

    @property
    def sock(self):
        return self.transport.get_extra_info(name='socket')

    def get_ttl(self):
        _socket = self.sock()
        return _socket.getsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL)

    def set_ttl(self, ttl):
        _socket = self.sock()
        _ttl = struct.pack('b', ttl)
        _socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, _ttl)

    def join_group(self, multicast_address, bind_address):
        _socket = self.sock()
        p_mcast_addr = socket.inet_aton(multicast_address)
        p_bind_addr = socket.inet_aton(bind_address)
        packed_ip_addr = p_mcast_addr + p_bind_addr
        _socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, packed_ip_addr)

    def leave_group(self, multicast_address, bind_address):
        _socket = self.sock()
        p_mcast_addr = socket.inet_aton(multicast_address)
        p_bind_addr = socket.inet_aton(bind_address)
        packed_ip_addr = p_mcast_addr + p_bind_addr
        _socket.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, packed_ip_addr)

    def connection_made(self, transport):
        self.transport = transport

    @classmethod
    def create_multicast_socket(cls, bind_address):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind_address, 0))
        sock.setblocking(False)
        return sock
