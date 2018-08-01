import sys
import argparse
import logging
from twisted.internet import reactor, defer
from txupnp.upnp import UPnP

log = logging.getLogger("txupnp")


def debug_device(u, include_gateway_xml=False, *_):
    print(u.get_debug_info(include_gateway_xml=include_gateway_xml))
    return defer.succeed(None)


@defer.inlineCallbacks
def get_external_ip(u, *_):
    ip = yield u.get_external_ip()
    print(ip)


@defer.inlineCallbacks
def list_mappings(u, *_):
    print(u.get_debug_info(include_gateway_xml=True))
    redirects = yield u.get_redirects()
    print("found {} redirects".format(len(redirects)))
    for redirect in redirects:
        print("\t", redirect)


cli_commands = {
    "debug_device": debug_device,
    "get_external_ip": get_external_ip,
    "list_mappings": list_mappings
}


@defer.inlineCallbacks
def run_command(found, u, command, debug_xml):
    if not found:
        print("failed to find gateway")
        reactor.callLater(0, reactor.stop)
        return
    if command not in cli_commands:
        print("unrecognized command: valid commands: %s" % list(cli_commands.keys()))
    else:
        yield cli_commands[command](u, debug_xml)


def main():
    parser = argparse.ArgumentParser(description="upnp command line utility")
    parser.add_argument(dest="command", type=str, help="debug_gateway | list_mappings | get_external_ip")
    parser.add_argument("--debug_logging", dest="debug_logging", default=False, action="store_true")
    parser.add_argument("--include_igd_xml", dest="include_igd_xml", default=False, action="store_true")
    args = parser.parse_args()
    if args.debug_logging:
        from twisted.python import log as tx_log
        observer = tx_log.PythonLoggingObserver(loggerName="txupnp")
        observer.start()
        log.setLevel(logging.DEBUG)
    command = args.command

    def show(err):
        print("error: {}".format(err))

    u = UPnP(reactor)
    d = u.discover()
    d.addCallback(run_command, u, command, args.include_igd_xml)
    d.addErrback(show)
    d.addBoth(lambda _: reactor.callLater(0, reactor.stop))
    reactor.run()


if __name__ == "__main__":
    main()
