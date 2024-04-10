from typing import Any
import CSEMessages
import CSECommon
import CSEHTTP
import json
import CSEClientSettings
import CSEUndercutResult

class CSECharacterTransaction:
  def __init__(self) -> None:
    self.m_Date = ""
    self.m_Buy = False
    self.m_Quantity = 0
    self.m_UnitPrice = 0
    self.m_TotalPrice = 0
    self.m_TypeId = 0
    self.m_CharacterId = 0

class UpdateCharacterMessage(CSEMessages.CSEMessageBase):
  def __init__(self):
    super().__init__()
    self.m_CharacterId = 0
    self.m_AccessToken = ""
    self.m_RefreshToken = ""
    self.m_SystemId = 0
    self.m_RegionId = 0
    self.m_ShipId = 0
    self.m_CharacterTransactions = list[CSECharacterTransaction]()

class CSECharacterTransaction:
  def __init__(self) -> None:
    self.m_Date = ""
    self.m_Buy = False
    self.m_Quantity = 0
    self.m_UnitPrice = 0
    self.m_TotalPrice = 0
    self.m_TypeId = 0
    self.m_CharacterId = 0

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
    self.m_TransactionsValueType = CSECharacterTransaction
    self.m_Transactions = list[self.m_TransactionsValueType]()
    self.m_AccessToken = ""
    self.m_RefreshToken = ""
    self.m_ExpiresDateString = ""
    self.m_CharacterSystemId = None
    self.m_CharacterRegionId = None
    self.m_ShipID = None
    self.m_Type = CSECommon.CHAR_TYPE_INVALID
    self.m_LoggedIn = True

class Model:
  def __init__(self) -> None:
    self.m_CharacterIdToCharDataValueType = CharacterData
    self.m_CharacterIdToCharData = dict[int, self.m_CharacterIdToCharDataValueType]()

  def GetCharDataById(self, char_id : int) -> CharacterData | None:
    data = self.m_CharacterIdToCharData.get(char_id)
    return data

  def UpdateCharacter(self, message: UpdateCharacterMessage):
    char_data = self.m_CharacterIdToCharData.get(message.m_CharacterId)
    if char_data:
      char_data.m_AccessToken = message.m_AccessToken
      char_data.m_RefreshToken = message.m_RefreshToken
      char_data.m_CharacterRegionId = message.m_RegionId
      char_data.m_CharacterSystemId = message.m_SystemId
      char_data.m_ShipID = message.m_ShipId
      char_data.m_Transactions = message.m_CharacterTransactions

  def HandleNewCharAuth(self, message: CSEMessages.CSEMessageNewCharAuth):
    char_data = self.m_CharacterIdToCharData.get(message.m_CharacterId)
    if char_data is None:
      char_data = CharacterData()
      self.m_CharacterIdToCharData[message.m_CharacterId] = char_data

    if char_data:
      char_data.m_CharacterId = message.m_CharacterId
      char_data.m_CharacterName = message.m_CharacterName
      char_data.m_AccessToken = message.m_AccessToken
      char_data.m_RefreshToken = message.m_RefreshToken
      char_data.m_ExpiresDateString = message.m_ExpiresDateString
      char_data.m_Type = message.m_Type
      char_data.m_LoggedIn = True

  def HandleUpdateCharacterOrders(self, message : CSEMessages.UpdateCharacterOrders):
    character_data = self.GetCharDataById(message.m_CharacterId)
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
  
  def HandleCharacterLoggedOut(self, message : CSEMessages.CharacterLoggedOut):
    char_data = self.m_CharacterIdToCharData.get(message.m_CharacterId)
    if char_data:
      char_data.m_LoggedIn = False