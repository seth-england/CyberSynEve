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

class CSEClient:
  def __init__(self) -> None:
    self.m_UUID = uuid.uuid4() # ID representing a unique instance of a running client
    self.m_LoggedIn = False
    self.m_CharacterID = 0
    self.m_CharacterName = ""
client = CSEClient()

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
  request.m_UUID = str(client.m_UUID)
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

if not client.m_LoggedIn:
  print("Failed to login. Make sure you're authorizing in the web browser when it pops up.")
  exit(0)

# Main Loop
while True:
  print("Select an option below: ")
  print("1) Find a profitable route")
  user_input = input()
  if user_input.find('1', 0, 0):
    print("Fetching from server...")
    print("DING DONG")
  continue