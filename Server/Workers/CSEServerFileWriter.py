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
import time
import CSECharacterModel

class FileWriter:
  def __init__(self, client_model : CSEClientModel.ClientModel, map_model : CSEMapModel.MapModel, market_model : CSEMarketModel.MarketModel, character_model : CSECharacterModel.Model, msg_system : CSEServerMessageSystem.MessageSystem):
    self.m_ClientModel = client_model
    self.m_MapModel = map_model
    self.m_MarketModel = market_model
    self.m_CharacterModel = character_model
    self.m_Thread : threading.Thread = None
    self.m_MsgSystem = msg_system
    self.m_ModelUpdateQueue = queue.Queue()

  def Main(self):
    self.m_MsgSystem.RegisterForModelUpdateQueue(threading.get_ident(), self.m_ModelUpdateQueue)
    
    while True:
      results = CSEServerModelUpdateHelper.ApplyAllUpdates(self.m_ModelUpdateQueue, self.m_MarketModel, self.m_ClientModel, self.m_MapModel, self.m_CharacterModel)

      # Write market model
      if results.m_AppliedMarketModelUpdate:
        file_path = CSECommon.MARKET_MODEL_FILE_PATH
        CSEFileSystem.WriteObjectJsonToFilePath(file_path, self.m_MarketModel)

      # Write routes to file
      if results.m_AppliedMapModelUpdate:
        self.m_MapModel.SerializeRouteData(CSECommon.ROUTES_FILE_PATH)

      # Write client model to file
      if results.m_AppliedClientModelUpdate:
        CSEFileSystem.WriteObjectJsonToFilePath(CSECommon.CLIENT_MODEL_FILE_PATH, self.m_ClientModel)

      # Write character model to file
      if results.m_AppliedCharacterModelUpdate:
        CSEFileSystem.WriteObjectJsonToFilePath(CSECommon.CHARACTER_MODEL_FILE_PATH, self.m_CharacterModel)

      time.sleep(CSECommon.STANDARD_SLEEP)
