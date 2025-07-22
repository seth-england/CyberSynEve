import * as CSEAppCommon from './CSEAppCommon'
import React from 'react'
import { CSEAppContext } from './CSEAppContext'
import { BuildURL } from './CSEAppBuildURL'
import { CreateCSEAppClientSettings } from './CSEAppClientSettings'

function CSEAppClientSettingsUpdater()
{
  const client_settings = CSEAppContext((state) => state.m_ClientSettings)
  const session_uuid = CSEAppContext((state) => state.m_SessionUUID)
  const client_id = CSEAppContext((state) => state.m_ClientID)
  const set_client_settings = CSEAppContext((state) => state.m_SetClientSettings)  
  const connected_to_server = CSEAppContext((state) => state.m_ConnectedToServer)

  async function Update()
  {
    if (!connected_to_server || !client_id)
    {
      return
    }

    let url = BuildURL(CSEAppCommon.SERVER_CLIENT_SETTINGS_URL, {m_SessionUUID: session_uuid, m_ClientID: client_id})
    try
    {
      const client_settings_json_string = JSON.stringify(client_settings)
      const params =
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: client_settings_json_string
      }
      const res = await fetch(url, params)
      if (!res.ok)
      {
        console.log("Client settings failed to send.")
      }
    }
    catch (err)
    {
      if (err instanceof Error)
      {
        console.log(err)
      }      
    }
  }

  async function GetSettings()
  {
    if (!connected_to_server || !client_id)
    {
      return
    }
 
    let url = BuildURL(CSEAppCommon.SERVER_CLIENT_SETTINGS_URL, {m_SessionUUID: session_uuid, m_ClientID: client_id})
    try
    {
      const res = await fetch(url)
      if (res.ok)
      {
        let res_json = await res.json()
        if (res_json)
        {
          let new_settings = CreateCSEAppClientSettings(res_json)
          set_client_settings(new_settings)
        }
      }
    }
    catch(err)
    {
      if (err instanceof Error)
      {
        console.log(err)
      }
    } 
  }

  React.useEffect(() => {Update()}, [client_settings, connected_to_server])
  React.useEffect(() => {GetSettings()}, [session_uuid, client_id, connected_to_server])

  return <></>
}

export default CSEAppClientSettingsUpdater