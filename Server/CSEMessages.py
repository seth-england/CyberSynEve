import aiohttp
import CSEScraper

class CSEMessageBase:
    def __init__(self, name = ""):
        self.m_Name = name

class CSEMessageScrapeRegionOrders(CSEMessageBase):
    def __init__(self, name = "") -> None:
        super().__init__()
        self.m_RegionName = ""
        self.m_RegionId = -1

class CSEMessageScrapeRegionOrdersResult(CSEMessageBase):
    def __init__(self, name = "") -> None:
        super().__init__()
        self.m_Result = CSEScraper.RegionOrdersScrape()