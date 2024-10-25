import MenuBase
import CSEClient
import MenuCharacterSelect
import urllib.parse
import CSECommon
import webbrowser
import MenuMain
import MenuCharacter

class MenuCharacterSelect(MenuBase.MenuBase):
  def __init__(self):
    super().__init__()
    self.m_NeedsChars = True

  def Start(self, client : CSEClient.CSEClient):
    self.m_Client = client
    num_chars = len(client.m_Characters)
    self.m_Characters = client.m_Characters
    if num_chars == 0:
      print("No characters, please log one in")
      self.m_NextMenu = MenuMain.MenuMain()
    else:
      print("Select a character below") 
      for i, character in enumerate(self.m_Characters):
        print(f'{i}) {character.m_CharacterName} {"Logged In" if character.m_LoggedIn else "Logged Out"}')

  def Update(self, user_input : str):
    i = int(user_input)
    count = len(self.m_Characters)
    if i < count:
      character = self.m_Characters[i]
      self.m_NextMenu = MenuCharacter.MenuCharacter(character)
    else:
      self.m_NextMenu = MenuMain.MenuMain()
      