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
AUTH = '/auth'
PING = '/ping'
MAP = '/map'
FULL_SCRAPE = '/full_scrape/'
MAP_SCRAPE = '/map_scrape/'
FULL_SCRAPE_URL = SERVER_URL + FULL_SCRAPE
MAP_SCRAPE_URL = SERVER_URL + MAP_SCRAPE

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

# Codes
ERROR_CODE = 404
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

#Files
PROJECT_ROOT_PATH = pathlib.Path(__file__).parent.parent.as_posix()
SCRAPER_PATH = PROJECT_ROOT_PATH + '/Scraper'
SCRAPE_FILE_PATH = SCRAPER_PATH + '/CurrentScrape'

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
    elif res.status == ERROR_CODE:
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
    elif res.status_code == ERROR_CODE:
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
    elif res.status_code == ERROR_CODE:
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

sys.path.append(SCRAPER_PATH)