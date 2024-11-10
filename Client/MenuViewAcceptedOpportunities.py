import MenuBase
import CSEClient
import urllib.parse
import CSECommon
import webbrowser
import MenuMain
import CSEClientUtil
import CSEHTTP
import requests

class MenuViewAcceptedOpportunities(MenuBase.MenuBase):
  def __init__(self, char : CSEClient.CSEClientCharacter):
    super().__init__()
    self.m_Character = char

  def Start(self, client : CSEClient.CSEClient):
    relevant_trades = [trade for trade in client.m_AcceptedOpportunities if trade.m_CharID == self.m_Character.m_CharacterId]
    length = len(relevant_trades)
    if length == 0:
      print("No accepted opportunities. The server may need more time to process.")
      self.m_NextMenu = MenuMain.MenuMain()
      return
    CSEClientUtil.PrintTrades(relevant_trades)
    self.m_Trades = relevant_trades
    self.m_Client = client
    print("Use x-y notation to mark opportunities are acted upon so they don't continue to show up. IE 2-6 will clear indices [2,6]")

  def Update(self, user_input : str):
    dash_index = user_input.find('-')
    if dash_index > 0 and dash_index < len(user_input) - 1:
      first_number_str = user_input[0:dash_index]
      if first_number_str.isnumeric():
        first_number = int(first_number_str)
        second_number_str = user_input[dash_index + 1:]
        if second_number_str.isnumeric():
          second_number = int(second_number_str)
          if first_number >= 0 and second_number < len(self.m_Trades):
            id_set = [trade.m_ID for trade in self.m_Trades]
            request = CSEHTTP.ClearOpportunitiesRequest()
            request.m_UUID = self.m_Client.m_UUID 
            request.m_IDs = id_set
            request_json = CSECommon.ObjectToJsonString(request)
            try: 
              requests.get(CSECommon.SERVER_CLEAR_OPPS_URL, json=request_json)
            except:
              print("Failed to delete opportunities from server.")
    self.m_NextMenu = MenuMain.MenuMain()     
      