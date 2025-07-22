import pathlib
import random
import time
import asyncio
import sys
import aiohttp
from json import JSONDecoder, JSONEncoder
import inspect
import json
import requests
import CSELogging
import socket
import datetime

hostname = socket.getfqdn()
local_ip = socket.gethostbyname_ex(hostname)[2][0]
DB_URL = '192.168.50.225'
if local_ip == DB_URL:
  DB_URL = '127.0.0.1'

# Server Locations
#SERVER_URL = 'http://192.168.50.225:5000'
SERVER_URL = 'http://127.0.0.1:5000'
SERVER_AUTH_ENDPOINT = '/auth'
SERVER_AUTH_URL = SERVER_URL + SERVER_AUTH_ENDPOINT
SERVER_CHECK_LOGIN_ENDPOINT = '/checklogin'
SERVER_CHECK_LOGIN_URL = SERVER_URL + SERVER_CHECK_LOGIN_ENDPOINT
SERVER_PING_ENDPOINT = '/ping'
SERVER_PING_URL = SERVER_URL + SERVER_PING_ENDPOINT
SERVER_ACCEPT_OPP_ENDPOINT = '/acceptopp'
SERVER_ACCEPT_OPP_URL = SERVER_URL + SERVER_ACCEPT_OPP_ENDPOINT
SERVER_ACCEPTED_OPP_ENDPOINT = '/acceptedopp'
SERVER_ACCEPTED_OPP_URL = SERVER_URL + SERVER_ACCEPTED_OPP_ENDPOINT
SERVER_CLEAR_OPPS_ENDPOINT = '/clearopps'
SERVER_CLEAR_OPPS_URL = SERVER_URL + SERVER_CLEAR_OPPS_ENDPOINT
SERVER_PROFITABLE_ENDPOINT = '/profitable'
SERVER_PROFITABLE_URL = SERVER_URL + SERVER_PROFITABLE_ENDPOINT
SERVER_CLIENT_SETTINGS_ENDPOINT = '/clientsettings'
SERVER_CLIENT_SETTINGS_URL = SERVER_URL + SERVER_CLIENT_SETTINGS_ENDPOINT
SERVER_UNDERCUT_ENDPOINT = '/undercut'
SERVER_UNDERCUT_URL = SERVER_URL + SERVER_UNDERCUT_ENDPOINT
SERVER_MARKET_BALANCE_ENDPOINT = '/marketbalance'
SERVER_MARKET_BALANCE_URL = SERVER_URL + SERVER_MARKET_BALANCE_ENDPOINT
SERVER_CHARACTERS_ENDPOINT = '/characters'
SERVER_CHARACTERS_URL = SERVER_URL + SERVER_CHARACTERS_ENDPOINT
SERVER_PORTRAIT_ENDPOINT = '/portrait'
SERVER_PORTRAIT_URL = SERVER_URL + SERVER_PORTRAIT_ENDPOINT 
SERVER_SAFETY_ENDPOINT = '/safety'
SERVER_SAFETY_URL = SERVER_URL + SERVER_SAFETY_ENDPOINT

# Eve server
import ProjectSettings
EVE_SERVER_ROOT = 'https://esi.evetech.net/dev/'
EVE_REGIONS = EVE_SERVER_ROOT + 'universe/regions/'
EVE_CONSTELLATIONS = EVE_SERVER_ROOT + 'universe/constellations/'
EVE_SYSTEMS = EVE_SERVER_ROOT + 'universe/systems/'
EVE_STARGATES = EVE_SERVER_ROOT + 'universe/stargates/'
EVE_STATIONS = EVE_SERVER_ROOT + 'universe/stations/'
EVE_MARKETS = EVE_SERVER_ROOT + 'markets/'
EVE_ITEM_TYPE_IDS = EVE_SERVER_ROOT + 'universe/types/'
EVE_CHARACTERS = EVE_SERVER_ROOT + 'characters/'
EVE_VERIFY = 'https://esi.evetech.net/verify/'
EVE_REFRESH_TOKEN = 'https://login.eveonline.com/v2/oauth/token/'
EVE_ROUTE = EVE_SERVER_ROOT + 'route/'

# Codes
CODE_NOT_FOUND = 404
CODE_BAD_PARAMS = 400
CODE_OK = 200
CODE_CHILL = 420
CODE_UNAUTHORIZED = 401
CODE_INTERNAL_SERVER_ERROR = 500

#Other
SHOULD_AUTHORIZE = False
TASK_LIMIT = 100
ERROR_PRONE_TASK_LIMIT = 10 # Task count for cases where all tasks might fail so we don't get in trouble with the eve server
ZERO_TOL = .0001
STATE_STRING = "CSEStateString"
CLIENT_ID = 'ba636c6aeae54c8386770bc919ef2bca'
SCOPES = 'publicData esi-location.read_location.v1 esi-location.read_ship_type.v1 esi-wallet.read_character_wallet.v1 esi-markets.read_character_orders.v1'
STANDARD_SLEEP = .1
PING_PERIOD = 15
INF = float("inf")
INVALID_UUID = ""
REASONABLE_ATTEMPTS = 5
FULL_PAGE_ORDER_COUNT = 1000
SERVER_ERROR_SLEEP_SECONDS = 60
APP_NAME = "KomissarTest"
SAFETY_TIME = 3600
OPPORTUNITY_STANDARD_EXPIRE = datetime.timedelta(days=1)

