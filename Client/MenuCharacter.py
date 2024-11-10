import MenuBase
import CSEClient
import MenuCharacterSelect
import urllib.parse
import CSECommon
import webbrowser
import MenuMain
import MenuFindOpportunities
import MenuViewAcceptedOpportunities

class MenuCharacter(MenuBase.MenuBase):
  def __init__(self, char : CSEClient.CSEClientCharacter):
    super().__init__()
    self.m_Character = char

  def Start(self, client : CSEClient.CSEClient):
    self.m_Client = client
    if not self.m_Character.m_LoggedIn:
      print("1) Login Character")
    else:
      print("1) Find Opportunities")
      print("2) Show Accepted Opportunities")

  def Update(self, user_input : str):
    if not self.m_Character.m_LoggedIn:
      if user_input.find('1') > -1:
        redirect_uri = urllib.parse.quote_plus(CSECommon.SERVER_AUTH_URL)
        scope = urllib.parse.quote_plus(CSECommon.SCOPES)
        param_string = f'response_type=code&redirect_uri={redirect_uri}&client_id={CSECommon.CLIENT_ID}&scope={scope}&state={self.m_Client.m_UUID} {CSECommon.CHAR_TYPE_TRADE_BOT}'
        webbrowser.open("https://login.eveonline.com/v2/oauth/authorize/?"+param_string)
        self.m_NextMenu = MenuMain.MenuMain()
      else:
        self.m_NextMenu = MenuMain.MenuMain()
    else:
      if user_input.find('1') > -1:
        self.m_NextMenu = MenuFindOpportunities.MenuFindOpportunities(self.m_Character)
      elif user_input.find('2') > -1:
        self.m_NextMenu = MenuViewAcceptedOpportunities.MenuViewAcceptedOpportunities(self.m_Character)
        self.m_NextMenu.m_NeedsAcceptedOpportunities = True
      else:
        self.m_NextMenu = MenuMain.MenuMain()     
      