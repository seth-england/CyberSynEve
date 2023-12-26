import aiohttp
import CSEScraper

class CSEMessageBase:
    def __init__(self, name = ""):
        self.m_Name = name

class CSEMessageScrapeRegionOrders(CSEMessageBase):
    def __init__(self) -> None:
        super().__init__()
        self.m_RegionName = ""
        self.m_RegionId = -1

class CSEMessageScrapeRegionOrdersResult(CSEMessageBase):
    def __init__(self) -> None:
        super().__init__()
        self.m_Result = CSEScraper.RegionOrdersScrape()

class CSEMessageNewClientAuth(CSEMessageBase):
    def __init__(self):
        super().__init__()
        self.m_CharacterId = 0
        self.m_CharacterName = ""
        self.m_AccessToken = ""
        self.m_RefreshToken = ""
        self.m_ExpiresDateString = ""