CHAR_TYPE_HAULER = "HAULER"
CHAR_TYPE_TRADE_BOT = "TRADE"
CHAR_TYPE_INVALID = "INVALID"
CHAR_TYPES = [ CHAR_TYPE_HAULER, CHAR_TYPE_TRADE_BOT, CHAR_TYPE_INVALID ]

#Files
CODE_ROOT_PATH = pathlib.Path(__file__).parent.parent.as_posix()
FILES_ROOT_PATH = 'X:/CSE'
SERIALIZED_FILE_EXT = '.cse'
SCRAPE_FILE_PATH = FILES_ROOT_PATH + '/Server/Scrape' + SERIALIZED_FILE_EXT
ROUTES_FILE_PATH = FILES_ROOT_PATH + '/Server/Routes' + SERIALIZED_FILE_EXT
CLIENT_MODEL_FILE_PATH = FILES_ROOT_PATH + '/Server/ClientModel' + SERIALIZED_FILE_EXT
MARKET_MODEL_FILE_PATH = FILES_ROOT_PATH + '/Server/MarketModel' + SERIALIZED_FILE_EXT
CHARACTER_MODEL_FILE_PATH = FILES_ROOT_PATH + '/Server/CharacterModel' + SERIALIZED_FILE_EXT
REGION_MARKET_SCRAPES_DIR = FILES_ROOT_PATH + '/Server/Scrapes/RegionMarkets/'
BACKUP_FILE_SUFFIX = 'BACK'
CLIENT_SETTINGS_FILE_PATH = 'ClientSettings' + SERIALIZED_FILE_EXT
CLIENT_FILE_PATH = 'Client' + SERIALIZED_FILE_EXT
MASTER_DB_PATH = FILES_ROOT_PATH + '/CSEMasterDB.db'

#Tables
TABLE_ORDER_HISTORY = "OrderHistory"
TABLE_CURRENT_ORDERS = "CurrentOrders"
TABLE_SALE_RECORD = "SaleRecords"
TABLE_ACCEPTED_OPPS = "AcceptedOpps"

#Modes
MODE_DEFAULT = 'cse_mode_default'
MODE_QUERY_ONLY = 'cse_mode_query'
MODE_SCRAPE_ONLY = 'cse_mode_scrape'

#Dats
DATETIME_DEFAULT_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

def SetObjectFromDict(self, dictionary):
  for key, value in dictionary.items():
    try:
      attr = self.__getattribute__(key)
    except:
      continue
    attribute_type = type(attr)
    if type(value) is dict:
      if attribute_type is dict:
        self.__setattr__(key, value)
      elif issubclass(attribute_type, object):
        SetObjectFromDict(attr, value)
    else:
      self.__setattr__(key, value)
  return

async def DecodeJsonAsyncHelper(session : aiohttp.ClientSession, url, **args):
  attempts = 0
  good_res = None
  while attempts < 3:
    await asyncio.sleep(random.uniform(.01, 1))
    try: 
      res = await session.get(url, **args)
    except:
      return None
    if res.ok:
      good_res = res
      break
    elif res.status == CODE_CHILL:
      raise Exception("Too many errors from the server")
    elif res.status == CODE_NOT_FOUND:
      return None
    elif res.status == CODE_INTERNAL_SERVER_ERROR:
      text = await res.text()
      dict = JSONDecoder().decode(text)
      error = dict.get('error')
      CSELogging.Log(f'Encountered internal server error accessing {url} sleeping for {SERVER_ERROR_SLEEP_SECONDS} {error}')
      time.sleep(SERVER_ERROR_SLEEP_SECONDS)
    elif res.status == CODE_BAD_PARAMS:
      return None
    attempts += 1
  if not good_res is None:
    text = await res.text()
    return JSONDecoder().decode(text)
  else:
    return None
  
def DecodeJsonFromURL(url, **args):
  attempts = 0
  good_res = None
  while attempts < 3:
    time.sleep(random.uniform(.01, 1))
    try:
      res = requests.get(url, **args)
    except:
      return None
    if res.ok:
      good_res = res
      break
    elif res.status_code == CODE_CHILL:
      raise Exception("Too many errors from the server")
    elif res.status_code == CODE_NOT_FOUND:
      return None
    elif res.status_code == CODE_INTERNAL_SERVER_ERROR:
      CSELogging.Log(f'Encountered internal server error accessing {url} sleeping for {SERVER_ERROR_SLEEP_SECONDS}')
      time.sleep(SERVER_ERROR_SLEEP_SECONDS)
    elif res.status_code == CODE_BAD_PARAMS:
      return None
    attempts += 1
  if not good_res is None:
    json_content = json.loads(res.content)
    return json_content
  else:
    return None
  
