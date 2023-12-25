import ProjectSettings
from telnetlib import NOP
from tracemalloc import take_snapshot
import requests
import webbrowser
import json
import CSECommon
import time
import pickle
import inspect
import aiohttp
import asyncio
from flask import Flask, request
from base64 import b64encode
from json import JSONDecoder, JSONEncoder
app = Flask(__name__)

class ScrapeBase:
  def __init__(self) -> None:
    self.m_Version = 0
    self.m_Valid = False
    self.m_Time = time.time()

class RegionIdsScrape(ScrapeBase):
  def __init__(self) -> None:
    super().__init__()
    self.m_Ids = {}

class RegionsScrape(ScrapeBase):
  def __init__(self) -> None:
    super().__init__()
    self.m_RegionIdToDict = {}

class ConstellationsScrape(ScrapeBase):
  def __init__(self) -> None:
    super().__init__()
    self.m_ConstellationIdToDict = {}

class SystemsScrape(ScrapeBase):
  def __init__(self) -> None:
    super().__init__()
    self.m_SystemsIdToDict = {}

class StargatesScrape(ScrapeBase):
  def __init__(self) -> None:
    super().__init__()
    self.m_StargateIdToDict = {}

class StationsScrape(ScrapeBase):
  def __init__(self) -> None:
    super().__init__()
    self.m_StationIdToDict = {}

class RegionOrdersScrape(ScrapeBase):
  def __init__(self) -> None:
    super().__init__()
    self.m_Orders = []
    self.m_RegionId = 0

class OrdersScape(ScrapeBase):
  def __init__(self) -> None:
    super().__init__()
    self.m_RegionIdToRegionOrdersScrape = dict[int, RegionOrdersScrape]()

class ScrapeFileFormat:
  def __init__(self) -> None:
    self.m_Version = 0
    self.m_RegionIdsScrape = RegionIdsScrape()
    self.m_RegionsScrape = RegionsScrape()
    self.m_ConstellationsScrape = ConstellationsScrape()
    self.m_SystemsScrape = SystemsScrape()
    self.m_StargatesScrape = StargatesScrape()
    self.m_StationsScrape = StationsScrape()
    self.m_OrdersScrape = OrdersScape()

# Retrieve the region ids
def ScrapeRegionIds() :
  scrape_result = RegionIdsScrape()

  args = {'datasource' : 'tranquility'}
  res = requests.get(CSECommon.EVE_REGIONS, data=args)
  if res.status_code == CSECommon.OK_CODE:
    print("Region IDs retrieved from EVE")
  else:
    print("Region IDs could not be retrieved from EVE")
    return scrape_result

  scrape_result.m_Ids = JSONDecoder().decode(res.text)
  
  scrape_result.m_Valid = True
  scrape_result.m_Time = time.time()
  return scrape_result

async def ScrapeIdToDict(ids, client_session : aiohttp.ClientSession, eve_server_path, id_field_name):
  tasks = []
  id_to_dict = {}
  for id in ids:
    search_path = eve_server_path + str(id) + '/'
    tasks.append(asyncio.ensure_future(CSECommon.DecodeJsonAsyncHelper(client_session, search_path)))
    if len(tasks) > CSECommon.TASK_LIMIT:
      finished_dicts = await asyncio.gather(*tasks)
      for dict in finished_dicts:
        if not dict is None:
          id = dict[id_field_name]
          id_to_dict[id] = dict
      tasks.clear()
  if len(tasks) > 0:
    finished_dicts = await asyncio.gather(*tasks)
    for dict in finished_dicts:
      if not dict is None:
        id = dict[id_field_name]
        id_to_dict[id] = dict
    tasks.clear()     

  finished_dicts = await asyncio.gather(*tasks)
  for dict in finished_dicts:
    if not dict is None:
      id = dict[id_field_name]
      id_to_dict[id] = dict

  return id_to_dict

async def ScrapeRegionData(region_ids, client_session : aiohttp.ClientSession) -> RegionsScrape :
  regions_scrape = RegionsScrape()
  id_to_dict = await ScrapeIdToDict(region_ids, client_session, CSECommon.EVE_REGIONS, 'region_id')
  regions_scrape.m_RegionIdToDict = id_to_dict
  regions_scrape.m_Valid = True
  regions_scrape.m_Time = time.time()
  return regions_scrape

async def ScrapeConstellations(constellation_ids, client_session : aiohttp.ClientSession) -> ConstellationsScrape :
  constellations_scrape = ConstellationsScrape()
  id_to_dict = await ScrapeIdToDict(constellation_ids, client_session, CSECommon.EVE_CONSTELLATIONS, 'constellation_id')
  constellations_scrape.m_ConstellationIdToDict = id_to_dict
  constellations_scrape.m_Valid = True
  constellations_scrape.m_Time = time.time()
  return constellations_scrape

async def ScrapeSystems(system_ids, client_session : aiohttp.ClientSession) -> SystemsScrape:
  systems_scrape = SystemsScrape()
  id_to_dict = await ScrapeIdToDict(system_ids, client_session, CSECommon.EVE_SYSTEMS, 'system_id')
  systems_scrape.m_SystemsIdToDict = id_to_dict
  systems_scrape.m_Valid = True
  systems_scrape.m_Time = time.time()
  return systems_scrape


async def ScrapeStargates(stargate_ids, client_session : aiohttp.ClientSession) -> StargatesScrape:
  stargate_scrape = StargatesScrape()   
  id_to_dict = await ScrapeIdToDict(stargate_ids, client_session, CSECommon.EVE_STARGATES, 'stargate_id')
  stargate_scrape.m_StargateIdToDict = id_to_dict
  stargate_scrape.m_Valid = True
  stargate_scrape.m_Time = time.time()
  return stargate_scrape

async def ScrapeStations(station_ids, client_session : aiohttp.ClientSession) -> StargatesScrape:
  stations_scrape = StationsScrape()   
  id_to_dict = await ScrapeIdToDict(station_ids, client_session, CSECommon.EVE_STATIONS, 'station_id')
  stations_scrape.m_StationIdToDict = id_to_dict
  stations_scrape.m_Valid = True
  stations_scrape.m_Time = time.time()
  return stations_scrape

async def ScrapeRegionOrders(region_id, client_session : aiohttp.ClientSession) -> RegionOrdersScrape:
  region_orders_scrape = RegionOrdersScrape()
  region_orders_scrape.m_RegionId = region_id
  orders = region_orders_scrape.m_Orders
  search_path = CSECommon.EVE_MARKETS + str(region_id) + '/' + 'orders/'
  blank_page = False
  page_number = 1
  while not blank_page:
    parameters = {'page' : str(page_number), 'order_type' : 'all'}
    result = await CSECommon.DecodeJsonAsyncHelper(client_session, search_path, params = parameters)
    if result is None:
      blank_page = True
      break
    else:
      for dict in result:
        orders.append(dict)
    page_number = page_number + 1
  region_orders_scrape.m_Valid = True
  region_orders_scrape.m_Time = time.time()
  return region_orders_scrape