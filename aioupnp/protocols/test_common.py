import asyncio
import inspect
import contextlib
import socket
import mock
import unittest


def async_test(f):
    def wrapper(*args, **kwargs):
        if inspect.iscoroutinefunction(f):
            future = f(*args, **kwargs)
        else:
            coroutine = asyncio.coroutine(f)
            future = coroutine(*args, **kwargs)
        asyncio.get_event_loop().run_until_complete(future)

    return wrapper


class TestBase(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.get_event_loop_policy().get_event_loop()


@contextlib.contextmanager
def mock_datagram_endpoint_factory(loop, expected_addr, replies=None, delay_reply=0.0, sent_packets=None):
    sent_packets = sent_packets if sent_packets is not None else []
    replies = replies or {}

    def sendto(p: asyncio.DatagramProtocol):
        def _sendto(data, addr):
            sent_packets.append(data)
            if (data, addr) in replies:
                loop.call_later(delay_reply, p.datagram_received, replies[(data, addr)], (expected_addr, 1900))
        return _sendto

    async def create_datagram_endpoint(proto_lam, sock=None):
            protocol = proto_lam()
            transport = asyncio.DatagramTransport(extra={'socket': mock_sock})
            transport.close = lambda: mock_sock.close()
            mock_sock.sendto = sendto(protocol)
            transport.sendto = mock_sock.sendto
            protocol.connection_made(transport)
            return transport, protocol

    with mock.patch('socket.socket') as mock_socket:
        mock_sock = mock.Mock(spec=socket.socket)
        mock_sock.setsockopt = lambda *_: None
        mock_sock.bind = lambda *_: None
        mock_sock.setblocking = lambda *_: None
        mock_sock.getsockname = lambda: "0.0.0.0"
        mock_sock.getpeername = lambda: ""
        mock_sock.close = lambda: None
        mock_sock.type = socket.SOCK_DGRAM
        mock_sock.fileno = lambda: 7

        mock_socket.return_value = mock_sock
        loop.create_datagram_endpoint = create_datagram_endpoint
        yield
