# Store and retrieves data about an item in a region including:
# - Price
# - Volume
import CSEScrapeHelper
import CSECommon
import CSEMessages
import sqlite3
import SQLEntities
import SQLHelpers
from datetime import datetime, timedelta

class ItemOrder:
  def __init__(self) -> None:
    self.m_BuyOrder = False
    self.m_ItemCount = 0
    self.m_Price = 0
    self.m_StationId = 0
  
  def Sort(self):
    return self.m_Price

# Data for an item in a particular region
class ItemData:
  def __init__(self):
    self.m_ItemId = -1
    self.m_RecentVolume = 0
    self.m_RecentLowPrice = 0
    self.m_RecentAveragePrice = 0
    self.m_RecentHighPrice = 0
    self.m_RecentOrderCount = 0
    self.m_RecentSellVolumeEstimate = 0
    self.m_RecentBuyVolumeEstimate = 0
    self.m_SellOrderVolume = 0
    self.m_BuyOrderVolume = 0
    self.m_BuyOrdersValueType = ItemOrder
    self.m_BuyOrders = list[self.m_BuyOrdersValueType]()
    self.m_SellOrdersValueType = ItemOrder
    self.m_SellOrders = list[self.m_SellOrdersValueType]()

class RecentItemData:
  def __init__(self):
    self.m_ItemID = 0
    self.m_RegionID = 0
    self.m_RecentSellVolume = 0
    self.m_RecentSellTotalPrice = 0.0
    self.m_RecentSellAveragePrice = 0.0
    self.m_RecentSellOrderCount = 0
    self.m_RecentBuyTotalPrice = 0.0
    self.m_RecentBuyVolume = 0
    self.m_RecentBuyAveragePrice = 0.0
    self.m_RecentBuyOrderCount = 0

class RegionData:
  def __init__(self) -> None:
    self.m_ItemIDToRegionItemDataValueType = ItemData
    self.m_ItemIDToRegionItemData = dict[int, ItemData]()
    self.m_RegionId = 0
    self.m_Time = ""

class EstimateBuyAndSellOrderCountResult:
  def __init__(self) -> None:
    self.m_SellVolume : int = 0
    self.m_BuyVolume : int = 0

def EstimateBuyAndSellVolumeCounts(total_volume : int, low_price : float, avg_price : float, high_price : float) -> EstimateBuyAndSellOrderCountResult:
  result = EstimateBuyAndSellOrderCountResult()
  result.m_BuyVolume = total_volume
  
  # Avg price does not deviate enough from low price, everything is a buy order
  low_diff = avg_price - low_price
  if low_diff < 1000:
    return result
  
  # High and low prices are the same. Though this could mean everything is a sell order
  # be conservative and assume everything is a buy order
  low_high_range = high_price - low_price
  if low_high_range < 1000:
    return result
  
  t = low_diff / low_high_range
  result.m_SellVolume = int(t * total_volume)
  result.m_BuyVolume = int((1 - t) * total_volume)
  return result

