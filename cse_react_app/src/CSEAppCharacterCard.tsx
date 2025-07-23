import * as CSEAppCommon from './CSEAppCommon'
import React from 'react'
import { BuildURL } from './CSEAppBuildURL'
import { CSEAppContext } from './CSEAppContext'
import type { PortraitResponse } from './CSEAppHTTP'
import opportunities_icon from './assets/coins.png'

const STATE_INIT = 0
const STATE_LOG_IN = 1
const STATE_LOGGED_IN = 2

function CSEAppCharacterCard({character_name, character_id, _logged_in, type}: any)
{
  const [state, set_state] = React.useState(STATE_INIT)
  let logged_in = React.useRef(_logged_in)
  const session_uuid = CSEAppContext((state) => state.m_SessionUUID)
  const [loop_counter, set_loop_counter] = React.useState(0)
  const internal_counter = React.useRef(0)
  const [portrait_string, set_portrait_string] = React.useState<string | null>(null)
  const client_id =  CSEAppContext((state) => state.m_ClientID)

  function Init()
  {
    function CounterFunc()
    {
      internal_counter.current += 1
      set_loop_counter(internal_counter.current)
    }
    const interval_id = setInterval(CounterFunc, 1000)
    return () => {clearInterval(interval_id)}
  }

  async function MainLoop()
  {
    if (!portrait_string)
    {
      let url = BuildURL(CSEAppCommon.SERVER_PORTRAIT_URL, {m_SessionUUID: session_uuid, m_ClientID: client_id, m_CharacterID: character_id})
      try
      {
        const res = await fetch(url)
        if (!res.ok)
        {
          throw Error(`HTTP error ${res.status}`)
        }

        const portrait_res: PortraitResponse = await res.json()
        if (portrait_res)
        {
          set_portrait_string(portrait_res.m_Portrait)
        }
      }
      catch(err)
      {
        if (err instanceof Error)
        {
          console.log(`${err.message}`)
        }
      }
    }
  }

  async function HandleLoginCharacter() 
  {
    let url = BuildURL("https://login.eveonline.com/v2/oauth/authorize/", {response_type: "code", redirect_uri: CSEAppCommon.SERVER_AUTH_URL, client_id: CSEAppCommon.CLIENT_ID, scope: CSEAppCommon.SCOPES, state: session_uuid})
    window.open(url, '_blank', 'width=600,height=600,noopener,noreferrer')
  }

  React.useEffect(() => {Init()}, [])
  React.useEffect(() => {MainLoop()}, [loop_counter])

  var avatar_jsx = (<div>No Portrait</div>)
  if (portrait_string)
  {
    avatar_jsx = 
    (
      <img src={portrait_string} className='w-32 h-32 m-2' alt="Image from memory" />
    )
  }
  
  var buttons_jsx = (<div>Buttons</div>)
  if (logged_in)
  {
    buttons_jsx = 
    (
      <div className='flex m-2'>
        <button>
          <img src={opportunities_icon} alt='Opportunities' className="w-4 h-4"></img>
        </button>
      </div>
    )
  }
  else
  {
    buttons_jsx = (<button className='self-center' onClick={HandleLoginCharacter}>
      Log In Character
    </button>)
  }

  var name_jsx = (<div className='m-2'>{character_name}</div>)

  return (
    <div className='flex flex-col justify-start items-start border-primary_accent w-full border-4'>
      {name_jsx}
      {avatar_jsx}
      {buttons_jsx}
    </div>
  )
}

export default CSEAppCharacterCard