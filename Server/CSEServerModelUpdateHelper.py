# Helps go through the model update queue and apply updates
import queue
import CSEMapModel
import CSEClientModel
import CSEMessages
import CSECommon
import CSEFileSystem
import CSEMarketModel

class ApplyUpdateResults:
  def __init__(self) -> None:
    self.m_AppliedAnyUpdate = False
    self.m_AppliedMarketModelUpdate = False
    self.m_AppliedClientModelUpdate = False
    self.m_AppliedMapModelUpdate = False

def ApplyAllUpdates(q : queue.Queue, market_model : CSEMarketModel.MarketModel, client_model : CSEClientModel.ClientModel, map_model : CSEMapModel.MapModel) -> ApplyUpdateResults:
  results = ApplyUpdateResults()
  
  while q.empty() is False:
    msg = q.get_nowait()
    if type(msg) == CSEMessages.CSEMessageScrapeRegionOrdersResult:
      if market_model:
        market_model.HandleScrapeRegionOrdersResult(msg.m_MarketRegionData)
        results.m_AppliedAnyUpdate = True
        results.m_AppliedMarketModelUpdate = True
    elif type(msg) == CSEClientModel.UpdateClientResponse:
      if client_model:
        client_model.HandleUpdateClientResponse(msg)
        results.m_AppliedAnyUpdate = True
        results.m_AppliedClientModelUpdate = True
    elif type(msg) == CSEMessages.NewRouteFound:
      if map_model:
        if msg:
          map_model.HandleNewRouteFound(msg)
          results.m_AppliedAnyUpdate = True
          results.m_AppliedMapModelUpdate = True
    elif type(msg) == CSEMessages.CSEMessageNewClientAuth:
      if client_model:
        client_model.OnNewClientAuth(msg)
        results.m_AppliedAnyUpdate = True
        results.m_AppliedClientModelUpdate = True
    elif type(msg) == CSEMessages.SetClientSettings:
      if client_model:
        client_model.HandleSetClientSettings(msg)
        results.m_AppliedAnyUpdate = True
        results.m_AppliedClientModelUpdate = True
    elif type(msg) == CSEMessages.UpdateCharacterOrders:
      if client_model:
        client_model.HandleUpdateCharacterOrders(msg)
        results.m_AppliedAnyUpdate = True
        results.m_AppliedClientModelUpdate = True
 
  return results