import logging
import sys
import textwrap
from collections import OrderedDict
from aioupnp.upnp import UPnP

log = logging.getLogger("aioupnp")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)-15s-%(filename)s:%(lineno)s->%(message)s'))
log.addHandler(handler)
log.setLevel(logging.WARNING)

base_usage = "\n".join(textwrap.wrap(
    "aioupnp [-h] [--debug_logging] [--interface=<interface>] [--gateway_address=<gateway_address>]"
    " [--lan_address=<lan_address>] [--timeout=<timeout>] [(--<header_key>=<value>)...]",
    100, subsequent_indent='  ', break_long_words=False)) + "\n"


def get_help(command):
    fn = getattr(UPnP, command)
    params = command + " " + " ".join(["[--%s=<%s>]" % (k, k) for k in fn.__annotations__ if k != 'return'])
    return base_usage + "\n".join(
        textwrap.wrap(params, 100, initial_indent='  ', subsequent_indent='  ', break_long_words=False)
    )


def main():
    commands = [n for n in dir(UPnP) if hasattr(getattr(UPnP, n, None), "_cli")]
    help_str = "\n".join(textwrap.wrap(
        " | ".join(commands), 100, initial_indent='  ', subsequent_indent='  ', break_long_words=False
    ))

    usage = \
        "\n%s\n" \
        "If m-search headers are provided as keyword arguments all of the headers to be used must be provided,\n" \
        "in the order they are to be used. For example:\n" \
        "  aioupnp --HOST=239.255.255.250:1900 --MAN=\"ssdp:discover\" --MX=1 --ST=upnp:rootdevice m_search\n\n" \
        "Commands:\n" \
        "%s\n\n" \
        "For help with a specific command:" \
        "  aioupnp help <command>\n" % (base_usage, help_str)

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
        'timeout': 30,
    }

    options = OrderedDict()
    command = None
    for arg in args:
        if arg.startswith("--"):
            if "=" in arg:
                k, v = arg.split("=")
            else:
                k, v = arg, True
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
        command.replace('-', '_'), options, options.pop('lan_address'), options.pop('gateway_address'),
        options.pop('timeout'), options.pop('interface'), kwargs
    )


if __name__ == "__main__":
    main()
