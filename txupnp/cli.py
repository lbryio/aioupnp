import os
import json
import argparse
import logging
from twisted.internet import reactor, defer
from txupnp.upnp import UPnP

log = logging.getLogger("txupnp")


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
    port = 51413
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


def _encode(x):
    if isinstance(x, bytes):
        return x.decode()
    elif isinstance(x, Exception):
        return str(x)
    return x


@defer.inlineCallbacks
def generate_test_data(u, *_):
    external_ip = yield u.get_external_ip()
    redirects = yield u.get_redirects()
    ext_port = yield u.get_next_mapping(4567, "UDP", "txupnp test mapping")
    delete = yield u.delete_port_mapping(ext_port, "UDP")
    after_delete = yield u.get_specific_port_mapping(ext_port, "UDP")

    commands_test_case = (
        ("get_external_ip", (), "1.2.3.4"),
        ("get_redirects", (), redirects),
        ("get_next_mapping", (4567, "UDP", "txupnp test mapping"), ext_port),
        ("delete_port_mapping", (ext_port, "UDP"), delete),
        ("get_specific_port_mapping", (ext_port, "UDP"), after_delete),
    )

    gateway = u.gateway
    device = list(gateway.devices.values())[0]
    assert device.manufacturer and device.modelName
    device_path = os.path.join(os.getcwd(), "%s %s" % (device.manufacturer, device.modelName))
    commands = gateway.debug_commands()
    with open(device_path, "w") as f:
        f.write(json.dumps({
            "router_address": u.router_ip,
            "client_address": u.lan_address,
            "port": gateway.port,
            "gateway_dict": gateway.as_dict(),
            'expected_devices': [
                {
                    'cache_control': 'max-age=1800',
                    'location': gateway.location,
                    'server': gateway.server,
                    'st': gateway.urn,
                    'usn': gateway.usn
                }
            ],
            'commands': commands,
            'ssdp': u.sspd_factory.get_ssdp_packet_replay(),
            'scpd': gateway.requester.dump_packets(),
            'soap': commands_test_case
        }, default=_encode, indent=2).replace(external_ip, "1.2.3.4"))
    print("Generated test data! -> %s" % device_path)


cli_commands = {
    "get_external_ip": get_external_ip,
    "list_mappings": list_mappings,
    "add_mapping": add_mapping,
    "delete_mapping": delete_mapping,
    "generate_test_data": generate_test_data,
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
        # from twisted.python import log as tx_log
        # observer = tx_log.PythonLoggingObserver(loggerName="txupnp")
        # observer.start()
        log.setLevel(logging.DEBUG)
    command = args.command
    command = command.replace("-", "_")
    if command not in cli_commands:
        print("unrecognized command: %s is not in %s" % (command, cli_commands.keys()))
        return

    def show(err):
        print("error: {}".format(err))

    u = UPnP(reactor, debug_ssdp=(command == "generate_test_data"))
    d = u.discover()
    d.addCallback(run_command, u, command, args.include_igd_xml)
    d.addErrback(show)
    d.addBoth(lambda _: reactor.callLater(0, reactor.stop))
    reactor.run()


if __name__ == "__main__":
    main()
