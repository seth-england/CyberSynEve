import time
import multiprocessing
import CSELogging

TYPE_INVALID = "INVALID"
TYPE_MARKET = "MARKET"

MARKET_REQUEST_LIMIT = 300
MARKET_REQUEST_LIMIT_TIME = 61

class CoordinatorEntry:
  def __init__(self) -> None:
    self.m_Type = TYPE_INVALID
    self.m_Time = 0
    self.m_Count = 0

class Coordinator:
  def __init__(self, lock : multiprocessing.Lock, request_list : list[CoordinatorEntry]) -> None:
    self.m_Lock : multiprocessing.Lock = lock
    self.m_RequestList : list[CoordinatorEntry] = request_list

  def WaitForMarketRequest(self, count : int):
    with self.m_Lock:
      count_last_minute = 0
      curr_time = int(time.time())

      # Detect if we're gonna go over the limit
      last_relevent_entry_index = 0
      for i, entry in enumerate(reversed(self.m_RequestList)):
        diff = curr_time - entry.m_Time
        if diff > MARKET_REQUEST_LIMIT_TIME:
          break
        if entry.m_Type != TYPE_MARKET:
          continue
        count_last_minute = count_last_minute + entry.m_Count 
        last_relevent_entry_index = len(self.m_RequestList) - 1 - i

      # Handle if we're gonna go over
      new_count = count_last_minute + count
      if new_count > MARKET_REQUEST_LIMIT:
        wait_time = 0
        for i in range(last_relevent_entry_index, len(self.m_RequestList)):
          entry = self.m_RequestList[i]
          if entry.m_Type != TYPE_MARKET:
            continue
          new_count -= entry.m_Count
          if new_count < MARKET_REQUEST_LIMIT:
            wait_time =  MARKET_REQUEST_LIMIT_TIME - (curr_time - entry.m_Time) + 1
            CSELogging.Log(f'{TYPE_MARKET} request limit reached, sleeping for {wait_time} seconds.', __file__)
            time.sleep(wait_time)
            break

      # Do some pruning
      self.m_RequestList = self.m_RequestList[last_relevent_entry_index:]

      # Add the new element
      new_entry = CoordinatorEntry()
      new_entry.m_Count = count
      new_entry.m_Time = int(time.time())
      new_entry.m_Type = TYPE_MARKET
      self.m_RequestList.append(new_entry)

        

        

      
        
      

    
