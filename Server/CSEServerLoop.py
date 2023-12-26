# Responsible for scraping the Eve server and reporting the results
import ProjectSettings
ProjectSettings.Init()
import CSECommon
import requests
import webbrowser
import json
import CSEMapModel
import CSEScraper
import asyncio
import aiohttp
import multiprocessing
import CSEMarketModel
import CSELogging
import CSEServerOrderScaper
import CSEMessages
import typing
import pickle
import CSEItemModel
import CSEClientModel
import CSEServerClientUpdater
from flask import Flask, request
from base64 import b64encode
from telnetlib import NOP

class CSEServerLoopData:
  def __init__(self):
    self.m_Scrape = CSEScraper.ScrapeFileFormat()
    self.m_Connector = aiohttp.TCPConnector(limit=50)
    self.m_ClientSession = aiohttp.ClientSession(connector=self.m_Connector)
    self.m_ServerToLoopQueue : multiprocessing.Queue = None
    self.m_MapModel = CSEMapModel.CSEMapModel()
    self.m_RegionScrapeIndex = 0
    self.m_MarketModel = CSEMarketModel.CSEMarketModel()
    self.m_OrderScraperProcess = None
    self.m_OrderScraperPipe = None
    self.m_OrderScrapeSent = False
    self.m_ItemModel = CSEItemModel.CSEItemModel()
    self.m_ClientModel = CSEClientModel.CSEClientModel()
    self.m_NextClientToUpdateIndex = 0
    self.m_ClientUpdater : CSEServerClientUpdater.CSEServerClientUpdaterClass = None
  
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
  with open(CSECommon.SCRAPE_FILE_PATH, "wb") as scrape_file:
    pickle.dump(scrape, scrape_file)

def Main(server_to_loop_queue : multiprocessing.Queue):
  asyncio.run(CSEServerLoopMain(server_to_loop_queue))

