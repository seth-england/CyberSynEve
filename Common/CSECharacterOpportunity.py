import CSEHTTP

class CSECharacterOpportunity:
  def __init__(self):
    self.m_CharacterID = 0
    self.m_CharacterName = "Invalid"
    self.m_StartRegionID = 0
    self.m_StartRegionName = "Invalid"
    self.m_EndRegionID = 0
    self.m_EndRegionName = "Invalid"
    self.m_TotalBuyPrice = 0.0
    self.m_TotalSellPrice = 0.0
    self.m_Profit = 0.0
    self.m_RateOfProfit = 0.0
    self.m_TotalVolume = 0.0
    self.m_MaxVolume = 0.0
    self.m_MinSingleVolume = 0.0
    self.m_MaxSingleVolume = 0.0
    self.m_MaxTotalSellPrice = 0.0
    self.m_StartBuy = False
    self.m_Trades = list[CSEHTTP.ProfitableTrade]()