import * as CSEAppCommon from './CSEAppCommon'
import React from 'react'
import { CSEAppContext } from './CSEAppContext'
import * as CSEAppHTTP from './CSEAppHTTP'
import {BuildURL} from './CSEAppBuildURL'

let STATE_PING = 0
let STATE_LOGIN = 2

function Welcome()
{
  let [welcome_state, SetWelcomeState] = React.useState(STATE_PING)
  const connected_to_server = CSEAppContext((state) => state.m_ConnectedToServer)
  const has_ping_error = CSEAppContext((state) => state.m_HasPingErrorMessage)
  const ping_error_message = CSEAppContext((state) => state.m_PingErrorMessage)
  const session_uuid = CSEAppContext((state) => state.m_SessionUUID)
  //const request_ping = CSEAppContext((state) => state.m_RequestPing)
  //const set_request_ping = CSEAppContext((state) => state.m_SetRequestPing)
  const client_id = CSEAppContext((state) => state.m_ClientID)
  const set_app_state = CSEAppContext((state) => state.m_SetAppState)

  async function StatePing()
  {
    if (welcome_state != STATE_PING)
    {
      return
    }

    if (connected_to_server)
    {
      SetWelcomeState(STATE_LOGIN)
      return
    }
  }

  async function StateLogin()
  {
    if (welcome_state != STATE_LOGIN)
    {
      return
    }

    if (!connected_to_server)
    {
      SetWelcomeState(STATE_PING)
      return
    }

    if (!client_id)
    {
      return
    } 
    
    set_app_state(CSEAppCommon.CSE_STATE_MAIN)
  }

  function HandleLoginClick(e: any)
  {
    let url = BuildURL("https://login.eveonline.com/v2/oauth/authorize/", {response_type: "code", redirect_uri: CSEAppCommon.SERVER_AUTH_URL, client_id: CSEAppCommon.CLIENT_ID, scope: CSEAppCommon.SCOPES, state: session_uuid})
    window.open(url, '_blank', 'width=600,height=600,noopener,noreferrer')
  }

  React.useEffect(() => {StatePing();}, [welcome_state, connected_to_server, has_ping_error] )
  React.useEffect(() => {StateLogin();},[welcome_state, connected_to_server, client_id] )

  const [isVisible, setIsVisible] = React.useState(false);
  React.useEffect(() => { setIsVisible(true); }, []);

  let has_error = !connected_to_server && has_ping_error

  let loading_bounce = 
  (
    <div>
      <p className="text-lg md:text-xl text-primary_text mb-6">
        {has_error ? "Trying again..." : "Loading..."}
      </p>
      <div className="flex justify-center space-x-2">
        <div className="w-3 h-3 bg-primary_text rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
        <div className="w-3 h-3 bg-primary_text rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
        <div className="w-3 h-3 bg-primary_text rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
      </div>
    </div>
  )

  let login_button = 
  (
    <button className='flex self-center items-center justify-center w-6/12' onClick={HandleLoginClick}>
      Log In With Main EVE Account
    </button>
  )

  let content = loading_bounce
  if (welcome_state == STATE_LOGIN)
  {
    content = login_button
  }

  let error_content =
  (
    <h1 className='flex items-center justify-center self-center text-sm text-warning w-6/12'>
      {ping_error_message}
    </h1>
  )

  return (
    <div className="flex items-center justify-center min-h-screen min-w-screen bg-gradient-to-br from-primary_bg to-secondary_bg">
      <div
        className={`flex text-center flex-col transition-opacity duration-1000 ${
          isVisible ? 'opacity-100' : 'opacity-0'
        }`}
      >
        <h1 className="text-4xl md:text-5xl font-bold text-primary_text mb-4">
          Cyber Syn Eve
        </h1>
        {has_error ? error_content : <></>}
        {content}
      </div>
    </div>
  )
}

export default Welcome