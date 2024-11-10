import ProjectSettings
ProjectSettings.Init()
import CSECommon
import requests
import webbrowser
import json
import CSEMapModel
import CSEScrapeHelper
import asyncio
import aiohttp
import multiprocessing
import CSEServer
import CSELogging
import CSEMessages
import CSEHTTP
import threading
import signal
import time
import sys
from flask import Flask, request, jsonify
from base64 import b64encode
from telnetlib import NOP
app = Flask(__name__)

CLIENT_SECRET = 'EfdmhqJg7vncmfAEshRANS4wMtcawguFLGZSyJ9Z'
server = CSEServer.CSEServer()

@app.route(CSECommon.SERVER_SAFETY_ENDPOINT)
def Safety():
  res = CSEHTTP.SafetyResponse()
  curr_time = time.time()
  diff = curr_time - server.m_MapModel.m_RouteData.m_LastSafetyUpdate.m_JitaToDodixieUnsafeTime
  if diff < CSECommon.SAFETY_TIME:
    res.m_JitaToDodixieSafe = False

  diff = curr_time - server.m_MapModel.m_RouteData.m_LastSafetyUpdate.m_JitaToAmarrUnsafeTime
  if diff < CSECommon.SAFETY_TIME:
    res.m_JitaToAmarrSafe = False
  json_string = CSECommon.ObjectToJsonString(res)
  return json_string, CSECommon.OK_CODE

@app.route(CSECommon.SERVER_CHARACTERS_ENDPOINT)
def Characters():
    dict = json.loads(request.json)
    http_request = CSEHTTP.CharactersRequest()
    CSECommon.FromJson(http_request, dict)
    char_ids = server.m_ClientModel.GetCharacterIds(http_request.m_UUID)
    res = CSEHTTP.CharactersResponse()
    if len(char_ids) > 0:
      for char_id in char_ids:
        char_data = server.m_CharacterModel.GetCharDataById(char_id)
        if char_data:
          res.m_CharacterIds.append(char_data.m_CharacterId)
          res.m_CharaterNames.append(char_data.m_CharacterName)
          res.m_CharacterTypes.append(char_data.m_Type)
          res.m_CharacterLoggedIn.append(char_data.m_LoggedIn)
    return CSECommon.ObjectToJsonString(res), CSECommon.OK_CODE
      

@app.route(CSECommon.SERVER_AUTH_ENDPOINT)
def Auth():
  with server.m_LockFlask:
    code = request.args.get('code')
    state : str = request.args.get('state')
    uuid, char_type = state.split()
    url_encoded = {'grant_type' : 'authorization_code', 'code' : code}
    user_and_pass = CSECommon.CLIENT_ID + ':' + CLIENT_SECRET
    user_and_pass = user_and_pass.encode("utf-8")
    user_and_pass_param = b64encode(user_and_pass).decode("ascii")
    header_params = {'Authorization' : 'Basic %s' % user_and_pass_param, 'Content-Type' : 'application/x-www-form-urlencoded', 'Host' : 'login.eveonline.com'}
    res = requests.post('https://login.eveonline.com/v2/oauth/token', data=url_encoded, headers=header_params)
    if res.status_code != CSECommon.OK_CODE:
      return "", res.status_code
    json_content = json.loads(res.content)
    access_token = json_content.get('access_token')
    refresh_token = json_content.get('refresh_token')
    

    # Verify the token
    query = {'user-agent': CSECommon.CLIENT_ID, 'token' : access_token}
    header = { 'Authorization': f'Bearer {access_token}', 'X-User-Agent': CSECommon.CLIENT_ID }
    res = requests.get(CSECommon.EVE_VERIFY, headers=header, data=query)
    if res.ok:
      json_content = json.loads(res.content)
      new_client_message = CSEMessages.CSEMessageNewCharAuth()
      new_client_message.m_CharacterId = json_content.get('CharacterID')
      new_client_message.m_CharacterName = json_content.get('CharacterName')
      new_client_message.m_AccessToken = access_token
      new_client_message.m_RefreshToken = refresh_token
      new_client_message.m_ExpiresDateString = json_content.get('ExpiresOn')
      new_client_message.m_UUID = uuid
      new_client_message.m_Type = char_type
      server.m_MsgSystem.QueueModelUpdateMessage(new_client_message)
      server.ScheduleClientUpdate(new_client_message.m_UUID)

    return "", CSECommon.OK_CODE
  
@app.route(CSECommon.SERVER_PING_ENDPOINT)
def Ping():
   with server.m_LockFlask:
    dict = json.loads(request.json)
    http_request = CSEHTTP.PingRequest()
    CSECommon.FromJson(http_request, dict)
    client = server.m_ClientModel.GetClientByUUID(http_request.m_UUID)
    if client:
      ping_message = CSEMessages.CSEMessageClientPing()
      ping_message.m_UUID = http_request.m_UUID
      ping_message.m_Settings = http_request.m_Settings
      server.m_MsgSystem.QueueModelUpdateMessage(ping_message)
      server.ScheduleClientUpdate(http_request.m_UUID)
    else:
      new_client_message = CSEMessages.CSEMessageNewClient()
      new_client_message.m_UUID = http_request.m_UUID
      new_client_message.m_Settings = http_request.m_Settings
      server.m_MsgSystem.QueueModelUpdateMessage(new_client_message)
      server.ScheduleClientUpdate(http_request.m_UUID)
    return "", CSECommon.OK_CODE
  
