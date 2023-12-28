# Store and retrieves data about an item in a region including:
# - Price
# - Volume
import CSEScraper

# Data for an item in a particular region
class ItemData:
  def __init__(self):
    self.m_Id = -1
    self.m_VolumeForSale = 0
    self.m_VolumeTimesPriceSum = 0 # The numerator of the mean price
    self.m_MeanPrice = 0

class CSEMarketRegionData:
  def __init__(self) -> None:
    self.m_ItemIDToRegionItemData = dict[int, ItemData]()

class MarketModel:
  def __init__(self) -> None:
    self.m_RegionIdToRegionData = dict[int, CSEMarketRegionData]()

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
    # Clear the existing region data
    region_data = CSEMarketRegionData()
    self.m_RegionIdToRegionData.update({scrape.m_RegionId : region_data})
    for order_dict in scrape.m_Orders:
      is_sell_order = not order_dict["is_buy_order"]
      if is_sell_order:
        item_id = order_dict["type_id"]
        item_data = region_data.m_ItemIDToRegionItemData.get(item_id)
        if not item_data:
          item_data = ItemData()
          region_data.m_ItemIDToRegionItemData[item_id] = item_data
        item_data.m_Id = item_id
        order_volume = order_dict["volume_remain"]
        order_price = order_dict["price"]
        item_data.m_VolumeForSale = item_data.m_VolumeForSale + order_volume
        item_data.m_VolumeTimesPriceSum = item_data.m_VolumeTimesPriceSum + (order_price * order_volume)
        if item_data.m_VolumeForSale > 0:
          item_data.m_MeanPrice = item_data.m_VolumeTimesPriceSum / item_data.m_VolumeForSale   
  
