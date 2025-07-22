import * as CSEAppCommon from './CSEAppCommon'
import React from 'react'
import { BuildURL } from './CSEAppBuildURL'
import { CSEAppContext } from './CSEAppContext'
import type { PingResponse } from './CSEAppHTTP'

function CSEAppPinger()
{
  const session_uuid = CSEAppContext((state) => state.m_SessionUUID)
  const set_ping_error_message = CSEAppContext((state) => state.m_SetPingErrorMessage)
  const set_has_ping_error_message = CSEAppContext((state) => state.m_SetHasPingErrorMessage)
  const set_connected_to_server = CSEAppContext((state) => state.m_SetConnectedToServer)
  const set_client_id = CSEAppContext((state) => state.m_SetClientId)
  const request_ping = CSEAppContext((state) => state.m_RequestPing)
  const set_request_ping = CSEAppContext((state) => state.m_SetRequestPing)
  const set_character_count = CSEAppContext((state) => state.m_SetCharacterCount)

  async function PingServer() 
  {
    let url = BuildURL(CSEAppCommon.CSE_PING_URL, {m_SessionUUID: session_uuid})
    try
    {
      const res = await fetch(url)
      if (!res.ok)
      {
        throw Error(`HTTP error ${res.status}`)
      }
      
      set_has_ping_error_message(false)
      set_connected_to_server(true)
      try
      {
        let ping_res: PingResponse = await res.json()
        if (ping_res)
        {
          if (ping_res.m_ClientId)
          {
            set_client_id(ping_res.m_ClientId)
            set_character_count(ping_res.m_CharacterCount)
          }
        } 
      }
      catch(err)
      {
        console.log("PingResponse invalid")
        if (err instanceof Error)
        {
          console.log(`${err.message}`)
        }
      }
    }
    catch(err)
    {
      if (err instanceof Error)
      {
        set_ping_error_message(`HTTP Error ${err.message}`)
        set_has_ping_error_message(true)
        set_connected_to_server(false)
        return
      }
    }
  }

  async function SetupPing()
  {
    setInterval(PingServer, 1000)
  }

  async function PingFromRequest()
  {
    if (!request_ping)
    {
      return
    }

    try
    {
      PingServer()
      set_request_ping(false)
    }
    catch(err)
    {

    }
  }
  
  React.useEffect(() => {SetupPing()}, [] )
  React.useEffect(() => {PingFromRequest()}, [request_ping] )

  return (
    <></>
  )
}

export default CSEAppPinger