import './CSEAppCommon'
import React from 'react'
import { CSEAppContext } from './CSEAppContext'
import { CreateCSEAppClientSettings } from './CSEAppClientSettings'

export function CSEAppPanels()
{
  const client_settings = CSEAppContext((state) => state.m_ClientSettings)
  const set_client_settings = CSEAppContext((state) => state.m_SetClientSettings)
  const [panel_sizes_vert, SetPanelSizesVert] = React.useState([5, 90, 5])
  const [panel_sizes_horz, SetPanelSizesHorz] = React.useState([33, 33, 34])
  const panel_sizes_vert_ref = React.useRef(panel_sizes_vert)
  const panel_sizes_horz_ref = React.useRef(panel_sizes_horz)
  const container_ref = React.useRef(null)
  const [is_dragging, set_is_dragging] = React.useState(false)
  const drag_start = React.useRef(0)
  const drag_horz = React.useRef(false)
  const drag_index = React.useRef(0)
  const last_delta = React.useRef(0)

  function HandleMouseMove(e: any)
  {
    if (!container_ref.current || drag_start.current === null)
    {
      return
    }

    let new_panel_sizes_horz = [...panel_sizes_horz]
    if (drag_horz)
    {
      const container_width = container_ref.current.offsetWidth
      const delta_x = e.clientX - drag_start.current
      let delta_pct = (delta_x / container_width) * 100
      if (drag_index.current === 0)
      {
        // Clip our delta_pct if it's taking us beyond min or max
        let naive_0 = panel_sizes_horz[0] + delta_pct
        let naive_1 = panel_sizes_horz[1] - delta_pct
        let actual_0 = Math.max(10, Math.min(80, panel_sizes_horz[0] + delta_pct))
        let actual_1 = Math.max(10, Math.min(80, panel_sizes_horz[1] - delta_pct))
        let diff_0 = actual_0 - naive_0
        let diff_1 = actual_1 - naive_1
        let diff_abs = Math.max(Math.abs(diff_0), Math.abs(diff_1))
        if (diff_abs > 0)
        {
          delta_pct = last_delta.current
        } 

        new_panel_sizes_horz[0] = Math.max(10, Math.min(80, panel_sizes_horz[0] + delta_pct))
        new_panel_sizes_horz[1] = Math.max(10, Math.min(80, panel_sizes_horz[1] - delta_pct))
        new_panel_sizes_horz[2] = 100 - new_panel_sizes_horz[0] - new_panel_sizes_horz[1]
        last_delta.current = delta_pct
      }
      else
      {
        // Clip our delta_pct if it's taking us beyond min or max
        let naive_1 = panel_sizes_horz[1] + delta_pct
        let naive_2 = panel_sizes_horz[2] - delta_pct
        let actual_1 = Math.max(10, Math.min(80, panel_sizes_horz[1] + delta_pct))
        let actual_2 = Math.max(10, Math.min(80, panel_sizes_horz[2] - delta_pct))
        let diff_1 = actual_1 - naive_1
        let diff_2 = actual_2 - naive_2
        let diff_abs = Math.max(Math.abs(diff_1), Math.abs(diff_2))
        if (diff_abs > 0)
        {
          delta_pct = last_delta.current
        } 
        
        new_panel_sizes_horz[1] = Math.max(10, Math.min(80, panel_sizes_horz[1] + delta_pct))
        new_panel_sizes_horz[2] = Math.max(10, Math.min(80, panel_sizes_horz[2] - delta_pct))
        new_panel_sizes_horz[0] = 100 - new_panel_sizes_horz[1] - new_panel_sizes_horz[2]
        last_delta.current = delta_pct
      }
    }

    SetPanelSizesHorz(new_panel_sizes_horz)
    panel_sizes_horz_ref.current = new_panel_sizes_horz
  }

  function HandleMouseUp()
  {
    set_is_dragging(false)
    last_delta.current = 0
    document.removeEventListener('mousemove', HandleMouseMove);
    document.removeEventListener('mouseup', HandleMouseUp);
    let new_client_settings = CreateCSEAppClientSettings(client_settings)
    new_client_settings.m_PanelsVertSize = panel_sizes_vert_ref.current as typeof new_client_settings.m_PanelsVertSize
    new_client_settings.m_PanelsHorzSize = panel_sizes_horz_ref.current as typeof new_client_settings.m_PanelsHorzSize
    set_client_settings(new_client_settings)
  }

  function OnMouseDownHorz(e: any, index: number)
  {
    set_is_dragging(true)
    drag_horz.current = true
    drag_start.current = e.clientX
    drag_index.current = index
    document.addEventListener('mousemove', HandleMouseMove);
    document.addEventListener('mouseup', HandleMouseUp)
  }

  function HandleSettingsChanged()
  {
    SetPanelSizesHorz(client_settings.m_PanelsHorzSize)
    SetPanelSizesVert(client_settings.m_PanelsVertSize)
    panel_sizes_horz_ref.current = client_settings.m_PanelsHorzSize
    panel_sizes_vert_ref.current = client_settings.m_PanelsVertSize
  }
  React.useEffect(() => {HandleSettingsChanged()}, [client_settings])

  return (
    <div className='w-screen h-screen bg-primary_bg'>
      <div className='flex h-1/12 w-screen' style={{height: `${panel_sizes_vert[0]}%`}}>
        Header
      </div>
      <div className='h-1 bg-primary_accent'></div>
      <div className='flex w-screen' ref={container_ref} style={{height: `${panel_sizes_vert[1]}%`}}>
        <h1 className='flex items-center justify-center text-primary_text' style={{width: `${panel_sizes_horz[0]}%`}}>
          Column 1
        </h1>
        <div className='w-1 bg-primary_accent cursor-ew-resize' onMouseDown={(e) => OnMouseDownHorz(e, 0)}></div>
        <h1 className='flex items-center justify-center text-primary_text' style={{width: `${panel_sizes_horz[1]}%`}}>
          Column 2
        </h1>
        <div className='w-1 bg-primary_accent cursor-ew-resize' onMouseDown={(e) => OnMouseDownHorz(e, 1)}></div>
        <h1 className='flex items-center justify-center text-primary_text' style={{width: `${panel_sizes_horz[2]}%`}}>
          Column 3
        </h1>
      </div>
      <div className='h-1 bg-primary_accent'></div>
      <div className='flex h-1/12 w-screen' style={{height: `${panel_sizes_vert[2]}%`}}>
        Footer
      </div>
    </div>
  )
}

export default CSEAppPanels