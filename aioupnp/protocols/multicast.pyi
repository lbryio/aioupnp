import typing
import socket
import asyncio

@typing.runtime
class MulticastProtocol(asyncio.DatagramProtocol):
    def __init__(self, multicast_address: str, bind_address: str) -> typing.NoReturn:
        self.multicast_address: str = multicast_address
        self.bind_address: str = bind_address
        self.transport: asyncio.DatagramTransport = None

    def sock(self) -> socket.SocketType:
        ...

    def get_ttl(self) -> int:
        ...

    def set_ttl(self, ttl: typing.Optional[int]) -> typing.NoReturn:
        ...

    def join_group(self, multicast_address: str, bind_address: str) -> typing.NoReturn:
        ...

    def leave_group(self, multicast_address: str, bind_address: str) -> typing.NoReturn:
        ...

    def connection_made(self, transport: asyncio.Transport) -> typing.NoReturn:
        ...

    @classmethod
    def create_multicast_socket(cls, bind_address: str) -> socket.SocketType:
        ...
