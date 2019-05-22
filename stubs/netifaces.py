import typing


AF_APPLETALK = 5
AF_ASH = 18
AF_ATMPVC = 8
AF_ATMSVC = 20
AF_AX25 = 3
AF_BLUETOOTH = 31
AF_BRIDGE = 7
AF_DECnet = 12
AF_ECONET = 19
AF_FILE = 1
AF_INET = 2
AF_INET6 = 10
AF_IPX = 4
AF_IRDA = 23
AF_ISDN = 34
AF_KEY = 15
AF_LINK = 17
AF_NETBEUI = 13
AF_NETLINK = 16
AF_NETROM = 6
AF_PACKET = 17
AF_PPPOX = 24
AF_ROSE = 11
AF_ROUTE = 16
AF_SECURITY = 14
AF_SNA = 22
AF_UNIX = 1
AF_UNSPEC = 0
AF_WANPIPE = 25
AF_X25 = 9

version = '0.10.7'


# functions
def gateways(*args, **kwargs) -> typing.Dict[typing.Union[str, int],
                                             typing.Union[typing.Dict[int, typing.Tuple[str, str]],
                                                          typing.List[typing.Tuple[str, str, bool]]]]:
    """
    Obtain a list of the gateways on this machine.

    Returns a dict whose keys are equal to the address family constants,
    e.g. netifaces.AF_INET, and whose values are a list of tuples of the
    format (<address>, <interface>, <is_default>).

    There is also a special entry with the key 'default', which you can use
    to quickly obtain the default gateway for a particular address family.

    There may in general be multiple gateways; different address
    families may have different gateway settings (e.g. AF_INET vs AF_INET6)
    and on some systems it's also possible to have interface-specific
    default gateways.
    """
    pass


def ifaddresses(*args, **kwargs) -> typing.Dict[int, typing.List[typing.Dict[str, str]]]:
    """
    Obtain information about the specified network interface.

    Returns a dict whose keys are equal to the address family constants,
    e.g. netifaces.AF_INET, and whose values are a list of addresses in
    that family that are attached to the network interface.
    """
    pass


def interfaces(*args, **kwargs) -> typing.List[str]:
    """ Obtain a list of the interfaces available on this machine. """
    pass


# no classes
# variables with complex values

address_families = {
    0: 'AF_UNSPEC',
    1: 'AF_FILE',
    2: 'AF_INET',
    3: 'AF_AX25',
    4: 'AF_IPX',
    5: 'AF_APPLETALK',
    6: 'AF_NETROM',
    7: 'AF_BRIDGE',
    8: 'AF_ATMPVC',
    9: 'AF_X25',
    10: 'AF_INET6',
    11: 'AF_ROSE',
    12: 'AF_DECnet',
    13: 'AF_NETBEUI',
    14: 'AF_SECURITY',
    15: 'AF_KEY',
    16: 'AF_NETLINK',
    17: 'AF_PACKET',
    18: 'AF_ASH',
    19: 'AF_ECONET',
    20: 'AF_ATMSVC',
    22: 'AF_SNA',
    23: 'AF_IRDA',
    24: 'AF_PPPOX',
    25: 'AF_WANPIPE',
    31: 'AF_BLUETOOTH',
    34: 'AF_ISDN',
}

__loader__ = None  # (!) real value is ''

__spec__ = None  # (!) real value is ''

