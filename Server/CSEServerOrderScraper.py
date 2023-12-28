import multiprocessing
import CSEMessages
import asyncio
import CSEScraper
import CSELogging
import aiohttp
import queue
import threading
import time
import CSECommon
import CSEItemModel

class OrderScraper:
  def __init__(self):
    self.m_ServerToSelfQueue : queue.Queue = None
    self.m_SelfToServerQueue : queue.Queue = None
    self.m_ParentPipe = None
    self.m_ScrapeMessageSet = False
    self.m_Thread : threading.Thread = None
    self.m_ItemModel : CSEItemModel.ItemModel = None

  async def Main(self):
    connector = aiohttp.TCPConnector(limit=50)
    client_session = aiohttp.ClientSession(connector=connector)
    while True:
      if not self.m_ServerToSelfQueue.empty():
        message = self.m_ServerToSelfQueue.get_nowait()
        if type(message) is CSEMessages.CSEMessageScrapeRegionOrders:
          self.m_ScrapeMessage = message
          self.m_ScrapeMessageSet = True
          CSELogging.Log(f'SCRAPING ORDERS FROM REGION {self.m_ScrapeMessage.m_RegionName}', __file__)
          result = CSEMessages.CSEMessageScrapeRegionOrdersResult()
          result.m_Result = await CSEScraper.ScrapeRegionOrders(self.m_ScrapeMessage.m_RegionId, client_session)
          CSELogging.Log(f'SCRAPED ORDERS FROM REGION {self.m_ScrapeMessage.m_RegionName}', __file__)
          self.m_SelfToServerQueue.put_nowait(result)
        else:
         raise Exception("Unimplemented message type")    
      else:
        time.sleep(CSECommon.STANDARD_SLEEP)
     

def Main(scraper : OrderScraper):
  asyncio.run(scraper.Main())
  