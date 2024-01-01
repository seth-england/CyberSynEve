import ProjectSettings
ProjectSettings.Init()
import CSECommon
import requests
import webbrowser
import json
import CSEMapModel
import CSEScraper
import asyncio
import aiohttp
import multiprocessing
import CSEServer
import CSELogging
import CSEMessages
import CSEHTTP
import threading
import signal
from flask import Flask, request, jsonify
from base64 import b64encode
from telnetlib import NOP
app = Flask(__name__)

CLIENT_SECRET = 'EfdmhqJg7vncmfAEshRANS4wMtcawguFLGZSyJ9Z'

#class CSEServer:
#  def __init__(self) -> None:
#    self.m_ServerToLoopQueue : multiprocessing.Queue = None
#    self.m_LoopProcess : multiprocessing.Process = None

server = CSEServer.CSEServer()

@app.route(CSECommon.SERVER_AUTH_ENDPOINT)
def Auth():
  with server.m_LockFlask:
    code = request.args.get('code')
    uuid = request.args.get('state')
    url_encoded = {'grant_type' : 'authorization_code', 'code' : code}
    user_and_pass = CSECommon.CLIENT_ID + ':' + CLIENT_SECRET
    user_and_pass = user_and_pass.encode("utf-8")
    user_and_pass_param = b64encode(user_and_pass).decode("ascii")
    header_params = {'Authorization' : 'Basic %s' % user_and_pass_param, 'Content-Type' : 'application/x-www-form-urlencoded', 'Host' : 'login.eveonline.com'}
    res = requests.post('https://login.eveonline.com/v2/oauth/token', data=url_encoded, headers=header_params)
    json_content = json.loads(res.content)
    access_token = json_content['access_token']
    refresh_token = json_content['refresh_token']

    # Verify the token
    query = {'user-agent': CSECommon.CLIENT_ID, 'token' : access_token}
    header = { 'Authorization': f'Bearer {access_token}', 'X-User-Agent': CSECommon.CLIENT_ID }
    res = requests.get(CSECommon.EVE_VERIFY, headers=header, data=query)
    if res.ok:
      json_content = json.loads(res.content)
      new_client_message = CSEMessages.CSEMessageNewClientAuth()
      new_client_message.m_CharacterId = json_content.get('CharacterID')
      new_client_message.m_CharacterName = json_content.get('CharacterName')
      new_client_message.m_AccessToken = access_token
      new_client_message.m_RefreshToken = refresh_token
      new_client_message.m_ExpiresDateString = json_content.get('ExpiresOn')
      new_client_message.m_UUID = uuid
      server.m_MsgSystem.QueueModelUpdateMessage(new_client_message)
      server.ScheduleClientUpdate(new_client_message.m_CharacterId)

    return "", CSECommon.OK_CODE

@app.route(CSECommon.SERVER_CHECK_LOGIN_ENDPOINT)
def CheckLogin():
  with server.m_LockFlask:
    dict = json.loads(request.json)
    http_request = CSEHTTP.CheckLoginRequest()
    CSECommon.SetObjectFromDict(http_request, dict)
    res = CSEHTTP.CheckLoginRequestResponse()
    client = server.m_ClientModel.GetClientByUUID(http_request.m_UUID)
    if client:
      res.m_UUID = client.m_UUID
      res.m_CharacterID = client.m_CharacterId
      res.m_CharacterName = client.m_CharacterName
      res.m_LoggedIn = True
    return jsonify(res.__dict__), CSECommon.OK_CODE
  
@app.route(CSECommon.SERVER_PING_ENDPOINT)
def Ping():
  with server.m_LockFlask:
    dict = json.loads(request.json)
    http_request = CSEHTTP.PingRequest()
    CSECommon.FromJson(http_request, dict)
    client = server.m_ClientModel.GetClientByUUID(http_request.m_UUID)
    if client:
      server.ScheduleClientUpdate(client.m_CharacterId)
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
      res.m_Route = client.m_ProfitableRoute
      res_json = CSECommon.ObjectToJsonDict(res)
      server.ScheduleClientUpdate(client.m_CharacterId)
      return jsonify(res_json), CSECommon.OK_CODE
    return "", CSECommon.NOT_FOUND_CODE

server.m_Thread = threading.Thread(target=CSEServer.Main, args=(server,))
server.m_Thread.start()
print("CSEServer STARTED SERVER LOOP")

#CSEScraper.Init()
#g_MapModel = CSEMapModel.CSEMapModel()
#g_MapModel.CreateFromScrape(CSEScraper.CurrentScrape)
#print("Server Init Done")