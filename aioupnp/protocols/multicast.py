import asyncio
import socket
import struct


class MulticastProtocol(asyncio.DatagramProtocol):
    """Multicast Protocol."""

    def __init__(self, multicast_address, bind_address) -> None:
        """Multicast Protocol.

        :param str or bytes multicast_address:
        :param str or bytes bind_address:
        :return None:
        """
        self.multicast_address = multicast_address
        self.bind_address = bind_address
        self.transport = None

    @property
    def sock(self):
        """Multicast Socket.

        :return socket.socket:
        """
        return self.transport.get_extra_info(name="socket")

    def get_ttl(self):
        """Get Time-To-Live for the address.

        :return int ttl: Amount of time(seconds) an address will be static.
        """
        _socket = self.sock()
        return _socket.getsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL)

    def set_ttl(self, ttl):
        """Set Time-To-Live for the address.

        :param int ttl: Time-To-Live(seconds)
        :return None:
        """
        _socket = self.sock()
        _ttl = struct.pack('b', ttl)
        _socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, _ttl)

    def join_group(self, multicast_address, bind_address):
        """Join Multicast address with bound socket address.

        :param str multicast_address: Multicast Address
        :param str bind_address: Bound Address
        """
        _socket = self.sock()
        p_mcast_addr = socket.inet_aton(multicast_address)
        p_bind_addr = socket.inet_aton(bind_address)
        packed_ip_addr = p_mcast_addr + p_bind_addr
        _socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, packed_ip_addr)

    def leave_group(self, multicast_address, bind_address):
        """Leave Multicast group.

        :param str multicast_address: Multicast Address.
        :param str or bytes bind_address: Bind address.
        """
        _socket = self.sock()
        p_mcast_addr = socket.inet_aton(multicast_address)
        p_bind_addr = socket.inet_aton(bind_address)
        packed_ip_addr = p_mcast_addr + p_bind_addr
        _socket.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, packed_ip_addr)

    def connection_made(self, transport):
        """When connection is established, assign DatagramTransport.

        :param asyncio.Transport transport:
        """
        self.transport = transport

    @classmethod
    def create_multicast_socket(cls, bind_address):
        """Creates a multicast socket.

        :param str or bytes bind_address:
        :return socket
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind_address, 0))
        sock.setblocking(False)
        return sock
