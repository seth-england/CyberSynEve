import CSEClient

class MenuBase:
  def __init__(self):
    self.m_NextMenu : MenuBase = None
    self.m_NeedsChars = False
    self.m_NeedsOpportunities = False
    self.m_NeedsAcceptedOpportunities = False
    pass

  def Start(self, client : CSEClient.CSEClient):
    pass

  def Update(self, user_input : str):
    return

  def GetNextMenu(self):
    return self.m_NextMenu
  
  def ResetFlags(self):
    self.m_NeedsChars = False

  def ResetFlags(self):
    self.m_NeedsChars = False
    self.m_NeedsOpportunities = False
    self.m_NeedsAcceptedOpportunities = False