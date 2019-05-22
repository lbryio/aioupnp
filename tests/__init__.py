import asyncio
import unittest
import contextlib
import socket
from unittest import mock
from unittest.case import _Outcome


try:
    from asyncio.runners import _cancel_all_tasks
except ImportError:
    # this is only available in py3.7
    def _cancel_all_tasks(loop):
        pass


@contextlib.contextmanager
def mock_tcp_and_udp(loop, udp_expected_addr=None, udp_replies=None, udp_delay_reply=0.0, sent_udp_packets=None,
                     tcp_replies=None, tcp_delay_reply=0.0, sent_tcp_packets=None):
    sent_udp_packets = sent_udp_packets if sent_udp_packets is not None else []
    udp_replies = udp_replies or {}

    sent_tcp_packets = sent_tcp_packets if sent_tcp_packets is not None else []
    tcp_replies = tcp_replies or {}

    async def create_connection(protocol_factory, host=None, port=None):
        def write(p: asyncio.Protocol):
            def _write(data):
                sent_tcp_packets.append(data)
                if data in tcp_replies:
                    loop.call_later(tcp_delay_reply, p.data_received, tcp_replies[data])
                    return
                else:
                    pass

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


class AsyncioTestCase(unittest.TestCase):
    # Implementation inspired by discussion:
    #  https://bugs.python.org/issue32972

    maxDiff = None

    async def asyncSetUp(self):  # pylint: disable=C0103
        pass

    async def asyncTearDown(self):  # pylint: disable=C0103
        pass

    def run(self, result=None):  # pylint: disable=R0915
        orig_result = result
        if result is None:
            result = self.defaultTestResult()
            startTestRun = getattr(result, 'startTestRun', None)  # pylint: disable=C0103
            if startTestRun is not None:
                startTestRun()

        result.startTest(self)

        testMethod = getattr(self, self._testMethodName)  # pylint: disable=C0103
        if (getattr(self.__class__, "__unittest_skip__", False) or
                getattr(testMethod, "__unittest_skip__", False)):
            # If the class or method was skipped.
            try:
                skip_why = (getattr(self.__class__, '__unittest_skip_why__', '')
                            or getattr(testMethod, '__unittest_skip_why__', ''))
                self._addSkip(result, self, skip_why)
            finally:
                result.stopTest(self)
            return
        expecting_failure_method = getattr(testMethod,
                                           "__unittest_expecting_failure__", False)
        expecting_failure_class = getattr(self,
                                          "__unittest_expecting_failure__", False)
        expecting_failure = expecting_failure_class or expecting_failure_method
        outcome = _Outcome(result)

        self.loop = asyncio.new_event_loop()  # pylint: disable=W0201
        asyncio.set_event_loop(self.loop)
        self.loop.set_debug(True)

        try:
            self._outcome = outcome

            with outcome.testPartExecutor(self):
                self.setUp()
                self.loop.run_until_complete(self.asyncSetUp())
            if outcome.success:
                outcome.expecting_failure = expecting_failure
                with outcome.testPartExecutor(self, isTest=True):
                    maybe_coroutine = testMethod()
                    if asyncio.iscoroutine(maybe_coroutine):
                        self.loop.run_until_complete(maybe_coroutine)
                outcome.expecting_failure = False
                with outcome.testPartExecutor(self):
                    self.loop.run_until_complete(self.asyncTearDown())
                    self.tearDown()

            self.doAsyncCleanups()

            try:
                _cancel_all_tasks(self.loop)
                self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            finally:
                asyncio.set_event_loop(None)
                self.loop.close()

            for test, reason in outcome.skipped:
                self._addSkip(result, test, reason)
            self._feedErrorsToResult(result, outcome.errors)
            if outcome.success:
                if expecting_failure:
                    if outcome.expectedFailure:
                        self._addExpectedFailure(result, outcome.expectedFailure)
                    else:
                        self._addUnexpectedSuccess(result)
                else:
                    result.addSuccess(self)
            return result
        finally:
            result.stopTest(self)
            if orig_result is None:
                stopTestRun = getattr(result, 'stopTestRun', None)  # pylint: disable=C0103
                if stopTestRun is not None:
                    stopTestRun()  # pylint: disable=E1102

            # explicitly break reference cycles:
            # outcome.errors -> frame -> outcome -> outcome.errors
            # outcome.expectedFailure -> frame -> outcome -> outcome.expectedFailure
            outcome.errors.clear()
            outcome.expectedFailure = None

            # clear the outcome, no more needed
            self._outcome = None

    def doAsyncCleanups(self):  # pylint: disable=C0103
        outcome = self._outcome or _Outcome()
        while self._cleanups:
            function, args, kwargs = self._cleanups.pop()
            with outcome.testPartExecutor(self):
                maybe_coroutine = function(*args, **kwargs)
                if asyncio.iscoroutine(maybe_coroutine):
                    self.loop.run_until_complete(maybe_coroutine)
