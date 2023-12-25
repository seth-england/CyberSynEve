import multiprocessing
import CSEMessages
import asyncio
import CSEScraper
import CSELogging
import aiohttp

class CSEServerOrderScraperClass:
    def __init__(self):
        self.m_ParentPipe = None
        self.m_ScrapeMessageSet = False

    async def Main(self):
        connector = aiohttp.TCPConnector(limit=50)
        client_session = aiohttp.ClientSession(connector=connector)
        while True:
            self.m_ParentPipe.poll(None)
            message = self.m_ParentPipe.recv()
            if type(message) is CSEMessages.CSEMessageScrapeRegionOrders:
                self.m_ScrapeMessage = message
                self.m_ScrapeMessageSet = True
                CSELogging.Log(f'SCRAPING ORDERS FROM REGION {self.m_ScrapeMessage.m_RegionName}', __file__)
                result = CSEMessages.CSEMessageScrapeRegionOrdersResult()
                result.m_Result = await CSEScraper.ScrapeRegionOrders(self.m_ScrapeMessage.m_RegionId, client_session)
                CSELogging.Log(f'SCRAPED ORDERS FROM REGION {self.m_ScrapeMessage.m_RegionName}', __file__)
                self.m_ParentPipe.send(result)         
       

def Main(pipe,):
  scraper = CSEServerOrderScraperClass()
  scraper.m_ParentPipe = pipe
  asyncio.run(scraper.Main())
    