import datetime

class Connection:
  def __init__(self):
    self.m_SessionUUID = ""
    self.m_LastContact = datetime.datetime.now(datetime.timezone.utc)
    self.m_ClientID: int | None = None