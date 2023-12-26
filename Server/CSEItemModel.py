# Stores and allows basic info about an item to be queried by id
import CSEScraper

class CSEItemModelItemData:
    def __init__(self) -> None:
        self.m_Id = 0
        self.m_Name = ""
        self.m_Description = ""
        self.m_Mass = 0.0
        self.m_Volume = 0.0

class CSEItemModel:
    def __init__(self) -> None:
        self.m_ItemIdToItemData = dict[int, CSEItemModelItemData]()

    def CreateFromScrape(self, scrape: CSEScraper.ItemsScrape) -> None:
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
            self.m_ItemIdToItemData.update({item_id: item_data})
