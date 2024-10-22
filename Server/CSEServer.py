# Responsible for scraping the Eve server and reporting the results
import multiprocessing.managers
import multiprocessing.process
import multiprocessing.queues
import ProjectSettings
ProjectSettings.Init()
import CSECommon
import requests
import webbrowser
import json
import CSEMapModel
import CSEScrapeHelper
import asyncio
import aiohttp
import multiprocessing
import CSEMarketModel
import CSELogging
import CSEServerOrderScraper
import CSEMessages
import typing
import pickle
import CSEItemModel
import CSEClientModel
import Workers.CSEServerClientUpdater as CSEServerClientUpdater
import threading
import time
import inspect
import queue
import copy
import CSEFileSystem
import os
import Workers.CSEServerFileWriter as CSEServerFileWriter
import CSEServerMessageSystem
import Workers.CSEServerFileWriter as CSEServerFileWriter
import CSEServerModelUpdateHelper
import CSECharacterModel
import Workers.CSEServerWorker as CSEServerWorker
import multiprocessing
import CSEServerRequestCoordinator
import Workers.CSESafetyChecker as CSESafetyChecker
import sqlite3
import SQLEntities
import SQLHelpers
import Workers.CSEServerOrderProcessor
import datetime
from multiprocessing.managers import BaseManager
from base64 import b64encode
from telnetlib import NOP

CSESERVER_ORDER_SCRAPE_WORKERS_COUNT = 1
sqlite3.threadsafety = 1

class MultiprocessingManager(multiprocessing.managers.SyncManager):
    # nothing
    pass      

class CSEServer:
  def __init__(self):
    self.m_Scrape = CSEScrapeHelper.ScrapeFileFormat()
    self.m_Connector : aiohttp.TCPConnector = None
    self.m_ClientSession : aiohttp.ClientSession = None
    self.m_MapModel = CSEMapModel.MapModel()
    self.m_RegionScrapeIndex = 0
    self.m_MarketModel = CSEMarketModel.MarketModel()
    self.m_OrderScraper : CSEServerOrderScraper.OrderScraper = None
    self.m_ItemModel = CSEItemModel.ItemModel()
    self.m_ClientModel = CSEClientModel.ClientModel()
    self.m_Thread : threading.Thread = None
    self.m_LockFlask = threading.Lock()
    self.m_MsgSystem = CSEServerMessageSystem.g_MessageSystem
    self.m_FileWriter : CSEServerFileWriter.FileWriter = None
    self.m_ModelUpdateQueue = None
    self.m_OrderProcessingQueue = list[CSEScrapeHelper.RegionOrdersScrape]()
    self.m_CharacterModel = CSECharacterModel.Model()
    self.m_WorkerClientUpdater = CSEServerWorker.Worker()
    self.m_WorkerOrderScraper = CSEServerWorker.Worker()
    self.m_WorkerOrderProcessor = CSEServerWorker.Worker()
    self.m_WorkerFileWriter = CSEServerWorker.Worker()
    self.m_WorkerSafety = CSEServerWorker.Worker()
    self.m_MultiprocessingManager = MultiprocessingManager()
    self.m_ServerRequestCoordinator : CSEServerRequestCoordinator.Coordinator = None

  def ScheduleClientUpdate(self, uuid : str):
      client_data = self.m_ClientModel.GetClientByUUID(uuid)
      if client_data:
        args = (uuid,)
        self.m_WorkerClientUpdater.m_ArgsQueue.put_nowait(args)
        self.m_WorkerClientUpdater.m_FuncQueue.put_nowait(CSEServerClientUpdater.Main)
        self.m_WorkerClientUpdater.Wake()  

def WriteScrape(scrape):
  # Write up to date scrape to file
  CSEFileSystem.WriteObjectJsonToFilePath(CSECommon.SCRAPE_FILE_PATH, scrape)

def Main(server : CSEServer):
  asyncio.run(CSEServerLoopMain(server))

