# Helps go through the model update queue and apply updates
import queue
import CSEMapModel
import CSEClientModel
import CSEMessages
import CSECommon
import CSEFileSystem
import CSEMarketModel

def ApplyAllUpdates(q : queue.Queue, market_model : CSEMarketModel.MarketModel, client_model : CSEClientModel.ClientModel, map_model : CSEMapModel.MapModel) -> None:
  while q.empty() is False:
    msg = q.get_nowait()
    if type(msg) == CSEMessages.CSEMessageScrapeRegionOrdersResult:
      if market_model:
        market_model.HandleScrapeRegionOrdersResult(msg.m_MarketRegionData)
    elif type(msg) == CSEMessages.UpdateClientResponse:
      if client_model:
        client_model.HandleUpdateClientResponse(msg)      
    elif type(msg) == CSEMessages.NewRouteFound:
      if map_model:
        if msg:
          map_model.HandleNewRouteFound(msg)
    elif type(msg) == CSEMessages.CSEMessageNewClientAuth:
      if client_model:
        client_model.OnNewClientAuth(msg)