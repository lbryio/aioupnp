import unittest
from unittest import mock
from aioupnp.upnp import UPnP


class mock_netifaces:
    @staticmethod
    def gateways():
        return {
            "default": {
                2: [
                    "192.168.1.1",
                    "test0"
                ]
            },
            2: [
                [
                    "192.168.1.1",
                    "test0",
                    True
                ]
            ]
        }
    @staticmethod
    def interfaces():
        return ['test0']

    @staticmethod
    def ifaddresses(interface):
        return {
            "test0": {
                17: [
                    {
                        "addr": "01:02:03:04:05:06",
                        "broadcast": "ff:ff:ff:ff:ff:ff"
                    }
                ],
                2: [
                    {
                        "addr": "192.168.1.2",
                        "netmask": "255.255.255.0",
                        "broadcast": "192.168.1.255"
                    }
                ],
            },
        }[interface]


class TestParseInterfaces(unittest.TestCase):
    def test_parse_interfaces(self):
        with mock.patch('aioupnp.interfaces.get_netifaces') as patch:
            patch.return_value = mock_netifaces

            lan, gateway = UPnP.get_lan_and_gateway(interface_name='test0')
            self.assertEqual(gateway, '192.168.1.1')
            self.assertEqual(lan, '192.168.1.2')
