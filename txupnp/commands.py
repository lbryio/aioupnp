from txupnp.util import return_types, none_or_str, none


class SCPDCommands:  # TODO use type annotations
    def debug_commands(self) -> dict:
        raise NotImplementedError()

    @staticmethod
    @return_types(none)
    def AddPortMapping(NewRemoteHost: str, NewExternalPort: int, NewProtocol: str, NewInternalPort: int,
                       NewInternalClient: str, NewEnabled: bool, NewPortMappingDescription: str,
                       NewLeaseDuration: str = '') -> None:
        """Returns None"""
        raise NotImplementedError()

    @staticmethod
    @return_types(bool, bool)
    def GetNATRSIPStatus() -> (bool, bool):
        """Returns (NewRSIPAvailable, NewNATEnabled)"""
        raise NotImplementedError()

    @staticmethod
    @return_types(none_or_str, int, str, int, str, bool, str, int)
    def GetGenericPortMappingEntry(NewPortMappingIndex) -> (none_or_str, int, str, int, str, bool, str, int):
        """
        Returns (NewRemoteHost, NewExternalPort, NewProtocol, NewInternalPort, NewInternalClient, NewEnabled,
                 NewPortMappingDescription, NewLeaseDuration)
        """
        raise NotImplementedError()

    @staticmethod
    @return_types(int, str, bool, str, int)
    def GetSpecificPortMappingEntry(NewRemoteHost, NewExternalPort, NewProtocol) -> (int, str, bool, str, int):
        """Returns (NewInternalPort, NewInternalClient, NewEnabled, NewPortMappingDescription, NewLeaseDuration)"""
        raise NotImplementedError()

    @staticmethod
    @return_types(none)
    def SetConnectionType(NewConnectionType) -> None:
        """Returns None"""
        raise NotImplementedError()

    @staticmethod
    @return_types(str)
    def GetExternalIPAddress() -> str:
        """Returns (NewExternalIPAddress)"""
        raise NotImplementedError()

    @staticmethod
    @return_types(str, str)
    def GetConnectionTypeInfo() -> (str, str):
        """Returns (NewConnectionType, NewPossibleConnectionTypes)"""
        raise NotImplementedError()

    @staticmethod
    @return_types(str, str, int)
    def GetStatusInfo() -> (str, str, int):
        """Returns (NewConnectionStatus, NewLastConnectionError, NewUptime)"""
        raise NotImplementedError()

    @staticmethod
    @return_types(none)
    def ForceTermination() -> None:
        """Returns None"""
        raise NotImplementedError()

    @staticmethod
    @return_types(none)
    def DeletePortMapping(NewRemoteHost, NewExternalPort, NewProtocol) -> None:
        """Returns None"""
        raise NotImplementedError()

    @staticmethod
    @return_types(none)
    def RequestConnection() -> None:
        """Returns None"""
        raise NotImplementedError()

    @staticmethod
    def GetCommonLinkProperties():
        """Returns (NewWANAccessType, NewLayer1UpstreamMaxBitRate, NewLayer1DownstreamMaxBitRate, NewPhysicalLinkStatus)"""
        raise NotImplementedError()

    @staticmethod
    def GetTotalBytesSent():
        """Returns (NewTotalBytesSent)"""
        raise NotImplementedError()

    @staticmethod
    def GetTotalBytesReceived():
        """Returns (NewTotalBytesReceived)"""
        raise NotImplementedError()

    @staticmethod
    def GetTotalPacketsSent():
        """Returns (NewTotalPacketsSent)"""
        raise NotImplementedError()

    @staticmethod
    def GetTotalPacketsReceived():
        """Returns (NewTotalPacketsReceived)"""
        raise NotImplementedError()

    @staticmethod
    def X_GetICSStatistics():
        """Returns (TotalBytesSent, TotalBytesReceived, TotalPacketsSent, TotalPacketsReceived, Layer1DownstreamMaxBitRate, Uptime)"""
        raise NotImplementedError()

    @staticmethod
    def GetDefaultConnectionService():
        """Returns (NewDefaultConnectionService)"""
        raise NotImplementedError()

    @staticmethod
    def SetDefaultConnectionService(NewDefaultConnectionService) -> None:
        """Returns (None)"""
        raise NotImplementedError()

    @staticmethod
    @return_types(none)
    def SetEnabledForInternet(NewEnabledForInternet) -> None:
        raise NotImplementedError()

    @staticmethod
    @return_types(bool)
    def GetEnabledForInternet() -> bool:
        raise NotImplementedError()

    @staticmethod
    def GetMaximumActiveConnections(NewActiveConnectionIndex):
        raise NotImplementedError()

    @staticmethod
    @return_types(str, str)
    def GetActiveConnections() -> (str, str):
        """Returns (NewActiveConnDeviceContainer, NewActiveConnectionServiceID"""
        raise NotImplementedError()
