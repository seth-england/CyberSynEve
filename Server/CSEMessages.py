import aiohttp
import CSEScrapeHelper
import CSEHTTP
import CSEClientSettings
import CSEUndercutResult

class CSEMessageBase:
  def __init__(self):
    pass

class CSEMessageScrapeRegionOrders(CSEMessageBase):
  def __init__(self) -> None:
    super().__init__()
    self.m_RegionId = -1
    self.m_RegionName = ""
    self.m_RegionIndex = 0

class CSEMessageScrapeRegionOrdersResult(CSEMessageBase):
  def __init__(self) -> None:
    super().__init__()
    self.m_RegionName = ""
    self.m_MarketRegionData = None

class CSEMessageNewCharAuth(CSEMessageBase):
  def __init__(self):
    super().__init__()
    self.m_CharacterId = 0
    self.m_CharacterName = ""
    self.m_AccessToken = ""
    self.m_RefreshToken = ""
    self.m_ExpiresDateString = ""
    self.m_UUID = ""
    self.m_Type = ""

class CSEMessageNewClient(CSEMessageBase):
  def __init__(self):
    super().__init__()
    self.m_UUID = ""
    self.m_Settings = CSEClientSettings.Settings()

class CSEMessageUpdateClient(CSEMessageBase):
  def __init__(self):
    self.m_UUID = ""

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

class NewRouteFound(CSEMessageBase):
  def __init__(self):
    super().__init__()
    self.m_OriginSystemId = 0
    self.m_DestSystemId = 0
    self.m_Route = list[int]()

class SetClientSettings(CSEMessageBase):
  def __init__(self):
    super().__init__()
    self.m_UUID = ""
    self.m_Settings = CSEClientSettings.Settings()

class UpdateCharacterOrders(CSEMessageBase):
  def __init__(self):
    super().__init__()
    self.m_CharacterId = 0
    self.m_OrderDictArray = list[dict]()