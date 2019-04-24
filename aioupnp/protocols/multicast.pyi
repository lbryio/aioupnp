from asyncio import DatagramTransport, DatagramProtocol
from socket import SocketType

from typing import runtime, Union, NoReturn


@runtime
class MulticastProtocol(DatagramProtocol):
    def __init__(self, multicast_address: str, bind_address: str) -> None:
        self.multicast_address: str = multicast_address
        self.bind_address: str = bind_address
        self.transport: Union[DatagramTransport, None] = None

    def sock(self) -> SocketType:
        ...

    def get_ttl(self) -> int:
        ...

    def set_ttl(self, ttl: int = 1) -> NoReturn:
        ...

    def join_group(self, multicast_address: str, bind_address: str) -> NoReturn:
        ...

    def leave_group(self, multicast_address: str, bind_address: str) -> NoReturn:
        ...

    @classmethod
    def create_multicast_socket(cls, bind_address: str) -> SocketType:
        ...
