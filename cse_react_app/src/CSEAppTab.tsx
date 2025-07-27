import React from 'react'
import * as CSEAppCommon from './CSEAppCommon'
import type { CSEAppTabRequest } from './CSEAppTabRequest'

export interface CSEAppTab
{
  m_Name: string,
  m_ID: string,
  m_Element: React.JSX.Element
  m_DOMElement: React.RefObject<HTMLDivElement | null>
  m_Request: CSEAppTabRequest // The request that created this tab
}
