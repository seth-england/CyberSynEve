# Periodically gets info from the eve server about a client

import requests
import CSEMessages
import multiprocessing
import CSECommon
import json
import CSEMapModel

class CSEServerClientUpdaterClass:
  def __init__(self, server_to_self_queue : multiprocessing.Queue, self_to_server_queue : multiprocessing.Queue, map_model : CSEMapModel.CSEMapModel) -> None:
    self.m_ServerToSelfQueue = server_to_self_queue
    self.m_SelfToServerQueue = self_to_server_queue
    self.m_MapModel = map_model
    self.m_Process : multiprocessing.Process = None

def Main(updater : CSEServerClientUpdaterClass):
  while True:
    if not updater.m_ServerToSelfQueue.empty():
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
          response.m_CharacterSystemId = solar_system_id
          response.m_CharacterRegionId = region_id
          updater.m_SelfToServerQueue.put_nowait(response)