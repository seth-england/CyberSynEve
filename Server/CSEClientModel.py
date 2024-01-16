from typing import Any
import CSEMessages
import CSECommon
import CSEHTTP
import json
import CSEClientSettings
import CSEUndercutResult

class CharacterOrder:
  def __init__(self) -> None:
    self.m_Duration = 0
    self.m_IsBuyOrder = False
    self.m_IssuedTime = ""
    self.m_StationId = 0
    self.m_OrderId = 0
    self.m_Price = 0
    self.m_RegionId = 0
    self.m_ItemTypeId = 0
    self.m_VolumeRemain = 0
    self.m_VolumeTotal = 0

class CharacterData:
  def __init__(self) -> None:
    self.m_CharacterId = 0
    self.m_CharacterName = ""
    self.m_OrdersValueType = CharacterOrder
    self.m_Orders = list[self.m_OrdersValueType]()

class CSEClientData:
  def __init__(self) -> None:
    self.m_CharacterId = 0
    self.m_CharacterName = ""
    self.m_AccessToken = ""
    self.m_RefreshToken = ""
    self.m_ExpiresDateString = ""
    self.m_CharacterSystemId = None
    self.m_CharacterRegionId = None
    self.m_ShipID = None
    self.m_UUID = "" # A unique identifier for a client running somewhere in the world
    self.m_ProfitableQueryResult = None
    self.m_ProfitableResult = CSEHTTP.CSEProfitableResult()
    self.m_Settings = CSEClientSettings.Settings()
    self.m_CharacterIdToCharacterDataValueType = CharacterData
    self.m_CharacterIdToCharacterData = dict[int, self.m_CharacterIdToCharacterDataValueType]()
    self.m_UndercutResult = CSEUndercutResult.CSEUndercutResult()

class ClientModel:
  def __init__(self) -> None:
    self.m_CharacterIdToClientDataValueType = CSEClientData
    self.m_CharacterIdToClientData = dict[int, self.m_CharacterIdToClientDataValueType]()
    return

  def GetClientByIndex(self, index : int):
    # Check if key exists
    keys = list(self.m_CharacterIdToClientData.keys())
    key_len = len(keys)
    if index >= key_len:
      return None
    
    # Get client data
    key = keys[index]
    client_data = self.m_CharacterIdToClientData[key]
    return client_data
  
  def GetClientByCharacterId(self, character_id : int) -> CSEClientData or None:
    client_data = self.m_CharacterIdToClientData.get(character_id)
    return client_data
  
  def GetCharacterDataByCharacterId(self, character_id : int) -> CharacterData or None:
    client_data = self.GetClientByCharacterId(character_id)
    if client_data is None:
      return None
    character_data = client_data.m_CharacterIdToCharacterData.get(character_id)
    return character_data
  
  def GetClientByUUID(self, uuid) -> CSEClientData or None:
    for client_data in self.m_CharacterIdToClientData.values():
      if client_data.m_UUID == uuid:
        return client_data
    return None
  
  def GetCharacterOrders(self, character_id : int) -> list[CharacterOrder] or None:
    character_data = self.GetCharacterDataByCharacterId(character_id)
    if character_data is None:
      return None
    return character_data.m_Orders
  
  def HandleUpdateCharacterOrders(self, message : CSEMessages.UpdateCharacterOrders):
    character_data = self.GetCharacterDataByCharacterId(message.m_CharacterId)
    if character_data is None:
      return
    
    character_data.m_Orders.clear()
    for order_dict in message.m_OrderDictArray:
      new_order = CharacterOrder()
      is_buy_order = order_dict.get('is_buy_order')
      if is_buy_order:
        new_order.m_IsBuyOrder = is_buy_order
      duration = order_dict.get('duration')
      if duration:
        new_order.m_Duration = duration
      issued = order_dict.get('issued')
      if issued:
        new_order.m_IssuedTime = issued
      station_id = order_dict.get('location_id')
      if station_id:
        new_order.m_StationId = station_id
      order_id = order_dict.get('order_id')
      if order_id:
        new_order.m_OrderId = order_id
      price = order_dict.get('price')
      if price:
        new_order.m_Price = price
      region_id = order_dict.get('region_id')
      if region_id:
        new_order.m_RegionId = region_id
      type_id = order_dict.get('type_id')
      if type_id:
        new_order.m_ItemTypeId = type_id
      volume_remain = order_dict.get('volume_remain')
      if volume_remain:
        new_order.m_VolumeRemain = volume_remain
      volume_total = order_dict.get('volume_total')
      if volume_total:
        new_order.m_VolumeTotal = volume_total
      character_data.m_Orders.append(new_order)
      
  
  def OnNewClientAuth(self, message : CSEMessages.CSEMessageNewClientAuth):
    client_data = self.m_CharacterIdToClientData.get(message.m_CharacterId)
    # Client data does not exist, create it
    if client_data is None:
      client_data = CSEClientData()
      self.m_CharacterIdToClientData[message.m_CharacterId] = client_data

    character_data = client_data.m_CharacterIdToCharacterData.get(message.m_CharacterId)
    if character_data is None:
      character_data = CharacterData()
      character_data.m_CharacterId = message.m_CharacterId
      client_data.m_CharacterIdToCharacterData[character_data.m_CharacterId] = character_data
    character_data.m_CharacterName = message.m_CharacterName

    # Copy client data from message
    client_data.m_CharacterId = message.m_CharacterId
    client_data.m_CharacterName = message.m_CharacterName
    client_data.m_AccessToken = message.m_AccessToken
    client_data.m_RefreshToken = message.m_RefreshToken
    client_data.m_ExpiresDateString = message.m_ExpiresDateString
    client_data.m_UUID = message.m_UUID

  def HandleUpdateClientResponse(self, message: CSEMessages.UpdateClientResponse):
    client_data = self.m_CharacterIdToClientData.get(message.m_CharacterId)
    if client_data:
      client_data.m_AccessToken = message.m_AccessToken
      client_data.m_RefreshToken = message.m_RefreshToken
      client_data.m_CharacterRegionId = message.m_RegionId
      client_data.m_CharacterSystemId = message.m_SystemId
      client_data.m_ShipID = message.m_ShipId
      if client_data.m_ProfitableResult and client_data.m_ProfitableResult.m_Valid:
        if message.m_ProfitableQueryResult.m_Valid:
          client_data.m_ProfitableResult = message.m_ProfitableQueryResult
      else:
        client_data.m_ProfitableResult = message.m_ProfitableQueryResul
      if client_data.m_UndercutResult and client_data.m_UndercutResult.m_Valid:
        if message.m_UndercutQueryResult.m_Valid:
          client_data.m_UndercutResult = message.m_UndercutQueryResult
      else:
        client_data.m_UndercutResult = message.m_UndercutQueryResult
  
  def HandleSetClientSettings(self, message: CSEMessages.SetClientSettings):
    client_data = self.GetClientByUUID(message.m_UUID)
    if client_data:
      client_data.m_Settings = message.m_Settings