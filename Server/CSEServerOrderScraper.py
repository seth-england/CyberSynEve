import multiprocessing
import CSEMessages
import asyncio
import CSEScrapeHelper
import CSELogging
import aiohttp
import queue
import threading
import time
import CSECommon
import CSEItemModel
import CSEMarketModel
import CSEServerMessageSystem
import Workers.CSEServerWorker as CSEServerWorker

async def ScrapeRegionOrders(region_id, client_session : aiohttp.ClientSession, item_model : CSEItemModel.ItemModel) -> CSEScrapeHelper.RegionOrdersScrape:
  region_orders_scrape = CSEScrapeHelper.RegionOrdersScrape()
  region_orders_scrape.m_RegionId = region_id

  # Generate a list of type ids on the market
  search_path = CSECommon.EVE_MARKETS + str(region_id) + '/' + 'orders/'
  blank_page = False
  page_number = 1
  unique_type_ids = {}
  while not blank_page:
    parameters = {'page' : str(page_number), 'order_type' : 'all'}
    result = await CSECommon.DecodeJsonAsyncHelper(client_session, search_path, params = parameters)
    if result is None:
      blank_page = True
      break
    else:
      order_count = len(result)
      if order_count < CSECommon.FULL_PAGE_ORDER_COUNT:
        blank_page = True
      for dict in result:
        type_id = dict.get('type_id')
        if type_id:
          valid_item = item_model.GetItemDataFromID(type_id)
          if valid_item:
            unique_type_ids[int(type_id)] = True
            order_dict_array = region_orders_scrape.m_ItemIdToOrderDictArray.get(type_id)
            if order_dict_array is None:
              order_dict_array = list()
              region_orders_scrape.m_ItemIdToOrderDictArray[type_id] = order_dict_array
            order_dict_array.append(dict)
          else:
            stop = 0
    page_number = page_number + 1

  # Get the history data of the type ids on the market
  search_path = CSECommon.EVE_MARKETS + str(region_id) + '/' + 'history/'
  tasks = []
  task_type_ids = []
  for i, type_id in enumerate(list(unique_type_ids.keys())):
    parameters = {'region_id' : region_id, 'type_id' : type_id}
    task_type_ids.append(type_id)
    tasks.append(asyncio.ensure_future(CSECommon.DecodeJsonAsyncHelper(client_session, search_path, params=parameters)))
    if len(tasks) > CSECommon.TASK_LIMIT:
      finished_dicts = await asyncio.gather(*tasks)
      for j, dict in enumerate(finished_dicts):
        if not dict is None:
          task_type_id = task_type_ids[j]
          region_orders_scrape.m_ItemIdToHistoryDictArray[task_type_id] = dict
      tasks.clear()
      task_type_ids.clear()
  if len(tasks) > 0:
    finished_dicts = await asyncio.gather(*tasks)
    for j, dict in enumerate(finished_dicts):
      if not dict is None:
        task_type_id = task_type_ids[j]
        region_orders_scrape.m_ItemIdToHistoryDictArray[task_type_id] = dict
    tasks.clear()
    task_type_ids.clear()

  region_orders_scrape.m_Valid = True
  region_orders_scrape.m_Time = time.time()
  return region_orders_scrape

async def Main(worker : CSEServerWorker.Worker, region_id : int, region_index : int, region_name : str):
  CSELogging.Log(f'{region_index}. SCRAPING ORDERS FROM REGION {region_name}', __file__)
  result = CSEMessages.CSEMessageScrapeRegionOrdersResult()
  scrape = await ScrapeRegionOrders(region_id, worker.m_ClientSession, worker.m_AllModels.m_ItemModel)
  result.m_MarketRegionData = CSEMarketModel.ConvertRegionsOrdersScrapeToRegionMarketData(scrape)
  result.m_RegionName = region_name
  worker.m_MsgSystem.QueueModelUpdateMessage(result)
  CSELogging.Log(f'SCRAPED ORDERS FROM REGION {region_name}', __file__)
  