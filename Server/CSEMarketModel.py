# Store and retrieves data about an item in a region including:
# - Price
# - Volume
import CSEScraper

# Data for an item in a particular region
class CSEMarketRegionItemData:
  def __init__(self):
    self.m_Id = -1
    self.m_VolumeForSale = 0
    self.m_VolumeTimesPriceSum = 0 # The numerator of the mean price
    self.m_MeanPrice = 0

class CSEMarketRegionData:
  def __init__(self) -> None:
    self.m_ItemIDToRegionItemData = dict()

class CSEMarketModel:
  def __init__(self) -> None:
    self.m_RegionIdToRegionData = dict()

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
          item_data = CSEMarketRegionItemData()
          region_data.m_ItemIDToRegionItemData[item_id] = item_data
        item_data.m_Id = item_id
        order_volume = order_dict["volume_remain"]
        order_price = order_dict["price"]
        item_data.m_VolumeForSale = item_data.m_VolumeForSale + order_volume
        item_data.m_VolumeTimesPriceSum = item_data.m_VolumeTimesPriceSum + (order_price * order_volume)
        if item_data.m_VolumeForSale > 0:
          item_data.m_MeanPrice = item_data.m_VolumeTimesPriceSum / item_data.m_VolumeForSale   
  
