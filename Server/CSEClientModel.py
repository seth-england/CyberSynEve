from typing import Any
import CSEMessages
import CSECommon
import json

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

class ClientModel:
  def __init__(self) -> None:
    self.m_CharacterIdToClientDataValueType = CSEClientData
    self.m_CharacterIdToClientData = dict[int, self.m_CharacterIdToClientDataValueType]()
    return
  
  def ToJson(self) -> str:
    res = json.dumps(self, cls=CSECommon.GenericEncoder)
    return res
  
  def FromJson(self, json_dict):
    CSECommon.FromJson(self, json_dict)

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
  
  def GetClientByUUID(self, uuid) -> CSEClientData or None:
    for client_data in self.m_CharacterIdToClientData.values():
      if client_data.m_UUID == uuid:
        return client_data
    return None
  
  def OnNewClientAuth(self, message : CSEMessages.CSEMessageNewClientAuth):
    client_data = self.m_CharacterIdToClientData.get(message.m_CharacterId)
    # Client data does not exist, create it
    if client_data is None:
      client_data = CSEClientData()
      self.m_CharacterIdToClientData[message.m_CharacterId] = client_data
    
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