class MarketModel:
  def __init__(self) -> None:
    self.m_RegionIdToRegionDataValueType = RegionData
    self.m_RegionIdToRegionData = dict[int, self.m_RegionIdToRegionDataValueType]()

  def GetRecentItemData(self, conn : sqlite3.Connection, region_id : int, item_id : int, time_delta : timedelta) -> RecentItemData:
    now = datetime.utcnow()
    cutoff = now - time_delta
    result = RecentItemData()
    cursor = conn.execute(f'SELECT * FROM {CSECommon.TABLE_SALE_RECORD} WHERE m_RegionID = ? AND m_ItemID = ? AND m_Date > ?', (region_id, item_id, cutoff))
    all_relevant_sales : list[SQLEntities.SQLSaleRecord] = SQLHelpers.ConstructInstancesFromCursor(cursor, SQLEntities.SQLSaleRecord)
    for sale in all_relevant_sales:
      result.m_ItemID = sale.m_ItemID
      result.m_RegionID = sale.m_RegionID
      if sale.m_BuyOrder:
        result.m_RecentBuyVolume += sale.m_Volume
        result.m_RecentBuyTotalPrice += (sale.m_Price * sale.m_Volume)
        result.m_RecentBuyOrderCount = result.m_RecentBuyOrderCount + 1
      else:
        result.m_RecentSellVolume += sale.m_Volume
        result.m_RecentSellTotalPrice += (sale.m_Price * sale.m_Volume)
        result.m_RecentSellOrderCount = result.m_RecentSellOrderCount + 1
    
    if result.m_RecentBuyVolume > 0:
      result.m_RecentBuyAveragePrice = result.m_RecentBuyTotalPrice / result.m_RecentBuyVolume
    
    if result.m_RecentSellVolume > 0:
      result.m_RecentSellAveragePrice = result.m_RecentSellTotalPrice / result.m_RecentSellVolume

    return result
  
  def GetItemIdsFromRegionId(self, conn : sqlite3.Connection, region_id : int) -> list[int]:
    result = list[int]()
    cursor = conn.execute(f'SELECT DISTINCT m_ItemID FROM {CSECommon.TABLE_CURRENT_ORDERS} WHERE m_RegionID = ?', (region_id,))
    from_current_orders : list[SQLEntities.SQLOrder] = SQLHelpers.ConstructInstancesFromCursor(cursor, SQLEntities.SQLOrder)
    cursor = conn.execute(f'SELECT DISTINCT m_ItemID FROM {CSECommon.TABLE_SALE_RECORD} WHERE m_RegionID = ?', (region_id,))
    from_sale_record : list[SQLEntities.SQLSaleRecord] = SQLHelpers.ConstructInstancesFromCursor(cursor, SQLEntities.SQLSaleRecord)
    result = [order.m_ItemID for order in from_current_orders] + [order.m_ItemID for order in from_sale_record]
    result = list(set(result))
    return result

  def GetSellOrderCount(self, conn : sqlite3.Connection, region_id : int, item_id : int) -> int:
    result = 0
    cursor = conn.execute(f'SELECT * FROM {CSECommon.TABLE_CURRENT_ORDERS} WHERE m_RegionID = ? AND m_ItemID = ?', (region_id, item_id))
    rows = cursor.fetchall()
    result = len(rows)
    return result

def ProcessRegionOrderScrape(scrape : CSEScrapeHelper.RegionOrdersScrape, conn : sqlite3.Connection):
  SQLHelpers.CreateTable(conn, CSECommon.TABLE_CURRENT_ORDERS, SQLEntities.SQLOrder)
  SQLHelpers.CreateTable(conn, CSECommon.TABLE_SALE_RECORD, SQLEntities.SQLSaleRecord)
  
  now = datetime.utcnow()
  order_id_to_order = dict[int, SQLEntities.SQLOrder]()

  for item_id, order_dict_array in scrape.m_ItemIdToOrderDictArray.items():
    for order_dict in order_dict_array:
      order = SQLEntities.SQLOrder()
      order.m_RegionID = scrape.m_RegionId

      duration = order_dict.get('duration')
      if duration:
        order.m_Duration = duration

      is_buy_order = order_dict.get('is_buy_order')
      if is_buy_order is not None:
        order.m_BuyOrder = is_buy_order

      date = order_dict.get('issued')
      if date:
        order.m_Date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")

      location_id = order_dict.get('location_id')
      if location_id:
        order.m_LocationID = location_id

      min_volume = order_dict.get('min_volume')
      if min_volume:
        order.m_MinVolume = min_volume

      order_id = order_dict.get('order_id')
      if order_id:
        order.m_ID = order_id

      price = order_dict.get('price')
      if price:
        order.m_Price = price

      range = order_dict.get('range')
      if range:
        order.m_Range = range
      
      system_id = order_dict.get('system_id')
      if system_id:
        order.m_SystemID = system_id

      type_id = order_dict.get('type_id')
      if type_id:
        order.m_ItemID = type_id

      volume_remain = order_dict.get('volume_remain')
      if volume_remain:
        order.m_VolumeRemain = volume_remain

      volume_total = order_dict.get('volume_total')
      if volume_total:
        order.m_VolumeTotal = volume_total

      order_id_to_order[order.m_ID] = order

  # Compare the current set of orders with the previous set of orders
  for order_id, order in order_id_to_order.items():
    previous_order = SQLHelpers.GetEntityById(conn, CSECommon.TABLE_CURRENT_ORDERS, SQLEntities.SQLOrder, order_id)
    if previous_order is None:
      continue

    volume_diff = previous_order.m_VolumeRemain - order.m_VolumeRemain
    if volume_diff > 0:
      sale_record = SQLEntities.SQLSaleRecord()
      sale_record.m_ID = str(order.m_ID) + str(order.m_VolumeRemain)
      sale_record.m_OrderID = order.m_ID
      sale_record.m_RegionID = order.m_RegionID
      sale_record.m_SystemID = order.m_SystemID
      sale_record.m_ItemID = order.m_ItemID
      sale_record.m_BuyOrder = order.m_BuyOrder
      sale_record.m_Date = now
      sale_record.m_Price = order.m_Price
      sale_record.m_Volume = volume_diff
      SQLHelpers.InsertOrUpdateInstanceInTable(conn, CSECommon.TABLE_SALE_RECORD, sale_record)
    
  conn.execute(f'DELETE FROM {CSECommon.TABLE_CURRENT_ORDERS} WHERE m_RegionID=?', (scrape.m_RegionId,))
  conn.commit()

  for order in order_id_to_order.values():
    SQLHelpers.InsertOrUpdateInstanceInTable(conn, CSECommon.TABLE_CURRENT_ORDERS, order)

  conn.commit()
    

  #recent_time_delta = timedelta(days=5)
  #region_data = RegionData()
  #region_data.m_RegionId = scrape.m_RegionId
  #current_date_time = datetime.now()
  #current_date_time_string = current_date_time.strftime("%H:%M:%S")
  #region_data.m_Time = current_date_time_string
  #for item_id, order_dict_array in scrape.m_ItemIdToHistoryDictArray.items():
  #  item_data = ItemData()
  #  item_data.m_ItemId = item_id
  #  region_data.m_ItemIDToRegionItemData[item_id] = item_data
  #  
  #  # Figure out which dicts are recent
  #  recent_order_dicts = list[dict]()
  #  for order_dict in order_dict_array:
  #    order_date = order_dict.get('date')
  #    if order_date is None:
  #      continue
  #    order_date_obj = datetime.strptime(order_date, "%Y-%m-%d").date()
  #    diff = datetime.today().date() - order_date_obj
  #    if diff < recent_time_delta:
  #      recent_order_dicts.append(order_dict)
