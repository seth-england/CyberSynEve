import MenuBase
import CSEClient
import MenuCharacterSelect
import urllib.parse
import CSECommon
import webbrowser
import MenuMain
import CSEHTTP
import CSECharacterOpportunity

class MenuViewOpportunity(MenuBase.MenuBase):
  def __init__(self, opp : CSECharacterOpportunity.CSECharacterOpportunity):
    super().__init__()
    self.m_Opp = opp
    self.m_NeedsOpportunities = True

  def Start(self, client : CSEClient.CSEClient):
    for i, trade in enumerate(self.m_Opp.m_Trades):
      print(f'{i: 3}.) {trade.m_ItemCount: 4} {trade.m_StartAveragePrice/1000000: 7.3f}m {trade.m_ItemName} ROP: {trade.m_RateOfProfit * 100:.1f}% Profit: {trade.m_Profit/1000000:.1f}m')
      
  def Update(self, user_input : str):
    self.m_NextMenu = MenuMain.MenuMain()