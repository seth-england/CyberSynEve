# Store and retrieves data about an item in a region including:
# - Price
# - Volume
import CSEScrapeHelper
import CSECommon
import CSEMessages
from datetime import datetime, timedelta

class ItemOrder:
  def __init__(self) -> None:
    self.m_BuyOrder = False
    self.m_Volume = 0
    self.m_Price = 0
    self.m_StationId = 0
  
  def Sort(self):
    return self.m_Price

# Data for an item in a particular region
class ItemData:
  def __init__(self):
    self.m_ItemId = -1
    self.m_RecentVolume = 0
    self.m_RecentAveragePrice = 0
    self.m_RecentHighPrice = 0
    self.m_RecentOrderCount = 0
    self.m_SellOrderVolume = 0
    self.m_BuyOrderVolume = 0
    self.m_BuyOrdersValueType = ItemOrder
    self.m_BuyOrders = list[self.m_BuyOrdersValueType]()
    self.m_SellOrdersValueType = ItemOrder
    self.m_SellOrders = list[self.m_SellOrdersValueType]()

class RegionData:
  def __init__(self) -> None:
    self.m_ItemIDToRegionItemDataValueType = ItemData
    self.m_ItemIDToRegionItemData = dict[int, ItemData]()
    self.m_RegionId = 0

class MarketModel:
  def __init__(self) -> None:
    self.m_RegionIdToRegionDataValueType = RegionData
    self.m_RegionIdToRegionData = dict[int, self.m_RegionIdToRegionDataValueType]()

  def GetSellOrderCount(self, region_id : int, item_id : int) -> int:
    result = 0
    item_data = self.GetItemDataFromRegionIdAndItemId(region_id, item_id)
    if item_data:
      if item_data.m_SellOrders:
        result = len(item_data.m_SellOrders)
    return result
  
  def GetSellOrderVolume(self, region_id : int, item_id : int) -> int:
    result = 0
    item_data = self.GetItemDataFromRegionIdAndItemId(region_id, item_id)
    if item_data:
      result = item_data.m_SellOrderVolume
    return result

  def GetMeanSellPriceOfItemBelowVolumePercent(self, region_id : int, item_id : int, volume_pct : float = .1) -> float:
    mean_price = 0.0
    item_data = self.GetItemDataFromRegionIdAndItemId(region_id, item_id)
    if item_data is None:
      return mean_price
    
    total_volume = item_data.m_SellOrderVolume
    if total_volume < CSECommon.ZERO_TOL:
      return mean_price

    # Consider the orders below a certain volume
    considered_volume = 0
    considered_price = 0
    should_break = False
    for order in item_data.m_SellOrders:
      order_volume = order.m_Volume
      new_considered_volume = considered_volume + order_volume
      new_considered_volume_pct = new_considered_volume / total_volume
      if new_considered_volume_pct > volume_pct:
        should_break = True
        sub_volume_pct = new_considered_volume_pct - volume_pct
        sub_volume = item_data.m_SellOrderVolume * sub_volume_pct
        new_considered_volume -= sub_volume
        order_volume -= sub_volume
      considered_volume = new_considered_volume
      considered_price = considered_price + order.m_Price * order_volume
      if should_break:
        break
    
    if considered_volume > CSECommon.ZERO_TOL:
      mean_price = considered_price / considered_volume
    
    return mean_price


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
    
def ConvertRegionsOrdersScrapeToRegionMarketData(scrape : CSEScrapeHelper.RegionOrdersScrape) -> RegionData():
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
      highest_price = recent_order_dict.get('highest')
      volume = recent_order_dict.get('volume')
      if average > CSECommon.ZERO_TOL and volume > CSECommon.ZERO_TOL and item_data.m_RecentVolume > 0:
        weight = volume / item_data.m_RecentVolume
        item_data.m_RecentAveragePrice = item_data.m_RecentAveragePrice + weight * average
        item_data.m_RecentHighPrice = item_data.m_RecentHighPrice + weight * highest_price

  # Process orders
  for item_id, order_dict_array in scrape.m_ItemIdToOrderDictArray.items():
    item_data = region_data.m_ItemIDToRegionItemData.get(item_id)
    if item_data is None:
      continue
    for order_dict in order_dict_array:
      item_order = ItemOrder()
      buy_order = order_dict.get('is_buy_order')
      if buy_order:
        item_order.m_BuyOrder = buy_order
      price = order_dict.get('price')
      if price:
        item_order.m_Price = price
      volume = order_dict.get('volume_remain')
      if volume:
        item_order.m_Volume = volume
      station_id = order_dict.get('location_id')
      if station_id:
        item_order.m_StationId = station_id
      if item_order.m_BuyOrder:
        item_data.m_BuyOrders.append(item_order)
        item_data.m_BuyOrderVolume += volume
      else:
        item_data.m_SellOrders.append(item_order)
        item_data.m_SellOrderVolume += volume

  # Sort orders
  for item_data in region_data.m_ItemIDToRegionItemData.values():
    item_data.m_BuyOrders = sorted(item_data.m_BuyOrders, key=ItemOrder.Sort)
    item_data.m_SellOrders = sorted(item_data.m_SellOrders, key=ItemOrder.Sort)

  return region_data   
        

  
