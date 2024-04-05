from typing import Any
import CSEMessages
import CSECommon
import CSEHTTP
import json
import CSEClientSettings
import CSEUndercutResult

class UpdateClientResponse(CSEMessages.CSEMessageBase):
  def __init__(self):
    super().__init__()
    self.m_UUID = ""
    self.m_ProfitableQueryResult = CSEHTTP.CSEProfitableResult()
    self.m_UndercutQueryResult = CSEUndercutResult.CSEUndercutResult()
    self.m_MarketBalanceQueryResult = CSEHTTP.CSEMarketBalanceQueryResult()

class CSEClientData:
  def __init__(self) -> None:
    self.m_CharacterIds = list[int]()
    self.m_UUID = "" # A unique identifier for a client running somewhere in the world
    self.m_ProfitableQueryResult = None
    self.m_ProfitableResult = CSEHTTP.CSEProfitableResult()
    self.m_Settings = CSEClientSettings.Settings()
    self.m_UndercutResult = CSEUndercutResult.CSEUndercutResult()
    self.m_MarketBalanceQueryResult = CSEHTTP.CSEMarketBalanceQueryResult()

class ClientModel:
  def __init__(self) -> None:
    self.m_UUIDToClientDataValueType = CSEClientData
    self.m_UUIDToClientData = dict[str, self.m_UUIDToClientDataValueType]()
    return

  def GetClientByIndex(self, index : int):
    # Check if key exists
    keys = list(self.m_UUIDToClientData.keys())
    key_len = len(keys)
    if index >= key_len:
      return None
    
    # Get client data
    key = keys[index]
    client_data = self.m_UUIDToClientData[key]
    return client_data
  
  def GetClientByUUID(self, uuid) -> CSEClientData | None:
    return self.m_UUIDToClientData.get(uuid)
  
  def GetCharacterIds(self, uuid : str) -> set[int]:
    result = set[int]()
    client_data = self.GetClientByUUID(uuid)
    if client_data:
      result = client_data.m_CharacterIds
    return result
      
  def HandleNewCharAuth(self, message : CSEMessages.CSEMessageNewCharAuth):
    client_data = self.m_UUIDToClientData.get(message.m_UUID)
    # Client data does not exist, create it
    if client_data is None:
      client_data = CSEClientData()
      self.m_UUIDToClientData[message.m_UUID] = client_data

    client_data.m_CharacterIds.append(message.m_CharacterId)
    client_data.m_CharacterIds = list(set(client_data.m_CharacterIds))

  def HandleUpdateClientResponse(self, message: UpdateClientResponse):
    client_data = self.m_UUIDToClientData.get(message.m_UUID)
    if client_data:
      if client_data.m_ProfitableResult and client_data.m_ProfitableResult.m_Valid:
        if message.m_ProfitableQueryResult.m_Valid:
          client_data.m_ProfitableResult = message.m_ProfitableQueryResult
      else:
        client_data.m_ProfitableResult = message.m_ProfitableQueryResult
      if client_data.m_UndercutResult and client_data.m_UndercutResult.m_Valid:
        if message.m_UndercutQueryResult.m_Valid:
          client_data.m_UndercutResult = message.m_UndercutQueryResult
      else:
        client_data.m_UndercutResult = message.m_UndercutQueryResult
      client_data.m_MarketBalanceQueryResult = message.m_MarketBalanceQueryResult
    
  
  def HandleSetClientSettings(self, message: CSEMessages.SetClientSettings):
    client_data = self.GetClientByUUID(message.m_UUID)
    if client_data:
      client_data.m_Settings = message.m_Settings
  
  def HandleNewClient(self, message: CSEMessages.CSEMessageNewClient):
    client_data = self.m_UUIDToClientData.get(message.m_UUID)
    # Client data does not exist, create it
    if client_data is None:
      client_data = CSEClientData()
      client_data.m_UUID = message.m_UUID
      client_data.m_Settings = message.m_Settings
      self.m_UUIDToClientData[message.m_UUID] = client_data