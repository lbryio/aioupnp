import sys
import argparse
import logging
from twisted.internet import reactor, defer
from txupnp.upnp import UPnP

log = logging.getLogger("txupnp")


@defer.inlineCallbacks
def run_command(found, u, command):
    if not found:
        print("failed to find gateway")
        reactor.callLater(0, reactor.stop)
        return
    if command == "debug_device":
        external_ip = yield u.get_external_ip()
        print(u.get_debug_info())
        print("external ip: ", external_ip)
    if command == "list_mappings":
        redirects = yield u.get_redirects()
        print("found {} redirects".format(len(redirects)))
        for redirect in redirects:
            print("\t", redirect)


def main():
    parser = argparse.ArgumentParser(description="upnp command line utility")
    parser.add_argument(dest="command", type=str, help="debug_gateway | list_mappings")
    parser.add_argument("--debug_logging", dest="debug_logging", default=False, action="store_true")
    args = parser.parse_args()
    if args.debug_logging:
        from twisted.python import log as tx_log
        observer = tx_log.PythonLoggingObserver(loggerName="txupnp")
        observer.start()
        log.setLevel(logging.DEBUG)
    command = args.command
    if command not in ['debug_device', 'list_mappings']:
        return sys.exit(0)

    u = UPnP(reactor)
    d = u.discover()
    d.addCallback(run_command, u, command)
    d.addBoth(lambda _: reactor.callLater(0, reactor.stop))
    reactor.run()


if __name__ == "__main__":
    main()
