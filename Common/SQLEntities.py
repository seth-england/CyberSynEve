import sqlite3
import datetime

class SQLOrder:
  def __init__(self) -> None:
    self.m_ID = 0
    self.m_RegionID = 0
    self.m_Duration = 0
    self.m_BuyOrder = False
    self.m_Date = datetime.datetime.utcnow()
    self.m_LocationID = 0
    self.m_MinVolume = 0
    self.m_Price = 0.0
    self.m_Range = 0
    self.m_SystemID = 0
    self.m_ItemID = 0
    self.m_VolumeRemain = 0
    self.m_VolumeTotal = 0
  
class SQLOrderHistory:
  def __init__(self) -> None:
    self.m_ID = "INVALID"
    self.m_RegionID = 0
    self.m_ItemID = 0
    self.m_AveragePrice = 0.0
    self.m_Date = datetime.datetime.utcnow()
    self.m_HighestPrice = 0.0
    self.m_LowestPrice = 0.0
    self.m_OrderCount = 0
    self.m_Volume = 0

class SQLSaleRecord:
  def __init__(self) -> None:
    self.m_ID = "INVALID"
    self.m_OrderID = 0
    self.m_RegionID = 0
    self.m_SystemID = 0
    self.m_ItemID = 0
    self.m_BuyOrder = False
    self.m_Date = datetime.datetime.utcnow()
    self.m_Price = 0.0
    self.m_Volume = 0
