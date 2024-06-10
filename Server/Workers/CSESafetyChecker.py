import CSEMessages
import CSECommon
import CSEClientModel
import CSEServerModelUpdateHelper
import Queries.CSEProfitableQuery as CSEProfitableQuery
import CSEClientSettings
import CSEScrapeHelper
import Queries.CSEMarketBalanceQuery as CSEMarketBalanceQuery
import CSECharacterModel
import Workers.CSEServerWorker as CSEServerWorker
import time

def Main(worker : CSEServerWorker.Worker):
  header = {'User-Agent': 'komissar1500@gmail.com', 'Accept-Encoding': 'gzip'}
  ship_ids = list[int]()
  bane_id = worker.m_AllModels.m_ItemModel.GetItemIdFromName('Bane')
  karura_id = worker.m_AllModels.m_ItemModel.GetItemIdFromName('Karura')
  hubris_id = worker.m_AllModels.m_ItemModel.GetItemIdFromName('Hubris')
  valravn_id = worker.m_AllModels.m_ItemModel.GetItemIdFromName('Valravn')
  test_id = worker.m_AllModels.m_ItemModel.GetItemIdFromName("Abaddon")
  ship_ids.append(bane_id)
  ship_ids.append(karura_id)
  ship_ids.append(hubris_id)
  ship_ids.append(valravn_id)
  check_time = CSECommon.SAFETY_TIME
  jita_id = worker.m_AllModels.m_MapModel.GetSystemIdByName("Jita")
  dodixie_id = worker.m_AllModels.m_MapModel.GetSystemIdByName("Dodixie")
  amarr_id = worker.m_AllModels.m_MapModel.GetSystemIdByName("Amarr")
  jita_to_dodixie_system_ids = []
  jita_to_dodixie_system_ids.append(worker.m_AllModels.m_MapModel.GetSystemIdByName("Tama"))
  jita_to_dodixie_system_ids.append(worker.m_AllModels.m_MapModel.GetSystemIdByName("Sujarento"))
  jita_to_dodixie_system_ids.append(worker.m_AllModels.m_MapModel.GetSystemIdByName("Onatoh"))
  jita_to_dodixie_system_ids.append(worker.m_AllModels.m_MapModel.GetSystemIdByName("Tannolen"))
  jita_to_amarr_system_ids = []
  jita_to_amarr_system_ids.append(worker.m_AllModels.m_MapModel.GetSystemIdByName("Ahbazon"))
  while True:
    result = CSEMessages.SafetyUpdated()

    # Jita to Dodixie
    if jita_to_dodixie_system_ids:
      for system_id in jita_to_dodixie_system_ids:
        system_data = worker.m_AllModels.m_MapModel.GetSystemById(system_id)
        if system_data:
          if system_data.m_Security <= 0.5:
            for ship_id in ship_ids:
              url = f'https://zkillboard.com/api/systemID/{system_data.m_Id}/shipTypeID/{ship_id}/pastSeconds/{check_time}/'
              res = CSECommon.DecodeJsonFromURL(url, headers = header)
              if res:
                result.m_JitaToDodixieUnsafeTime = time.time()
                break

    # Jita to Amarr
    if jita_to_amarr_system_ids:
      for system_id in jita_to_amarr_system_ids:
        system_data = worker.m_AllModels.m_MapModel.GetSystemById(system_id)
        if system_data:
          if system_data.m_Security <= 0.5:
            for ship_id in ship_ids:
              url = f'https://zkillboard.com/api/systemID/{system_data.m_Id}/shipTypeID/{ship_id}/pastSeconds/{check_time}/'
              res = CSECommon.DecodeJsonFromURL(url, headers = header)
              if res:
                result.m_JitaToAmarrUnsafeTime = time.time()
                break


    worker.m_MsgSystem.QueueModelUpdateMessage(result)
    time.sleep(5)