# Stores and allows basic info about an item to be queried by id
import CSEScrapeHelper

class CSEItemModelItemData:
  def __init__(self) -> None:
    self.m_Id = 0
    self.m_Name = ""
    self.m_Description = ""
    self.m_Mass = 0.0
    self.m_Volume = 0.0
    self.m_Capacity = 0.0
    self.m_MarketGroupId = None

class ItemModel:
  def __init__(self) -> None:
    self.m_ItemIdToItemData = dict[int, CSEItemModelItemData]()
    self.m_ItemNameToAdditionalCapacity = dict[str, float]()
    self.m_ItemNameToAdditionalCapacity['Occator'] = 62500

  def GetItemDataFromID(self, item_id : int) -> CSEItemModelItemData | None:
    item = self.m_ItemIdToItemData.get(item_id)
    return item
  
  def GetItemIdFromName(self, name : str) -> int | None:
    for item in self.m_ItemIdToItemData.values():
      if item.m_Name == name:
        return item.m_Id
    return None
  
  def GetAllItemIds(self) -> list[int]:
    return list(self.m_ItemIdToItemData.keys())

  def CreateFromScrape(self, scrape: CSEScrapeHelper.ItemsScrape) -> None:
    for item_id, item_dict in scrape.m_ItemIdToDict.items():
      item_data = CSEItemModelItemData()
      item_data.m_Id = item_id
      name = item_dict.get('name')
      if name:
        item_data.m_Name = name
      descr = item_dict.get('description')
      if descr:
        item_data.m_Description = descr
      mass = item_dict.get('mass')
      if mass:
        item_data.m_Mass = mass
      volume = item_dict.get('volume')
      if volume:
        item_data.m_Volume = volume
      capacity = item_dict.get('capacity')
      if capacity:
        additional_capacity = self.m_ItemNameToAdditionalCapacity.get(name)
        if additional_capacity:
          capacity = capacity + additional_capacity
        item_data.m_Capacity = capacity
      market_group_id = item_dict.get('market_group_id')
      if market_group_id:
        item_data.m_MarketGroupId = market_group_id
      self.m_ItemIdToItemData.update({item_id: item_data})
