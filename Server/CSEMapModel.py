import ProjectSettings
from copy import deepcopy
from ctypes import Array
import CSECommon
import CSEScraper
import copy
from telnetlib import NOP

class CSERegionModel:
    def __init__(self) -> None:
        self.m_Name = ""
        self.m_Id = 0

class CSESystemModel:
    def __init__(self):
        self.m_Name = ""
        self.m_RegionId = 0
        self.m_Id = 0
        self.m_AdjcentSystemsIds = []
        self.m_X = 0
        self.m_Z = 0

class CSEConstellation:
    def __init__(self):
        self.m_Name = ""
        self.m_RegionId = 0
        self.m_Id = 0

class CSEStargate:
    def __init__(self):
        self.m_Name = ""
        self.m_DestSystemId = 0
        self.m_Id = 0

class CSEMapModel:
    def __init__(self):
        self.m_Regions = []
        self.m_Systems = []
        self.m_SystemIdToSystemIndex = {}
        self.m_Constellations = []
        self.m_ConstellationIdToIndex = {}
        self.m_Stargates = []
        self.m_StargateIdToIndex = {}

    def GetRegionByIndex(self, index : int) -> CSERegionModel or None:
        if index < len(self.m_Regions):
            return self.m_Regions[index]
        else:
            return None

    def GetStargateById(self, stargate_id) -> CSEStargate or None:
        index = self.m_StargateIdToIndex.get(stargate_id)
        if index:
            return self.m_Stargates[index]
        else:
            return None

    def GetSystemById(self, system_id) -> CSESystemModel | None:
        system_index = self.m_SystemIdToSystemIndex.get(system_id)
        if system_index == None:
            return None
        return self.m_Systems[system_index]    

    def CreateFromScrape(self, scrape : CSEScraper.ScrapeFileFormat):
        # Gather the regions
        for region_dict in scrape.m_RegionsScrape.m_RegionIdToDict.values():
            region_entry = CSERegionModel()
            region_entry.m_Id = region_dict["region_id"]
            region_entry.m_Name = region_dict["name"]
            self.m_Regions.append(region_entry)

        # Gather the constellations
        constellation_index = 0
        for constellation_dict in scrape.m_ConstellationsScrape.m_ConstellationIdToDict.values():
            constellation_entry = CSEConstellation()
            constellation_entry.m_Name = constellation_dict['name']
            constellation_entry.m_RegionId = constellation_dict['region_id']
            constellation_entry.m_Id = constellation_dict['constellation_id']
            self.m_Constellations.append(deepcopy(constellation_entry))
            self.m_ConstellationIdToIndex[constellation_entry.m_Id] = constellation_index
            constellation_index += 1

        # Gather the stargates
        stargate_index = 0
        for stargate_dict in scrape.m_StargatesScrape.m_StargateIdToDict.values():
            stargate_entry = CSEStargate()
            stargate_entry.m_Name = stargate_dict['name']
            destination_dict = stargate_dict['destination']
            system_id = destination_dict['system_id']
            stargate_entry.m_DestSystemId = system_id
            stargate_entry.m_Id = stargate_dict['stargate_id']
            self.m_Stargates.append(deepcopy(stargate_entry))
            self.m_StargateIdToIndex[stargate_entry.m_Id] = stargate_index
            stargate_index += 1

        # Gather the systems
        system_index = 0
        for system_dict in scrape.m_SystemsScrape.m_SystemsIdToDict.values():
            system_entry = CSESystemModel()
            system_entry.m_Name = system_dict['name']
            constellation_id = system_dict['constellation_id']
            constellation_index = self.m_ConstellationIdToIndex[constellation_id]
            constellation = self.m_Constellations[constellation_index]
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
            self.m_Systems.append(deepcopy(system_entry))
            self.m_SystemIdToSystemIndex[system_entry.m_Id] = system_index
            system_index += 1
        
        return