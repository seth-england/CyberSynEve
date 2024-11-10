import CSECommon
import CSEHTTP

def PrintTrades(trades : list[CSEHTTP.ProfitableTrade]):
    for i, trade in enumerate(trades):
      print(f'{i: 3}.) {trade.m_ItemCount: 4} {trade.m_StartAveragePrice/1000000: 7.3f}m {trade.m_ItemName} ROP: {trade.m_RateOfProfit * 100:.1f}% Profit: {trade.m_Profit/1000000:.1f}m') 