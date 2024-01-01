import CSEMessages

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

class GetProfitableRoute:
  def __init__(self):
    self.m_UUID = ""
  
class GetProfitableRouteResponse:
  def __init__(self):
    self.m_UUID = ""
    self.m_Route = CSEMessages.ProfitableRoute() 


