import logging
from twisted.web.client import HTTPConnectionPool, _HTTP11ClientFactory
from twisted.web._newclient import HTTPClientParser, BadResponseVersion, HTTP11ClientProtocol, RequestNotSent
from twisted.web._newclient import TransportProxyProducer, RequestGenerationFailed
from twisted.python.failure import Failure
from twisted.internet.defer import Deferred, fail, maybeDeferred
from twisted.internet.defer import CancelledError


log = logging.getLogger()


class DirtyHTTPParser(HTTPClientParser):
    def parseVersion(self, strversion):
        """
        Parse version strings of the form Protocol '/' Major '.' Minor. E.g.
        b'HTTP/1.1'.  Returns (protocol, major, minor).  Will raise ValueError
        on bad syntax.
        """
        try:
            proto, strnumber = strversion.split(b'/')
            major, minor = strnumber.split(b'.')
            major, minor = int(major), int(minor)
        except ValueError as e:
            log.exception("got a bad http version: %s", strversion)
            if b'HTTP1.1' in strversion:
                return ("HTTP", 1, 1)
            raise BadResponseVersion(str(e), strversion)
        if major < 0 or minor < 0:
            raise BadResponseVersion(u"version may not be negative",
                                     strversion)
        return (proto, major, minor)


class DirtyHTTPClientProtocol(HTTP11ClientProtocol):
    def request(self, request):
        if self._state != 'QUIESCENT':
            return fail(RequestNotSent())

        self._state = 'TRANSMITTING'
        _requestDeferred = maybeDeferred(request.writeTo, self.transport)

        def cancelRequest(ign):
            # Explicitly cancel the request's deferred if it's still trying to
            # write when this request is cancelled.
            if self._state in (
                    'TRANSMITTING', 'TRANSMITTING_AFTER_RECEIVING_RESPONSE'):
                _requestDeferred.cancel()
            else:
                self.transport.abortConnection()
                self._disconnectParser(Failure(CancelledError()))

        self._finishedRequest = Deferred(cancelRequest)

        # Keep track of the Request object in case we need to call stopWriting
        # on it.
        self._currentRequest = request

        self._transportProxy = TransportProxyProducer(self.transport)
        self._parser = DirtyHTTPParser(request, self._finishResponse)
        self._parser.makeConnection(self._transportProxy)
        self._responseDeferred = self._parser._responseDeferred

        def cbRequestWritten(ignored):
            if self._state == 'TRANSMITTING':
                self._state = 'WAITING'
                self._responseDeferred.chainDeferred(self._finishedRequest)

        def ebRequestWriting(err):
            if self._state == 'TRANSMITTING':
                self._state = 'GENERATION_FAILED'
                self.transport.abortConnection()
                self._finishedRequest.errback(
                    Failure(RequestGenerationFailed([err])))
            else:
                self._log.failure(
                    u'Error writing request, but not in valid state '
                    u'to finalize request: {state}',
                    failure=err,
                    state=self._state
                )

        _requestDeferred.addCallbacks(cbRequestWritten, ebRequestWriting)

        return self._finishedRequest


class DirtyHTTP11ClientFactory(_HTTP11ClientFactory):
    def buildProtocol(self, addr):
        return DirtyHTTPClientProtocol(self._quiescentCallback)


class DirtyPool(HTTPConnectionPool):
    _factory = DirtyHTTP11ClientFactory
