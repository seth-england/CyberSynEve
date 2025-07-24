import './App.css'
import React from 'react'
import * as CSEAppCommon from './CSEAppCommon'
import Welcome from './CSEAppWelcome'
import {CSEAppContext} from './CSEAppContext'
import CSEAppPanels from './CSEAppPanels'
import CSEAppClientSettingsUpdater from './CSEAppClientSettingsUpdater'
import CSEAppPinger from './CSEAppPinger'
import CSEAppTabList from './CSEAppTabList'

function App() 
{
  const app_state = CSEAppContext((state) => state.m_AppState)
  const set_primary_tab_list = CSEAppContext((state) => state.m_SetPrimaryTabList)
  const set_secondary_tab_list = CSEAppContext((state) => state.m_SetSecondaryTabList)

  let content =
  (
    <></>
  )
  if (app_state === CSEAppCommon.CSE_STATE_WELCOME)
  {
    content = (<Welcome/>)
  }
  else if (app_state === CSEAppCommon.CSE_STATE_MAIN)
  {
    content = (<CSEAppPanels/>)
  }

  function CreateTabLists()
  {
    const primary_tab_list = (<CSEAppTabList m_ID={CSEAppCommon.TAB_LIST_PRIMARY}/>)
    const secondary_tab_list = (<CSEAppTabList m_ID={CSEAppCommon.TAB_LIST_SECONDARY}/>)
    set_primary_tab_list(primary_tab_list)
    set_secondary_tab_list(secondary_tab_list)
  }

  React.useEffect(() => {CreateTabLists()}, [])

  return (
    <>
      <CSEAppPinger/>
      <CSEAppClientSettingsUpdater/>
      {content}
    </>
  )
}

export default App
