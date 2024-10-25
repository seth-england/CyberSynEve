import MenuBase
import CSEClient
import MenuCharacterSelect
import urllib.parse
import CSECommon
import webbrowser
import MenuMain

class MenuMain(MenuBase.MenuBase):
  def __init__(self):
    super().__init__()

  def Start(self, client : CSEClient.CSEClient):
    self.m_Client = client
    print("Select an option below: ") 
    print("1) Login New Character")
    print("2) Characters")
    pass

  def Update(self, user_input : str):
    if user_input.find('1') > -1:
      redirect_uri = urllib.parse.quote_plus(CSECommon.SERVER_AUTH_URL)
      scope = urllib.parse.quote_plus(CSECommon.SCOPES)
      param_string = f'response_type=code&redirect_uri={redirect_uri}&client_id={CSECommon.CLIENT_ID}&scope={scope}&state={self.m_Client.m_UUID} {CSECommon.CHAR_TYPE_TRADE_BOT}'
      webbrowser.open("https://login.eveonline.com/v2/oauth/authorize/?"+param_string)
      self.m_NextMenu = MenuMain()
    if user_input.find('2') > -1:
      self.m_NextMenu = MenuCharacterSelect.MenuCharacterSelect()