@app.route(CSECommon.SERVER_PROFITABLE_ENDPOINT)
def Profitable():
  with server.m_LockFlask:
    dict = json.loads(request.json)
    http_request = CSEHTTP.GetProfitableRoute()
    CSECommon.FromJson(http_request, dict)
    client = server.m_ClientModel.GetClientByUUID(http_request.m_UUID)
    if client:
      res = CSEHTTP.GetProfitableRouteResponse()
      res.m_UUID = http_request.m_UUID
      res.m_ProfitableResult = client.m_ProfitableResult
      res_json = CSECommon.ObjectToJsonDict(res)
      server.ScheduleClientUpdate(http_request.m_UUID)
      return jsonify(res_json), CSECommon.OK_CODE
    return "", CSECommon.NOT_FOUND_CODE
  
@app.route(CSECommon.SERVER_CLIENT_SETTINGS_ENDPOINT, methods = ['POST'])
def SetClientSettings():
  with server.m_LockFlask:
    dict = json.loads(request.json)
    http_request = CSEHTTP.SetClientSettings()
    CSECommon.FromJson(http_request, dict)
    message = CSEMessages.SetClientSettings()
    message.m_UUID = http_request.m_UUID
    message.m_Settings = http_request.m_Settings
    server.m_MsgSystem.QueueModelUpdateMessage(message)
  return "", CSECommon.OK_CODE

@app.route(CSECommon.SERVER_UNDERCUT_ENDPOINT)
def Undercut():
  with server.m_LockFlask:
    dict = json.loads(request.json)
    http_request = CSEHTTP.UndercutRequest()
    CSECommon.FromJson(http_request, dict)
    response = CSEHTTP.UndercutResponse()
    client = server.m_ClientModel.GetClientByUUID(http_request.m_UUID)
    if client:
      response.m_UUID = http_request.m_UUID
      response.m_CharacterId = http_request.m_CharacterId
      response.m_Result = client.m_UndercutResult
      return CSECommon.ObjectToJsonString(response), CSECommon.OK_CODE
    else:
      return "", CSECommon.NOT_FOUND_CODE
  return "", CSECommon.NOT_FOUND_CODE

@app.route(CSECommon.SERVER_MARKET_BALANCE_ENDPOINT)
def MarketBalance():
  with server.m_LockFlask:
    dict = json.loads(request.json)
    http_request = CSEHTTP.MarketBalanceRequest()
    CSECommon.FromJson(http_request, dict)
    response = CSEHTTP.MarketBalanceResponse()
    client = server.m_ClientModel.GetClientByUUID(http_request.m_UUID)
    if client:
      response.m_UUID = http_request.m_UUID
      response.m_Result = client.m_MarketBalanceQueryResult
      return CSECommon.ObjectToJsonString(response), CSECommon.OK_CODE
    else:
      return "", CSECommon.NOT_FOUND_CODE
  return "", CSECommon.NOT_FOUND_CODE

@app.route(CSECommon.SERVER_ACCEPT_OPP_ENDPOINT)
def AcceptOpp():
  with server.m_LockFlask:
    dict = json.loads(request.json)
    http_request = CSEHTTP.AcceptOpportunity()
    CSECommon.FromJson(http_request, dict)
    success = server.m_CharacterModel.HandleAcceptedOpps(http_request, server.m_DBConn)
    if success:
      return "", CSECommon.OK_CODE
    else:
      return "", CSECommon.NOT_FOUND_CODE
    
@app.route(CSECommon.SERVER_ACCEPTED_OPP_ENDPOINT)
def AcceptedOpp():
  with server.m_LockFlask:
    dict = json.loads(request.json)
    http_request = CSEHTTP.AcceptedOpportunitiesRequest()
    CSECommon.FromJson(http_request, dict)
    trades = server.m_CharacterModel.GetAcceptedOpps(server.m_DBConn, http_request.m_CharIDs, CSECommon.OPPORTUNITY_STANDARD_EXPIRE)
    response = CSEHTTP.AcceptedOpportunitiesResponse()
    response.m_UUID = http_request.m_UUID
    response.m_CharIDs = http_request.m_CharIDs
    response.m_Trades = trades
    return CSECommon.ObjectToJsonString(response), CSECommon.OK_CODE
  
@app.route(CSECommon.SERVER_CLEAR_OPPS_ENDPOINT)
def ClearOpps():
  with server.m_LockFlask:
    dict = json.loads(request.json)
    http_request = CSEHTTP.ClearOpportunitiesRequest()
    CSECommon.FromJson(http_request, dict)
    server.m_CharacterModel.ClearAcceptedOpps(server.m_DBConn, http_request.m_IDs)
    server.m_DBConn.commit()
    return "", CSECommon.OK_CODE

def Start(mode):
  server.m_Thread = threading.Thread(target=CSEServer.Main, args=(server, mode))
  server.m_Thread.start()
  print("CSEServer STARTED SERVER LOOP")
  return app