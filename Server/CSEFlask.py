import ProjectSettings
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
import CSEServerClientConnection
import datetime
import CSEClientSettings
import CSEClientModel
from flask import Flask, request, jsonify
from flask_cors import CORS
from base64 import b64encode
from telnetlib import NOP
from uuid import UUID
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

CLIENT_SECRET = 'EfdmhqJg7vncmfAEshRANS4wMtcawguFLGZSyJ9Z'
server = CSEServer.CSEServer()

class ValidateConnectionResult:
  def __init__(self):
    self.m_Connection: CSEServerClientConnection.Connection | None = None
    self.m_Client: CSEClientModel.CSEClientData | None = None
    self.m_ConnectionUUID: str | None = None
    self.m_ClientID: int | None = None

def ValidateConnection(request) -> ValidateConnectionResult:
  res = ValidateConnectionResult()
  session_uuid = request.values.get('m_SessionUUID')
  client_id = request.values.get("m_ClientID")
  if type(session_uuid) == str:
    try:
      UUID(session_uuid)
      res.m_ConnectionUUID = session_uuid
    except:
      pass
    res.m_Connection = server.m_ServerClientConnections.get(session_uuid)
  if type(client_id) == str:
    try:
      client_id = int(client_id)
      res.m_Client = server.m_ClientModel.GetClientById(client_id)
      res.m_ClientID = client_id
    except:
      pass
  return res

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
  return json_string, CSECommon.CODE_OK

@app.route(CSECommon.SERVER_CHARACTERS_ENDPOINT)
def Characters():
  session_uuid = request.values.get('m_SessionUUID')
  client_id = request.values.get("m_ClientID")
  if type(session_uuid) != str or type(client_id) != str:
    return "", CSECommon.CODE_BAD_PARAMS
  client_id = int(client_id)

  char_ids = server.m_ClientModel.GetCharacterIds(client_id)
  res = CSEHTTP.CharactersResponse()
  if len(char_ids) > 0:
    for char_id in char_ids:
      char_data = server.m_CharacterModel.GetCharDataById(char_id)
      if char_data:
        char_http = CSEHTTP.CharacterHTTP()
        char_http.m_CharacterID = char_data.m_CharacterId
        char_http.m_CharacterName = char_data.m_CharacterName
        char_http.m_CharacterType = char_data.m_Type
        char_http.m_CharacterLoggedIn = char_data.m_LoggedIn
        res.m_Characters.append(char_http)
  return CSECommon.ObjectToJsonString(res), CSECommon.CODE_OK



@app.route(CSECommon.SERVER_AUTH_ENDPOINT)
def Auth():
  with server.m_LockFlask:
    code = request.args.get('code')
    session_uuid : str = request.args.get('state')
    url_encoded = {'grant_type' : 'authorization_code', 'code' : code}
    user_and_pass = CSECommon.CLIENT_ID + ':' + CLIENT_SECRET
    user_and_pass = user_and_pass.encode("utf-8")
    user_and_pass_param = b64encode(user_and_pass).decode("ascii")
    header_params = {'Authorization' : 'Basic %s' % user_and_pass_param, 'Content-Type' : 'application/x-www-form-urlencoded', 'Host' : 'login.eveonline.com'}
    res = requests.post('https://login.eveonline.com/v2/oauth/token', data=url_encoded, headers=header_params)
    if res.status_code != CSECommon.CODE_OK:
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
      
      # Get the account id
      character_id = json_content.get('CharacterID')
      client_id = character_id

      client_conn = server.m_ServerClientConnections.get(session_uuid)
      if client_conn is None:
        return "Client is not connected, please login!", CSECommon.CODE_INTERNAL_SERVER_ERROR
      elif client_conn and client_conn.m_ClientID:
        client_id = client_conn.m_ClientID
      else:
        client_id = character_id
        client_conn.m_ClientID = client_id
        new_client_message = CSEMessages.CSEMessageNewClient()
        new_client_message.m_ClientId = client_id
        server.m_MsgSystem.QueueModelUpdateMessage(new_client_message)
        server.m_ClientModel.HandleNewClient(new_client_message)
        server.ScheduleClientUpdate(client_id)        

      character_login_message = CSEMessages.CSEMessageNewCharAuth()
      character_login_message.m_CharacterId = character_id
      character_login_message.m_CharacterName = json_content.get('CharacterName')
      character_login_message.m_AccessToken = access_token
      character_login_message.m_RefreshToken = refresh_token
      character_login_message.m_ExpiresDateString = json_content.get('ExpiresOn')
      character_login_message.m_ClientId = client_id
      server.m_MsgSystem.QueueModelUpdateMessage(character_login_message)
      server.ScheduleClientUpdate(character_login_message.m_ClientId)

    return "", CSECommon.CODE_OK
  
