import CSEServerAllModels
import queue
import CSEServerMessageSystem
import CSECommon
import time
import asyncio
import aiohttp
import CSEServerModelUpdateHelper
import os
import multiprocessing
import CSEServerRequestCoordinator
import sqlite3

class Worker:
  def __init__(self) -> None:
    self.m_AllModels = CSEServerAllModels.Models()
    self.m_FuncQueue : multiprocessing.Queue = None
    self.m_ArgsQueue : multiprocessing.Queue = None
    self.m_RetQueue : multiprocessing.Queue = None
    self.m_Process : multiprocessing.Process = None
    self.m_MsgSystem : CSEServerMessageSystem.MessageSystem = None
    self.m_ModelUpdateQueue = multiprocessing.Queue()
    self.m_Condition = multiprocessing.Condition()
    self.m_Connector : aiohttp.TCPConnector = None
    self.m_ClientSession : aiohttp.ClientSession = None
    self.m_Coordinator : CSEServerRequestCoordinator.Coordinator = None

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
    
  def WorkerMain(self, msg_system, func_q, args_q, model_q, condition, coordinator, ret_q):
    try:
      self.m_MsgSystem = msg_system
      self.m_FuncQueue = func_q
      self.m_ArgsQueue = args_q
      self.m_RetQueue = ret_q
      self.m_ModelUpdateQueue = model_q
      self.m_Condition = condition
      self.m_Coordinator = coordinator
      self.m_Condition.acquire()
      self.m_AllModels.CreateAllModels()
      self.m_MsgSystem.RegisterForModelUpdateQueue(os.getpid(), self.m_ModelUpdateQueue)
      self.WorkerMainLoop()
    except Exception as e:
      raise e
  
  def WorkerMainAsync(self, msg_system, func_q, args_q, model_q, condition, coordinator, ret_q):
    try:
      self.m_MsgSystem = msg_system
      self.m_FuncQueue = func_q
      self.m_ArgsQueue = args_q
      self.m_RetQueue = ret_q
      self.m_ModelUpdateQueue = model_q
      self.m_Condition = condition
      self.m_Coordinator = coordinator
      self.m_Condition.acquire()
      self.m_AllModels.CreateAllModels()
      self.m_MsgSystem.RegisterForModelUpdateQueue(os.getpid(), self.m_ModelUpdateQueue)
      asyncio.run(self.WorkerMainAsyncLoop())
    except Exception as e:
      raise e

  def WorkerMainLoop(self):
    while True:
      while not self.m_FuncQueue.empty():
        CSEServerModelUpdateHelper.ApplyAllUpdates(self.m_ModelUpdateQueue, self.m_AllModels.m_MarketModel, self.m_AllModels.m_ClientModel, self.m_AllModels.m_MapModel, self.m_AllModels.m_CharacterModel)
        func = self.m_FuncQueue.get_nowait()
        if func:
          args = None
          if not self.m_ArgsQueue.empty():
            args = self.m_ArgsQueue.get_nowait()
          if args:
            func(self, *args)
          else:
            func(self)
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
          args = None
          if not self.m_ArgsQueue.empty():
            args = self.m_ArgsQueue.get_nowait()
          if args:
            await func(self, *args)
          else:
            await func(self)
      self.m_Condition.wait()
      self.m_Condition.acquire()
      
    