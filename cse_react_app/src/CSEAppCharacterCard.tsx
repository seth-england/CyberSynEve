import * as CSEAppCommon from './CSEAppCommon'
import React from 'react'
import { BuildURL } from './CSEAppBuildURL'
import { CSEAppContext } from './CSEAppContext'

const STATE_INIT = 0
const STATE_LOG_IN = 1
const STATE_LOGGED_IN = 2

function CSEAppCharacterCard({character_name, character_id, _logged_in, type}: any)
{
  const [state, set_state] = React.useState(STATE_INIT)
  let logged_in = React.useRef(_logged_in)
  const session_uuid = CSEAppContext((state) => state.m_SessionUUID)

  async function Init()
  {
    if (state != STATE_INIT)
    {
      return
    }

    if (logged_in.current)
    {
      set_state(STATE_LOGGED_IN)
    }
    else
    {
      set_state(STATE_LOG_IN)
    }
  }

  async function HandleLoginCharacter() 
  {
    let url = BuildURL("https://login.eveonline.com/v2/oauth/authorize/", {response_type: "code", redirect_uri: CSEAppCommon.SERVER_AUTH_URL, client_id: CSEAppCommon.CLIENT_ID, scope: CSEAppCommon.SCOPES, state: session_uuid})
    window.open(url, '_blank', 'width=600,height=600,noopener,noreferrer')
  }

  React.useEffect(() => {Init()}, [])

  var avatar_jsx = (<div>Placeholder</div>)
  
  var buttons_jsx = (<div>Buttons</div>)
  if (state == STATE_LOGGED_IN)
  {
    buttons_jsx = (<div>Logged In</div>)
  }
  else
  {
    buttons_jsx = (<button className='self-center' onClick={HandleLoginCharacter}>
      Log In Character
    </button>)
  }

  return (
    <div className='flex flex-col border-primary_accent w-full border-4'>
      {character_name}
      {avatar_jsx}
      {buttons_jsx}
    </div>
  )
}

export default CSEAppCharacterCard