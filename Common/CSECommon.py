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

# Server Locations
SERVER_URL = 'http://127.0.0.1:5000'
SERVER_AUTH_ENDPOINT = '/auth'
SERVER_AUTH_URL = SERVER_URL + SERVER_AUTH_ENDPOINT
SERVER_CHECK_LOGIN_ENDPOINT = '/checklogin'
SERVER_CHECK_LOGIN_URL = SERVER_URL + SERVER_CHECK_LOGIN_ENDPOINT
SERVER_PING_ENDPOINT = '/ping'
SERVER_PING_URL = SERVER_URL + SERVER_PING_ENDPOINT

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
EVE_VERIFY = 'https://esi.evetech.net/verify/'
EVE_REFRESH_TOKEN = 'https://login.eveonline.com/v2/oauth/token/'
EVE_ROUTE = EVE_SERVER_ROOT + 'route/'

# Codes
NOT_FOUND_CODE = 404
BAD_PARAMS_CODE = 400
OK_CODE = 200
CHILL_CODE = 420

#Other
SHOULD_AUTHORIZE = False
TASK_LIMIT = 100
ERROR_PRONE_TASK_LIMIT = 10 # Task count for cases where all tasks might fail so we don't get in trouble with the eve server
ZERO_TOL = .0001
STATE_STRING = "CSEStateString"
CLIENT_ID = 'ba636c6aeae54c8386770bc919ef2bca'
SCOPES = 'publicData esi-location.read_location.v1 esi-location.read_ship_type.v1'
STANDARD_SLEEP = .1
PING_PERIOD = 15

#Files
PROJECT_ROOT_PATH = pathlib.Path(__file__).parent.parent.as_posix()
SCRAPER_PATH = PROJECT_ROOT_PATH + '/Scraper'
SCRAPE_FILE_PATH = SCRAPER_PATH + '/CurrentScrape'
ROUTES_FILE_PATH = PROJECT_ROOT_PATH + '/Server/Routes'
CLIENT_MODEL_FILE_PATH = PROJECT_ROOT_PATH + '/Server/ClientModel'

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
    res = await session.get(url, **args)
    if res.ok:
      good_res = res
      break
    elif res.status == CHILL_CODE:
      raise Exception("Too many errors from the server")
    elif res.status == NOT_FOUND_CODE:
      return None
    elif res.start == BAD_PARAMS_CODE:
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
    res = requests.get(url, **args)
    if res.ok:
      good_res = res
      break
    elif res.status_code == CHILL_CODE:
      raise Exception("Too many errors from the server")
    elif res.status_code == NOT_FOUND_CODE:
      return None
    elif res.status_code == BAD_PARAMS_CODE:
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
    res = requests.post(url, **args)
    if res.ok:
      good_res = res
      break
    elif res.status_code == CHILL_CODE:
      raise Exception("Too many errors from the server")
    elif res.status_code == NOT_FOUND_CODE:
      return None
    elif res.status_code == BAD_PARAMS_CODE:
      return None
    attempts += 1
  if not good_res is None:
    json_content = json.loads(res.content)
    return json_content
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
        if not member_name.startswith('__') and not inspect.ismethod(value):
          result_dict[member_name] = value
      return result_dict
    return json.JSONEncoder.default(self, obj)
  
def FromJsonTypedDictHelper(o : dict, json_dict : dict, dict_type):
  for key, value in json_dict.items():
    value_object = dict_type()
    FromJson(value_object, value)
    o[int(key)] = value_object

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
      if value_type is dict:
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
            for key, value in value.items():
              attr[int(key)] = value
        else:
          FromJson(attr, value)
      else:
        o.__setattr__(key, value)

sys.path.append(SCRAPER_PATH)