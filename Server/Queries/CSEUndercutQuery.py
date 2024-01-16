import CSEClientModel
from CSEUndercutResult import CSEUndercutResultEntry
from CSEUndercutResult import CSEUndercutResult
import CSEMarketModel
import CSEItemModel
import CSEMapModel

def UndercutQuery \
(
  character_id : int,
  client_model : CSEClientModel.ClientModel,
  market_model : CSEMarketModel.MarketModel,
  item_model : CSEItemModel.ItemModel,
  map_model : CSEMapModel.MapModel
) -> CSEUndercutResult:
  
  result = CSEUndercutResult()
  result.m_Valid = True
  character_orders = client_model.GetCharacterOrders(character_id)
  for character_order in character_orders:
    item_market_data = market_model.GetItemDataFromRegionIdAndItemId(character_order.m_RegionId, character_order.m_ItemTypeId)
    item_data = item_model.GetItemDataFromID(character_order.m_ItemTypeId)
    if item_data is None:
      continue
    if item_market_data is None:
      continue
    region_orders = list()
    if character_order.m_IsBuyOrder:
      region_orders = item_market_data.m_BuyOrders
    else:
      region_orders = item_market_data.m_SellOrders
    better_orders_same_station = list[CSEMarketModel.ItemOrder]()
    for region_order in region_orders:
      if region_order.m_Price < character_order.m_Price:
        if region_order.m_StationId == character_order.m_StationId:
          better_orders_same_station.append(region_order)
      else:
        break
    if len(better_orders_same_station) > 0:
      new_result = CSEUndercutResultEntry()
      new_result.m_SelfVolume = character_order.m_VolumeRemain
      new_result.m_SelfPrice = character_order.m_Price
      new_result.m_RecentSellVolumeEst = item_market_data.m_RecentVolume * .1
      new_result.m_ItemId = character_order.m_ItemTypeId
      new_result.m_ItemName = item_data.m_Name
      new_result.m_RegionId = character_order.m_RegionId
      new_result.m_RegionName = map_model.GetRegionName(character_order.m_RegionId)
      for order in better_orders_same_station:
        if order.m_Price < new_result.m_LowestPrice:
          new_result.m_LowestPrice = order.m_Price
        new_result.m_Volume += order.m_Volume
      result.m_ResultsSameStation.append(new_result)
  return result
    
      