import ProjectSettings
ProjectSettings.Init()
import requests
import CSECommon
import webbrowser
import urllib.parse
import uuid
import CSEHTTP
import json
import time
import threading
import CSEClientSettings
import CSEFileSystem

class CSEClient:
  def __init__(self) -> None:
    self.m_UUID = str(uuid.uuid4()) # ID representing a unique instance of a running client
    self.m_LoggedIn = False
    self.m_CharacterID = 0
    self.m_CharacterName = ""
    self.m_PingThread : threading.Thread() = None
    self.m_ClientSettings = CSEClientSettings.Settings()
client = CSEClient()

def PingThread():
  while True:
    request = CSEHTTP.PingRequest()
    request.m_UUID = client.m_UUID
    request_json = json.dumps(request.__dict__)
    try: 
      requests.get(CSECommon.SERVER_PING_URL, json=request_json)
    except:
      pass
    time.sleep(CSECommon.PING_PERIOD)

CSEFileSystem.ReadObjectFromFileJson(CSECommon.CLIENT_SETTINGS_FILE_PATH, client.m_ClientSettings)
CSEFileSystem.WriteObjectJsonToFilePath(CSECommon.CLIENT_SETTINGS_FILE_PATH, client.m_ClientSettings)

# Log the user in
redirect_uri = urllib.parse.quote_plus(CSECommon.SERVER_AUTH_URL)
scope = urllib.parse.quote_plus(CSECommon.SCOPES)
param_string = f'response_type=code&redirect_uri={redirect_uri}&client_id={CSECommon.CLIENT_ID}&scope={scope}&state={client.m_UUID}'
webbrowser.open("https://login.eveonline.com/v2/oauth/authorize/?"+param_string)

# Wait for the user to authorize and for the server to recognize that authorization
print("Logging you in...")
attempts_remaning = 15
while attempts_remaning > 0 and not client.m_LoggedIn:
  request = CSEHTTP.CheckLoginRequest()
  request.m_UUID = client.m_UUID
  request_json = json.dumps(request.__dict__)
  res_dict = CSECommon.DecodeJsonFromURL(CSECommon.SERVER_CHECK_LOGIN_URL, json=request_json)
  if res_dict:
    res = CSEHTTP.CheckLoginRequestResponse()
    CSECommon.SetObjectFromDict(res, res_dict)
    if res.m_LoggedIn:
      request = CSEHTTP.SetClientSettings()
      request.m_UUID = client.m_UUID
      request.m_Settings = client.m_ClientSettings
      request_json = json.dumps(CSECommon.ObjectToJsonDict(request))
      CSECommon.PostAndDecodeJsonFromURL(CSECommon.SERVER_CLIENT_SETTINGS_URL, json=request_json)
      print(f'Welcome {res.m_CharacterName}')
      client.m_UUID = res.m_UUID
      client.m_CharacterID = res.m_CharacterID
      client.m_CharacterName = res.m_CharacterName
      client.m_LoggedIn = True
    else:
      print(f'Logging in... ({attempts_remaning : .0f} attempts remaining)')
      attempts_remaning = max(0, attempts_remaning - 1)
      time.sleep(1)
  else:
    print(f'Logging in... ({attempts_remaning : .0f} attempts remaining)')
    attempts_remaning = max(0, attempts_remaning - 1)
    time.sleep(1)

# Handle login failure
if not client.m_LoggedIn:
  print("Failed to login. Make sure you're authorizing in the web browser when it pops up.")
  exit(0)

# Spin up ping thread
client.m_PingThread = threading.Thread(target=PingThread, args=())
client.m_PingThread.start()

# Main Loop
while True:
  print("Select an option below: ") 
  print("1) Find a profitable route")
  print("2) Find undercuts")
  user_input = input()

  # Profitable query 
  if user_input.find('1') > -1:
    print("Fetching from server...")
    request = CSEHTTP.GetProfitableRoute()
    request.m_UUID = client.m_UUID
    request_json = json.dumps(request, cls=CSECommon.GenericEncoder)
    res_json = CSECommon.DecodeJsonFromURL(CSECommon.SERVER_PROFITABLE_URL, json=request_json)
    if res_json:
      res = CSEHTTP.GetProfitableRouteResponse()
      CSECommon.FromJson(res, res_json)
      if res.m_ProfitableResult.m_Valid:
        for i,profitable_result in enumerate(res.m_ProfitableResult.m_Entries):
          print(f'{i}. {profitable_result.m_RateOfProfit * 100:.1f}% {profitable_result.m_Profit:,.1f} ISK {profitable_result.m_ItemCount} {profitable_result.m_ItemName} -> {profitable_result.m_SellRegionName}')
        print("Profitable items and where to sell. Press numbers for more info. Press anything else to go back.")
        while True:
          user_input = input()
          if user_input.isnumeric():
            index = int(user_input)
            if index < len(res.m_ProfitableResult.m_Entries):
              profitable_result = res.m_ProfitableResult.m_Entries[index]
              for key, value in profitable_result.__dict__.items():
                if type(value) is float:
                  print(f'{key}: {value:,.1f}')
                else:
                  print(f'{key}: {value}')
            else:
              break
          else:
            break
        pass
      else:
        print("Unable to retrieve profitable results from server. The server may still be working.")
    else:
      print("Unable to retrieve profitable results from server. The server may still be working.")
  # Undercut query
  elif user_input.find('2') > -1:
    request = CSEHTTP.UndercutRequest()
    request.m_UUID = client.m_UUID
    request.m_CharacterId = client.m_CharacterID
    request_json = CSECommon.ObjectToJsonString(request)
    res_json = CSECommon.DecodeJsonFromURL(CSECommon.SERVER_UNDERCUT_URL, json=request_json)
    if res_json:
      res = CSEHTTP.UndercutResponse()
      CSECommon.FromJson(res, res_json)
      if res.m_Result.m_Valid:
        for result in res.m_Result.m_ResultsSameStation:
          print(f'{result.m_RegionName} {result.m_ItemName} price: {result.m_SelfPrice} volume: {result.m_SelfVolume} undercut by lowest price: {result.m_LowestPrice} and volume {result.m_ItemCount} recent sell volume is about {result.m_RecentSellVolumeEst}')
        pass
      else:
         print("Unable to retrieve undercut results from server. The server may still be working.")
    else:
      print("Unable to retrieve undercut results from server. The server may still be working.")

  continue