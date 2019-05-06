import logging
from typing import List, Any, AnyStr, Optional
from collections import OrderedDict

log = logging.getLogger(__name__)


class CaseInsensitive:
    """Case Insensitive."""

    def __init__(self, **kwargs: OrderedDict) -> None:
        """CaseInsensitive

        :param kwargs:
        """
        for k, v in kwargs.items():
            if not k.startswith("_"):
                setattr(self, k, v)

    def __getattr__(self, item: str) -> AnyStr[Optional[AttributeError]]:
        """

        :param item:
        :return:
        """
        for k in self.__class__.__dict__.keys():
            if k.lower() == item.lower():
                return self.__dict__.get(k)
        raise AttributeError(item)

    def __setattr__(self, item: str, value: str) -> AnyStr[Optional[AttributeError]]:
        """

        :param item:
        :param value:
        :return:
        """
        for k, v in self.__class__.__dict__.items():
            if k.lower() == item.lower():
                self.__dict__[k] = value
                return
        if not item.startswith("_"):
            self.__dict__[item] = value
            return
        raise AttributeError(item)

    def as_dict(self) -> OrderedDict:
        """

        :return:
        """

        def __filter_keys(*args):
            while iter(args):
                arg = next(args)
                if not arg.__str__().startswith("_"):
                    yield arg
                continue

        def __filter_values(*args):
            while iter(args):
                arg = next(args)
                if not callable(arg):
                    yield arg
                continue

        return OrderedDict({__filter_keys(self.__dict__.keys()): __filter_values(self.__dict__.values())})


class Service(CaseInsensitive):
    """Service."""

    serviceType: str = None
    serviceId: str = None
    controlURL: str = None
    eventSubURL: str = None
    SCPDURL: str = None


class Device(CaseInsensitive):
    """Device."""

    serviceList: List[Service] = None
    deviceList: List = None
    deviceType: List = None
    friendlyName: str = None
    manufacturer: str = None
    manufacturerURL: str = None
    modelDescription: str = None
    modelName: str = None
    modelNumber: int = None
    modelURL: str = None
    serialNumber: int = None
    udn: Any = None
    upc: Any = None
    presentationURL: str = None
    iconList: List = None

    def __init__(self, devices: List[AnyStr], services: List[Service], **kwargs: OrderedDict) -> None:
        """Device().

        :param devices:
        :param services:
        :param kwargs:
        """
        super(Device, self).__init__(**kwargs)
        if self.serviceList and "service" in self.serviceList:
            new_services = getattr(self.serviceList, "service")
            if isinstance(new_services, dict):
                new_services = [new_services]
            services.extend([Service(**service) for service in new_services])
        if self.deviceList:
            for kw in getattr(self.deviceList, "values"):
                if isinstance(kw, dict):
                    d = Device(devices, services, **kw)
                    devices.append(d)
                elif isinstance(kw, list):
                    for _inner_kw in kw:
                        d = Device(devices, services, **_inner_kw)
                        devices.append(d)
                else:
                    log.warning("Failed to parse device:\n%s.", kw)
