from collections import OrderedDict
import typing
import netifaces
from aioupnp.fault import UPnPError


def get_netifaces():  # pragma: no cover
    return netifaces


def ifaddresses(iface: str) -> typing.Dict[int, typing.List[typing.Dict[str, str]]]:
    return get_netifaces().ifaddresses(iface)


def _get_interfaces() -> typing.List[str]:
    return get_netifaces().interfaces()


def _get_gateways() -> typing.Dict[typing.Union[str, int],
                                             typing.Union[typing.Dict[int, typing.Tuple[str, str]],
                                                          typing.List[typing.Tuple[str, str, bool]]]]:
    return get_netifaces().gateways()


def get_interfaces() -> typing.Dict[str, typing.Tuple[str, str]]:
    gateways = _get_gateways()
    infos = gateways[netifaces.AF_INET]
    assert isinstance(infos, list), TypeError(f"expected list from netifaces, got a dict")
    interface_infos: typing.List[typing.Tuple[str, str, bool]] = infos
    result: typing.Dict[str, typing.Tuple[str, str]] = OrderedDict(
        (interface_name, (router_address, ifaddresses(interface_name)[netifaces.AF_INET][0]['addr']))
        for router_address, interface_name, _ in interface_infos
    )
    for interface_name in _get_interfaces():
        if interface_name in ['lo', 'localhost'] or interface_name in result:
            continue
        addresses = ifaddresses(interface_name)
        if netifaces.AF_INET in addresses:
            address = addresses[netifaces.AF_INET][0]['addr']
            gateway_guess = ".".join(address.split(".")[:-1] + ["1"])
            result[interface_name] = (gateway_guess, address)
    _default = gateways['default']
    assert isinstance(_default, dict), TypeError(f"expected dict from netifaces, got a list")
    default: typing.Dict[int, typing.Tuple[str, str]] = _default
    result['default'] = result[default[netifaces.AF_INET][1]]
    return result


def get_gateway_and_lan_addresses(interface_name: str) -> typing.Tuple[str, str]:
    for iface_name, (gateway, lan) in get_interfaces().items():
        if interface_name == iface_name:
            return gateway, lan
    raise UPnPError(f'failed to get lan and gateway addresses for {interface_name}')
