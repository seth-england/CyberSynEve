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

CLIENT_STATE_PRE = "kPre"
CLIENT_STATE_MAIN = "kMain"
CLIENT_STATE_PROFITABLE = "kProfit"
CLIENT_STATE_CHAR_TYPE = "kCharType"

class CSEClientCharacter:
  def __init__(self) -> None:
    self.m_CharacterId = 0
    self.m_CharacterName = ""
    self.m_Type = CSECommon.CHAR_TYPE_INVALID
    self.m_LoggedIn = False

class CSEClientSerializedValues:
  def __init__(self) -> None:
    self.m_UUID = CSECommon.INVALID_UUID

class CSEClient:
  def __init__(self) -> None:
    self.m_SerializedValues = CSEClientSerializedValues()
    self.m_Characters = list[CSEClientCharacter]()
    self.m_UUID = CSECommon.INVALID_UUID # ID representing a unique instance of a running client
    self.m_LoggedIn = False
    self.m_CharacterID = 0 # Main character
    self.m_CharacterName = ""
    self.m_PingThread : threading.Thread() = None
    self.m_ClientSettings = CSEClientSettings.Settings()
    self.m_Lock = threading.Lock()
    self.m_State = CLIENT_STATE_PRE
    self.m_ProfitableResult = CSEHTTP.CSEProfitableResult()
    self.m_AcceptedOpportunities = list[CSEHTTP.ProfitableTrade]()

  def TransitionMain(self):
    print("Select an option below: ") 
    print("1) Find a profitable route")
    print("2) Market balance")
    print("3) Login Character")
    print("4) Print Characters")
    print("5) Print Safety")
    self.m_State = CLIENT_STATE_MAIN
  
  def UpdateMain(self, user_input : str):
    if user_input.find('1') > -1:
      self.TransitionProfitable()
    elif user_input.find('2') > -1:
      self.TransitionBalance()
    elif user_input.find('3') > -1:
      self.TransitionCharType()
    elif user_input.find('4') > -1:
      self.TransitionPrintChars()
    elif user_input.find('5') > -1:
      self.TransitionSafety()
      return
    
  def TransitionPrintChars(self):
    request = CSEHTTP.CharactersRequest()
    request.m_UUID = self.m_UUID
    request_json = CSECommon.ObjectToJsonString(request)
    res_json = CSECommon.DecodeJsonFromURL(CSECommon.SERVER_CHARACTERS_URL, json=request_json)
    if res_json:
      res = CSEHTTP.CharactersResponse()
      CSECommon.FromJson(res, res_json)
      for id, name, type, logged_in in zip(res.m_CharacterIds, res.m_CharaterNames, res.m_CharacterTypes, res.m_CharacterLoggedIn):
        print(f'{name} {type} {"Logged In" if logged_in else "X Logged Out X"}')
    self.TransitionMain()

  def TransitionProfitable(self):
    self.m_State = CLIENT_STATE_PROFITABLE
    print("Fetching from server...")
    request = CSEHTTP.GetProfitableRoute()
    request.m_UUID = self.m_UUID
    request_json = json.dumps(request, cls=CSECommon.GenericEncoder)
    res_json = CSECommon.DecodeJsonFromURL(CSECommon.SERVER_PROFITABLE_URL, json=request_json)
    if res_json:
      res = CSEHTTP.GetProfitableRouteResponse()
      CSECommon.FromJson(res, res_json)
      if res.m_ProfitableResult.m_Valid:
        self.m_ProfitableResult = res.m_ProfitableResult
        for i,profitable_result in enumerate(res.m_ProfitableResult.m_Entries):
          if not profitable_result.m_AlreadyListed:
            print(f'{i: 3}.) {profitable_result.m_ItemCount: 4} {profitable_result.m_BuyPricePerUnit/1000000: 7.3f}m {profitable_result.m_ItemName} ROP: {profitable_result.m_RateOfProfit * 100:.1f}% Profit: {profitable_result.m_Profit/1000000:.1f}m -> {profitable_result.m_SellRegionName}')
      else:
        print("Not found.")
        self.TransitionMain()
      
  def UpdateProfitable(self, user_input : str):
    if user_input.isnumeric():
      index = int(user_input)
      if index < len(self.m_ProfitableResult.m_Entries):
        profitable_result = self.m_ProfitableResult.m_Entries[index]
        for key, value in profitable_result.__dict__.items():
          if type(value) is float:
            print(f'{key}: {value:,.1f}')
          else:
            print(f'{key}: {value}')
      else:
        print("Not found.")
        self.TransitionMain()
    else:
      self.TransitionMain()
  
  def TransitionBalance(self):    
    request = CSEHTTP.MarketBalanceRequest()
    request.m_UUID = self.m_UUID
    request_json = CSECommon.ObjectToJsonString(request)
    res_json = CSECommon.DecodeJsonFromURL(CSECommon.SERVER_MARKET_BALANCE_URL, json=request_json)
    if res_json:
      res = CSEHTTP.MarketBalanceResponse()
      CSECommon.FromJson(res, res_json)
      if res.m_Result.m_Valid:
        print(f'Balance of recent market transactions is: {res.m_Result.m_Balance:,.1f}')
      else:
         print("Unable to retrieve undercut results from server. The server may still be working.")
    else:
       print("Unable to retrieve undercut results from server. The server may still be working.")
    self.TransitionMain()

  def TransitionSafety(self):
    res_json = CSECommon.DecodeJsonFromURL(CSECommon.SERVER_SAFETY_URL)
    if res_json:
      res = CSEHTTP.SafetyResponse()
      CSECommon.FromJson(res, res_json)
      print(f'Jita To Dodixie: {'Safe' if res.m_JitaToDodixieSafe else "X NOT SAFE X"}')
      print(f'Jita To Amarr: {'Safe' if res.m_JitaToAmarrSafe else "X NOT SAFE X"}')
    self.TransitionMain()

  def TransitionLoginCharacter(self, char_type : str):
    redirect_uri = urllib.parse.quote_plus(CSECommon.SERVER_AUTH_URL)
    scope = urllib.parse.quote_plus(CSECommon.SCOPES)
    param_string = f'response_type=code&redirect_uri={redirect_uri}&client_id={CSECommon.CLIENT_ID}&scope={scope}&state={self.m_UUID} {char_type}'
    webbrowser.open("https://login.eveonline.com/v2/oauth/authorize/?"+param_string)
    self.TransitionMain()
  
  def TransitionCharType(self):
    print("Select Character Type")
    for i, type in enumerate(CSECommon.CHAR_TYPES):
      print(f'{i}) {type}')
    self.m_State = CLIENT_STATE_CHAR_TYPE

  def UpdateCharType(self, user_input : str):
    numeric = user_input.isnumeric()
    if numeric:
      number = int(user_input)
      if number >= 0 and number < len(CSECommon.CHAR_TYPES):
        self.TransitionLoginCharacter(CSECommon.CHAR_TYPES[number])
    else:
      print("Invalid input")
      self.TransitionMain()

  def PingServer(self):
    CSEFileSystem.ReadObjectFromFileJson(CSECommon.CLIENT_SETTINGS_FILE_PATH, self.m_ClientSettings)
    request = CSEHTTP.PingRequest()
    request.m_UUID = self.m_UUID
    request.m_Settings = self.m_ClientSettings
    request_json = CSECommon.ObjectToJsonString(request)
    try: 
      requests.get(CSECommon.SERVER_PING_URL, json=request_json)
    except:
      pass

  def RetrieveCharacters(self):
    self.m_Characters.clear()
    request = CSEHTTP.CharactersRequest()
    request.m_UUID = self.m_UUID
    request_json = json.dumps(request.__dict__)
    res_dict = None
    for i in range(0, CSECommon.REASONABLE_ATTEMPTS):
      res_dict = CSECommon.DecodeJsonFromURL(CSECommon.SERVER_CHARACTERS_URL, json=request_json)
      if res_dict:
        break
    if res_dict:
      res = CSEHTTP.CharactersResponse()
      CSECommon.FromJson(res, res_dict)
      if len(res.m_CharacterIds) == 0:
        return
      for id, name, type, logged_in in zip(res.m_CharacterIds, res.m_CharaterNames, res.m_CharacterTypes, res.m_CharacterLoggedIn):
        new_char = CSEClientCharacter()
        new_char.m_CharacterId = id
        new_char.m_CharacterName = name
        new_char.m_Type = type
        new_char.m_LoggedIn = logged_in
        self.m_Characters.append(new_char)
  
  def RetrieveOpportunities(self):
    request = CSEHTTP.GetProfitableRoute()
    request.m_UUID = self.m_UUID
    request_json = json.dumps(request, cls=CSECommon.GenericEncoder)
    res_json = CSECommon.DecodeJsonFromURL(CSECommon.SERVER_PROFITABLE_URL, json=request_json)
    if res_json:
      res = CSEHTTP.GetProfitableRouteResponse()
      CSECommon.FromJson(res, res_json)
      if res.m_ProfitableResult.m_Valid:
        self.m_ProfitableResult = res.m_ProfitableResult

  def RetrieveAcceptedOpportunities(self, char_ids : list[int]):
    request = CSEHTTP.AcceptedOpportunitiesRequest()
    request.m_UUID = self.m_UUID
    request.m_CharIDs = char_ids
    request_json = json.dumps(request, cls=CSECommon.GenericEncoder)
    res_json = CSECommon.DecodeJsonFromURL(CSECommon.SERVER_ACCEPTED_OPP_URL, json=request_json)
    if res_json:
      res = CSEHTTP.AcceptedOpportunitiesResponse()
      CSECommon.FromJson(res, res_json)
      self.m_AcceptedOpportunities = res.m_Trades