def PostAndDecodeJsonFromURL(url, **args):
  attempts = 0
  good_res = None
  while attempts < 3:
    time.sleep(random.uniform(.01, 1))
    try:
      res = requests.post(url, **args)
    except:
      return None
    if res.ok:
      good_res = res
      break
    elif res.status_code == CODE_CHILL:
      raise Exception("Too many errors from the server")
    elif res.status_code == CODE_NOT_FOUND:
      return None
    elif res.status_code == CODE_INTERNAL_SERVER_ERROR:
      CSELogging.Log(f'Encountered internal server error accessing {url} sleeping for {SERVER_ERROR_SLEEP_SECONDS}')
      time.sleep(SERVER_ERROR_SLEEP_SECONDS)
    elif res.status_code == CODE_BAD_PARAMS:
      return None
    attempts += 1
  if not good_res is None:
    try:
      json_content = json.loads(res.content)
      return json_content
    except:
      return None
  else:
    return None
  
class GenericEncoder(JSONEncoder):
  def default(self, obj):
    if isinstance(obj, object):
      member_names = inspect.getmembers(obj)
      result_dict = {}
      for member_name_tuple in member_names:
        member_name = member_name_tuple[0]
        value = getattr(obj, member_name)
        if member_name.startswith('__'):
          continue
        elif inspect.ismethod(value) or inspect.isbuiltin(value):
          continue
        if not member_name.startswith('__') and not inspect.ismethod(value) and not type(value) is type:
          if type(value) is datetime.datetime:
            value = value.strftime(DATETIME_DEFAULT_FORMAT)
          result_dict[member_name] = value
      return result_dict
    return json.JSONEncoder.default(self, obj)

def ObjectToJsonString(o:object):
  try:
    json_string = json.dumps(o, cls=GenericEncoder)
  except Exception as e:
    pass
  return json_string

def ObjectToJsonDict(o:object):
  json_string = ObjectToJsonString(o)
  json_dict = json.loads(json_string)
  return json_dict
  
def FromJsonTypedListHelper(o : list, json_list : dict, list_type):
  for value in json_list:
    value_object = list_type()
    FromJson(value_object, value)
    o.append(value_object)

def FromJsonTypedDictHelper(o : dict, json_dict : dict, dict_type):
  for key, value in json_dict.items():
    value_object = dict_type()
    FromJson(value_object, value)
    if type(key) == str:
      if key.isnumeric():
        o[int(key)] = value_object
      else:
        o[key] = value_object
    else:
      o[key] = value_object

def FromJsonListHelper(o : list, json_list : list):
  for value in json_list:
    if type(value) is dict:
      new_dict = dict()
      FromJsonDictHelper(new_dict, value)
      o.append(new_dict)
    elif type(value) is list:
      new_list = list()
      FromJsonListHelper(new_list, value)
      o.append(new_list)
    else:
      o.append(value)    
  

def FromJsonDictHelper(o : dict, json_dict : dict):
  for key, value in json_dict.items():
    if type(value) is dict:
      new_dict = dict()
      FromJsonDictHelper(new_dict, value)
      if key.isnumeric():
        o[int(key)] = new_dict
      else:
        o[key] = new_dict
    elif type(value) is list:
      new_list = list()
      FromJsonListHelper(new_list, value)
      if key.isnumeric():
        o[int(key)] = new_list
      else:
        o[key] = new_list
    else:
      if key.isnumeric():
        o[int(key)] = value
      else:
        o[key] = value      

def FromJson(o : object, json_dict : dict):
  for key, value in json_dict.items():
    attr = None 
    try:
      attr = o.__getattribute__(key)
    except:
      pass
    if attr is not None:
      value_type = type(value)
      attr_type = type(attr)
      if inspect.ismethod(value):
        continue
      elif attr_type is type:
        continue
      elif attr_type is datetime.datetime:
        value = datetime.datetime.strptime(value, DATETIME_DEFAULT_FORMAT)
        o.__setattr__(key, value)
      elif value_type is dict:
        # The member is a dict
        if attr_type is dict:
          # Check that it doesn't have a special value type
          type_key = key + 'ValueType'
          type_value = None
          try:
            type_value = o.__getattribute__(type_key)
          except:
            pass
          if type_value:
            FromJsonTypedDictHelper(attr, value, type_value)
          else:
            FromJsonDictHelper(attr, value)
        else:
          FromJson(attr, value)
      elif value_type is list:
        if attr_type is list:
          # Check that it doesn't have a special value type
          type_key = key + 'ValueType'
          type_value = None
          try:
            type_value = o.__getattribute__(type_key)
          except:
            pass
          if type_value:
            FromJsonTypedListHelper(attr, value, type_value)
          else:
            FromJsonListHelper(attr, value)
        else:
          o.__setattr__(key, value) 
      else:
        o.__setattr__(key, value)