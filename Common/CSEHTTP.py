import CSECommon
import CSEClientSettings
import CSEUndercutResult

class CSEMarketBalanceQueryResult:
  def __init__(self) -> None:
    self.m_Valid = False
    self.m_Balance = 0

class CSEProfitableResultEntry:
  def __init__(self) -> None:
    self.m_Valid = False
    self.m_ItemName = ""
    self.m_ItemId = 0
    self.m_Profit = -CSECommon.INF
    self.m_BuyRegionId = 0
    self.m_BuyRegionName = ""
    self.m_BuyPrice = 0
    self.m_BuyPricePerUnit = 0
    self.m_BuyRegionSellOrderCount = 0
    self.m_ItemCount = 0
    self.m_RateOfProfit = 0.0
    self.m_SellPrice = 0
    self.m_SellPricePerUnit = 0
    self.m_SellRegionId = 0
    self.m_SellRegionName = ""
    self.m_SellRegionSellOrderCount = 0
    self.m_AlreadyListed = False

  def SortFunc(self):
    return self.m_RateOfProfit

class CSEProfitableResult:
  def __init__(self) -> None:
    self.m_Valid = False
    self.m_EntriesValueType = CSEProfitableResultEntry
    self.m_Entries = list[self.m_EntriesValueType]()

class CheckLoginRequest:
  def __init__(self):
    self.m_UUID = ""
    pass

class CheckLoginRequestResponse:
  def __init__(self):
    self.m_UUID = ""
    self.m_CharacterID = 0
    self.m_CharacterName = ""
    self.m_LoggedIn = False

class PingRequest:
  def __init__(self):
    self.m_UUID = ""
    self.m_Settings = CSEClientSettings.Settings()

class GetProfitableRoute:
  def __init__(self):
    self.m_UUID = ""
  
class GetProfitableRouteResponse:
  def __init__(self):
    self.m_UUID = ""
    self.m_ProfitableResult = CSEProfitableResult()

class SetClientSettings:
  def __init__(self) -> None:
    self.m_UUID = ""
    self.m_Settings = CSEClientSettings.Settings()

class UndercutRequest:
  def __init__(self) -> None:
    self.m_UUID = ""
    self.m_CharacterId = 0

class UndercutResponse:
  def __init__(self) -> None:
    self.m_UUID = ""
    self.m_CharacterId = 0
    self.m_Result = CSEUndercutResult.CSEUndercutResult()

class MarketBalanceRequest:
  def __init__(self) -> None:
    self.m_UUID = ""

class MarketBalanceResponse:
  def __init__(self) -> None:
    self.m_UUID = ""
    self.m_Result = CSEMarketBalanceQueryResult()

class CharactersRequest:
  def __init__(self) -> None:
    self.m_UUID = ""

class CharactersResponse:
  def __init__(self) -> None:
    self.m_UUID = ""
    self.m_CharacterIds = list[int]()
    self.m_CharaterNames = list[str]()
    self.m_CharacterTypes = list[str]()
    self.m_CharacterLoggedIn = list[bool]()

class SafetyResponse:
  def __init__(self) -> None:
    self.m_JitaToDodixieSafe = True
    self.m_JitaToAmarrSafe = True