# Periodically gets info from the eve server about a client
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
import sqlite3
import SQLHelpers
import MySQLHelpers

def Main(worker : CSEServerWorker.Worker, uuid : str):
  CSEServerModelUpdateHelper.ApplyAllUpdates(worker.m_ModelUpdateQueue, worker.m_AllModels.m_MarketModel, worker.m_AllModels.m_ClientModel, worker.m_AllModels.m_MapModel, worker.m_AllModels.m_CharacterModel)
  client_update_message = CSEClientModel.UpdateClientResponse()
  client_update_message.m_UUID = uuid
  conn = MySQLHelpers.Connect()
  character_ids = worker.m_AllModels.m_ClientModel.GetCharacterIds(client_update_message.m_UUID)
  for character_id in character_ids:
    char_data = worker.m_AllModels.m_CharacterModel.GetCharDataById(character_id)
    if char_data is None:
      continue
    if not char_data.m_LoggedIn:
      continue
    char_update_message = CSECharacterModel.UpdateCharacterMessage()
    char_update_message.m_CharacterId = character_id
    # Validate the access token
    query = {'grant_type':'refresh_token', 'refresh_token':char_data.m_RefreshToken, 'client_id':CSECommon.CLIENT_ID}
    header = {'Content-Type':'application/x-www-form-urlencoded', 'Host':'login.eveonline.com'}
    res = CSECommon.PostAndDecodeJsonFromURL(CSECommon.EVE_REFRESH_TOKEN, headers=header, data=query)
    if res:
      char_update_message.m_AccessToken = res.get('access_token')
      char_update_message.m_RefreshToken = res.get('refresh_token')
    else:
      logged_out_message = CSEMessages.CharacterLoggedOut()
      logged_out_message.m_ClientUUID = uuid
      logged_out_message.m_CharacterId = character_id
      worker.m_MsgSystem.QueueModelUpdateMessage(logged_out_message)
      continue
    # Update the location of the character
    location_url = f'{CSECommon.EVE_SERVER_ROOT}characters/{character_id}/location/'
    query = {'character_id': character_id, 'token' : char_update_message.m_AccessToken}
    res = CSECommon.DecodeJsonFromURL(location_url, params=query)
    region_id = None
    if res:
      solar_system_id = res.get('solar_system_id')
      region_id = worker.m_AllModels.m_MapModel.GetRegionIdBySystemId(solar_system_id)
      char_update_message.m_SystemId = solar_system_id
      char_update_message.m_RegionId = region_id
    # Get the character's ship
    ship_url = f'{CSECommon.EVE_SERVER_ROOT}characters/{character_id}/ship/'
    query = {'character_id': char_update_message.m_CharacterId, 'token' : char_update_message.m_AccessToken}
    res = CSECommon.DecodeJsonFromURL(ship_url, params=query)
    if res:
      char_update_message.m_ShipId = res.get('ship_type_id')
    # Get the character's transactions
    transactions_url = f'{CSECommon.EVE_SERVER_ROOT}characters/{character_id}/wallet/transactions/'
    query = {'character_id': char_update_message.m_CharacterId, 'token' : char_update_message.m_AccessToken}
    res = CSECommon.DecodeJsonFromURL(transactions_url, params=query)
    if res:
      for transaction_json in res:
        new_trans = CSECharacterModel.CSECharacterTransaction()
        date = transaction_json.get('date')
        if date:
          new_trans.m_Date = date
        buy = transaction_json.get('is_buy')
        if buy:
          new_trans.m_Buy = buy
        quantity = transaction_json.get('quantity')
        if quantity:
          new_trans.m_Quantity = quantity
        unit_price = transaction_json.get('unit_price')
        if unit_price:
          new_trans.m_UnitPrice = unit_price
        new_trans.m_TotalPrice = new_trans.m_UnitPrice * new_trans.m_Quantity
        type_id = transaction_json.get('type_id')
        if type_id:
          new_trans.m_TypeId = type_id
        char_id = transaction_json.get('client_id')
        if char_id:
          new_trans.m_CharacterId = char_id
        char_update_message.m_CharacterTransactions.append(new_trans)

    # Get the character's orders
    character_orders_scrape = CSEScrapeHelper.ScrapeCurrentCharacterOrders(char_update_message.m_CharacterId, char_update_message.m_AccessToken)
    update_character_orders_message = CSEMessages.UpdateCharacterOrders()
    update_character_orders_message.m_CharacterId = char_update_message.m_CharacterId
    update_character_orders_message.m_OrderDictArray = character_orders_scrape.m_OrderDictArray 
    worker.m_MsgSystem.QueueModelUpdateMessage(update_character_orders_message)
    worker.m_MsgSystem.QueueModelUpdateMessage(char_update_message)
    CSEServerModelUpdateHelper.ApplyAllUpdates(worker.m_ModelUpdateQueue, worker.m_AllModels.m_MarketModel, worker.m_AllModels.m_ClientModel, worker.m_AllModels.m_MapModel, worker.m_AllModels.m_CharacterModel)      
    worker.m_MsgSystem.QueueModelUpdateMessage(char_update_message)

    # Run profitable query
    client = worker.m_AllModels.m_ClientModel.GetClientByUUID(client_update_message.m_UUID)
    client_settings = CSEClientSettings.Settings()
    max_ship_volume = None
    ship_item = worker.m_AllModels.m_ItemModel.GetItemDataFromID(char_update_message.m_ShipId)
    if ship_item:
      max_ship_volume = ship_item.m_Capacity
    if client:
      client_settings = client.m_Settings         
    if region_id:
      profitable_result = \
      CSEProfitableQuery.ProfitableQuery\
      ( \
        conn,
        worker.m_AllModels.m_MapModel, 
        worker.m_AllModels.m_MarketModel, 
        worker.m_AllModels.m_ItemModel,
        worker.m_AllModels.m_CharacterModel,
        character_ids,
        character_id,
        region_id,
        pct_of_recent_volume_limit=client_settings.m_ProfitableSettings.m_PctOfRecentVolume,
        max_ship_volume=max_ship_volume, 
        min_order_count=client_settings.m_ProfitableSettings.m_MinOrderCount,
        min_profit=client_settings.m_ProfitableSettings.m_MinProfit,
        min_profit_rate=client_settings.m_ProfitableSettings.m_MinRateOfProfit
      )
      if profitable_result.m_Valid:
        client_update_message.m_ProfitableQueryResult.m_Valid = True
        client_update_message.m_ProfitableQueryResult.m_ProfitableTrades += profitable_result.m_ProfitableTrades


  # Market balance query
  profitable_query_transactions = list()
  for character_id in character_ids:
    char_data = worker.m_AllModels.m_CharacterModel.GetCharDataById(character_id)
    if char_data.m_Type == CSECommon.CHAR_TYPE_HAULER or char_data.m_Type == CSECommon.CHAR_TYPE_TRADE_BOT:
      profitable_query_transactions.extend(char_data.m_Transactions)
  client_update_message.m_MarketBalanceQueryResult = CSEMarketBalanceQuery.Query(profitable_query_transactions, worker.m_AllModels.m_ItemModel)

  worker.m_MsgSystem.QueueModelUpdateMessage(client_update_message)
  conn.close()