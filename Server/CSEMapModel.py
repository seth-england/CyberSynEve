import ProjectSettings
from copy import deepcopy
from ctypes import Array
import CSECommon
import CSEScraper
import copy
import requests
import pickle
import CSELogging
from telnetlib import NOP

class CSERegionData:
  def __init__(self) -> None:
    self.m_Name = ""
    self.m_Id = 0

class CSESystemData:
  def __init__(self):
    self.m_Name = ""
    self.m_RegionId = 0
    self.m_Id = 0
    self.m_AdjcentSystemsIds = []
    self.m_X = 0
    self.m_Z = 0

class CSEConstellationData:
  def __init__(self):
    self.m_Name = ""
    self.m_RegionId = 0
    self.m_Id = 0

class CSEStargateData:
  def __init__(self):
    self.m_Name = ""
    self.m_DestSystemId = 0
    self.m_Id = 0

class RouteData:
  def __init__(self) -> None:
    # Route is a list of system ids
    self.m_Version = 0
    self.m_SystemIdToSystemIdToShortestRoute = dict[int, dict[int, list[int]]]()

class CSEMapModel:
  def __init__(self):
    self.m_RegionIdToRegion = dict[int, CSERegionData]()
    self.m_SystemIdToSystem = dict[int, CSESystemData]()
    self.m_ConstellationIdToConstellation = dict[int, CSEConstellationData]()
    self.m_StargateIdToStargate = dict[int, CSEStargateData]()
    self.m_RouteData = RouteData()

  def GetRegionByIndex(self, index : int) -> CSERegionData or None:
    key_list = list(self.m_RegionIdToRegion.keys())
    if index >= len(key_list):
      return None
    key = key_list[index]
    value = self.m_RegionIdToRegion.get(key)
    return value
  
  def GetRegionIdBySystemId(self, system_id : int) -> int or None:
    system = self.m_SystemIdToSystem.get(system_id)
    if system is None:
      return None
    return system.m_RegionId
      
  def GetStargateById(self, stargate_id) -> CSEStargateData or None:
    return self.m_StargateIdToStargate.get(stargate_id)
      
  def GetSystemById(self, system_id) -> CSESystemData | None:
    return self.m_SystemIdToSystem.get(system_id)
  
  # Returns a list of system ids
  def GetRouteData(self, origin_system_id, dest_system_id) -> list[int] or None:
    # Look at already cached routes
    origin_dict = self.m_RouteData.m_SystemIdToSystemIdToShortestRoute.get(origin_system_id)
    if origin_dict:
      route = origin_dict.get(dest_system_id)
      if route:
        return route
    
    # Pull from eve servers
    url = CSECommon.EVE_ROUTE + str(origin_system_id) + '/' + str(dest_system_id) + '/'
    parameters = { 'destination': dest_system_id, 'flag': 'shortest', 'origin': origin_system_id }
    route = CSECommon.DecodeJsonFromURL(url, params=parameters)

    # Cache the route if we found it
    if route:
      if not origin_dict:
        origin_dict = dict[int, list[int]]()
        self.m_RouteData.m_SystemIdToSystemIdToShortestRoute[origin_system_id] = origin_dict
      origin_dict[dest_system_id] = route
  
  def SerializeRouteData(self, dest):
    try:
      pickle.dump(self.m_RouteData, dest)
    except:
      CSELogging.Log("FAILED TO SERIALIZE ROUTE DATA", __file__)

  def DeserializeRouteData(self, source):
    try:
      route_data = pickle.load(source)
      if route_data:
        if route_data.m_Version == self.m_RouteData.m_Version:
          self.m_RouteData = route_data
        else:
          CSELogging.Log("FAILED TO DESERIALIZE ROUTE DATA, VERSION MISMATCH", __file__)
    except:
      CSELogging.Log("FAILED TO DESERIALIZE ROUTE DATA", __file__)
    
  def CreateFromScrape(self, scrape : CSEScraper.ScrapeFileFormat):
    # Gather the regions
    for region_dict in scrape.m_RegionsScrape.m_RegionIdToDict.values():
      region_entry = CSERegionData()
      region_entry.m_Id = region_dict["region_id"]
      region_entry.m_Name = region_dict["name"]
      self.m_RegionIdToRegion[region_entry.m_Id] = region_entry

    # Gather the constellations
    for constellation_dict in scrape.m_ConstellationsScrape.m_ConstellationIdToDict.values():
      constellation_entry = CSEConstellationData()
      constellation_entry.m_Name = constellation_dict['name']
      constellation_entry.m_RegionId = constellation_dict['region_id']
      constellation_entry.m_Id = constellation_dict['constellation_id']
      self.m_ConstellationIdToConstellation[constellation_entry.m_Id] = constellation_entry

    # Gather the stargates
    for stargate_dict in scrape.m_StargatesScrape.m_StargateIdToDict.values():
      stargate_entry = CSEStargateData()
      stargate_entry.m_Name = stargate_dict['name']
      destination_dict = stargate_dict['destination']
      system_id = destination_dict['system_id']
      stargate_entry.m_DestSystemId = system_id
      stargate_entry.m_Id = stargate_dict['stargate_id']
      self.m_StargateIdToStargate[stargate_entry.m_Id] = stargate_entry

    # Gather the systems
    for system_dict in scrape.m_SystemsScrape.m_SystemsIdToDict.values():
      system_entry = CSESystemData()
      system_entry.m_Name = system_dict['name']
      constellation_id = system_dict['constellation_id']
      constellation = self.m_ConstellationIdToConstellation[constellation_id]
      system_entry.m_RegionId = constellation.m_RegionId
      system_entry.m_Id = system_dict['system_id']
      if 'stargates' in system_dict:
        for stargate_id in system_dict['stargates']:
          stargate = self.GetStargateById(stargate_id)
          if stargate:
            system_entry.m_AdjcentSystemsIds.append(stargate.m_DestSystemId)
      position_dict = system_dict['position']
      system_entry.m_X = position_dict['x']
      system_entry.m_Z = position_dict['z']
      self.m_SystemIdToSystem[system_entry.m_Id] = system_entry
    
    return