import CSEServerAllModels
import queue
import threading
import CSEServerMessageSystem
import CSECommon
import time
import asyncio
import aiohttp
import CSEServerModelUpdateHelper
import os
import multiprocessing

class Worker:
  def __init__(self) -> None:
    self.m_AllModels = CSEServerAllModels.Models()
    self.m_FuncQueue : queue.Queue = None
    self.m_ArgsQueue : queue.Queue = None
    self.m_Thread : threading.Thread = None
    self.m_MsgSystem : CSEServerMessageSystem.MessageSystem = None
    self.m_ModelUpdateQueue = queue.Queue()
    self.m_Condition : threading.Condition = None
    self.m_Connector : aiohttp.TCPConnector = None
    self.m_ClientSession : aiohttp.ClientSession = None

  def Wake(self):
    if self.m_Condition.acquire(False):
      self.m_Condition.notify()
      self.m_Condition.release()

  def IsSleeping(self):
    if self.m_Condition.acquire(False):
      self.m_Condition.release()
      return True
    else:
      return False
    
  def WorkerMain(self):
    try:
      self.m_Condition = threading.Condition()
      self.m_Condition.acquire()
      self.m_AllModels.CreateAllModels()
      self.m_MsgSystem.RegisterForModelUpdateQueue(threading.get_ident(), self.m_ModelUpdateQueue)
      self.WorkerMainLoop()
    finally:
      os._exit(1)
  
  def WorkerMainAsync(self):
    try:
      self.m_Condition = threading.Condition()
      self.m_Condition.acquire()
      self.m_AllModels.CreateAllModels()
      self.m_MsgSystem.RegisterForModelUpdateQueue(threading.get_ident(), self.m_ModelUpdateQueue)
      asyncio.run(self.WorkerMainAsyncLoop())
    finally:
      os._exit(1)

  def WorkerMainLoop(self):
    while True:
      while not self.m_FuncQueue.empty():
        CSEServerModelUpdateHelper.ApplyAllUpdates(self.m_ModelUpdateQueue, self.m_AllModels.m_MarketModel, self.m_AllModels.m_ClientModel, self.m_AllModels.m_MapModel, self.m_AllModels.m_CharacterModel)
        func = self.m_FuncQueue.get_nowait()
        if func:
          args = self.m_ArgsQueue.get_nowait()
          func(*args)
      self.m_Condition.wait()
      self.m_Condition.acquire()

  async def WorkerMainAsyncLoop(self):
    self.m_Connector = aiohttp.TCPConnector(limit=50)
    self.m_ClientSession = aiohttp.ClientSession(connector=self.m_Connector)
    while True:
      self.m_Condition.acquire()
      while not self.m_FuncQueue.empty():
        CSEServerModelUpdateHelper.ApplyAllUpdates(self.m_ModelUpdateQueue, self.m_AllModels.m_MarketModel, self.m_AllModels.m_ClientModel, self.m_AllModels.m_MapModel, self.m_AllModels.m_CharacterModel)
        func = self.m_FuncQueue.get_nowait()
        if func:
          args = self.m_ArgsQueue.get_nowait()
          await func(*args)
      self.m_Condition.wait()
      self.m_Condition.acquire()
      
    