import unittest
from aioupnp.device import CaseInsensitive


class _TestService(CaseInsensitive):
    serviceType = None
    serviceId = None
    controlURL = None
    eventSubURL = None
    SCPDURL = None


class TestCaseInsensitive(unittest.TestCase):
    def test_initialize(self):
        s = _TestService(
            serviceType="test", serviceId="test id", controlURL="/test", eventSubURL="/test2", SCPDURL="/test3"
        )
        self.assertEqual('test', getattr(s, 'serviceType'))
        self.assertEqual('test', getattr(s, 'servicetype'))
        self.assertEqual('test', getattr(s, 'SERVICETYPE'))

        s = _TestService(
            servicetype="test", serviceid="test id", controlURL="/test", eventSubURL="/test2", SCPDURL="/test3"
        )
        self.assertEqual('test', getattr(s, 'serviceType'))
        self.assertEqual('test', getattr(s, 'servicetype'))
        self.assertEqual('test', getattr(s, 'SERVICETYPE'))

        self.assertDictEqual({
            'serviceType': 'test',
            'serviceId': 'test id',
            'controlURL': "/test",
            'eventSubURL': "/test2",
            'SCPDURL': "/test3"
        }, s.as_dict())

    def test_set_attr(self):
        s = _TestService(
            serviceType="test", serviceId="test id", controlURL="/test", eventSubURL="/test2", SCPDURL="/test3"
        )
        self.assertEqual('test', getattr(s, 'serviceType'))
        s.servicetype = 'foo'
        self.assertEqual('foo', getattr(s, 'serviceType'))
        self.assertEqual('foo', getattr(s, 'servicetype'))
        self.assertEqual('foo', getattr(s, 'SERVICETYPE'))
