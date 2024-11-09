import ProjectSettings
from copy import deepcopy
from ctypes import Array
import CSECommon
import CSEScrapeHelper
import copy
import requests
import pickle
import CSELogging
import CSEFileSystem
import CSEServerMessageSystem
import CSEMessages
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
    self.m_Security = 0

class CSEConstellationData:
  def __init__(self):
    self.m_Name = ""
    self.m_RegionId = 0
    self.m_Id = 0

class CSEStargateData:
  def __init__(self):
    self.m_Name = ""
    self.m_DestSystemId = 0
    self.m_OriginSystemId = 0
    self.m_Id = 0

class RouteData:
  def __init__(self) -> None:
    # Route is a list of system ids
    self.m_SystemIdToSystemIdToShortestRoute = dict[int, dict[int, list[int]]]()
    self.m_LastSafetyUpdate = CSEMessages.SafetyUpdated()

class CSEStationData:
  def __init__(self) -> None:
    self.m_Name = "Invalid"
    self.m_Id = 0
    self.m_SystemId = 0

class MapModel:
  def __init__(self):
    self.m_RegionIdToRegion = dict[int, CSERegionData]()
    self.m_SystemIdToSystem = dict[int, CSESystemData]()
    self.m_ConstellationIdToConstellation = dict[int, CSEConstellationData]()
    self.m_StargateIdToStargate = dict[int, CSEStargateData]()
    self.m_StationIdToStation = dict[int, CSEStationData]()
    self.m_RouteData = RouteData()

  def GetSystemIds(self) -> list[int]:
    system_ids = list(self.m_SystemIdToSystem.keys())
    return system_ids

  def GetRegionByIndex(self, index : int) -> CSERegionData | None:
    key_list = list(self.m_RegionIdToRegion.keys())
    if index >= len(key_list):
      return None
    key = key_list[index]
    value = self.m_RegionIdToRegion.get(key)
    return value
  
  def GetAllRegionIds(self) -> list[int]:
    key_list = list(self.m_RegionIdToRegion.keys())
    return key_list
  
  def GetRegionIdBySystemId(self, system_id : int) -> int | None:
    system = self.m_SystemIdToSystem.get(system_id)
    if system is None:
      return None
    return system.m_RegionId
      
  def GetStargateById(self, stargate_id) -> CSEStargateData or None:
    return self.m_StargateIdToStargate.get(stargate_id)
  
  def GetSystemById(self, system_id) -> CSESystemData | None:
    return self.m_SystemIdToSystem.get(system_id)
  
  def GetStargateIdsFromRegionId(self, region_id) -> list[int]:
    result = list[int]()
    for stargate_id, stargate in self.m_StargateIdToStargate.items():
      stargate_region_id = self.GetRegionIdBySystemId(stargate.m_OriginSystemId)
      if stargate_region_id == region_id:
        result.append(stargate_id)
    return result
  
  def GetAdjacentRegionIds(self, region_id : int) -> set[int]:
    result_list = list[int]()
    stargate_ids = self.GetStargateIdsFromRegionId(region_id)
    for stargate_id in stargate_ids:
      stargate = self.m_StargateIdToStargate.get(stargate_id)
      if stargate:
        dest_region_id = self.GetRegionIdBySystemId(stargate.m_DestSystemId)
        if dest_region_id != region_id:
          result_list.append(dest_region_id)
    result = set(result_list)
    return result
  
  def GetSystemIdByName(self, system_name : str) -> int | None:
    for system_data in self.m_SystemIdToSystem.values():
      if system_data.m_Name == system_name:
        return system_data.m_Id
    return None
  
  def GetMajorHubRegionIds(self) -> set[int]:
    result = set[int]()
    forge_id = self.GetRegionIdByName("The Forge")
    if forge_id:
      result = result.union(set[int]({forge_id}))
    domain_id = self.GetRegionIdByName("Domain")
    if domain_id:
      result = result.union(set[int]({domain_id}))
    heimatar_id = self.GetRegionIdByName("Heimatar")
    if heimatar_id:
      result = result.union(set[int]({heimatar_id}))
    sinq_id = self.GetRegionIdByName("Sinq Laison")
    if sinq_id:
      result = result.union(set[int]({sinq_id}))
    metropolis_id = self.GetRegionIdByName("Metropolis")
    if metropolis_id:
      result = result.union(set[int]({metropolis_id}))
    curse_id = self.GetRegionIdByName("Curse")
    if curse_id:
      result = result.union(set[int]({curse_id}))
    delve_id = self.GetRegionIdByName("Delve")
    if delve_id:
      result = result.union(set[int]({delve_id}))
    stain_id = self.GetRegionIdByName("Stain")
    if stain_id:
      result = result.union(set[int]({stain_id}))
    venal_id = self.GetRegionIdByName("Venal")
    if venal_id:
      result = result.union(set[int]({venal_id}))  
    return result

  def GetMajorHubStationIds(self) -> set[int]:
    result = set[int]()
    jita_hub_id = self.GetStationIdByName("Jita IV - Moon 4 - Caldari Navy Assembly Plant")
    if jita_hub_id:
      result = result.union(set[int]({jita_hub_id}))
    amarr_hub_id = self.GetStationIdByName("Amarr VIII (Oris) - Emperor Family Academy")
    if amarr_hub_id:
      result = result.union(set[int]({amarr_hub_id}))
    rens_hub_id = self.GetStationIdByName("Rens VI - Moon 8 - Brutor Tribe Treasury")
    if rens_hub_id:
      result = result.union(set[int]({rens_hub_id}))
    dodixie_hub_id = self.GetStationIdByName("Dodixie IX - Moon 20 - Federation Navy Assembly Plant")
    if dodixie_hub_id:
      result = result.union(set[int]({dodixie_hub_id}))
    hek_hub_id = self.GetStationIdByName("Hek VIII - Moon 12 - Boundless Creation Factory")
    if hek_hub_id:
      result = result.union(set[int]({hek_hub_id}))    
    return result
  
  def RegionIdToHubId(self, region_id : int, station_ids : list[int]) -> int | None:
    for station_id in station_ids:
      station = self.m_StationIdToStation.get(station_id)
      if station:
        system = self.m_SystemIdToSystem.get(station.m_SystemId)
        if system:
          if system.m_RegionId == region_id:
            return station_id
    return None

  def GetRegionIdByName(self, name: str) -> int | None:
    for region in self.m_RegionIdToRegion.values():
      if region.m_Name == name:
        return region.m_Id
    return None

  def GetStationIdByName(self, name: str) -> int | None:
    for station in self.m_StationIdToStation.values():
      if station.m_Name == name:
        return station.m_Id
    return None    
  
  # Returns a list of system ids
  def GetRouteData(self, origin_system_id, dest_system_id, msg_system : CSEServerMessageSystem.MessageSystem) -> list[int] | None:    
    # Pull from eve servers
    url = CSECommon.EVE_ROUTE + str(origin_system_id) + '/' + str(dest_system_id) + '/'
    parameters = { 'destination': dest_system_id, 'flag': 'shortest', 'origin': origin_system_id }
    route = CSECommon.DecodeJsonFromURL(url, params=parameters)

    # Cache the route if we found it
    if route:
      msg = CSEMessages.NewRouteFound()
      msg.m_Route = route
      msg.m_OriginSystemId = origin_system_id
      msg.m_DestSystemId = dest_system_id
      msg_system.QueueModelUpdateMessage(msg)
    
    return route
  
  def HandleNewRouteFound(self, message : CSEMessages.NewRouteFound):
    if message.m_Route:
     origin_dict = self.m_RouteData.m_SystemIdToSystemIdToShortestRoute.get(message.m_OriginSystemId)
     if not origin_dict:
       origin_dict = dict[int, list[int]]()
       self.m_RouteData.m_SystemIdToSystemIdToShortestRoute[message.m_OriginSystemId] = origin_dict
     origin_dict[message.m_DestSystemId] = message.m_Route   
  
  def HandleSafetyUpdated(self, message : CSEMessages.SafetyUpdated):
    if message.m_JitaToDodixieUnsafeTime > 0:
      self.m_RouteData.m_LastSafetyUpdate.m_JitaToDodixieUnsafeTime = message.m_JitaToDodixieUnsafeTime
    if message.m_JitaToAmarrUnsafeTime > 0:
      self.m_RouteData.m_LastSafetyUpdate.m_JitaToAmarrUnsafeTime = message.m_JitaToAmarrUnsafeTime

  def SerializeRouteData(self, file_path : str):
    CSEFileSystem.WriteObjectJsonToFilePath(file_path, self.m_RouteData)

  def DeserializeRouteData(self, file_path : str):
    CSEFileSystem.ReadObjectFromFileJson(file_path, self.m_RouteData)
  
  def GetRegionById(self, region_id : int) -> CSERegionData | None:
    return self.m_RegionIdToRegion.get(region_id)
  
  def GetRegionName(self, region_id : int) -> str:
    region = self.GetRegionById(region_id)
    if region:
      return region.m_Name
    return ""

  def CreateFromScrape(self, scrape : CSEScrapeHelper.ScrapeFileFormat):
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
      stargate_entry.m_OriginSystemId = stargate_dict['system_id']
      stargate_entry.m_Id = stargate_dict['stargate_id']
      self.m_StargateIdToStargate[stargate_entry.m_Id] = stargate_entry

    # Gather the systems
    for system_dict in scrape.m_SystemsScrape.m_SystemsIdToDict.values():
      system_entry = CSESystemData()
      system_entry.m_Name = system_dict['name']
      security = system_dict.get('security_status')
      if security:
        system_entry.m_Security = security
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

    # Gather the stations
    for station_dict in scrape.m_StationsScrape.m_StationIdToDict.values():
      station_entry = CSEStationData()
      station_id = station_dict.get('station_id')
      if station_id:
        station_entry.m_Id = station_id
      name = station_dict.get('name')
      if name:
        station_entry.m_Name = name
      system_id = station_dict.get('system_id')
      if system_id:
        station_entry.m_SystemId = system_id
      self.m_StationIdToStation[station_id] = station_entry
    
    return