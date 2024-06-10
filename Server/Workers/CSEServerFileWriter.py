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
import Workers.CSEServerWorker as CSEServerWorker

def Main(worker : CSEServerWorker.Worker):   
  while True:
    results = CSEServerModelUpdateHelper.ApplyAllUpdates(worker.m_ModelUpdateQueue, worker.m_AllModels.m_MarketModel, worker.m_AllModels.m_ClientModel, worker.m_AllModels.m_MapModel, worker.m_AllModels.m_CharacterModel)
    # Write market model
    if results.m_AppliedMarketModelUpdate:
      file_path = CSECommon.MARKET_MODEL_FILE_PATH
      CSEFileSystem.WriteObjectJsonToFilePath(file_path, worker.m_AllModels.m_MarketModel)
    # Write routes to file
    if results.m_AppliedMapModelUpdate:
      worker.m_AllModels.m_MapModel.SerializeRouteData(CSECommon.ROUTES_FILE_PATH)
    # Write client model to file
    if results.m_AppliedClientModelUpdate:
      CSEFileSystem.WriteObjectJsonToFilePath(CSECommon.CLIENT_MODEL_FILE_PATH, worker.m_AllModels.m_ClientModel)
    # Write character model to file
    if results.m_AppliedCharacterModelUpdate:
      CSEFileSystem.WriteObjectJsonToFilePath(CSECommon.CHARACTER_MODEL_FILE_PATH, worker.m_AllModels.m_CharacterModel)
    time.sleep(CSECommon.STANDARD_SLEEP)
