from collections import OrderedDict
import typing
import logging

log = logging.getLogger(__name__)


class CaseInsensitive:
    def __init__(self, **kwargs: typing.Dict[str, typing.Union[str, typing.Dict[str, typing.Any],
                                                               typing.List[typing.Any]]]) -> None:
        keys: typing.List[str] = list(kwargs.keys())
        for k in keys:
            if not k.startswith("_"):
                assert k in kwargs
                setattr(self, k, kwargs[k])

    def __getattr__(self, item: str) -> typing.Union[str, typing.Dict[str, typing.Any], typing.List]:
        keys: typing.List[str] = list(self.__class__.__dict__.keys())
        for k in keys:
            if k.lower() == item.lower():
                value: typing.Optional[typing.Union[str, typing.Dict[str, typing.Any],
                                                    typing.List]] = self.__dict__.get(k)
                assert value is not None and isinstance(value, (str, dict, list))
                return value
        raise AttributeError(item)

    def __setattr__(self, item: str,
                    value: typing.Union[str, typing.Dict[str, typing.Any], typing.List]) -> None:
        assert isinstance(value, (str, dict)), ValueError(f"got type {str(type(value))}, expected str")
        keys: typing.List[str] = list(self.__class__.__dict__.keys())
        for k in keys:
            if k.lower() == item.lower():
                self.__dict__[k] = value
                return
        if not item.startswith("_"):
            self.__dict__[item] = value
            return
        raise AttributeError(item)

    def as_dict(self) -> typing.Dict[str, typing.Union[str, typing.Dict[str, typing.Any], typing.List]]:
        result: typing.Dict[str, typing.Union[str, typing.Dict[str, typing.Any], typing.List]] = OrderedDict()
        keys: typing.List[str] = list(self.__dict__.keys())
        for k in keys:
            if not k.startswith("_"):
                result[k] = self.__getattr__(k)
        return result


class Service(CaseInsensitive):
    serviceType: typing.Optional[str] = None
    serviceId: typing.Optional[str] = None
    controlURL: typing.Optional[str] = None
    eventSubURL: typing.Optional[str] = None
    SCPDURL: typing.Optional[str] = None


class Device(CaseInsensitive):
    serviceList: typing.Optional[typing.Dict[str, typing.Union[typing.Dict[str, typing.Any], typing.List]]] = None
    deviceList: typing.Optional[typing.Dict[str, typing.Union[typing.Dict[str, typing.Any], typing.List]]] = None
    deviceType: typing.Optional[str] = None
    friendlyName: typing.Optional[str] = None
    manufacturer: typing.Optional[str] = None
    manufacturerURL: typing.Optional[str] = None
    modelDescription: typing.Optional[str] = None
    modelName: typing.Optional[str] = None
    modelNumber: typing.Optional[str] = None
    modelURL: typing.Optional[str] = None
    serialNumber: typing.Optional[str] = None
    udn: typing.Optional[str] = None
    upc: typing.Optional[str] = None
    presentationURL: typing.Optional[str] = None
    iconList: typing.Optional[str] = None

    def __init__(self, devices: typing.List['Device'], services: typing.List[Service],
                 **kwargs: typing.Dict[str, typing.Union[str, typing.Dict[str, typing.Any], typing.List]]) -> None:
        super(Device, self).__init__(**kwargs)
        if self.serviceList and "service" in self.serviceList:
            if isinstance(self.serviceList['service'], dict):
                assert isinstance(self.serviceList['service'], dict)
                svc_list: typing.Dict[str, typing.Any] = self.serviceList['service']
                services.append(Service(**svc_list))
            elif isinstance(self.serviceList['service'], list):
                services.extend(Service(**svc) for svc in self.serviceList["service"])

        if self.deviceList:
            for kw in self.deviceList.values():
                if isinstance(kw, dict):
                    devices.append(Device(devices, services, **kw))
                elif isinstance(kw, list):
                    for _inner_kw in kw:
                        devices.append(Device(devices, services, **_inner_kw))
                else:
                    log.warning("failed to parse device:\n%s", kw)