async def CSEServerLoopMain(server_to_loop_queue : multiprocessing.Queue):
  server_data = CSEServerLoopData()
  server_data.m_ServerToLoopQueue = server_to_loop_queue

  # Get existing scrape from file
  CSELogging.Log("LOADING SCRAPE FROM FILE", __file__)
  try:
    with open(CSECommon.SCRAPE_FILE_PATH, "rb") as scrape_file:
      server_data.m_Scrape = pickle.load(scrape_file)
      if server_data.m_Scrape.m_Version != CSEScraper.ScrapeFileFormat().m_Version:
        CSELogging.Log("LOAD FROM FILE FAILURE, NEW VERSION", __file__)
        server_data.m_Scrape = CSEScraper.ScrapeFileFormat()
      else:
        CSELogging.Log("LOAD FROM FILE SUCCESS", __file__)
  except FileNotFoundError:
    CSELogging.Log("LOAD FROM FILE FAILURE COULD NOT OPEN FILE", __file__)
  except EOFError:
    CSELogging.Log("LOAD FROM FILE FAILURE REACHED UNEXPECTED END OF FILE", __file__)

  if not server_data.m_Scrape.m_ItemsScrape.m_Valid:
    CSELogging.Log("SCRAPING ITEM TYPES", __file__)
    server_data.m_Scrape.m_ItemsScrape = await CSEScraper.ScrapeItemTypes(server_data.m_ClientSession)
    CSELogging.Log("SCRAPED ITEM TYPES", __file__)
    WriteScrape(server_data.m_Scrape)

  if not server_data.m_Scrape.m_RegionIdsScrape.m_Valid:
    CSELogging.Log("SCRAPING REGION IDS", __file__)
    server_data.m_Scrape.m_RegionIdsScrape = CSEScraper.ScrapeRegionIds()
    CSELogging.Log("REGION IDS SCRAPED", __file__)
    WriteScrape(server_data.m_Scrape)

  if not server_data.m_Scrape.m_RegionsScrape.m_Valid:
    CSELogging.Log("SCRAPING REGIONS", __file__)
    server_data.m_Scrape.m_RegionsScrape = await CSEScraper.ScrapeRegionData(server_data.m_Scrape.m_RegionIdsScrape.m_Ids, server_data.m_ClientSession)
    CSELogging.Log("REGIONS SCRAPED", __file__)
    WriteScrape(server_data.m_Scrape)

  if not server_data.m_Scrape.m_ConstellationsScrape.m_Valid:
    CSELogging.Log("SCRAPING CONSTELLATIONS", __file__)
    constellation_ids = []
    for region_dict in server_data.m_Scrape.m_RegionsScrape.m_RegionIdToDict.values():
      for constellation_id in region_dict['constellations']:
        constellation_ids.append(constellation_id)
    server_data.m_Scrape.m_ConstellationsScrape = await CSEScraper.ScrapeConstellations(constellation_ids, server_data.m_ClientSession)
    CSELogging.Log("CONSTELLATIONS SCRAPED", __file__)
    WriteScrape(server_data.m_Scrape)

  if not server_data.m_Scrape.m_SystemsScrape.m_Valid:
    CSELogging.Log("SCRAPING SYSTEMS", __file__)
    system_ids = []
    for constellation_dict in server_data.m_Scrape.m_ConstellationsScrape.m_ConstellationIdToDict.values():
      constellation_systems = constellation_dict['systems']
      for system_id in constellation_systems:
        system_ids.append(system_id)
    server_data.m_Scrape.m_SystemsScrape = await CSEScraper.ScrapeSystems(system_ids, server_data.m_ClientSession)
    CSELogging.Log("SYSTEMS SCRAPED", __file__)

  if not server_data.m_Scrape.m_StargatesScrape.m_Valid:
    CSELogging.Log("SCRAPING STARGATES", __file__)
    stargate_ids = []
    for system_dict in server_data.m_Scrape.m_SystemsScrape.m_SystemsIdToDict.values():
      try:
        for stargate_id in system_dict['stargates']:
          stargate_ids.append(stargate_id)
      except:
        NOP
    server_data.m_Scrape.m_StargatesScrape = await CSEScraper.ScrapeStargates(stargate_ids, server_data.m_ClientSession)
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
    server_data.m_Scrape.m_StationsScrape = await CSEScraper.ScrapeStations(station_ids, server_data.m_ClientSession)
    CSELogging.Log("SCRAPED STATIONS", __file__)
    WriteScrape(server_data.m_Scrape)

  # Write up to date scrape to file
  WriteScrape(server_data.m_Scrape)
  CSELogging.Log("INITIAL SCRAPE COMPLETE", __file__)

  CSELogging.Log("CREATE MAP MODEL", __file__)
  server_data.m_MapModel.CreateFromScrape(server_data.m_Scrape)

  CSELogging.Log("CREATE ITEM MODEL", __file__)
  server_data.m_ItemModel.CreateFromScrape(server_data.m_Scrape.m_ItemsScrape)

  # Init order scrape from file
  for region_orders_scrape in server_data.m_Scrape.m_OrdersScrape.m_RegionIdToRegionOrdersScrape.values():
     if region_orders_scrape.m_Valid is True:
      server_data.m_MarketModel.OnRegionOrdersScraped(region_orders_scrape)
  server_data.m_Scrape.m_OrdersScrape.m_Valid = True

  # Start scraping orders
  server_data.m_OrderScraperPipe, order_scraper_pipe_other_side = multiprocessing.Pipe()
  server_data.m_OrderScraperProcess = multiprocessing.Process(target=CSEServerOrderScaper.Main, args=(order_scraper_pipe_other_side,))
  server_data.m_OrderScraperProcess.start()

  # Start updating clients
  server_data.m_ClientUpdater = CSEServerClientUpdater.CSEServerClientUpdaterClass(multiprocessing.Queue(), multiprocessing.Queue(), server_data.m_MapModel)
  server_data.m_ClientUpdater.m_Process = multiprocessing.Process(target=CSEServerClientUpdater.Main, args=(server_data.m_ClientUpdater,))
  server_data.m_ClientUpdater.m_Process.start()

  while True:
    # Manage order scraping
    if not server_data.m_OrderScrapeSent:
      region_to_scrape = server_data.m_MapModel.GetRegionByIndex(server_data.m_RegionScrapeIndex)
      if region_to_scrape:
        scrape_region_orders = CSEMessages.CSEMessageScrapeRegionOrders()
        scrape_region_orders.m_RegionId = region_to_scrape.m_Id
        scrape_region_orders.m_RegionName = region_to_scrape.m_Name
        server_data.m_OrderScraperPipe.send(scrape_region_orders)
        server_data.m_OrderScrapeSent = True
      else:
        server_data.m_RegionScrapeIndex = 0
    else:
      if server_data.m_OrderScraperPipe.poll():
        scrape_result = server_data.m_OrderScraperPipe.recv()
        if type(scrape_result) is CSEMessages.CSEMessageScrapeRegionOrdersResult:
          server_data.m_MarketModel.OnRegionOrdersScraped(scrape_result.m_Result)
          server_data.m_Scrape.m_OrdersScrape.m_RegionIdToRegionOrdersScrape.update({scrape_result.m_Result.m_RegionId : scrape_result.m_Result})
          server_data.m_RegionScrapeIndex += 1
          WriteScrape(server_data.m_Scrape)
          server_data.m_OrderScrapeSent = False

    # Handle server message
    if not server_data.m_ServerToLoopQueue.empty():
      message = server_data.m_ServerToLoopQueue.get_nowait()
      if type(message) == CSEMessages.CSEMessageNewClientAuth:
        server_data.m_ClientModel.OnNewClientAuth(message)
        server_data.ScheduleClientUpdate(message.m_CharacterId)
      else:
        raise AssertionError("Unimplemented message")
    
    # Recieve client updates from child
    while not server_data.m_ClientUpdater.m_SelfToServerQueue.empty():
      response = server_data.m_ClientUpdater.m_SelfToServerQueue.get_nowait()
      if type(response) == CSEMessages.CSEMessageUpdateClientResponse:
        server_data.m_ClientModel.HandleUpdateClientResponse(response)
      else:
        raise AssertionError("Unimplemented message")

        

        
