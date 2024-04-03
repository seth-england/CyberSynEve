import CSEClientModel
import CSEHTTP
import CSEItemModel

def Query(character_transactions : list[CSEClientModel.CSECharacterTransaction], item_model : CSEItemModel.ItemModel) -> CSEHTTP.CSEMarketBalanceQueryResult:
  result = CSEHTTP.CSEMarketBalanceQueryResult()
  result.m_Valid = True
  excluded_item_names = {'PLEX', 'Large Skill Injector'}
  profit = 0
  loss = 0

  for character_transaction in character_transactions:
    item_data = item_model.GetItemDataFromID(character_transaction.m_TypeId)
    if item_data is None:
      continue
    excluded = item_data.m_Name in excluded_item_names
    if excluded:
      continue
    if character_transaction.m_Buy:
      loss += character_transaction.m_TotalPrice
    else:
      profit += character_transaction.m_TotalPrice
  result.m_Balance = profit - loss
  return result

