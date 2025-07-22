import './App.css'
import * as CSEAppCommon from './CSEAppCommon'
import Welcome from './CSEAppWelcome'
import {CSEAppContext} from './CSEAppContext'
import CSEAppPanels from './CSEAppPanels'
import CSEAppClientSettingsUpdater from './CSEAppClientSettingsUpdater'
import CSEAppPinger from './CSEAppPinger'

function App() 
{
  const app_state = CSEAppContext((state) => state.m_AppState)

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

  return (
    <>
      <CSEAppPinger/>
      <CSEAppClientSettingsUpdater/>
      {content}
    </>
  )
}

export default App
