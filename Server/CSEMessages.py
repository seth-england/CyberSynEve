import aiohttp
import CSEScraper

class CSEMessageBase:
  def __init__(self):
    pass

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
    self.m_UUID = ""

class CSEMessageUpdateClient(CSEMessageBase):
  def __init__(self):
    self.m_CharacterId = 0
    self.m_AccessToken = ""
    self.m_RefreshToken = ""

class UpdateClientResponse(CSEMessageBase):
  def __init__(self):
    self.m_CharacterId = 0
    self.m_AccessToken = ""
    self.m_RefreshToken = ""
    self.m_SystemId = 0
    self.m_RegionId = 0
    self.m_ShipId = 0

class CheckClientLogin(CSEMessageBase):
  def __init__(self):
    super().__init__()
    self.m_UUID = 0

class CheckClientLoginResponse(CSEMessageBase):
  def __init__(self):
    super().__init__()
    self.m_IsLoggedIn = False
    self.m_CharacterID = 0
    self.m_CharacterName = ""