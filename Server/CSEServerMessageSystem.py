# Handles passing messages via queues that can be read by all listeners

import multiprocessing

class MessageSystem:
  def __init__(self, q_list, lock) -> None:
    self.m_ModelUpdateQueues = q_list
    self.m_Lock = lock
    pass

  def RegisterForModelUpdateQueue(self, id : int, q):
    with self.m_Lock:
      self.m_ModelUpdateQueues.append(q)

  def QueueModelUpdateMessage(self, msg):
    try:
      with self.m_Lock:
        for q in self.m_ModelUpdateQueues:
          q.put_nowait(msg)
    except:
      pass

g_MessageSystem = None
    