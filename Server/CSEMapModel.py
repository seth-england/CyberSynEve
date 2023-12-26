import ProjectSettings
from copy import deepcopy
from ctypes import Array
import CSECommon
import CSEScraper
import copy
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

class CSEMapModel:
  def __init__(self):
    self.m_RegionIdToRegion = dict[int, CSERegionData]()
    self.m_SystemIdToSystem = dict[int, CSESystemData]()
    self.m_ConstellationIdToConstellation = dict[int, CSEConstellationData]()
    self.m_StargateIdToStargate = dict[int, CSEStargateData]()

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