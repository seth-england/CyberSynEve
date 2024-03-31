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
from flask import Flask, request
from base64 import b64encode
from telnetlib import NOP

class CSEServer:
  def __init__(self):
    self.m_Scrape = CSEScrapeHelper.ScrapeFileFormat()
    self.m_Connector : aiohttp.TCPConnector = None
    self.m_ClientSession : aiohttp.ClientSession = None
    self.m_MapModel = CSEMapModel.MapModel()
    self.m_RegionScrapeIndex = 28
    self.m_MarketModel = CSEMarketModel.MarketModel()
    self.m_OrderScraper : CSEServerOrderScraper.OrderScraper = None
    self.m_ItemModel = CSEItemModel.ItemModel()
    self.m_ClientModel = CSEClientModel.ClientModel()
    self.m_NextClientToUpdateIndex = 0
    self.m_ClientUpdater : CSEServerClientUpdater.ClientUpdater = None
    self.m_Thread : threading.Thread = None
    self.m_LockFlask = threading.Lock()
    self.m_MsgSystem = CSEServerMessageSystem.g_MessageSystem
    self.m_FileWriter : CSEServerFileWriter.FileWriter = None
    self.m_ModelUpdateQueue = queue.Queue()

  def ScheduleClientUpdate(self, character_id : int):
      client_data = self.m_ClientModel.GetClientByCharacterId(character_id)
      if client_data:
        message = CSEMessages.CSEMessageUpdateClient()
        message.m_CharacterId = client_data.m_CharacterId
        message.m_AccessToken = client_data.m_AccessToken
        message.m_RefreshToken = client_data.m_RefreshToken
        self.m_ClientUpdater.m_ServerToSelfQueue.put_nowait(message)

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

  # Create item model
  CSELogging.Log("CREATE ITEM MODEL", __file__)
  server_data.m_ItemModel.CreateFromScrape(server_data.m_Scrape.m_ItemsScrape)

  # Start scraping orders
  server_data.m_OrderScraper = CSEServerOrderScraper.OrderScraper()
  server_data.m_OrderScraper.m_ServerToSelfQueue = queue.Queue()
  server_data.m_OrderScraper.m_SelfToServerQueue = queue.Queue()
  server_data.m_OrderScraper.m_ItemModel = server_data.m_ItemModel
  server_data.m_OrderScraper.m_MsgSystem = server_data.m_MsgSystem
  server_data.m_OrderScraper.m_Thread = threading.Thread(target=CSEServerOrderScraper.Main, args=(server_data.m_OrderScraper,))
  server_data.m_OrderScraper.m_Thread.start()

  # Start updating clients
  server_data.m_ClientUpdater = CSEServerClientUpdater.ClientUpdater()
  server_data.m_ClientUpdater.m_ServerToSelfQueue = queue.Queue()
  server_data.m_ClientUpdater.m_SelfToServerQueue = queue.Queue()
  server_data.m_ClientUpdater.m_MapModel = copy.deepcopy(server_data.m_MapModel)
  server_data.m_ClientUpdater.m_MarketModel = copy.deepcopy(server_data.m_MarketModel)
  server_data.m_ClientUpdater.m_ClientModel = copy.deepcopy(server_data.m_ClientModel)
  server_data.m_ClientUpdater.m_MsgSystem = server_data.m_MsgSystem
  server_data.m_ClientUpdater.m_ItemModel = server_data.m_ItemModel
  server_data.m_ClientUpdater.m_Thread = threading.Thread(target=CSEServerClientUpdater.Main, args=(server_data.m_ClientUpdater,))
  server_data.m_ClientUpdater.m_Thread.start()

  # Start serializing files
  server_data.m_FileWriter = CSEServerFileWriter.FileWriter(copy.deepcopy(server_data.m_ClientModel), copy.deepcopy(server_data.m_MapModel), copy.deepcopy(server_data.m_MarketModel), server_data.m_MsgSystem)
  server_data.m_FileWriter.m_Thread = threading.Thread(target=CSEServerFileWriter.FileWriter.Main, args=(server_data.m_FileWriter,))
  server_data.m_FileWriter.m_Thread.start()

  # Listen for model updates
  server_data.m_MsgSystem.RegisterForModelUpdateQueue(threading.get_ident(), server_data.m_ModelUpdateQueue)

  while True:
    # Manage order scraping
    if server_data.m_OrderScraper.m_ServerToSelfQueue.empty():
      region_to_scrape = server_data.m_MapModel.GetRegionByIndex(server_data.m_RegionScrapeIndex)
      if region_to_scrape:
        scrape_region_orders = CSEMessages.CSEMessageScrapeRegionOrders()
        scrape_region_orders.m_RegionId = region_to_scrape.m_Id
        scrape_region_orders.m_RegionName = region_to_scrape.m_Name
        scrape_region_orders.m_RegionIndex = server_data.m_RegionScrapeIndex
        server_data.m_OrderScraper.m_ServerToSelfQueue.put_nowait(scrape_region_orders)
        server_data.m_RegionScrapeIndex += 1
      else:
        server_data.m_RegionScrapeIndex = 0
    
    CSEServerModelUpdateHelper.ApplyAllUpdates(server_data.m_ModelUpdateQueue, server_data.m_MarketModel, server_data.m_ClientModel, server_data.m_MapModel)

    # Let http messages get processed
    server_data.m_LockFlask.release()
    time.sleep(.1)
    while server_data.m_LockFlask.locked():
      time.sleep(.1)
    server_data.m_LockFlask.acquire()
    
