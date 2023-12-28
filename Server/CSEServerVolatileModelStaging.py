# A staging area of volatile models for other threads to pull copies from
import threading
import CSEMarketModel
import CSEClientModel

class ModelStaging:
  def __init__(self) -> None:
    self.m_Lock = threading.Lock()
    self.m_MarketModel = CSEMarketModel.MarketModel()
    self.m_ClientModel = CSEClientModel.ClientModel()
    self.m_LastStageId = 0