async def CSEServerLoopMain(server_data : CSEServer):
  #test_conn = sqlite3.connect("Test.db")
  #SQLHelpers.CreateTable(test_conn, "TestTable", SQLEntities.SQLOrderHistory)
  #test_order = SQLEntities.SQLOrderHistory()
  #test_order.m_ID = 1
  #test_order.m_Date = (test_order.m_Date + datetime.timedelta(days=1))
  #SQLHelpers.InsertOrUpdateInstanceInTable(test_conn, "TestTable", test_order)
  #test_conn.commit()
  #test_get = SQLHelpers.GetEntityById(test_conn, "TestTable", SQLEntities.SQLOrderHistory, test_order.m_ID)
  #sqlite3.Time

  # Make sure the master db is unlocked
  clear_conn = SQLHelpers.Connect(CSECommon.MASTER_DB_PATH)
  clear_conn.commit()
  clear_conn.close()
  
  server_data.m_Connector = aiohttp.TCPConnector(limit=50)
  server_data.m_ClientSession = aiohttp.ClientSession(connector=server_data.m_Connector)
  
  server_data.m_LockFlask.acquire()

  # Get existing scrape from file
  CSELogging.Log("LOADING SCRAPE FROM FILE", __file__)

  server_data.m_MultiprocessingManager.register("MessageSystem", CSEServerMessageSystem.MessageSystem)
  server_data.m_MultiprocessingManager.register("RequestCoordinator", CSEServerRequestCoordinator.Coordinator)
  server_data.m_MultiprocessingManager.register("RegionOrdersScrape", CSEScrapeHelper.RegionOrdersScrape)
  server_data.m_MultiprocessingManager.start()

  # Set up shared message system
  server_data.m_MsgSystem = server_data.m_MultiprocessingManager.MessageSystem(server_data.m_MultiprocessingManager.list(), server_data.m_MultiprocessingManager.Lock())
  CSEServerMessageSystem.g_MessageSystem = server_data.m_MsgSystem
  server_data.m_ModelUpdateQueue = server_data.m_MultiprocessingManager.Queue()

  # Set up shared coordinator
  server_data.m_ServerRequestCoordinator = server_data.m_MultiprocessingManager.RequestCoordinator(server_data.m_MultiprocessingManager.Lock(), server_data.m_MultiprocessingManager.list())

  func_q = server_data.m_MultiprocessingManager.Queue()
  args_q = server_data.m_MultiprocessingManager.Queue()
  model_q = server_data.m_MultiprocessingManager.Queue()
  ret_q = server_data.m_MultiprocessingManager.Queue()
  condition = server_data.m_MultiprocessingManager.Condition()
  server_data.m_WorkerClientUpdater = CSEServerWorker.Worker()
  server_data.m_WorkerClientUpdater.m_FuncQueue = func_q
  server_data.m_WorkerClientUpdater.m_ArgsQueue = args_q
  server_data.m_WorkerClientUpdater.m_ModelUpdateQueue = model_q
  server_data.m_WorkerClientUpdater.m_RetQueue = ret_q
  server_data.m_WorkerClientUpdater.m_Condition = condition
  server_data.m_WorkerClientUpdater.m_Process = multiprocessing.Process(target=CSEServerWorker.Worker.WorkerMain, args=(server_data.m_WorkerClientUpdater, server_data.m_MsgSystem, func_q, args_q, model_q, condition, server_data.m_ServerRequestCoordinator, ret_q))
  server_data.m_WorkerClientUpdater.m_Process.daemon = True
  server_data.m_WorkerClientUpdater.m_Process.start()

  func_q = server_data.m_MultiprocessingManager.Queue()
  args_q = server_data.m_MultiprocessingManager.Queue()
  model_q = server_data.m_MultiprocessingManager.Queue()
  ret_q = server_data.m_MultiprocessingManager.Queue()
  condition = server_data.m_MultiprocessingManager.Condition()
  server_data.m_WorkerOrderScraper = CSEServerWorker.Worker()
  server_data.m_WorkerOrderScraper.m_FuncQueue = func_q
  server_data.m_WorkerOrderScraper.m_ArgsQueue = args_q
  server_data.m_WorkerOrderScraper.m_ModelUpdateQueue = model_q
  server_data.m_WorkerOrderScraper.m_RetQueue = ret_q
  server_data.m_WorkerOrderScraper.m_Condition = condition
  server_data.m_WorkerOrderScraper.m_Process = multiprocessing.Process(target=CSEServerWorker.Worker.WorkerMainAsync, args=(server_data.m_WorkerOrderScraper,server_data.m_MsgSystem, func_q, args_q, model_q, condition, server_data.m_ServerRequestCoordinator, ret_q))
  server_data.m_WorkerOrderScraper.m_Process.daemon = True
  server_data.m_WorkerOrderScraper.m_Process.start()

  func_q = server_data.m_MultiprocessingManager.Queue()
  args_q = server_data.m_MultiprocessingManager.Queue()
  model_q = server_data.m_MultiprocessingManager.Queue()
  ret_q = server_data.m_MultiprocessingManager.Queue()
  condition = server_data.m_MultiprocessingManager.Condition()
  server_data.m_WorkerOrderProcessor = CSEServerWorker.Worker()
  server_data.m_WorkerOrderProcessor.m_FuncQueue = func_q
  server_data.m_WorkerOrderProcessor.m_ArgsQueue = args_q
  server_data.m_WorkerOrderProcessor.m_ModelUpdateQueue = model_q
  server_data.m_WorkerOrderProcessor.m_RetQueue = ret_q
  server_data.m_WorkerOrderProcessor.m_Condition = condition
  server_data.m_WorkerOrderProcessor.m_Process = multiprocessing.Process(target=CSEServerWorker.Worker.WorkerMain, args=(server_data.m_WorkerOrderProcessor,server_data.m_MsgSystem, func_q, args_q, model_q, condition, server_data.m_ServerRequestCoordinator, ret_q))
  server_data.m_WorkerOrderProcessor.m_Process.daemon = True
  server_data.m_WorkerOrderProcessor.m_Process.start()

  func_q = server_data.m_MultiprocessingManager.Queue()
  args_q = server_data.m_MultiprocessingManager.Queue()
  model_q = server_data.m_MultiprocessingManager.Queue()
  ret_q = server_data.m_MultiprocessingManager.Queue()
  condition = server_data.m_MultiprocessingManager.Condition()
  server_data.m_WorkerFileWriter = CSEServerWorker.Worker()
  server_data.m_WorkerFileWriter.m_FuncQueue = func_q
  server_data.m_WorkerFileWriter.m_ArgsQueue = args_q
  server_data.m_WorkerFileWriter.m_ModelUpdateQueue = model_q
  server_data.m_WorkerFileWriter.m_RetQueue = ret_q
  server_data.m_WorkerFileWriter.m_Condition = condition
  server_data.m_WorkerFileWriter.m_Process = multiprocessing.Process(target=CSEServerWorker.Worker.WorkerMain, args=(server_data.m_WorkerFileWriter, server_data.m_MsgSystem, func_q, args_q, model_q, condition, server_data.m_ServerRequestCoordinator, ret_q))
  server_data.m_WorkerFileWriter.m_Process.daemon = True
  server_data.m_WorkerFileWriter.m_Process.start()

  func_q = server_data.m_MultiprocessingManager.Queue()
  args_q = server_data.m_MultiprocessingManager.Queue()
  model_q = server_data.m_MultiprocessingManager.Queue()
  ret_q = server_data.m_MultiprocessingManager.Queue()
  condition = server_data.m_MultiprocessingManager.Condition()
  server_data.m_WorkerSafety = CSEServerWorker.Worker()
  server_data.m_WorkerSafety.m_FuncQueue = func_q
  server_data.m_WorkerSafety.m_ArgsQueue = args_q
  server_data.m_WorkerSafety.m_ModelUpdateQueue = model_q
  server_data.m_WorkerSafety.m_RetQueue = ret_q
  server_data.m_WorkerSafety.m_Condition = condition
  server_data.m_WorkerSafety.m_Process = multiprocessing.Process(target=CSEServerWorker.Worker.WorkerMain, args=(server_data.m_WorkerSafety, server_data.m_MsgSystem, func_q, args_q, model_q, condition, server_data.m_ServerRequestCoordinator, ret_q))
  server_data.m_WorkerSafety.m_Process.daemon = True
  server_data.m_WorkerSafety.m_Process.start()

  CSEFileSystem.ReadObjectFromFileJson(CSECommon.SCRAPE_FILE_PATH, server_data.m_Scrape)

  if not server_data.m_Scrape.m_RegionIdsScrape.m_Valid:
    CSELogging.Log("SCRAPING REGION IDS", __file__)
    server_data.m_Scrape.m_RegionIdsScrape = CSEScrapeHelper.ScrapeRegionIds()
    CSELogging.Log("REGION IDS SCRAPED", __file__)
    WriteScrape(server_data.m_Scrape)

  if not server_data.m_Scrape.m_RegionsScrape.m_Valid:
    CSELogging.Log("SCRAPING REGIONS", __file__)
    server_data.m_Scrape.m_RegionsScrape = await CSEScrapeHelper.ScrapeRegionData(server_data.m_Scrape.m_RegionIdsScrape.m_Ids, server_data.m_ClientSession)
    CSELogging.Log("REGIONS SCRAPED", __file__)
    WriteScrape(server_data.m_Scrape)

  if not server_data.m_Scrape.m_ConstellationsScrape.m_Valid:
    CSELogging.Log("SCRAPING CONSTELLATIONS", __file__)
    constellation_ids = []
    for region_dict in server_data.m_Scrape.m_RegionsScrape.m_RegionIdToDict.values():
      for constellation_id in region_dict['constellations']:
        constellation_ids.append(constellation_id)
    server_data.m_Scrape.m_ConstellationsScrape = await CSEScrapeHelper.ScrapeConstellations(constellation_ids, server_data.m_ClientSession)
    CSELogging.Log("CONSTELLATIONS SCRAPED", __file__)
    WriteScrape(server_data.m_Scrape)
 
  if not server_data.m_Scrape.m_SystemsScrape.m_Valid:
    CSELogging.Log("SCRAPING SYSTEMS", __file__)
    system_ids = []
    for constellation_dict in server_data.m_Scrape.m_ConstellationsScrape.m_ConstellationIdToDict.values():
      constellation_systems = constellation_dict['systems']
      for system_id in constellation_systems:
        system_ids.append(system_id)
    server_data.m_Scrape.m_SystemsScrape = await CSEScrapeHelper.ScrapeSystems(system_ids, server_data.m_ClientSession)
    CSELogging.Log("SYSTEMS SCRAPED", __file__)
    WriteScrape(server_data.m_Scrape)

  if not server_data.m_Scrape.m_StargatesScrape.m_Valid:
    CSELogging.Log("SCRAPING STARGATES", __file__)
    stargate_ids = []
    for system_dict in server_data.m_Scrape.m_SystemsScrape.m_SystemsIdToDict.values():
      try:
        for stargate_id in system_dict['stargates']:
          stargate_ids.append(stargate_id)
      except:
        NOP
    server_data.m_Scrape.m_StargatesScrape = await CSEScrapeHelper.ScrapeStargates(stargate_ids, server_data.m_ClientSession)
    CSELogging.Log("STARGATES SCRAPED", __file__)
    WriteScrape(server_data.m_Scrape)

  if not server_data.m_Scrape.m_StationsScrape.m_Valid:
    CSELogging.Log("SCRAPING STATIONS", __file__)
    station_ids = []
    for system_dict in server_data.m_Scrape.m_SystemsScrape.m_SystemsIdToDict.values():
      try:
        for station_id in system_dict['stations']:
          station_ids.append(station_id)
      except:
        NOP
    server_data.m_Scrape.m_StationsScrape = await CSEScrapeHelper.ScrapeStations(station_ids, server_data.m_ClientSession)
    CSELogging.Log("SCRAPED STATIONS", __file__)
    WriteScrape(server_data.m_Scrape)

  if not server_data.m_Scrape.m_ItemsScrape.m_Valid:
    CSELogging.Log("SCRAPING ITEM TYPES", __file__)
    server_data.m_Scrape.m_ItemsScrape = await CSEScrapeHelper.ScrapeItemTypes(server_data.m_ClientSession)
    CSELogging.Log("SCRAPED ITEM TYPES", __file__)
    WriteScrape(server_data.m_Scrape)

  # Write up to date scrape to file
  WriteScrape(server_data.m_Scrape)
  CSELogging.Log("INITIAL SCRAPE COMPLETE", __file__)

  # Create map model
  CSELogging.Log("CREATE MAP MODEL", __file__)
  server_data.m_MapModel.CreateFromScrape(server_data.m_Scrape)
  
  # Create item model
  CSELogging.Log("CREATING ITEM MODEL", __file__)
  server_data.m_ItemModel.CreateFromScrape(server_data.m_Scrape.m_ItemsScrape)

  # Deserialize routes
  server_data.m_MapModel.DeserializeRouteData(CSECommon.ROUTES_FILE_PATH)

  # Deserialize client model
  CSELogging.Log("READING CLIENT MODEL FROM FILE", __file__)
  CSEFileSystem.ReadObjectFromFileJson(CSECommon.CLIENT_MODEL_FILE_PATH, server_data.m_ClientModel)

  # Deserialize market model
  CSELogging.Log("READING MARKET MODEL FROM FILE", __file__)
  CSEFileSystem.ReadObjectFromFileJson(CSECommon.MARKET_MODEL_FILE_PATH, server_data.m_MarketModel)

  # Deserialize character model
  CSELogging.Log("CREATING CHARACTER MODEL", __file__)
  CSEFileSystem.ReadObjectFromFileJson(CSECommon.CHARACTER_MODEL_FILE_PATH, server_data.m_CharacterModel)

  CSELogging.Log("STARTING THREADS", __file__)

  # Listen for model updates
  server_data.m_MsgSystem.RegisterForModelUpdateQueue(os.getpid(), server_data.m_ModelUpdateQueue)

  # Wait for threads to finish
  while True:
    if not server_data.m_WorkerClientUpdater.IsSleeping():
      continue

    if not server_data.m_WorkerFileWriter.IsSleeping():
      continue

    if not server_data.m_WorkerSafety.IsSleeping():
      continue
  
    if not server_data.m_WorkerOrderScraper.IsSleeping():
      continue
  
    if not server_data.m_WorkerOrderProcessor.IsSleeping():
      continue
    
    break

  server_data.m_WorkerFileWriter.m_FuncQueue.put_nowait(CSEServerFileWriter.Main)
  server_data.m_WorkerFileWriter.Wake()

  server_data.m_WorkerSafety.m_FuncQueue.put_nowait(CSESafetyChecker.Main)
  server_data.m_WorkerSafety.Wake()

  scrape_region_ids = list(server_data.m_MapModel.GetMajorHubRegionIds())
  #scrape_region_ids = list(server_data.m_MapModel.GetAllRegionIds())[5:]

  while True:
    # Check if we've crashed
    is_alive = server_data.m_WorkerClientUpdater.m_Process.is_alive()
    if not is_alive:
      os.abort()
    
    is_alive = server_data.m_WorkerOrderScraper.m_Process.is_alive()
    if not is_alive:
      os.abort()
      
    is_alive = server_data.m_WorkerFileWriter.m_Process.is_alive()
    if not is_alive:
      os.abort()

    is_alive = server_data.m_WorkerSafety.m_Process.is_alive()
    if not is_alive:
      os.abort()

    is_alive = server_data.m_WorkerOrderProcessor.m_Process.is_alive()
    if not is_alive:
      os.abort()

    # Manage order scraping
    if server_data.m_WorkerOrderScraper.IsSleeping():
      if not server_data.m_WorkerOrderScraper.m_RetQueue.empty():
        region_scrape : CSEScrapeHelper.RegionOrdersScrape = server_data.m_WorkerOrderScraper.m_RetQueue.get_nowait()
        server_data.m_OrderProcessingQueue.append(region_scrape)

      if server_data.m_RegionScrapeIndex >= len(scrape_region_ids):
        server_data.m_RegionScrapeIndex = 0
      region_to_scrape_id = scrape_region_ids[server_data.m_RegionScrapeIndex]
      region_to_scrape = server_data.m_MapModel.GetRegionById(region_to_scrape_id)
      if region_to_scrape:
        args = (region_to_scrape.m_Id, server_data.m_RegionScrapeIndex, region_to_scrape.m_Name)
        server_data.m_WorkerOrderScraper.m_ArgsQueue.put_nowait(args)
        server_data.m_WorkerOrderScraper.m_FuncQueue.put_nowait(CSEServerOrderScraper.Main)
        server_data.m_WorkerOrderScraper.Wake()
        server_data.m_RegionScrapeIndex += 1

    if server_data.m_WorkerOrderProcessor.IsSleeping():
      count = len(server_data.m_OrderProcessingQueue)
      if count > 0:
        scrape = server_data.m_OrderProcessingQueue[count - 1]
        args = (scrape,)
        server_data.m_WorkerOrderProcessor.m_ArgsQueue.put_nowait(args)
        server_data.m_WorkerOrderProcessor.m_FuncQueue.put_nowait(Workers.CSEServerOrderProcessor.Main)
        server_data.m_WorkerOrderProcessor.Wake()
        server_data.m_OrderProcessingQueue.pop()

    
    CSEServerModelUpdateHelper.ApplyAllUpdates(server_data.m_ModelUpdateQueue, server_data.m_MarketModel, server_data.m_ClientModel, server_data.m_MapModel, server_data.m_CharacterModel)

    # Test db locking
    test_conn = SQLHelpers.Connect(CSECommon.MASTER_DB_PATH)
    test_item_id = 41
    cursor = test_conn.execute(f'SELECT * FROM {CSECommon.TABLE_CURRENT_ORDERS} WHERE m_ItemId = ?', (test_item_id,))
    sale_records : list[SQLEntities.SQLSaleRecord] = SQLHelpers.ConstructInstancesFromCursor(cursor, SQLEntities.SQLOrder)
    test_conn.close()

    # Let http messages get processed
    server_data.m_LockFlask.release()
    time.sleep(.1)
    while server_data.m_LockFlask.locked():
      time.sleep(.1)
    server_data.m_LockFlask.acquire()
    
