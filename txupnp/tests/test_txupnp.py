import sys
import logging
from twisted.internet import reactor, defer
from txupnp.upnp import UPnP
from txupnp.fault import UPnPError

log = logging.getLogger("txupnp")


@defer.inlineCallbacks
def test(ext_port=4446, int_port=4446, proto='UDP', timeout=1):
    u = UPnP(reactor)
    found = yield u.discover(timeout=timeout)
    if not found:
        print("failed to find gateway")
        defer.returnValue(None)
    external_ip = yield u.get_external_ip()
    assert external_ip, "Failed to get the external IP"
    log.info(external_ip)
    try:
        yield u.get_specific_port_mapping(ext_port, proto)
    except UPnPError as err:
        if 'NoSuchEntryInArray' in str(err):
            pass
        else:
            log.error("there is already a redirect")
            raise AssertionError()
    yield u.add_port_mapping(ext_port, proto, int_port, u.lan_address, 'woah', 0)
    redirects = yield u.get_redirects()
    if (ext_port, u.lan_address, proto) in map(lambda x: (x[1], x[4], x[2]), redirects):
        log.info("made redirect")
    else:
        log.error("failed to make redirect")
        raise AssertionError()
    yield u.delete_port_mapping(ext_port, proto)
    redirects = yield u.get_redirects()
    if (ext_port, u.lan_address, proto) not in map(lambda x: (x[1], x[4], x[2]),  redirects):
        log.info("tore down redirect")
    else:
        log.error("failed to tear down redirect")
        raise AssertionError()
    r = yield u.get_rsip_nat_status()
    log.info(r)
    r = yield u.get_status_info()
    log.info(r)
    r = yield u.get_connection_type_info()
    log.info(r)


@defer.inlineCallbacks
def run_tests(timeout=1):
    for p in ['UDP']:
        yield test(proto=p, timeout=timeout)


def main(timeout):
    d = run_tests(timeout)
    d.addErrback(log.exception)
    d.addBoth(lambda _: reactor.callLater(0, reactor.stop))
    reactor.run()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        log.setLevel(logging.DEBUG)
        timeout = int(sys.argv[1])
    else:
        timeout = 1
    main(timeout)
