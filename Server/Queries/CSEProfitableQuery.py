import CSEMapModel
import CSEMarketModel
import CSEItemModel
import CSECommon
import CSECharacterModel
import sqlite3
import datetime
from CSEHTTP import CSEProfitableResult, CSEProfitableResultEntry

def ProfitableQuery(conn : sqlite3.Connection,
                    map_model : CSEMapModel.MapModel,
                    market_model : CSEMarketModel.MarketModel,
                    item_model : CSEItemModel.ItemModel,
                    char_model : CSECharacterModel.Model,
                    char_ids : list[int],
                    starting_region_id : int,
                    pct_of_recent_volume_limit : float = .1,
                    end_region_id : int | None = None, 
                    max_ship_volume : int | None = None,
                    min_order_count : int | None = None,
                    min_profit_rate : int | None = None,
                    min_profit : int | None = None) -> CSEProfitableResult:
  result = CSEProfitableResult()
  time_delta = datetime.timedelta(days=5)

  start_region = map_model.GetRegionById(starting_region_id)
  if start_region is None:
    return result

  # Build the set of relevent regions
  end_region_ids = list[int]()
  if end_region_id:
    end_region_ids.append(end_region_id)
  else:
    # Find adjacent regions
    end_region_ids = map_model.GetAdjacentRegionIds(starting_region_id)
    # Add major hubs
    hub_ids = map_model.GetMajorHubRegionIds()
    end_region_ids = end_region_ids.union(hub_ids)

  # Build the set of relevent items
  start_region_item_ids = market_model.GetItemIdsFromRegionId(conn, starting_region_id)
  filtered_item_ids = list[int]()
  for start_region_item_id in start_region_item_ids:
    start_market_item_data = market_model.GetRecentItemData(conn, starting_region_id, start_region_item_id, time_delta)
    item_data = item_model.GetItemDataFromID(start_region_item_id) 
    if start_market_item_data and item_data:
      if start_market_item_data.m_RecentSellOrderCount >= min_order_count and \
         item_data.m_Volume > CSECommon.ZERO_TOL and \
         start_market_item_data.m_RecentSellAveragePrice > CSECommon.ZERO_TOL:
        filtered_item_ids.append(start_region_item_id)

  # For each item find the most profitable region, then see if it's profitable to
  # meet our requirements
  profitable_entries = list[CSEProfitableResultEntry]()
  for item_id in filtered_item_ids:
    # Sanity check
    start_market_item_data = market_model.GetRecentItemData(conn, starting_region_id, item_id, time_delta)
    item_data = item_model.GetItemDataFromID(item_id)
    if item_data is None:
      continue
    if start_market_item_data is None:
      continue

    # How many can we fit on the ship
    item_count_capacity = CSECommon.INF
    if max_ship_volume:
      item_count_capacity = int(max_ship_volume / item_data.m_Volume)

    # For each region check profitability for that region
    for end_region_id in end_region_ids:
      potential_entry = CSEProfitableResultEntry()
      # Sanity check
      if end_region_id == starting_region_id:
        continue
      end_market_item_data = market_model.GetRecentItemData(conn, end_region_id, item_id, time_delta)
      if end_market_item_data is None:
        continue
      if end_market_item_data.m_RecentSellOrderCount < min_order_count:
        continue
      if end_market_item_data.m_RecentSellAveragePrice < CSECommon.ZERO_TOL:
        continue
      end_region = map_model.GetRegionById(end_region_id)
      if end_region is None:
        continue
      item_count = int(min(item_count_capacity, end_market_item_data.m_RecentSellVolume * pct_of_recent_volume_limit))
      item_count = int(min(item_count, start_market_item_data.m_RecentSellVolume * pct_of_recent_volume_limit))
      if item_count < 1:
        continue
      
      # Calculate profit
      buy_unit_price = start_market_item_data.m_RecentSellAveragePrice
      sell_unit_price = end_market_item_data.m_RecentSellAveragePrice
      if buy_unit_price < CSECommon.ZERO_TOL:
        continue
      if sell_unit_price < CSECommon.ZERO_TOL:
        continue
      buy_price = buy_unit_price * item_count
      sell_price = sell_unit_price * item_count
      profit = sell_price - buy_price
      rate_of_profit = profit / buy_price
      if profit < min_profit:
        continue
      if rate_of_profit < min_profit_rate:
        continue
      
      potential_entry.m_Valid = True
      potential_entry.m_ItemName = item_data.m_Name
      potential_entry.m_ItemId = item_data.m_Id
      potential_entry.m_Profit = profit
      potential_entry.m_BuyRegionId = start_region.m_Id
      potential_entry.m_BuyRegionName = start_region.m_Name
      potential_entry.m_BuyPrice = buy_price
      potential_entry.m_BuyPricePerUnit = buy_price / item_count
      potential_entry.m_BuyRegionSellOrderCount = market_model.GetSellOrderCount(conn, starting_region_id, item_id)
      potential_entry.m_ItemCount = item_count
      potential_entry.m_RateOfProfit = rate_of_profit
      potential_entry.m_SellPrice = sell_price
      potential_entry.m_SellPricePerUnit = sell_price / item_count
      potential_entry.m_SellRegionId = end_region_id
      potential_entry.m_SellRegionName = end_region.m_Name
      potential_entry.m_SellRegionSellOrderCount = market_model.GetSellOrderCount(conn, end_region_id, item_id)
      profitable_entries.append(potential_entry)

  # Sort the profitable entries
  if len(profitable_entries) > 0:
    # Sort the entries
    profitable_entries = sorted(profitable_entries, key=CSEProfitableResultEntry.SortFunc)
    profitable_entries.reverse()
    result.m_Entries = profitable_entries
    result.m_Valid = True

  # Figure out which entries are already listed
  for profitable_entry in profitable_entries:
    for char_id in char_ids:
      profitable_entry.m_AlreadyListed = char_model.HasSellOrderForItemInRegion(char_id, profitable_entry.m_ItemId, profitable_entry.m_SellRegionId)
      if profitable_entry.m_AlreadyListed:
        break

  
  return result  
