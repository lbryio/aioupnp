def none_or_str(x):
    return None if not x or x == 'None' else str(x)


class SCPDCommands:
    def debug_commands(self) -> dict:
        raise NotImplementedError()

    @staticmethod
    async def AddPortMapping(NewRemoteHost: str, NewExternalPort: int, NewProtocol: str, NewInternalPort: int,
                       NewInternalClient: str, NewEnabled: bool, NewPortMappingDescription: str,
                       NewLeaseDuration: str = '') -> None:
        """Returns None"""
        raise NotImplementedError()

    @staticmethod
    async def GetNATRSIPStatus() -> (bool, bool):
        """Returns (NewRSIPAvailable, NewNATEnabled)"""
        raise NotImplementedError()

    @staticmethod
    async def GetGenericPortMappingEntry(NewPortMappingIndex: int) -> (none_or_str, int, str, int, str, bool, str, int):
        """
        Returns (NewRemoteHost, NewExternalPort, NewProtocol, NewInternalPort, NewInternalClient, NewEnabled,
                 NewPortMappingDescription, NewLeaseDuration)
        """
        raise NotImplementedError()

    @staticmethod
    async def GetSpecificPortMappingEntry(NewRemoteHost: str, NewExternalPort: int, NewProtocol: str) -> (int, str, bool, str, int):
        """Returns (NewInternalPort, NewInternalClient, NewEnabled, NewPortMappingDescription, NewLeaseDuration)"""
        raise NotImplementedError()

    @staticmethod
    async def SetConnectionType(NewConnectionType: str) -> None:
        """Returns None"""
        raise NotImplementedError()

    @staticmethod
    async def GetExternalIPAddress() -> str:
        """Returns (NewExternalIPAddress)"""
        raise NotImplementedError()

    @staticmethod
    async def GetConnectionTypeInfo() -> (str, str):
        """Returns (NewConnectionType, NewPossibleConnectionTypes)"""
        raise NotImplementedError()

    @staticmethod
    async def GetStatusInfo() -> (str, str, int):
        """Returns (NewConnectionStatus, NewLastConnectionError, NewUptime)"""
        raise NotImplementedError()

    @staticmethod
    async def ForceTermination() -> None:
        """Returns None"""
        raise NotImplementedError()

    @staticmethod
    async def DeletePortMapping(NewRemoteHost: str, NewExternalPort: int, NewProtocol: str) -> None:
        """Returns None"""
        raise NotImplementedError()

    @staticmethod
    async def RequestConnection() -> None:
        """Returns None"""
        raise NotImplementedError()

    @staticmethod
    async def GetCommonLinkProperties():
        """Returns (NewWANAccessType, NewLayer1UpstreamMaxBitRate, NewLayer1DownstreamMaxBitRate, NewPhysicalLinkStatus)"""
        raise NotImplementedError()

    @staticmethod
    async def GetTotalBytesSent():
        """Returns (NewTotalBytesSent)"""
        raise NotImplementedError()

    @staticmethod
    async def GetTotalBytesReceived():
        """Returns (NewTotalBytesReceived)"""
        raise NotImplementedError()

    @staticmethod
    async def GetTotalPacketsSent():
        """Returns (NewTotalPacketsSent)"""
        raise NotImplementedError()

    @staticmethod
    def GetTotalPacketsReceived():
        """Returns (NewTotalPacketsReceived)"""
        raise NotImplementedError()

    @staticmethod
    async def X_GetICSStatistics() -> (int, int, int, int, str, str):
        """Returns (TotalBytesSent, TotalBytesReceived, TotalPacketsSent, TotalPacketsReceived, Layer1DownstreamMaxBitRate, Uptime)"""
        raise NotImplementedError()

    @staticmethod
    async def GetDefaultConnectionService():
        """Returns (NewDefaultConnectionService)"""
        raise NotImplementedError()

    @staticmethod
    async def SetDefaultConnectionService(NewDefaultConnectionService: str) -> None:
        """Returns (None)"""
        raise NotImplementedError()

    @staticmethod
    async def SetEnabledForInternet(NewEnabledForInternet: bool) -> None:
        raise NotImplementedError()

    @staticmethod
    async def GetEnabledForInternet() -> bool:
        raise NotImplementedError()

    @staticmethod
    async def GetMaximumActiveConnections(NewActiveConnectionIndex: int):
        raise NotImplementedError()

    @staticmethod
    async def GetActiveConnections() -> (str, str):
        """Returns (NewActiveConnDeviceContainer, NewActiveConnectionServiceID"""
        raise NotImplementedError()
