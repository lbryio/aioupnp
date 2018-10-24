import logging
from typing import List

log = logging.getLogger(__name__)


class CaseInsensitive:
    def __init__(self, **kwargs) -> None:
        for k, v in kwargs.items():
            if not k.startswith("_"):
                getattr(self, k)
                setattr(self, k, v)

    def __getattr__(self, item):
        for k in self.__class__.__dict__.keys():
            if k.lower() == item.lower():
                return self.__dict__.get(k)
        raise AttributeError(item)

    def __setattr__(self, item, value):
        for k, v in self.__class__.__dict__.items():
            if k.lower() == item.lower():
                self.__dict__[k] = value
                return
        raise AttributeError(item)

    def as_dict(self) -> dict:
        return {
            k: v for k, v in self.__dict__.items() if not k.startswith("_") and not callable(v)
        }


class Service(CaseInsensitive):
    serviceType = None
    serviceId = None
    controlURL = None
    eventSubURL = None
    SCPDURL = None


class Device(CaseInsensitive):
    serviceList = None
    deviceList = None
    deviceType = None
    friendlyName = None
    manufacturer = None
    manufacturerURL = None
    modelDescription = None
    modelName = None
    modelNumber = None
    modelURL = None
    serialNumber = None
    udn = None
    upc = None
    presentationURL = None
    iconList = None

    def __init__(self, devices: List, services: List, **kwargs) -> None:
        super(Device, self).__init__(**kwargs)
        if self.serviceList and "service" in self.serviceList:
            new_services = self.serviceList["service"]
            if isinstance(new_services, dict):
                new_services = [new_services]
            services.extend([Service(**service) for service in new_services])
        if self.deviceList:
            for kw in self.deviceList.values():
                if isinstance(kw, dict):
                    d = Device(devices, services, **kw)
                    devices.append(d)
                elif isinstance(kw, list):
                    for _inner_kw in kw:
                        d = Device(devices, services, **_inner_kw)
                        devices.append(d)
                else:
                    log.warning("failed to parse device:\n%s", kw)
