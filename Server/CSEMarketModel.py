# Store and retrieves data about an item in a region including:
# - Price
# - Volume
import CSEScraper
import CSECommon
import CSEMessages
from datetime import datetime, timedelta

# Data for an item in a particular region
class ItemData:
  def __init__(self):
    self.m_ItemId = -1
    self.m_RecentVolume = 0
    self.m_RecentAveragePrice = 0
    self.m_RecentOrderCount = 0

class RegionData:
  def __init__(self) -> None:
    self.m_ItemIDToRegionItemDataValueType = ItemData
    self.m_ItemIDToRegionItemData = dict[int, ItemData]()
    self.m_RegionId = 0

class MarketModel:
  def __init__(self) -> None:
    self.m_RegionIdToRegionDataValueType = RegionData
    self.m_RegionIdToRegionData = dict[int, self.m_RegionIdToRegionDataValueType]()

  def GetItemIdsFromRegionId(self, region_id : int) -> list[int]:
    region = self.m_RegionIdToRegionData.get(region_id)
    if region is None:
      return list()
    item_ids = list(region.m_ItemIDToRegionItemData.keys())
    return item_ids
  
  def GetItemDataFromRegionIdAndItemId(self, region_id : int, item_id : int) -> ItemData or None:
    region = self.m_RegionIdToRegionData.get(region_id)
    if region is None:
      return None
    item_data = region.m_ItemIDToRegionItemData.get(item_id)
    return item_data
  
  def GetUniverseItemData(self, item_id : int) -> ItemData or None:
    result = ItemData()
    
    # Get order volume and count
    total_recent_volume = 0
    for region in self.m_RegionIdToRegionData.values():
      region_item_data = region.m_ItemIDToRegionItemData.get(item_id)
      if region_item_data:
        result.m_RecentVolume += region_item_data.m_RecentVolume
        result.m_RecentOrderCount += region_item_data.m_RecentOrderCount

    if result.m_RecentVolume < CSECommon.ZERO_TOL or result.m_RecentOrderCount < CSECommon.ZERO_TOL:
      return result

    # Calculate galactic average price
    for region in self.m_RegionIdToRegionData.values():
      region_item_data = region.m_ItemIDToRegionItemData.get(item_id)
      if region_item_data:
        weight = region_item_data.m_RecentVolume / result.m_RecentVolume
        result.m_RecentAveragePrice = result.m_RecentAveragePrice + weight * region_item_data.m_RecentAveragePrice
    
    return result

  def HandleScrapeRegionOrdersResult(self, region_data : RegionData):
    self.m_RegionIdToRegionData.update({region_data.m_RegionId : region_data})
    
def ConvertRegionsOrdersScrapeToRegionMarketData(scrape : CSEScraper.RegionOrdersScrape) -> RegionData():
  recent_time_delta = timedelta(days=5)
  region_data = RegionData()
  region_data.m_RegionId = scrape.m_RegionId
  for item_id, order_dict_array in scrape.m_ItemIdToHistoryDictArray.items():
    item_data = ItemData()
    item_data.m_ItemId = item_id
    region_data.m_ItemIDToRegionItemData[item_id] = item_data
    
    # Figure out which dicts are recent
    recent_order_dicts = list[dict]()
    for order_dict in order_dict_array:
      order_date = order_dict.get('date')
      if order_date is None:
        continue
      order_date_obj = datetime.strptime(order_date, "%Y-%m-%d").date()
      diff = datetime.today().date() - order_date_obj
      if diff < recent_time_delta:
        recent_order_dicts.append(order_dict)

    # Calulate total volume from recent orders
    for recent_order_dict in recent_order_dicts:
      volume = recent_order_dict.get('volume')
      if volume:
        item_data.m_RecentVolume += volume
      order_count = recent_order_dict.get('order_count')
      if order_count:
        item_data.m_RecentOrderCount += order_count
    
    for recent_order_dict in recent_order_dicts:
      average = recent_order_dict.get('average')
      volume = recent_order_dict.get('volume')
      if average > CSECommon.ZERO_TOL and volume > CSECommon.ZERO_TOL and item_data.m_RecentVolume > 0:
        weight = volume / item_data.m_RecentVolume
        item_data.m_RecentAveragePrice = item_data.m_RecentAveragePrice + weight * average

  return region_data   
        

  
