import * as CSEAppCommon from './CSEAppCommon'
import React from 'react'
import { CSEAppContext } from './CSEAppContext'
import type {CSEAppTab} from './CSEAppTab'
import type { CSEAppTabRequest } from './CSEAppTabRequest'
import CSEAppOpportunityView from './CSEAppOpportunityView'
import { BoundingBoxFromDomRect, CalculateIntersectionArea, PointInBoundingBox, type BoundingBox, type Point } from './CSEAppMath'
import { CreateDragAndDropState, type CSEDragAndDropState } from './CSEDropRequest'
import { CreateOpportunityViewPrius, CreateTab } from './CSEAppTabFactory'

interface CSEAppTabListInput
{
  m_ID: string,
}

function CSEAppTabList(props: CSEAppTabListInput)
{
  const [tab_list, set_tab_list] = React.useState(new Array<CSEAppTab>())
  const tab_requests = CSEAppContext((state) => state.m_TabRequests)
  const set_tab_requests = CSEAppContext((state) => state.m_SetTabRequests)
  const serialized_tab_requests = CSEAppContext((state) => state.m_SerializedTabRequests)
  const set_serialized_tab_requests = CSEAppContext((state) => state.m_SetSerializedTabRequests)
  const serialized_tab_requests_ref = React.useRef<Array<CSEAppTabRequest>>(serialized_tab_requests)
  const drag_tab_id = React.useRef<string | null>(null)
  const drag_tab = React.useRef<CSEAppTab | null>(null)
  const drag_ghost = React.useRef<HTMLDivElement | null>(null)
  const drag_offset = React.useRef({ x: 0, y: 0 })
  const drag_and_drop_state = CSEAppContext((state) => state.m_DragAndDropState)
  const set_drag_and_drop_state = CSEAppContext((state) => state.m_SetDragAndDropState)
  const drag_and_drop_state_ref = React.useRef<CSEDragAndDropState>(drag_and_drop_state)
  const self_ref = React.useRef<HTMLDivElement | null>(null)
  
  function UpdateGlobalTabRequestsRef()
  {
    serialized_tab_requests_ref.current = serialized_tab_requests
  }
  React.useEffect(() => {UpdateGlobalTabRequestsRef()}, [serialized_tab_requests])

  function UpdateGlobalTabRequests(new_tab_list: CSEAppTab[])
  {
    // First remove all tab requests for this tab list
    let new_serialized_tab_requests = serialized_tab_requests_ref.current.filter((request) => request.m_TargetListID !== props.m_ID)

    for (const tab of new_tab_list)
    {
      new_serialized_tab_requests.push(tab.m_Request)
    }

    set_serialized_tab_requests(new_serialized_tab_requests)
  }

  function HandleTabRequest()
  {
    for (const tab_request of tab_requests)
    {
      if (tab_request.m_TargetListID === props.m_ID)
      {
        // Check that the tab request is not already in the tab list
        const existing_tab = tab_list.find((tab) => tab.m_Name === tab_request.m_Name)
        if (existing_tab)
        {
          // Remove the tab request from the tab requests array
          const new_tab_requests = tab_requests.filter((request) => request.m_Name !== tab_request.m_Name)
          set_tab_requests(new_tab_requests)
          return
        }

        const new_tab = CreateTab(tab_request)
        if (!new_tab)
        {
          const new_tab_requests = tab_requests.filter((elm) => elm.m_ID !== tab_request.m_ID)
          set_tab_requests(new_tab_requests)
          continue
        }

        var new_tab_list = [...tab_list, new_tab]
        set_tab_list(new_tab_list)
        UpdateGlobalTabRequests(new_tab_list)
      }
    }
  }

  React.useEffect(() => {HandleTabRequest()}, [tab_requests])

  function HandleTabClose(tab_id: string)
  {
    const new_tab_list = tab_list.filter((tab) => tab.m_ID !== tab_id)
    set_tab_list(new_tab_list)
    UpdateGlobalTabRequests(new_tab_list)

    const new_drag_and_drop_state: CSEDragAndDropState = CreateDragAndDropState()
    set_drag_and_drop_state(new_drag_and_drop_state)
    drag_and_drop_state_ref.current = new_drag_and_drop_state
  }

  function GetTabListInBounds(bounds: BoundingBox): HTMLDivElement | null
  {
    let best_tab_list: HTMLDivElement | null = null
    let best_intersection_area = 0

    const tab_lists = document.getElementsByClassName('CSEAppTabList')
    for (const tab_list of tab_lists)
    {
      const tab_list_element = tab_list as HTMLDivElement
      const tab_list_bounds = BoundingBoxFromDomRect(tab_list_element.getBoundingClientRect())
      const intersection_area = CalculateIntersectionArea(tab_list_bounds, bounds)
      if (intersection_area > 0 && intersection_area > best_intersection_area)
      {
        best_intersection_area = intersection_area
        best_tab_list = tab_list_element
      }
    }

    return best_tab_list
  }

  function HandleTabDrag(e: MouseEvent)
  {
    if (!drag_ghost.current)
    {
      return
    }

    const new_x = e.clientX - drag_offset.current.x
    const new_y = e.clientY - drag_offset.current.y

    const current_x = parseFloat(drag_ghost.current.style.left)
    const current_y = parseFloat(drag_ghost.current.style.top)

    const diff_x = new_x - current_x
    const diff_y = new_y - current_y

    drag_ghost.current.style.transform = `translate3d(${diff_x}px, ${diff_y}px, 0)`
    drag_ghost.current.style.transition = 'none'
    
    // Get the bounding box of the drag ghost
    const drag_ghost_bounds = BoundingBoxFromDomRect(drag_ghost.current.getBoundingClientRect())

    // Get the tab list at the mouse position
    const tab_list = GetTabListInBounds(drag_ghost_bounds)
    if (tab_list)
    {
      let new_drag_and_drop_state: CSEDragAndDropState =
      {
        ...drag_and_drop_state_ref.current,
        m_DropTargetListID: tab_list.id,
        m_Position: {m_X: e.clientX, m_Y: e.clientY},
        m_IsHovering: true,
        m_IsDropped: false,
      }
      set_drag_and_drop_state(new_drag_and_drop_state)
      drag_and_drop_state_ref.current = new_drag_and_drop_state
    }
    else
    {
      const new_drag_and_drop_state: CSEDragAndDropState =
      {
        ...drag_and_drop_state_ref.current,
        m_DropTargetListID: null,
      }
      set_drag_and_drop_state(new_drag_and_drop_state)
      drag_and_drop_state_ref.current = new_drag_and_drop_state
    }
  }

  function HandleTabDrop(e: MouseEvent)
  {
    const cleanup = () =>
    {
      drag_tab_id.current = null
      drag_tab.current = null
      document.removeEventListener('mousemove', HandleTabDrag)
      document.removeEventListener('mouseup', HandleTabDrop)
  
      // Remove ghost element
      if (drag_ghost.current && drag_ghost.current.parentNode)
      {
        drag_ghost.current.parentNode.removeChild(drag_ghost.current)
        drag_ghost.current = null
      }      
    }

    if (!drag_ghost.current)
    {
      cleanup()
      return
    }

    if (!drag_and_drop_state_ref.current.m_IsHovering)
    {
      cleanup()
      return
    }

    const identify_drop_target_result = IdentifyDropTarget(e.clientX, tab_list)

    const drag_ghost_bounds = BoundingBoxFromDomRect(drag_ghost.current.getBoundingClientRect())

    // Check if the tab is over a tab list
    const tab_lists = document.getElementsByClassName('CSEAppTabList')
    let best_tab_list: HTMLDivElement | null = null
    let best_tab_list_area = 0

    for (const tab_list_elm of tab_lists)
    {
      const tab_list_element = tab_list_elm as HTMLDivElement
      if (!tab_list_element)
      {
        continue
      }

      const tab_list_area = CalculateIntersectionArea(BoundingBoxFromDomRect(tab_list_element.getBoundingClientRect()), drag_ghost_bounds)
      if (tab_list_area > 0 && tab_list_area > best_tab_list_area)
      {
        best_tab_list_area = tab_list_area
        best_tab_list = tab_list_element
      }
    }

    let new_drag_and_drop_state: CSEDragAndDropState =
    {
      ...drag_and_drop_state_ref.current,
      m_DropTargetListID: best_tab_list ? best_tab_list.id : null,
      m_Position: {m_X: e.clientX, m_Y: e.clientY},
      m_IsHovering: false,
      m_IsDropped: true,
    }

    const dragging_into_same_list = best_tab_list === self_ref.current
    const dragging_into_self = dragging_into_same_list && identify_drop_target_result.m_BestTabID === drag_tab_id.current
    if (best_tab_list && !dragging_into_self)
    {
      if (dragging_into_same_list)
      {
        const [insert_index, new_tab_list_local] = HandleDropRequestLocal(new_drag_and_drop_state)
        if (insert_index !== -1)
        {
          const new_tab_list = new_tab_list_local.filter((tab, index) => (tab.m_ID !== drag_tab_id.current || insert_index === index))
          set_tab_list(new_tab_list)
          UpdateGlobalTabRequests(new_tab_list)
        }
        new_drag_and_drop_state.m_DropTargetListID = null
        new_drag_and_drop_state.m_IsDropped = false  
        set_drag_and_drop_state(new_drag_and_drop_state)     
        drag_and_drop_state_ref.current = new_drag_and_drop_state
      }
      else
      {
        const new_tab_list = tab_list.filter((tab) => tab.m_ID !== drag_tab_id.current)
        set_tab_list(new_tab_list)
        UpdateGlobalTabRequests(new_tab_list)
        set_drag_and_drop_state(new_drag_and_drop_state)
        drag_and_drop_state_ref.current = new_drag_and_drop_state
      }
    }
    else
    {
      new_drag_and_drop_state.m_DropTargetListID = null
      new_drag_and_drop_state.m_IsHovering = false
      new_drag_and_drop_state.m_IsDropped = false
      set_drag_and_drop_state(new_drag_and_drop_state)
      drag_and_drop_state_ref.current = new_drag_and_drop_state
    }

    cleanup()
  }

  function HandleTabClick(tab_id: string, e: React.MouseEvent<HTMLDivElement>)
  {
    e.preventDefault()
    
    // Get the tab element
    const tab_element = document.getElementById(tab_id)
    if (!tab_element) return

    const tab = tab_list.find((tab) => tab.m_ID === tab_id)
    if (!tab) return
    
    const rect = tab_element.getBoundingClientRect()
    
    // Store offset
    drag_offset.current = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    }
    
    // Create ghost element
    const ghost = document.createElement('div')
    ghost.innerHTML = tab_element.innerHTML
    ghost.className = tab_element.className + ' opacity-50'
    ghost.style.position = 'fixed'
    ghost.style.left = `${e.clientX - drag_offset.current.x}px`
    ghost.style.top = `${e.clientY - drag_offset.current.y}px`
    ghost.style.pointerEvents = 'none'
    ghost.style.zIndex = '1000'
    ghost.style.width = `${rect.width}px`
    ghost.style.height = `${rect.height}px`
    
    document.body.appendChild(ghost)
    drag_ghost.current = ghost
    drag_tab_id.current = tab_id
    drag_tab.current = tab

    // Set up drag and drop state
    let new_drag_and_drop_state: CSEDragAndDropState =
    {
      m_DropTargetListID: null,
      m_DropTabID: tab.m_ID,
      m_Element: tab,
      m_Position: {m_X: e.clientX, m_Y: e.clientY},
      m_IsHovering: false,
      m_IsDropped: false,
    }
    set_drag_and_drop_state(new_drag_and_drop_state)
    drag_and_drop_state_ref.current = new_drag_and_drop_state

    document.addEventListener('mousemove', HandleTabDrag)
    document.addEventListener('mouseup', HandleTabDrop)
  }

  interface IdentifyDropTargetResult
  {
    m_BestDiff: number,
    m_BestTabID: string | null,
    m_BestTab: CSEAppTab | null,
    m_BestTabLast: boolean,
  }
  function IdentifyDropTarget(x_pos: number, tab_list: CSEAppTab[]): IdentifyDropTargetResult
  {
    let result: IdentifyDropTargetResult = {m_BestDiff: Number.MAX_VALUE, m_BestTabID: null, m_BestTab: null, m_BestTabLast: false}

    for (const tab of tab_list)
    {
      const tab_element = tab.m_DOMElement.current
      if (!tab_element)
      {
        continue
      }

      const tab_element_rect = tab_element.getBoundingClientRect()
      const left = tab_element_rect.left
      const diff_abs = Math.abs(x_pos - left)
      if (diff_abs < result.m_BestDiff)
      {
        result.m_BestDiff = diff_abs
        result.m_BestTabID = tab.m_ID
        result.m_BestTab = tab
      }

      // If last element, check if the end of this tab is closer than the start
      // So we can drop it at the end
      if (tab === tab_list[tab_list.length - 1])
      {
        const right = tab_element_rect.right
        const diff_abs = Math.abs(x_pos - right)
        if (diff_abs < result.m_BestDiff)
        {
          result.m_BestDiff = diff_abs
          result.m_BestTabLast = true
        }
      }     
    }

    return result
  }

  function HandleDropRequest()
  {
    if (!drag_and_drop_state.m_IsDropped || drag_and_drop_state.m_DropTargetListID !== props.m_ID)
    {
      return
    }
  
    HandleDropRequestLocal(drag_and_drop_state)
  }
  
  React.useEffect(() => {HandleDropRequest()}, [drag_and_drop_state])

  function HandleDropRequestLocal(drop_state: CSEDragAndDropState): [number, CSEAppTab[]]
  {
    const identify_drop_target_result = IdentifyDropTarget(drop_state.m_Position.m_X, tab_list)
    if (!identify_drop_target_result)
    {
      return [-1, tab_list]
    }

    if (!drop_state.m_Element)
    {
      return [-1, tab_list]
    }

    let new_tab: CSEAppTab = drop_state.m_Element
    new_tab.m_Request.m_TargetListID = props.m_ID
    let insert_index = -1
    const index = tab_list.findIndex((tab) => tab.m_ID === identify_drop_target_result.m_BestTabID)

    let new_tab_list: CSEAppTab[] = tab_list

    if (tab_list.length === 0)
    {
      insert_index = 0
      new_tab_list = [new_tab]
    }
    else if (identify_drop_target_result.m_BestTabLast)
    {
      insert_index = tab_list.length
      new_tab_list = [...tab_list, new_tab]
    }
    else if (index === -1)
    {
      insert_index = -1
    }
    else if (index === 0)
    {
      insert_index = 0
      new_tab_list = [new_tab, ...tab_list]
    }
    else
    {
      insert_index = index
      new_tab_list = [...tab_list.slice(0, index), new_tab, ...tab_list.slice(index)]
    }
    set_tab_list(new_tab_list)
    UpdateGlobalTabRequests(new_tab_list)
    return [insert_index, new_tab_list]
  }

  const has_hovering_tab = drag_and_drop_state.m_IsHovering && drag_and_drop_state.m_DropTargetListID === props.m_ID
  const has_dropped_tab = drag_and_drop_state.m_IsDropped && drag_and_drop_state.m_DropTargetListID === props.m_ID
  let drop_target_result = IdentifyDropTarget(drag_and_drop_state.m_Position.m_X, tab_list)

  const drop_tab_jsx = <div className='w-1 h-full bg-secondary_accent'></div>

  let tab_names_jsx = tab_list.map(
    (tab) => 
    (
      <div 
        className='flex items-center justify-center bg-primary_bg border border-primary_border  shadow-sm hover:shadow-md hover:border-primary_accent transition-all duration-200 cursor-pointer group' 
        key={tab.m_ID}
        id={tab.m_ID}
        ref={tab.m_DOMElement}
        onMouseDown={(e: React.MouseEvent<HTMLDivElement>) => HandleTabClick(tab.m_ID, e)}
      >
        {(has_hovering_tab && !drop_target_result.m_BestTabLast && drop_target_result.m_BestTabID === tab.m_ID) ? drop_tab_jsx : <></>}
        <div className='text-sm px-2 font-medium text-primary_text hover:text-primary_accent transition-colors duration-200'>
          {tab.m_Name}
        </div>
        <div onMouseDown={(e: React.MouseEvent<HTMLDivElement>) => HandleTabClose(tab.m_ID)} className='flex text-center items-center justify-center text-xs h-full w-4 border border-primary_border text-primary_text hover:text-warning opacity-0 group-hover:opacity-100 transition-all duration-200'>
          x
        </div>
      </div>
    )
  )

  const tab_dividing_line_jsx = <div className='w-full bg-primary_accent h-1' />

  return (
    <div className='CSEAppTabList' id={props.m_ID} ref={self_ref}>
      <div className='flex flex-row w-full h-8'>
        {tab_names_jsx}
        {(has_hovering_tab && (drop_target_result.m_BestTabLast || tab_list.length === 0)) ? drop_tab_jsx : <></>}
      </div>
      {tab_dividing_line_jsx}
    </div>
  )
}

export default CSEAppTabList
