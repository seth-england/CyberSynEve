# Periodically gets info from the eve server about a client

import requests
import CSEMessages
import multiprocessing
import CSECommon
import queue
import threading
import CSEMapModel
import CSEClientModel
import CSEMarketModel
import CSEItemModel
import copy
import time
import random
import CSEServerMessageSystem
import CSEServerModelUpdateHelper
import Queries.CSEProfitableQuery as CSEProfitableQuery
import CSEClientSettings
import CSEScrapeHelper
import Queries.CSEUndercutQuery as CSEUndercutQuery
import Queries.CSEMarketBalanceQuery as CSEMarketBalanceQuery
import CSECharacterModel

class ClientUpdater:
  def __init__(self) -> None:
    self.m_ServerToSelfQueue : queue.Queue = None
    self.m_SelfToServerQueue : queue.Queue = None
    self.m_MapModel : CSEMapModel.MapModel = None
    self.m_ClientModel : CSEClientModel.ClientModel = None
    self.m_MarketModel : CSEMarketModel.MarketModel = None
    self.m_CharacterModel : CSECharacterModel.Model = None
    self.m_ItemModel : CSEItemModel.ItemModel = None
    self.m_Thread : threading.Thread = None
    self.m_LastStageId : int = None
    self.m_MsgSystem : CSEServerMessageSystem.MessageSystem = None
    self.m_ModelUpdateQueue = queue.Queue()    

def Main(updater : ClientUpdater):
  updater.m_MsgSystem.RegisterForModelUpdateQueue(threading.get_ident(), updater.m_ModelUpdateQueue)

  while True:
    if not updater.m_ServerToSelfQueue.empty():
      CSEServerModelUpdateHelper.ApplyAllUpdates(updater.m_ModelUpdateQueue, updater.m_MarketModel, updater.m_ClientModel, updater.m_MapModel, updater.m_CharacterModel)
      message = updater.m_ServerToSelfQueue.get_nowait()
      if type(message) is CSEMessages.CSEMessageUpdateClient:
        update_message : CSEMessages.CSEMessageUpdateClient = message
        client_update_message = CSEClientModel.UpdateClientResponse()
        client_update_message.m_UUID = message.m_UUID
        character_ids = updater.m_ClientModel.GetCharacterIds(client_update_message.m_UUID)
        for character_id in character_ids:
          char_data = updater.m_CharacterModel.GetCharDataById(character_id)
          if char_data is None:
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

          # Update the location of the character
          location_url = f'{CSECommon.EVE_SERVER_ROOT}characters/{character_id}/location/'
          query = {'character_id': character_id, 'token' : char_update_message.m_AccessToken}
          res = CSECommon.DecodeJsonFromURL(location_url, params=query)
          region_id = None
          if res:
            solar_system_id = res.get('solar_system_id')
            region_id = updater.m_MapModel.GetRegionIdBySystemId(solar_system_id)
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
          updater.m_MsgSystem.QueueModelUpdateMessage(update_character_orders_message)
          updater.m_MsgSystem.QueueModelUpdateMessage(char_update_message)
          CSEServerModelUpdateHelper.ApplyAllUpdates(updater.m_ModelUpdateQueue, updater.m_MarketModel, updater.m_ClientModel, updater.m_MapModel, updater.m_CharacterModel)      

          updater.m_MsgSystem.QueueModelUpdateMessage(char_update_message)

          # Run profitable query
          if char_data.m_Type == CSECommon.CHAR_TYPE_HAULER:
            client = updater.m_ClientModel.GetClientByUUID(client_update_message.m_UUID)
            client_settings = CSEClientSettings.Settings()
            max_ship_volume = None
            ship_item = updater.m_ItemModel.GetItemDataFromID(char_update_message.m_ShipId)
            if ship_item:
              max_ship_volume = ship_item.m_Capacity
            if client:
              client_settings = client.m_Settings         
            if region_id:
              client_update_message.m_ProfitableQueryResult = \
              CSEProfitableQuery.ProfitableQuery\
              ( \
                updater.m_MapModel, 
                updater.m_MarketModel, 
                updater.m_ItemModel, 
                region_id, 
                max_ship_volume=max_ship_volume, 
                min_order_count=client_settings.m_ProfitableSettings.m_MinOrderCount,
                min_profit=client_settings.m_ProfitableSettings.m_MinProfit,
                min_profit_rate=client_settings.m_ProfitableSettings.m_MinRateOfProfit
              ) 
        profitable_query_transactions = list()
        for character_id in character_ids:
          char_data = updater.m_CharacterModel.GetCharDataById(character_id)
          if char_data.m_Type == CSECommon.CHAR_TYPE_HAULER or char_data.m_Type == CSECommon.CHAR_TYPE_TRADE_BOT:
            profitable_query_transactions.extend(char_data.m_Transactions)
        client_update_message.m_MarketBalanceQueryResult = CSEMarketBalanceQuery.Query(profitable_query_transactions, updater.m_ItemModel)
        updater.m_MsgSystem.QueueModelUpdateMessage(client_update_message)
    else:
      time.sleep(CSECommon.STANDARD_SLEEP)