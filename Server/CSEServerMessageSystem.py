# Handles passing messages via queues that can be read by all listeners

import queue
import threading

class ModelUpdateQueueEntry:
  def __init__(self, id : int, q : queue.Queue) -> None:
    self.m_Id = id
    self.m_Queue = q

class MessageSystem:
  def __init__(self) -> None:
    self.m_ModelUpdateQueues = list[ModelUpdateQueueEntry]()
    self.m_Lock = threading.Lock()
    pass

  def RegisterForModelUpdateQueue(self, id : int, q : queue.Queue):
    with self.m_Lock:
      new_entry = ModelUpdateQueueEntry(id, q)
      self.m_ModelUpdateQueues.append(new_entry)

  def QueueModelUpdateMessage(self, msg):
    with self.m_Lock:
      for queue_entry in self.m_ModelUpdateQueues:
        queue_entry.m_Queue.put_nowait(msg)

g_MessageSystem = MessageSystem()
    