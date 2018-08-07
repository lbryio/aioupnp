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
    redirects = yield u.get_redirects()
    ext_ip = yield u.get_external_ip()
    for (ext_host, ext_port, proto, int_port, int_host, enabled, desc, lease) in redirects:
        print("{}:{}/{} --> {}:{} ({}) (expires: {}) - {} ".format(
            ext_host or ext_ip, ext_port, proto, int_host, int_port, "enabled" if enabled else "disabled",
            "never" if not lease else lease, desc)
        )


@defer.inlineCallbacks
def add_mapping(u, *_):
    port = 4567
    protocol = "UDP"
    description = "txupnp test mapping"
    ext_port = yield u.get_next_mapping(port, protocol, description)
    if ext_port:
        print("external port: %i to local %i/%s" % (ext_port, port, protocol))


@defer.inlineCallbacks
def delete_mapping(u, *_):
    port = 4567
    protocol = "UDP"
    yield u.delete_port_mapping(port, protocol)
    mapping = yield u.get_specific_port_mapping(port, protocol)
    if mapping:
        print("failed to remove mapping")
    else:
        print("removed mapping")


cli_commands = {
    "debug_device": debug_device,
    "get_external_ip": get_external_ip,
    "list_mappings": list_mappings,
    "add_mapping": add_mapping,
    "delete_mapping": delete_mapping
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
    import logging
    log = logging.getLogger("txupnp")
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)-15s-%(filename)s:%(lineno)s->%(message)s'))
    log.addHandler(handler)
    log.setLevel(logging.INFO)

    parser = argparse.ArgumentParser(description="upnp command line utility")
    parser.add_argument(dest="command", type=str, help="debug_gateway | list_mappings | get_external_ip | add_mapping | delete_mapping")
    parser.add_argument("--debug_logging", dest="debug_logging", default=False, action="store_true")
    parser.add_argument("--include_igd_xml", dest="include_igd_xml", default=False, action="store_true")
    args = parser.parse_args()
    if args.debug_logging:
        from twisted.python import log as tx_log
        observer = tx_log.PythonLoggingObserver(loggerName="txupnp")
        observer.start()
        log.setLevel(logging.DEBUG)
    command = args.command
    command = command.replace("-", "_")
    if command not in cli_commands:
        print("unrecognized command: %s is not in %s" % (command, cli_commands.keys()))
        return

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
