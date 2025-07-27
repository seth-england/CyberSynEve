import * as CSEAppCommon from "./CSEAppCommon"
import React from "react"
import type { CSEAppTab } from "./CSEAppTab"
import CSEAppOpportunityView from "./CSEAppOpportunityView"
import type { CSEAppTabRequest } from "./CSEAppTabRequest"

export interface CSEAppOpportunityViewPrius
{
  m_CharacterID: number | undefined,
}

export function CreateOpportunityViewPrius(props: Partial<CSEAppOpportunityViewPrius> = {}): CSEAppOpportunityViewPrius
{
  const defaults: CSEAppOpportunityViewPrius = 
  {
    m_CharacterID: undefined,
  }

  return {
    ...defaults,
    ...props,
  }
}

export function CreateTab(tab_request: CSEAppTabRequest): CSEAppTab | null
{
  let prius = null
  let element = null
  if (tab_request.m_Type === CSEAppCommon.TAB_TYPE_OPPORTUNITIES)
  {
    prius = tab_request.m_Prius as CSEAppOpportunityViewPrius
    element = <CSEAppOpportunityView props={prius} />
  }

  if (!prius || !element)
  {
    return null
  }

  const tab: CSEAppTab = 
  {
    m_Name: tab_request.m_Name,
    m_ID: tab_request.m_ID,
    m_Element: element,
    m_DOMElement: React.createRef<HTMLDivElement>(),
    m_Request: tab_request,
  }

  return tab
}
