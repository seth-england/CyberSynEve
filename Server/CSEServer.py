# Responsible for scraping the Eve server and reporting the results
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
from base64 import b64encode
from telnetlib import NOP

CSESERVER_ORDER_SCRAPE_WORKERS_COUNT = 1

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
    self.m_ModelUpdateQueue = queue.Queue()
    self.m_CharacterModel = CSECharacterModel.Model()
    self.m_WorkerClientUpdater = CSEServerWorker.Worker()
    self.m_WorkerOrderScrapers = list[CSEServerWorker.Worker]()
    self.m_WorkerFileWriter = CSEServerWorker.Worker()

  def ScheduleClientUpdate(self, uuid : str):
      client_data = self.m_ClientModel.GetClientByUUID(uuid)
      if client_data:
        args = (self.m_WorkerClientUpdater, uuid)
        self.m_WorkerClientUpdater.m_ArgsQueue.put_nowait(args)
        self.m_WorkerClientUpdater.m_FuncQueue.put_nowait(CSEServerClientUpdater.Main)
        self.m_WorkerClientUpdater.Wake()
        

def WriteScrape(scrape):
  # Write up to date scrape to file
  CSEFileSystem.WriteObjectJsonToFilePath(CSECommon.SCRAPE_FILE_PATH, scrape)

def Main(server : CSEServer):
  asyncio.run(CSEServerLoopMain(server))

async def CSEServerLoopMain(server_data : CSEServer):
  server_data.m_Connector = aiohttp.TCPConnector(limit=50)
  server_data.m_ClientSession = aiohttp.ClientSession(connector=server_data.m_Connector)
 
  server_data.m_LockFlask.acquire()

  # Get existing scrape from file
  CSELogging.Log("LOADING SCRAPE FROM FILE", __file__)

  server_data.m_WorkerClientUpdater = CSEServerWorker.Worker()
  server_data.m_WorkerClientUpdater.m_FuncQueue = queue.Queue()
  server_data.m_WorkerClientUpdater.m_ArgsQueue = queue.Queue()
  server_data.m_WorkerClientUpdater.m_MsgSystem = server_data.m_MsgSystem
  server_data.m_WorkerClientUpdater.m_Thread = threading.Thread(target=CSEServerWorker.Worker.WorkerMain, args=(server_data.m_WorkerClientUpdater,))
  server_data.m_WorkerClientUpdater.m_Thread.start()

  for i in range(0, CSESERVER_ORDER_SCRAPE_WORKERS_COUNT):
    worker = CSEServerWorker.Worker()
    worker = CSEServerWorker.Worker()
    worker.m_FuncQueue = queue.Queue()
    worker.m_ArgsQueue = queue.Queue()
    worker.m_MsgSystem = server_data.m_MsgSystem
    worker.m_Thread = threading.Thread(target=CSEServerWorker.Worker.WorkerMainAsync, args=(worker,))
    worker.m_Thread.start()
    server_data.m_WorkerOrderScrapers.append(worker)

  server_data.m_WorkerFileWriter = CSEServerWorker.Worker()
  server_data.m_WorkerFileWriter.m_FuncQueue = queue.Queue()
  server_data.m_WorkerFileWriter.m_ArgsQueue = queue.Queue()
  server_data.m_WorkerFileWriter.m_MsgSystem = server_data.m_MsgSystem
  server_data.m_WorkerFileWriter.m_Thread = threading.Thread(target=CSEServerWorker.Worker.WorkerMain, args=(server_data.m_WorkerFileWriter,))
  server_data.m_WorkerFileWriter.m_Thread.start()

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

  # Create item model
  CSELogging.Log("CREATING ITEM MODEL", __file__)
  server_data.m_ItemModel.CreateFromScrape(server_data.m_Scrape.m_ItemsScrape)

  CSELogging.Log("STARTING THREADS", __file__)

  # Listen for model updates
  server_data.m_MsgSystem.RegisterForModelUpdateQueue(threading.get_ident(), server_data.m_ModelUpdateQueue)

  # Wait for threads to finish
  while True:
    if not server_data.m_WorkerClientUpdater.IsSleeping():
      continue

    if not server_data.m_WorkerFileWriter.IsSleeping():
      continue
    
    not_sleeping = False
    for worker in server_data.m_WorkerOrderScrapers:
      if not worker.IsSleeping():
        not_sleeping = True
        break
    
    if not_sleeping:
      continue

    break

  server_data.m_WorkerFileWriter.m_FuncQueue.put_nowait(CSEServerFileWriter.Main)
  args = (server_data.m_WorkerFileWriter,)
  server_data.m_WorkerFileWriter.m_ArgsQueue.put(args)
  server_data.m_WorkerFileWriter.Wake()

  while True:
    # Manage order scraping
    for worker in server_data.m_WorkerOrderScrapers:
      if worker.IsSleeping():
          region_to_scrape = server_data.m_MapModel.GetRegionByIndex(server_data.m_RegionScrapeIndex)
          if region_to_scrape is None:
            server_data.m_RegionScrapeIndex = 0
            region_to_scrape = server_data.m_MapModel.GetRegionByIndex(server_data.m_RegionScrapeIndex)
          if region_to_scrape:
            args = (worker, region_to_scrape.m_Id, server_data.m_RegionScrapeIndex, region_to_scrape.m_Name)
            worker.m_ArgsQueue.put_nowait(args)
            worker.m_FuncQueue.put_nowait(CSEServerOrderScraper.Main)
            worker.Wake()
            server_data.m_RegionScrapeIndex += 1
    
    CSEServerModelUpdateHelper.ApplyAllUpdates(server_data.m_ModelUpdateQueue, server_data.m_MarketModel, server_data.m_ClientModel, server_data.m_MapModel, server_data.m_CharacterModel)

    # Let http messages get processed
    server_data.m_LockFlask.release()
    time.sleep(.1)
    while server_data.m_LockFlask.locked():
      time.sleep(.1)
    server_data.m_LockFlask.acquire()
    
