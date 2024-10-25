import MenuBase
import CSEClient
import MenuCharacterSelect
import urllib.parse
import CSECommon
import webbrowser
import MenuMain
import CSEHTTP
from CSECharacterOpportunity import CSECharacterOpportunity
import MenuViewOpportunity

SMALL_MAX_VOLUME = 60000
SMALL_MAX_SINGLE_VOLUME = 5000
SMALL_MAX_TOTAL_PRICE = 4000000000

BIG_MAX_VOLUME = 400000
BIG_MAX_SINGLE_VOLUME = 400000
BIG_MAX_TOTAL_PRICE = 1000000000

MIN_PROFIT = 5000000

def FindOpportunity(opps : list[CSECharacterOpportunity], trade : CSEHTTP.ProfitableTrade):
  volume = (trade.m_ItemVolume * trade.m_ItemCount)
  if trade.m_Profit < MIN_PROFIT:
    return None
  
  for opp in opps:
    if trade.m_EndRegionID != opp.m_EndRegionID:
      continue
    if trade.m_CharID != opp.m_CharacterID:
      continue
    if trade.m_StartBuy != opp.m_StartBuy:
      continue
    if volume < opp.m_MinSingleVolume:
      continue
    if volume > opp.m_MaxSingleVolume:
      continue
    new_total_volume = opp.m_TotalVolume + volume
    if new_total_volume > opp.m_MaxVolume:
      continue
    new_total_sell_price = opp.m_TotalSellPrice + trade.m_EndTotalPrice
    if new_total_sell_price > opp.m_MaxTotalSellPrice:
      continue
    return opp
  return None

def CreateOpportunityFromTrade(trade : CSEHTTP.ProfitableTrade, char_name : str) -> CSECharacterOpportunity | None:
  volume = (trade.m_ItemVolume * trade.m_ItemCount)
  result = None

  if trade.m_Profit < MIN_PROFIT:
    return None

  # Small?
  if volume < SMALL_MAX_VOLUME and volume < SMALL_MAX_SINGLE_VOLUME:
    if trade.m_EndTotalPrice < SMALL_MAX_TOTAL_PRICE:
      result = CSECharacterOpportunity()
      result.m_MaxVolume = SMALL_MAX_VOLUME
      result.m_MinSingleVolume = 0.0
      result.m_MaxSingleVolume = SMALL_MAX_SINGLE_VOLUME
      result.m_MaxTotalSellPrice = SMALL_MAX_TOTAL_PRICE

  # Large?
  if result is None:
    if volume < BIG_MAX_VOLUME and volume < BIG_MAX_SINGLE_VOLUME and volume > SMALL_MAX_VOLUME:
      if trade.m_EndTotalPrice < BIG_MAX_TOTAL_PRICE:
        result = CSECharacterOpportunity()
        result.m_MaxVolume = BIG_MAX_VOLUME
        result.m_MinSingleVolume = SMALL_MAX_SINGLE_VOLUME
        result.m_MaxSingleVolume = BIG_MAX_SINGLE_VOLUME
        result.m_MaxTotalSellPrice = BIG_MAX_TOTAL_PRICE

  if result:            
    result.m_CharacterID = trade.m_CharID
    result.m_CharacterName = char_name
    result.m_StartRegionID = trade.m_StartRegionID
    result.m_StartRegionName = trade.m_StartRegionName
    result.m_EndRegionID = trade.m_EndRegionID
    result.m_EndRegionName = trade.m_EndRegionName  
    result.m_StartBuy = trade.m_StartBuy

  return result

class MenuFindOpportunities(MenuBase.MenuBase):
  def __init__(self, char : CSEClient.CSEClientCharacter):
    super().__init__()
    self.m_Character = char
    self.m_NeedsOpportunities = True

  def Start(self, client : CSEClient.CSEClient):
    self.m_Trades = client.m_ProfitableResult.m_ProfitableTrades
    self.m_Opportunities = list[CSECharacterOpportunity]()
    for trade in self.m_Trades:
      if len(self.m_Opportunities) > 100:
        break
      if trade.m_CharID != self.m_Character.m_CharacterId:
        continue
      opp = FindOpportunity(self.m_Opportunities, trade)
      if opp is None:
        opp = CreateOpportunityFromTrade(trade, self.m_Character.m_CharacterName)
        if opp:
          self.m_Opportunities.append(opp)
      if opp is None:
        continue
      opp.m_Trades.append(trade)
      opp.m_TotalBuyPrice += trade.m_StartTotalPrice
      opp.m_TotalSellPrice += trade.m_EndTotalPrice
      opp.m_TotalVolume += (trade.m_ItemVolume * trade.m_ItemCount)
      
    for opp in self.m_Opportunities:
      opp.m_Profit = opp.m_TotalSellPrice - opp.m_TotalBuyPrice
      opp.m_RateOfProfit = opp.m_Profit / opp.m_TotalBuyPrice
    
    opp_count = len(self.m_Opportunities)
    if opp_count == 0:
      print("No opportunities available, the server may need time to update")
      self.m_NextMenu = MenuMain.MenuMain()
    else:
      for i, opp in enumerate(self.m_Opportunities):
        print(f'{i}) To {opp.m_EndRegionName} Buy ({"Buy Order" if opp.m_StartBuy else "Sell Order"}) {opp.m_TotalBuyPrice:,} Volume {opp.m_TotalVolume:,} Profit {opp.m_Profit:,} Rate {opp.m_RateOfProfit * 100}')
      
  def Update(self, user_input : str):
    opp_count = len(self.m_Opportunities)
    i = None
    try:
      i = int(user_input)
    except:
      self.m_NextMenu = MenuMain.MenuMain()
      return
    if i > 0 and i < opp_count:
      opp = self.m_Opportunities[i]
      self.m_NextMenu = MenuViewOpportunity.MenuViewOpportunity(opp)
      pass
    else:
      self.m_NextMenu = MenuMain.MenuMain()