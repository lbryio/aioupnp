import unittest
from typing import Optional, Union, Type, Protocol, Any
from aioupnp.device import CaseInsensitive


class TestService(CaseInsensitive):
    serviceType: Union[Type[Protocol], str] = None
    serviceId: Union[int, str] = None
    controlURL: str = None
    eventSubURL: str = None
    SCPDURL: str = None


class TestCaseInsensitive(unittest.TestCase):
    def test_initialize(self) -> Any[Optional[AssertionError]]:
        _kwargs = {
            'serviceType': "test",
            'serviceId': "test id",
            'controlURL': "/test",
            'eventSubURL': "/test2",
            'SCPDURL': "/test3"
        }
        s = TestService(**_kwargs)
        self.assertEqual("test", getattr(s, "serviceType"))
        self.assertEqual("test", getattr(s, "servicetype"))
        self.assertEqual("test", getattr(s, "SERVICETYPE"))
        self.assertDictEqual({
            'serviceType': "test",
            'serviceId': "test id",
            'controlURL': "/test",
            'eventSubURL': "/test2",
            'SCPDURL': "/test3"
        }, s.as_dict())

    def test_set_attr(self) -> Any[Optional[AssertionError]]:
        _kwargs = {
            'serviceType': "test",
            'serviceId': "test id",
            'controlURL': "/test",
            'eventSubURL': "/test2",
            'SCPDURL': "/test3"
        }
        s = TestService(**_kwargs)
        self.assertEqual("test", getattr(s, "serviceType"))
        s.servicetype = "foo"
        self.assertEqual("foo", getattr(s, "serviceType"))
        self.assertEqual("foo", getattr(s, "servicetype"))
        self.assertEqual("foo", getattr(s, "SERVICETYPE"))
