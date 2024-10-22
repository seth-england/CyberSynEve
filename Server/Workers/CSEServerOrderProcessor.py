# Serializes the latest versions of important files
import Workers.CSEServerWorker as CSEServerWorker
import CSEScrapeHelper
import CSEMarketModel
import sqlite3
import CSECommon
import SQLHelpers

def Main(worker : CSEServerWorker.Worker, region_scrape : CSEScrapeHelper.RegionOrdersScrape):
  conn = SQLHelpers.Connect(CSECommon.MASTER_DB_PATH)
  CSEMarketModel.ProcessRegionOrderScrape(region_scrape, conn)
  conn.commit()
  conn.close()