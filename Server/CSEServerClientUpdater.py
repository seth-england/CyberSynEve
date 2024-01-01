# Periodically gets info from the eve server about a client

import requests
import CSEMessages
import multiprocessing
import CSECommon
import queue
import threading
import CSEMapModel
import CSEServerVolatileModelStaging
import CSEClientModel
import CSEMarketModel
import CSEItemModel
import copy
import time
import random

class ClientUpdater:
  def __init__(self) -> None:
    self.m_ServerToSelfQueue : queue.Queue() = None
    self.m_SelfToServerQueue : queue.Queue() = None
    self.m_MapModel : CSEMapModel.MapModel = None
    self.m_ClientModel : CSEClientModel.ClientModel = None
    self.m_MarketModel : CSEMarketModel.MarketModel = None
    self.m_ItemModel : CSEItemModel.ItemModel = None
    self.m_Thread : threading.Thread = None
    self.m_ModelStaging : CSEServerVolatileModelStaging.ModelStaging = None
    self.m_LastStageId : int = None

  def CalculateProfitableRoute(self, character_id) -> CSEMessages.ProfitableRoute:
    result = CSEMessages.ProfitableRoute()

    # Get the client
    client_data = self.m_ClientModel.GetClientByCharacterId(character_id)
    if not client_data:
      result.m_Error = "Could not retrieve pilot's information"
      return result

    # Retrieve ship data
    ship_id = client_data.m_ShipID
    ship_data = self.m_ItemModel.GetItemDataFromID(ship_id)
    if ship_data is None:
      result.m_Error = "Could not retrieve pilot's ship information"
      return result
    ship_capacity = ship_data.m_Capacity

    # Find a close region
    start_region_id = client_data.m_CharacterRegionId
    start_system_id = client_data.m_CharacterSystemId
    end_region_id = None
    all_system_ids = self.m_MapModel.GetSystemIds()
    MAX_ATTEMPTS = 100
    ACCEPTABLE_JUMP_DISTANCE = 20
    for i in range(MAX_ATTEMPTS):
      system_index = random.randrange(0, len(all_system_ids))
      system_id = all_system_ids[system_index]
      system = self.m_MapModel.GetSystemById(system_id)
      if system is None:
        continue
      if system.m_RegionId == start_region_id:
        continue
      route = self.m_MapModel.GetRouteData(start_system_id, system_id)
      if not route:
        continue
      if len(route) > ACCEPTABLE_JUMP_DISTANCE:
        continue
      end_region_id = system.m_RegionId
      break
    
    if end_region_id is None:
      result.m_Error = "Could not find close enough region"
      return result
    
    start_region_data = self.m_MapModel.GetRegionById(start_region_id)
    end_region_data = self.m_MapModel.GetRegionById(end_region_id)

    if start_region_data is None:
      result.m_Error = "Start region is invalid"
      return result
    
    if end_region_data is None:
      result.m_Error = "End region is invalid"
      return result
    
    # Find an item to bring between the regions
    start_region_item_ids = self.m_MarketModel.GetItemIdsFromRegionId(start_region_id)
    MAX_SAMPLES = 100
    MIN_ORDER_VOLUME = 1000
    best_item_name = None
    best_item_profit = 0
    best_item_region_name = None
    best_item_investment = 0
    best_item_rate_of_profit = 0
    best_item_count = 0
    best_item_start_mean_price = 0
    best_item_end_mean_price = 0
    for i in range(MAX_SAMPLES):
      item_index = random.randrange(0, len(start_region_item_ids))
      item_id = start_region_item_ids[item_index]
      start_region_item_market_data = self.m_MarketModel.GetItemDataFromRegionIdAndItemId(start_region_id, item_id)
      if start_region_item_market_data is None:
        continue
      if start_region_item_market_data.m_RecentVolume < MIN_ORDER_VOLUME:
        continue
      item_data = self.m_ItemModel.GetItemDataFromID(item_id)
      if item_data is None:
        continue
      end_region_item_market_data = self.m_MarketModel.GetItemDataFromRegionIdAndItemId(end_region_id, item_id)
      if end_region_item_market_data is None:
        continue
      if end_region_item_market_data.m_RecentVolume < MIN_ORDER_VOLUME:
        continue
      item_volume = item_data.m_Volume
      if item_volume > ship_capacity:
        continue
      item_count = min(min(int(ship_capacity / item_volume), start_region_item_market_data.m_RecentVolume),end_region_item_market_data.m_RecentVolume)
      investment = start_region_item_market_data.m_RecentAveragePrice * item_count
      profit = end_region_item_market_data.m_RecentAveragePrice * item_count - investment
      rate_of_profit = profit / investment
      if profit > best_item_profit:
        best_item_name = item_data.m_Name
        best_item_profit = profit
        best_item_investment = investment
        best_item_rate_of_profit = rate_of_profit
        best_item_count = item_count
        best_item_start_mean_price = start_region_item_market_data.m_RecentAveragePrice
        best_item_end_mean_price = end_region_item_market_data.m_RecentAveragePrice
      
    if best_item_name is None:
      result.m_Error = "Could not find a profitable item"
      return result
    
    result.m_Valid = True
    result.m_BestItemName = best_item_name
    result.m_BestItemBuyRegionName = start_region_data.m_Name
    result.m_BestItemSellRegionName = end_region_data.m_Name
    result.m_BestItemProfit = best_item_profit
    result.m_Investment = best_item_investment
    result.m_RateOfProfit = best_item_rate_of_profit
    result.m_ItemCount = best_item_count
    result.m_StartRegionMeanPrice = best_item_start_mean_price
    result.m_EndRegionMeanPrice = best_item_end_mean_price
    return result
        

