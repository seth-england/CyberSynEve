import './App.css'
import './CSEAppCommon'
import React from 'react'
import * as CSEAppCommon from './CSEAppCommon'
import Welcome from './Welcome'
import './CSEAppPanels'
import { cse_app_default_context, CSEAppContext } from './CSEAppContext'
import CSEAppPanels from './CSEAppPanels'

class CSEReactApp
{
  m_State : any = null
  m_SetState : any = null
  m_ConnectedToServer : any = null
  m_SetConnectedToServer : any = null
  m_ClientSettings : any = null
}
var cse_app_context = new CSEAppContext()

async function PingServer()
{
  try
  {
    let json = 
    {
      m_UUID : "",
      
    }
    await fetch(CSEAppCommon.CSE_PING_URL)
  }
  catch (err)
  {
  }
}

function App() 
{
  const [count, setCount] = React.useState(0)
  let [app_state, SetAppState] = React.useState(CSEAppCommon.CSE_STATE_INIT)
  let [connected_to_server, SetConnectedToServer] = React.useState(false)
  let [uuid, SetUUID] = React.useState("")
  async function MainLoop()
  {
    if (app_state == CSEAppCommon.CSE_STATE_INIT)
    {
      // Try to open the client file, create one if we fail
      const client_file = await fetch('./client.cse')
      let client = null
      let client_file_success = false
      if (client_file.ok)
      {
        client = await client_file.json()
        if (client)
        {
          uuid = client.m_UUID
          client_file_success = true
        }
      }
      if (!client_file_success)
      {
        const generated_uuid = crypto.randomUUID();
        SetUUID(generated_uuid)
        const client_json =
        {
          m_UUID : generated_uuid,
        }
        
      }
    }

    
  }
  React.useEffect(() => {MainLoop()}, [] )

  return (
    <cse_app_default_context.Provider value={cse_app_context}>
      <CSEAppPanels />
    </cse_app_default_context.Provider>
  )
}

export default App