@app.route(CSECommon.SERVER_PING_ENDPOINT)
def Ping():
   with server.m_LockFlask:
    validate_result = ValidateConnection(request)
    if validate_result.m_ConnectionUUID is None:
      return "Invalid connection uuid", CSECommon.CODE_BAD_PARAMS
    existing_connection = validate_result.m_Connection
    if not existing_connection:
      existing_connection = CSEServerClientConnection.Connection()
      existing_connection.m_SessionUUID = validate_result.m_ConnectionUUID
      server.m_ServerClientConnections[validate_result.m_ConnectionUUID] = existing_connection
    existing_connection.m_LastContact = datetime.datetime.now(datetime.timezone.utc)
    
    if existing_connection.m_ClientID:
      server.ScheduleClientUpdate(existing_connection.m_ClientID)
    
    res = CSEHTTP.PingResponse()
    res.m_SessionUUID = existing_connection.m_SessionUUID
    res.m_ClientId = existing_connection.m_ClientID

    # Check if we have characters logged in
    character_ids = server.m_ClientModel.GetCharacterIds(res.m_ClientId)
    if character_ids:
      res.m_CharacterCount = len(character_ids)
      for char_id in character_ids:
        char_data = server.m_CharacterModel.GetCharDataById(char_id)
        if char_data and char_data.m_LoggedIn:
          res.m_LoggedInCharacterCount += 1

    res_string = CSECommon.ObjectToJsonString(res)
    return res_string, CSECommon.CODE_OK
  
@app.route(CSECommon.SERVER_PORTRAIT_ENDPOINT)
def Portrait():
   with server.m_LockFlask:
    validate_result = ValidateConnection(request)
    if validate_result.m_Connection is None or validate_result.m_Client is None:
      return "", CSECommon.CODE_BAD_PARAMS
    char_id = request.values.get('m_CharacterID')
    try:
      char_id = int(char_id)
    except:
      return "", CSECommon.CODE_BAD_PARAMS
    
    # Check that we own this character
    if char_id not in validate_result.m_Client.m_CharacterIds:
      return "Character is not owned by this client", CSECommon.CODE_UNAUTHORIZED

    char_data = server.m_CharacterModel.GetCharDataById(char_id)
    if char_data is None:
      return "Character not found", CSECommon.CODE_NOT_FOUND

    if char_data.m_Portrait is None:
      return "Portrait not found", CSECommon.CODE_NOT_FOUND

    res = CSEHTTP.PortraitResponse()
    res.m_SessionUUID = validate_result.m_ConnectionUUID
    res.m_ClientID = validate_result.m_ClientID
    res.m_CharacterID = char_id
    res.m_Portrait = char_data.m_Portrait 

    res_string = CSECommon.ObjectToJsonString(res)
    return res_string, CSECommon.CODE_OK

@app.route(CSECommon.SERVER_PROFITABLE_ENDPOINT)
def Profitable():
  with server.m_LockFlask:
    valid_result = ValidateConnection(request)
    if valid_result.m_Client is None:
      return "", CSECommon.CODE_BAD_PARAMS
      
    res = CSEHTTP.GetProfitableRouteResponse()
    res.m_UUID = valid_result.m_ClientID
    res.m_ProfitableResult = valid_result.m_Client.m_ProfitableResult
    res_json = CSECommon.ObjectToJsonDict(res)
    server.ScheduleClientUpdate(http_request.m_UUID)
    return jsonify(res_json), CSECommon.CODE_OK
    return "", CSECommon.CODE_NOT_FOUND

