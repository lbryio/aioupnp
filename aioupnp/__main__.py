import sys
import asyncio
import logging
import textwrap
import typing
from collections import OrderedDict
from aioupnp.upnp import UPnP
from aioupnp.commands import SOAPCommands

log = logging.getLogger("aioupnp")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)-15s-%(filename)s:%(lineno)s->%(message)s'))
log.addHandler(handler)
log.setLevel(logging.WARNING)

base_usage = "\n".join(textwrap.wrap(
    "aioupnp [-h] [--debug_logging] [--interface=<interface>] [--gateway_address=<gateway_address>]"
    " [--lan_address=<lan_address>] [--timeout=<timeout>] [(--<header_key>=<value>)...]",
    100, subsequent_indent='  ', break_long_words=False)) + "\n"


def get_help(command: str) -> str:
    annotations = UPnP.get_annotations(command)
    params = command + " " + " ".join(["[--%s=<%s>]" % (k, str(v)) for k, v in annotations.items() if k != 'return'])
    return base_usage + "\n".join(
        textwrap.wrap(params, 100, initial_indent='  ', subsequent_indent='  ', break_long_words=False)
    )


def main(argv: typing.Optional[typing.List[typing.Optional[str]]] = None,
         loop: typing.Optional[asyncio.AbstractEventLoop] = None) -> int:
    argv = argv or list(sys.argv)
    commands = list(SOAPCommands.SOAP_COMMANDS)
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

    args: typing.List[str] = [str(arg) for arg in argv[1:]]
    if args[0] in ['help', '-h', '--help']:
        if len(args) > 1:
            if args[1] in commands:
                print(get_help(args[1]))
                return 0
        print(usage)
        return 0

    defaults: typing.Dict[str, typing.Union[bool, str, int]] = {
        'debug_logging': False,
        'interface': 'default',
        'gateway_address': '',
        'lan_address': '',
        'timeout': 30,
        'unicast': False
    }

    options: typing.Dict[str, typing.Union[bool, str, int]] = OrderedDict()
    command = None
    for arg in args:
        if arg.startswith("--"):
            if "=" in arg:
                k, v = arg.split("=")
                options[k.lstrip('--')] = v
            else:
                options[arg.lstrip('--')] = True
        else:
            command = arg
            break
    if not command:
        print("no command given")
        print(usage)
        return 0
    kwargs = {}
    for arg in args[len(options)+1:]:
        if arg.startswith("--"):
            k, v = arg.split("=")
            k = k.lstrip('--')
            kwargs[k] = v
        else:
            break
    for k in defaults:
        if k not in options:
            options[k] = defaults[k]

    if options.pop('debug_logging'):
        log.setLevel(logging.DEBUG)

    lan_address: str = str(options.pop('lan_address'))
    gateway_address: str = str(options.pop('gateway_address'))
    timeout: int = int(options.pop('timeout'))
    interface: str = str(options.pop('interface'))
    unicast: bool = bool(options.pop('unicast'))

    UPnP.run_cli(
        command.replace('-', '_'), options, lan_address, gateway_address, timeout, interface, unicast, kwargs, loop
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