#
  #  # Calulate total volume from recent orders
  #  for recent_order_dict in recent_order_dicts:
  #    volume = recent_order_dict.get('volume')
  #    if volume:
  #      item_data.m_RecentVolume += volume
  #    order_count = recent_order_dict.get('order_count')
  #    if order_count:
  #      item_data.m_RecentOrderCount += order_count
  #  
  #  for recent_order_dict in recent_order_dicts:
  #    average = recent_order_dict.get('average')
  #    highest_price = recent_order_dict.get('highest')
  #    lowest_price = recent_order_dict.get('lowest')
  #    volume = recent_order_dict.get('volume')
  #    if average > CSECommon.ZERO_TOL and volume > CSECommon.ZERO_TOL and item_data.m_RecentVolume > 0:
  #      weight = volume / item_data.m_RecentVolume
  #      item_data.m_RecentAveragePrice = item_data.m_RecentAveragePrice + weight * average
  #      item_data.m_RecentHighPrice = item_data.m_RecentHighPrice + weight * highest_price
  #      item_data.m_RecentLowPrice = item_data.m_RecentLowPrice + weight * lowest_price
#
  #  estimates = EstimateBuyAndSellVolumeCounts(item_data.m_RecentVolume, item_data.m_RecentLowPrice, item_data.m_RecentAveragePrice, item_data.m_RecentHighPrice)
  #  item_data.m_RecentBuyVolumeEstimate = estimates.m_BuyVolume
  #  item_data.m_RecentSellVolumeEstimate = estimates.m_SellVolume
#
  ## Process orders
  #for item_id, order_dict_array in scrape.m_ItemIdToOrderDictArray.items():
  #  item_data = region_data.m_ItemIDToRegionItemData.get(item_id)
  #  if item_data is None:
  #    continue
  #  for order_dict in order_dict_array:
  #    item_order = ItemOrder()
  #    buy_order = order_dict.get('is_buy_order')
  #    if buy_order:
  #      item_order.m_BuyOrder = buy_order
  #    price = order_dict.get('price')
  #    if price:
  #      item_order.m_Price = price
  #    volume = order_dict.get('volume_remain')
  #    if volume:
  #      item_order.m_ItemCount = volume
  #    station_id = order_dict.get('location_id')
  #    if station_id:
  #      item_order.m_StationId = station_id
  #    if item_order.m_BuyOrder:
  #      item_data.m_BuyOrders.append(item_order)
  #      item_data.m_BuyOrderVolume += volume
  #    else:
  #      item_data.m_SellOrders.append(item_order)
  #      item_data.m_SellOrderVolume += volume
#
  ## Sort orders
  #for item_data in region_data.m_ItemIDToRegionItemData.values():
  #  item_data.m_BuyOrders = sorted(item_data.m_BuyOrders, key=ItemOrder.Sort)
  #  item_data.m_SellOrders = sorted(item_data.m_SellOrders, key=ItemOrder.Sort)
#
  #return region_data   
        

  
