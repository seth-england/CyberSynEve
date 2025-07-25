import React from 'react'
import type { Point } from './CSEAppMath'
import type { CSEAppTab } from './CSEAppTab'

export interface CSEDragAndDropState
{
  m_DropTargetListID: string | null,
  m_DropTabID: string | null,
  m_Element: CSEAppTab | null,
  m_Position: Point,
  m_IsHovering: boolean,
  m_IsDropped: boolean,
}

export function CreateDragAndDropState(): CSEDragAndDropState
{
  return {
    m_DropTargetListID: null,
    m_DropTabID: null,
    m_Element: null,
    m_Position: {m_X: 0, m_Y: 0},
    m_IsHovering: false,
    m_IsDropped: false,
  }
}