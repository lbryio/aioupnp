import logging
import sys
from aioupnp.upnp import UPnP

log = logging.getLogger("aioupnp")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)-15s-%(filename)s:%(lineno)s->%(message)s'))
log.addHandler(handler)
log.setLevel(logging.WARNING)


def get_help(command):
    fn = getattr(UPnP, command)
    params = command + " " + " ".join(["[--%s=<%s>]" % (k, k) for k in fn.__annotations__ if k != 'return'])
    return \
        "usage: aioupnp [--debug_logging=<debug_logging>] [--interface=<interface>]\n" \
        "              [--gateway_address=<gateway_address>]\n" \
        "              [--lan_address=<lan_address>] [--timeout=<timeout>]\n" \
        "              [--service=<service>]\n" \
        "              %s\n" % params


def main():
    commands = [n for n in dir(UPnP) if hasattr(getattr(UPnP, n, None), "_cli")]
    help_str = " | ".join(commands)
    usage = \
        "usage: aioupnp [-h] [--debug_logging=<debug_logging>] [--interface=<interface>]\n" \
        "              [--gateway_address=<gateway_address>]\n" \
        "              [--lan_address=<lan_address>] [--timeout=<timeout>]\n" \
        "              [--service=<service>]\n" \
        "              command [--<arg name>=<arg>]...\n" \
        "\n" \
        "commands: %s\n\nfor help with a specific command: aioupnp help <command>" % help_str

    args = sys.argv[1:]
    if args[0] in ['help', '-h', '--help']:
        if len(args) > 1:
            if args[1] in commands:
                sys.exit(get_help(args[1]))
        sys.exit(print(usage))

    defaults = {
        'debug_logging': False,
        'interface': 'default',
        'gateway_address': '',
        'lan_address': '',
        'timeout': 1,
        'service': '',  # if not provided try all of them
        'man': '',
        'mx': 1,
        'return_as_json': True
    }

    options = {}
    command = None
    for arg in args:
        if arg.startswith("--"):
            k, v = arg.split("=")
            k = k.lstrip('--')
            options[k] = v
        else:
            command = arg
            break
    if not command:
        print("no command given")
        sys.exit(print(usage))
    kwargs = {}
    for arg in args[len(options)+1:]:
        if arg.startswith("--"):
            k, v = arg.split("=")
            k = k.lstrip('--')
            kwargs[k] = v
        else:
            break
    for k, v in defaults.items():
        if k not in options:
            options[k] = v

    if options.pop('debug_logging'):
        log.setLevel(logging.DEBUG)

    UPnP.run_cli(
        command.replace('-', '_'), options.pop('lan_address'), options.pop('gateway_address'),
        options.pop('timeout'), options.pop('service'), options.pop('man'), options.pop('mx'),
        options.pop('interface'), kwargs
    )


if __name__ == "__main__":
    main()