def Main(updater : ClientUpdater):
  while True:
    if not updater.m_ServerToSelfQueue.empty():
      if updater.m_ModelStaging.m_LastStageId != updater.m_LastStageId:
        with updater.m_ModelStaging.m_Lock:
          updater.m_ClientModel = copy.deepcopy(updater.m_ModelStaging.m_ClientModel)
          updater.m_MarketModel = copy.deepcopy(updater.m_ModelStaging.m_MarketModel)
          updater.m_LastStageId = updater.m_ModelStaging.m_LastStageId

      message = updater.m_ServerToSelfQueue.get_nowait()
      if type(message) is CSEMessages.CSEMessageUpdateClient:
        update_message : CSEMessages.CSEMessageUpdateClient = message
        response = CSEMessages.UpdateClientResponse()
        response.m_CharacterId = update_message.m_CharacterId
        response.m_AccessToken = update_message.m_AccessToken
        response.m_RefreshToken = update_message.m_RefreshToken

        # Validate the access token
        query = {'grant_type':'refresh_token', 'refresh_token':update_message.m_RefreshToken, 'client_id':CSECommon.CLIENT_ID}
        header = {'Content-Type':'application/x-www-form-urlencoded', 'Host':'login.eveonline.com'}
        res = CSECommon.PostAndDecodeJsonFromURL(CSECommon.EVE_REFRESH_TOKEN, headers=header, data=query) #requests.post(CSECommon.EVE_REFRESH_TOKEN, headers=header, data=query)
        if res:
          response.m_AccessToken = res.get('access_token')
          response.m_RefreshToken = res.get('refresh_token')

        # Update the location of the character
        location_url = f'{CSECommon.EVE_SERVER_ROOT}characters/{update_message.m_CharacterId}/location/'
        query = {'character_id': response.m_CharacterId, 'token' : response.m_AccessToken}
        res = CSECommon.DecodeJsonFromURL(location_url, params=query)
        if res:
          solar_system_id = res.get('solar_system_id')
          region_id = updater.m_MapModel.GetRegionIdBySystemId(solar_system_id)
          response.m_SystemId = solar_system_id
          response.m_RegionId = region_id

        # Get the character's ship
        ship_url = f'{CSECommon.EVE_SERVER_ROOT}characters/{update_message.m_CharacterId}/ship/'
        query = {'character_id': response.m_CharacterId, 'token' : response.m_AccessToken}
        res = CSECommon.DecodeJsonFromURL(ship_url, params=query)
        if res:
          response.m_ShipId = res.get('ship_type_id')     

        # Update local client model with latest data
        updater.m_ClientModel.HandleUpdateClientResponse(response)

        response.m_ProfitableRoute = updater.CalculateProfitableRoute(response.m_CharacterId)
        updater.m_SelfToServerQueue.put_nowait(response)
    else:
      time.sleep(CSECommon.STANDARD_SLEEP)