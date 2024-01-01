# Serializes the latest versions of important files
import CSEClientModel
import CSEMapModel
import CSEMarketModel
import threading
import CSEServerModelUpdateHelper
import CSEServerMessageSystem
import CSECommon
import CSEFileSystem
import queue

class FileWriter:
  def __init__(self, client_model : CSEClientModel.ClientModel, map_model : CSEMapModel.MapModel, market_model : CSEMarketModel.MarketModel, msg_system : CSEServerMessageSystem.MessageSystem):
    self.m_ClientModel = client_model
    self.m_MapModel = map_model
    self.m_MarketModel = market_model
    self.m_Thread : threading.Thread = None
    self.m_MsgSystem = msg_system
    self.m_ModelUpdateQueue = queue.Queue()

  def Main(self):
    self.m_MsgSystem.RegisterForModelUpdateQueue(threading.get_ident(), self.m_ModelUpdateQueue)
    
    while True:
      CSEServerModelUpdateHelper.ApplyAllUpdates(self.m_ModelUpdateQueue, self.m_MarketModel, self.m_ClientModel, self.m_MapModel)

      # Write market model
      file_path = CSECommon.MARKET_MODEL_FILE_PATH
      CSEFileSystem.WriteObjectJsonToFilePath(file_path, self.m_MarketModel)

      # Write routes to file
      self.m_MapModel.SerializeRouteData(CSECommon.ROUTES_FILE_PATH)

      # Write client model to file
      CSEFileSystem.WriteObjectJsonToFilePath(CSECommon.CLIENT_MODEL_FILE_PATH, self.m_ClientModel)
