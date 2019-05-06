import socket

from typing import Union, Protocol, Type, List, Mapping, Sized

AF_UNSPEC: Union[Type[Protocol], Sized[int]] = 0
AF_UNIX: Union[Type[Protocol], Sized[int]] = 1
AF_FILE: Union[Type[Protocol], Sized[int]] = 1
AF_INET: Union[Type[Protocol], Sized[int]] = 2
AF_AX25: Union[Type[Protocol], Sized[int]] = 3
AF_IPX: Union[Type[Protocol], Sized[int]] = 4
AF_APPLETALK: Union[Type[Protocol], Sized[int]] = 5
AF_NETROM: Union[Type[Protocol], Sized[int]] = 6
AF_BRIDGE: Union[Type[Protocol], Sized[int]] = 7
AF_ATMPVC: Union[Type[Protocol], Sized[int]] = 8
AF_X25: Union[Type[Protocol], Sized[int]] = 9
AF_INET6: Union[Type[Protocol], Sized[int]] = 10
AF_ROSE: Union[Type[Protocol], Sized[int]] = 11
AF_DECnet: Union[Type[Protocol], Sized[int]] = 12
AF_NETBEUI: Union[Type[Protocol], Sized[int]] = 13
AF_SECURITY: Union[Type[Protocol], Sized[int]] = 14
AF_KEY: Union[Type[Protocol], Sized[int]] = 15
AF_NETLINK: Union[Type[Protocol], Sized[int]] = 16
AF_ROUTE: Union[Type[Protocol], Sized[int]] = 16
AF_LINK: Union[Type[Protocol], Sized[int]] = 17
AF_PACKET: Union[Type[Protocol], Sized[int]] = 17
AF_ASH: Union[Type[Protocol], Sized[int]] = 18
AF_ECONET: Union[Type[Protocol], Sized[int]] = 19
AF_ATMSVC: Union[Type[Protocol], Sized[int]] = 20
AF_SNA: Union[Type[Protocol], Sized[int]] = 22
AF_IRDA: Union[Type[Protocol], Sized[int]] = 23
AF_PPPOX: Union[Type[Protocol], Sized[int]] = 24
AF_WANPIPE: Union[Type[Protocol], Sized[int]] = 25
AF_BLUETOOTH: Union[Type[Protocol], Sized[int]] = 31
AF_ISDN: Union[Type[Protocol], Sized[int]] = 34

version = "0.10.7"


# functions

def gateways(*args, **kwargs) -> List[Union[Type, str]]:  # real signature unknown
    """
    Obtain a list of the gateways on this machine.

    Returns a dict whose keys are equal to the address family constants,
    e.g. netifaces.AF_INET, and whose values are a list of tuples of the
    format (<address>, <interface>, <is_default>).

    There is also a special entry with the key "default", which you can use
    to quickly obtain the default gateway for a particular address family.

    There may in general be multiple gateways; different address
    families may have different gateway settings (e.g. AF_INET vs AF_INET6)
    and on some systems it"s also possible to have interface-specific
    default gateways.
    """
    ...


def ifaddresses(*args, **kwargs) -> Mapping[int, Union[socket.SocketType, str]]:  # real signature unknown
    """
    Obtain information about the specified network interface.

    Returns a dict whose keys are equal to the address family constants,
    e.g. netifaces.AF_INET, and whose values are a list of addresses in
    that family that are attached to the network interface.
    """
    ...


def interfaces(*args, **kwargs) -> List[Union[socket.SocketKind, str]]:  # real signature unknown
    """ Obtain a list of the interfaces available on this machine. """
    ...


# no classes
# variables with complex values

address_families = {
    0: "AF_UNSPEC",
    1: "AF_FILE",
    2: "AF_INET",
    3: "AF_AX25",
    4: "AF_IPX",
    5: "AF_APPLETALK",
    6: "AF_NETROM",
    7: "AF_BRIDGE",
    8: "AF_ATMPVC",
    9: "AF_X25",
    10: "AF_INET6",
    11: "AF_ROSE",
    12: "AF_DECnet",
    13: "AF_NETBEUI",
    14: "AF_SECURITY",
    15: "AF_KEY",
    16: "AF_NETLINK",
    17: "AF_PACKET",
    18: "AF_ASH",
    19: "AF_ECONET",
    20: "AF_ATMSVC",
    22: "AF_SNA",
    23: "AF_IRDA",
    24: "AF_PPPOX",
    25: "AF_WANPIPE",
    31: "AF_BLUETOOTH",
    34: "AF_ISDN",
}

__loader__ = None  # (!) real value is ""

__spec__ = None  # (!) real value is ""

