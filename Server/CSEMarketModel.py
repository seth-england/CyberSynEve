# Store and retrieves data about an item in a region including:
# - Price
# - Volume
import CSEScraper
import CSECommon
from datetime import datetime, timedelta

# Data for an item in a particular region
class ItemData:
  def __init__(self):
    self.m_ItemId = -1
    self.m_RecentVolume = 0
    self.m_RecentAveragePrice = 0
    self.m_RecentOrderCount = 0

class CSEMarketRegionData:
  def __init__(self) -> None:
    self.m_ItemIDToRegionItemDataValueType = ItemData
    self.m_ItemIDToRegionItemData = dict[int, ItemData]()

class MarketModel:
  def __init__(self) -> None:
    self.m_RegionIdToRegionDataValueType = CSEMarketRegionData
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

  def OnRegionOrdersScraped(self, scrape : CSEScraper.RegionOrdersScrape) -> None:
    recent_time_delta = timedelta(days=5)

    # Clear the existing region data
    region_data = CSEMarketRegionData()
    self.m_RegionIdToRegionData.update({scrape.m_RegionId : region_data})
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
        

  
