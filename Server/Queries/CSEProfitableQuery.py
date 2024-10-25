import CSEMapModel
import CSEMarketModel
import CSEItemModel
import CSECommon
import CSECharacterModel
import sqlite3
import datetime
import MySQLHelpers
import copy
from CSEHTTP import CSEProfitableResult, CSEProfitableResultEntry, ProfitableTrade

def ProfitableQuery(conn : MySQLHelpers.Connection,
                    map_model : CSEMapModel.MapModel,
                    market_model : CSEMarketModel.MarketModel,
                    item_model : CSEItemModel.ItemModel,
                    char_model : CSECharacterModel.Model,
                    char_ids : list[int],
                    main_char_id : int,
                    starting_region_id : int,
                    pct_of_recent_volume_limit : float = .1,
                    end_region_id : int | None = None, 
                    max_ship_volume : int | None = None,
                    min_order_count : int | None = None,
                    min_profit_rate : int | None = None,
                    min_profit : int | None = None) -> CSEProfitableResult:
  result = CSEProfitableResult()
  time_delta = datetime.timedelta(days=1)
  all_possible_trades = list[ProfitableTrade]()

  start_region = map_model.GetRegionById(starting_region_id)
  if start_region is None:
    return result

  # Build the set of relevent regions
  end_region_ids = list[int]()
  if end_region_id:
    end_region_ids.append(end_region_id)
  else:
    # Add major hubs
    hub_ids = map_model.GetMajorHubRegionIds()
    end_region_ids = hub_ids

  # Assume that we're going to buy everything in the starting region,
  # create a profitable trade for buying a sell or buy order
  start_region_item_ids = item_model.GetAllItemIds()
  all_recent_item_data = market_model.GetRecentItemDataFromRegions(conn.cursor(), [starting_region_id] + list(end_region_ids), start_region_item_ids, time_delta)
  starting_region_recent_item_data = all_recent_item_data.get(starting_region_id)
  if starting_region_recent_item_data is None:
    return result

  for start_market_item_data in starting_region_recent_item_data.values():    
    item_id = start_market_item_data.m_ItemID
    item_data = item_model.GetItemDataFromID(item_id) 
    if start_market_item_data and item_data:
      if item_data.m_Volume > CSECommon.ZERO_TOL:
        # Sell order at start
        if start_market_item_data.m_RecentSellOrderCount >= min_order_count and \
           start_market_item_data.m_RecentSellAveragePrice > CSECommon.ZERO_TOL:
          trade = ProfitableTrade()
          trade.m_ItemID = item_id
          trade.m_StartRegionID = starting_region_id
          trade.m_StartBuy = False
          trade.m_StartAveragePrice = start_market_item_data.m_RecentSellAveragePrice
          trade.m_StartRegionName = start_region.m_Name
          trade.m_ItemName = item_data.m_Name
          trade.m_ItemVolume = item_data.m_Volume
          trade.m_CharID = main_char_id
          all_possible_trades.append(trade)
        
        # Buy order at start
        if start_market_item_data.m_RecentBuyOrderCount >= min_order_count and \
           start_market_item_data.m_RecentBuyAveragePrice > CSECommon.ZERO_TOL:
          trade = ProfitableTrade()
          trade.m_ItemID = item_id
          trade.m_StartRegionID = starting_region_id
          trade.m_StartBuy = True
          trade.m_StartAveragePrice = start_market_item_data.m_RecentBuyAveragePrice
          trade.m_StartRegionName = start_region.m_Name
          trade.m_ItemName = item_data.m_Name
          trade.m_ItemVolume = item_data.m_Volume
          trade.m_CharID = main_char_id
          all_possible_trades.append(trade)
          
  # For each item check other regions for a profitable trade
  item_count_capacity = CSECommon.INF
  for trade in all_possible_trades:
    if trade.m_Valid:
      continue
    for end_region_id, all_region_recent_item_data in all_recent_item_data.items():
      if end_region_id == trade.m_StartRegionID:
        continue
      end_region = map_model.GetRegionById(end_region_id)
      if end_region is None:
        continue
      end_market_item_data = all_region_recent_item_data.get(trade.m_ItemID)
      if end_market_item_data is None:
        continue
      if end_market_item_data.m_RegionID == starting_region_id:
        continue
      if end_market_item_data.m_RecentSellOrderCount < min_order_count:
          continue
      if end_market_item_data.m_RecentSellAveragePrice < CSECommon.ZERO_TOL:
          continue
      item_data = item_model.GetItemDataFromID(item_id)
      if item_data is None:
        continue
      start_market_item_data = all_recent_item_data[starting_region_id][trade.m_ItemID]
      item_count = int(min(item_count_capacity, end_market_item_data.m_RecentSellVolume * pct_of_recent_volume_limit))
      item_count = int(min(item_count, start_market_item_data.m_RecentSellVolume * pct_of_recent_volume_limit))
      if item_count < 1:
        continue
      buy_unit_price = trade.m_StartAveragePrice
      sell_unit_price = end_market_item_data.m_RecentSellAveragePrice
      if buy_unit_price < CSECommon.ZERO_TOL:
        continue
      if sell_unit_price < CSECommon.ZERO_TOL:
        continue
      buy_price = buy_unit_price * item_count
      sell_price = sell_unit_price * item_count
      profit = sell_price - buy_price
      rate_of_profit = profit / buy_price
      if profit > 0.0:
        new_trade = copy.deepcopy(trade)
        new_trade.m_EndRegionID = end_region.m_Id
        new_trade.m_EndRegionName = end_region.m_Name
        new_trade.m_ItemCount = item_count
        new_trade.m_Profit = profit
        new_trade.m_RateOfProfit = rate_of_profit
        new_trade.m_EndAveragePrice = sell_unit_price
        new_trade.m_StartTotalPrice = buy_price
        new_trade.m_EndTotalPrice = sell_price
        new_trade.m_Valid = True
        all_possible_trades.append(new_trade)

  # Figure out which entries are already listed
  for trade in all_possible_trades:
    if not trade.m_Valid:
      continue
    for char_id in char_ids:
      already_listed = char_model.HasSellOrderForItemInRegion(char_id, trade.m_ItemID, trade.m_EndRegionID)
      if already_listed:
        trade.m_Valid = False
        break
  
  all_possible_trades = [trade for trade in all_possible_trades if trade.m_Valid]
  if len(all_possible_trades) > 0:
    result.m_ProfitableTrades = all_possible_trades
    result.m_ProfitableTrades = sorted(result.m_ProfitableTrades, key=ProfitableTrade.SortByRateOfProfit)
    result.m_ProfitableTrades.reverse()
    result.m_Valid = True

  return result  
