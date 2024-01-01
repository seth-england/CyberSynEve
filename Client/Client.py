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

class CSEClient:
  def __init__(self) -> None:
    self.m_UUID = str(uuid.uuid4()) # ID representing a unique instance of a running client
    self.m_LoggedIn = False
    self.m_CharacterID = 0
    self.m_CharacterName = ""
    self.m_PingThread : threading.Thread() = None
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
  user_input = input()
  if user_input.find('1', 0, 0):
    print("Fetching from server...")
    request = CSEHTTP.GetProfitableRoute()
    request.m_UUID = client.m_UUID
    request_json = json.dumps(request, cls=CSECommon.GenericEncoder)
    res_json = CSECommon.DecodeJsonFromURL(CSECommon.SERVER_PROFITABLE_URL, json=request_json)
    if res_json:
      res = CSEHTTP.GetProfitableRouteResponse()
      CSECommon.FromJson(res, res_json)
      if res.m_Route.m_Valid:
        print(f'Item name: {res.m_Route.m_BestItemName}')
        print(f'Buy Region: {res.m_Route.m_BestItemBuyRegionName}')
        print(f'Sell Region: {res.m_Route.m_BestItemSellRegionName}')
        print(f'Profit: {res.m_Route.m_BestItemProfit}')
        print(f'Rate Of Profit: {res.m_Route.m_RateOfProfit}')
        print(f'Item Count: {res.m_Route.m_ItemCount}')
        print(f'Start Region Mean Price: {res.m_Route.m_StartRegionMeanPrice}')
        print(f'End Region Mean Price {res.m_Route.m_EndRegionMeanPrice}')
      else:
        print("Unable to retrieve best route from server. The server may still be working.")
        if len(res.m_Route.m_Error) > 0:
          print(f'Servers says: {res.m_Route.m_Error}')
    else:
      print("Unable to retrieve best route from server. The server may still be working.")

        

  continue