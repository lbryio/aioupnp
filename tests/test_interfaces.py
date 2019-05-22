from unittest import mock
from aioupnp.fault import UPnPError
from aioupnp.upnp import UPnP
from tests import AsyncioTestCase


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


class TestParseInterfaces(AsyncioTestCase):
    def test_parse_interfaces(self):
        with mock.patch('aioupnp.interfaces.get_netifaces') as patch:
            patch.return_value = mock_netifaces

            lan, gateway = UPnP.get_lan_and_gateway(interface_name='test0')
            self.assertEqual(gateway, '192.168.1.1')
            self.assertEqual(lan, '192.168.1.2')

    async def test_netifaces_fail(self):
        checked = []
        with mock.patch('aioupnp.interfaces.get_netifaces') as patch:
            patch.return_value = mock_netifaces
            try:
                await UPnP.discover(interface_name='test1')
            except UPnPError as err:
                self.assertEqual(str(err), 'failed to get lan and gateway addresses for test1')
                checked.append(True)
            else:
                self.assertTrue(False)
        self.assertTrue(len(checked) == 1)