@app.route(CSECommon.SERVER_CLIENT_SETTINGS_ENDPOINT, methods= ['GET'])
def GetClientSettings():
  with server.m_LockFlask:
    session_uuid = request.values.get('m_SessionUUID')
    client_id = request.values.get("m_ClientID")
    if type(session_uuid) != str or type(client_id) != str:
      return "", CSECommon.CODE_BAD_PARAMS
    
    client_id = int(client_id)

    client_settings = CSEClientSettings.Settings()
    existing_connection = server.m_ServerClientConnections.get(session_uuid)
    if existing_connection:
      if existing_connection.m_ClientID == client_id:
        client = server.m_ClientModel.GetClientById(client_id)
        if client:
          return CSECommon.ObjectToJsonString(client.m_Settings), CSECommon.CODE_OK
      else:
        return "", CSECommon.CODE_NOT_FOUND
    else:
      return "", CSECommon.CODE_NOT_FOUND
  return "", CSECommon.CODE_OK

@app.route(CSECommon.SERVER_CLIENT_SETTINGS_ENDPOINT, methods= ['PUT'])
def SetClientSettings():
  with server.m_LockFlask:
    session_uuid = request.values.get('m_SessionUUID')
    client_id = request.values.get("m_ClientID")
    if type(session_uuid) != str or type(client_id) != str:
      return "", CSECommon.CODE_BAD_PARAMS
    client_id = int(client_id)
    
    dict = json.loads(request.data)
    message = CSEMessages.SetClientSettings()
    CSECommon.FromJson(message.m_Settings, dict)
    message.m_ClientID = client_id
    server.m_MsgSystem.QueueModelUpdateMessage(message)
  return "", CSECommon.CODE_OK

@app.route(CSECommon.SERVER_UNDERCUT_ENDPOINT)
def Undercut():
  with server.m_LockFlask:
    dict = json.loads(request.json)
    http_request = CSEHTTP.UndercutRequest()
    CSECommon.FromJson(http_request, dict)
    response = CSEHTTP.UndercutResponse()
    client = server.m_ClientModel.GetClientById(http_request.m_UUID)
    if client:
      response.m_UUID = http_request.m_UUID
      response.m_CharacterId = http_request.m_CharacterId
      response.m_Result = client.m_UndercutResult
      return CSECommon.ObjectToJsonString(response), CSECommon.CODE_OK
    else:
      return "", CSECommon.CODE_NOT_FOUND
  return "", CSECommon.CODE_NOT_FOUND

@app.route(CSECommon.SERVER_MARKET_BALANCE_ENDPOINT)
def MarketBalance():
  with server.m_LockFlask:
    dict = json.loads(request.json)
    http_request = CSEHTTP.MarketBalanceRequest()
    CSECommon.FromJson(http_request, dict)
    response = CSEHTTP.MarketBalanceResponse()
    client = server.m_ClientModel.GetClientById(http_request.m_UUID)
    if client:
      response.m_UUID = http_request.m_UUID
      response.m_Result = client.m_MarketBalanceQueryResult
      return CSECommon.ObjectToJsonString(response), CSECommon.CODE_OK
    else:
      return "", CSECommon.CODE_NOT_FOUND
  return "", CSECommon.CODE_NOT_FOUND

@app.route(CSECommon.SERVER_ACCEPT_OPP_ENDPOINT)
def AcceptOpp():
  with server.m_LockFlask:
    dict = json.loads(request.json)
    http_request = CSEHTTP.AcceptOpportunity()
    CSECommon.FromJson(http_request, dict)
    success = server.m_CharacterModel.HandleAcceptedOpps(http_request, server.m_DBConn)
    if success:
      return "", CSECommon.CODE_OK
    else:
      return "", CSECommon.CODE_NOT_FOUND
    
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
    return CSECommon.ObjectToJsonString(response), CSECommon.CODE_OK
  
@app.route(CSECommon.SERVER_CLEAR_OPPS_ENDPOINT)
def ClearOpps():
  with server.m_LockFlask:
    dict = json.loads(request.json)
    http_request = CSEHTTP.ClearOpportunitiesRequest()
    CSECommon.FromJson(http_request, dict)
    server.m_CharacterModel.ClearAcceptedOpps(server.m_DBConn, http_request.m_IDs)
    server.m_DBConn.commit()
    return "", CSECommon.CODE_OK

def Start(mode):
  server.m_Thread = threading.Thread(target=CSEServer.Main, args=(server, mode))
  server.m_Thread.start()
  print("CSEServer STARTED SERVER LOOP")
  return app