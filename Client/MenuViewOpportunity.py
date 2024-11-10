import MenuBase
import CSEClient
import MenuCharacterSelect
import urllib.parse
import CSECommon
import webbrowser
import MenuMain
import CSEHTTP
import CSECharacterOpportunity
import json
import requests
import datetime
import CSEClientUtil

class MenuViewOpportunity(MenuBase.MenuBase):
  def __init__(self, opp : CSECharacterOpportunity.CSECharacterOpportunity):
    super().__init__()
    self.m_Opp = opp
    CSEClientUtil.PrintTrades(self.m_Opp.m_Trades)
    self.m_NeedsOpportunities = True

  def Start(self, client : CSEClient.CSEClient):
    self.m_Client = client
    print("a) Accept opportunity")
      
  def Update(self, user_input : str):
    user_input = user_input.capitalize()
    if user_input.find('A') > -1:
      request = CSEHTTP.AcceptOpportunity()
      request.m_UUID = self.m_Client.m_UUID
      for trade in self.m_Opp.m_Trades:
        trade.m_AcceptedTime = datetime.datetime.utcnow()
        request.m_Trades.append(trade)
      request_json = json.dumps(request, cls=CSECommon.GenericEncoder)
      try:
        requests.get(CSECommon.SERVER_ACCEPT_OPP_URL, json=request_json)
      except Exception as e:
        print("Failed to accept opportunity")
    self.m_NextMenu = MenuMain.MenuMain()