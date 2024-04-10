import CSECharacterModel
import CSEClientModel
import CSEItemModel
import CSEMapModel
import CSEMarketModel
import CSEScrapeHelper
import CSECommon
import CSEFileSystem

class Models:
  def __init__(self) -> None:
    self.m_CharacterModel = CSECharacterModel.Model()
    self.m_ClientModel = CSEClientModel.ClientModel()
    self.m_ItemModel = CSEItemModel.ItemModel()
    self.m_MapModel = CSEMapModel.MapModel()
    self.m_MarketModel = CSEMarketModel.MarketModel()
    self.m_Scrape = CSEScrapeHelper.ScrapeFileFormat()

  def CreateAllModels(self):
    CSEFileSystem.ReadObjectFromFileJson(CSECommon.SCRAPE_FILE_PATH, self.m_Scrape)
    self.m_MapModel.CreateFromScrape(self.m_Scrape)
    self.m_MapModel.DeserializeRouteData(CSECommon.ROUTES_FILE_PATH)
    CSEFileSystem.ReadObjectFromFileJson(CSECommon.CLIENT_MODEL_FILE_PATH, self.m_ClientModel)
    CSEFileSystem.ReadObjectFromFileJson(CSECommon.MARKET_MODEL_FILE_PATH, self.m_MarketModel)
    CSEFileSystem.ReadObjectFromFileJson(CSECommon.CHARACTER_MODEL_FILE_PATH, self.m_CharacterModel)
    self.m_ItemModel.CreateFromScrape(self.m_Scrape.m_ItemsScrape)