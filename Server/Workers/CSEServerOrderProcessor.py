# Serializes the latest versions of important files
import Workers.CSEServerWorker as CSEServerWorker
import CSEScrapeHelper
import CSEMarketModel
import sqlite3
import CSECommon
import MySQLHelpers

def Main(worker : CSEServerWorker.Worker, region_scrape : CSEScrapeHelper.RegionOrdersScrape):
  conn = MySQLHelpers.Connect()
  CSEMarketModel.ProcessRegionOrderScrape(region_scrape, conn)
  conn.commit()
  conn.close()