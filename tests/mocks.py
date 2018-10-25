import asyncio
import contextlib
import socket
import mock


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

@contextlib.contextmanager
def mock_tcp_endpoint_factory(loop, replies=None, delay_reply=0.0, sent_packets=None):
    sent_packets = sent_packets if sent_packets is not None else []
    replies = replies or {}

    def write(p: asyncio.Protocol):
        def _write(data):
            sent_packets.append(data)
            if data in replies:
                loop.call_later(delay_reply, p.data_received, replies[data])
        return _write

    async def create_connection(protocol_factory, host=None, port=None):
            protocol = protocol_factory()
            transport = asyncio.Transport(extra={'socket': mock_sock})
            transport.close = lambda: mock_sock.close()
            mock_sock.write = write(protocol)
            transport.write = mock_sock.write
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
        mock_sock.type = socket.SOCK_STREAM
        mock_sock.fileno = lambda: 7

        mock_socket.return_value = mock_sock
        loop.create_connection = create_connection
        yield


@contextlib.contextmanager
def mock_tcp_and_udp(loop, udp_expected_addr, udp_replies=None, udp_delay_reply=0.0, sent_udp_packets=None,
                     tcp_replies=None, tcp_delay_reply=0.0, tcp_sent_packets=None):
    sent_udp_packets = sent_udp_packets if sent_udp_packets is not None else []
    udp_replies = udp_replies or {}

    tcp_sent_packets = tcp_sent_packets if tcp_sent_packets is not None else []
    tcp_replies = tcp_replies or {}

    async def create_connection(protocol_factory, host=None, port=None):
        def write(p: asyncio.Protocol):
            def _write(data):
                tcp_sent_packets.append(data)
                if data in tcp_replies:
                    loop.call_later(tcp_delay_reply, p.data_received, tcp_replies[data])

            return _write

        protocol = protocol_factory()
        transport = asyncio.Transport(extra={'socket': mock.Mock(spec=socket.socket)})
        transport.close = lambda: None
        transport.write = write(protocol)
        protocol.connection_made(transport)
        return transport, protocol

    async def create_datagram_endpoint(proto_lam, sock=None):
        def sendto(p: asyncio.DatagramProtocol):
            def _sendto(data, addr):
                sent_udp_packets.append(data)
                if (data, addr) in udp_replies:
                    loop.call_later(udp_delay_reply, p.datagram_received, udp_replies[(data, addr)],
                                    (udp_expected_addr, 1900))

            return _sendto

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
        loop.create_connection = create_connection
        yield
