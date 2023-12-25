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
from flask import Flask, request
from base64 import b64encode
from telnetlib import NOP

class CSEServerLoopData:
    def __init__(self):
      self.m_Scrape = CSEScraper.ScrapeFileFormat()
      self.m_Connector = aiohttp.TCPConnector(limit=50)
      self.m_ClientSession = aiohttp.ClientSession(connector=self.m_Connector)
      self.m_Queue = None
      self.m_MapModel = CSEMapModel.CSEMapModel()
      self.m_RegionScrapeIndex = 0
      self.m_MarketModel = CSEMarketModel.CSEMarketModel()
      self.m_OrderScraperProcess = None
      self.m_OrderScraperPipe = None
      self.m_OrderScrapeSent = False
    
def WriteScrape(scrape):
    # Write up to date scrape to file
    scrape_file = open(CSECommon.SCRAPE_FILE_PATH, "w")
    json_string = CSECommon.GenericEncoder().encode(scrape)
    scrape_file.write(json_string)
    scrape_file.close()

def Main(queue):
  asyncio.run(CSEServerLoopMain(queue))

async def CSEServerLoopMain(queue):
    server_data = CSEServerLoopData()
    server_data.m_Queue = queue

    # Get existing scrape from file
    CSELogging.Log("LOADING SCRAPE FROM FILE", __file__)
    scrape_file = open(CSECommon.SCRAPE_FILE_PATH, "r")
    try:
        scrape_file_dict = json.load(scrape_file)
        CSECommon.SetObjectFromDict(server_data.m_Scrape, scrape_file_dict)
        CSELogging.Log("LOAD FROM FILE SUCCESS", __file__)
    except:
        CSELogging.Log("LOAD FROM FILE FAILURE", __file__)
    scrape_file.close()

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

    #server_data.m_Queue.put(server_data.m_Scrape)
    #requests.post(CSECommon.FULL_SCRAPE_URL)

    # Write up to date scrape to file
    WriteScrape(server_data.m_Scrape)
    CSELogging.Log("INITIAL SCRAPE COMPLETE", __file__)

    CSELogging.Log("INIT MAP MODEL", __file__)
    server_data.m_MapModel.CreateFromScrape(server_data.m_Scrape)

    # Start scraping orders
    server_data.m_OrderScraperPipe, order_scraper_pipe_other_side = multiprocessing.Pipe()
    server_data.m_OrderScraperProcess = multiprocessing.Process(target=CSEServerOrderScaper.Main, args=(order_scraper_pipe_other_side,))
    server_data.m_OrderScraperProcess.start()

    for region_orders_scrape in server_data.m_Scrape.m_OrdersScrape.m_RegionIdToRegionOrdersScrape.values():
         if region_orders_scrape.m_Valid is True:
            server_data.m_MarketModel.OnRegionOrdersScraped(region_orders_scrape)

    server_data.m_Scrape.m_OrdersScrape.m_Valid = True    

    while True:
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
