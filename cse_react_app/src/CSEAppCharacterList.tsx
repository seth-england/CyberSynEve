import * as CSEAppCommon from './CSEAppCommon'
import React from 'react'
import { BuildURL } from './CSEAppBuildURL'
import { CSEAppContext } from './CSEAppContext'
import * as CSEAppHTTP from './CSEAppHTTP'
import CSEAppCharacterCard from './CSEAppCharacterCard'

function CSEAppCharacterList()
{
  const session_uuid = CSEAppContext((state) => state.m_SessionUUID)
  const client_id = CSEAppContext((state) => state.m_ClientID)
  const connected_to_server = CSEAppContext((state) => state.m_ConnectedToServer)
  const [character_list, set_character_list] = React.useState(new Array<CSEAppHTTP.Character>())
  const character_count = CSEAppContext((state) => state.m_CharacterCount)
  const logged_in_character_count = CSEAppContext((state) => state.m_LoggedInCharacterCount)

  async function FetchCharacters() 
  {
    if (!connected_to_server || !client_id)
    {
      return
    }
    
    let url = BuildURL(CSEAppCommon.SERVER_CHARACTERS_URL, {m_SessionUUID: session_uuid, m_ClientID: client_id})
    try
    {
      const res = await fetch(url)
      if (res.ok)
      {
        const res_json: CSEAppHTTP.CharactersResponse = await res.json()
        set_character_list(res_json.m_Characters)
      }
      else
      {
        throw Error(`HTTP error ${res.status}`)
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

  React.useEffect(() => {FetchCharacters()}, [connected_to_server, session_uuid, client_id, character_count, logged_in_character_count])

  async function HandleLoginCharacter() 
  {
    let url = BuildURL("https://login.eveonline.com/v2/oauth/authorize/", {response_type: "code", redirect_uri: CSEAppCommon.SERVER_AUTH_URL, client_id: CSEAppCommon.CLIENT_ID, scope: CSEAppCommon.SCOPES, state: session_uuid})
    window.open(url, '_blank', 'width=600,height=600,noopener,noreferrer')
  }

  const char_to_jsx = (character : CSEAppHTTP.Character) =>
  (
    <CSEAppCharacterCard 
     key={character.m_CharacterID} 
     character_name={character.m_CharacterName} 
     character_id={character.m_CharacterID}
     _logged_in={character.m_CharacterLoggedIn}
     type={character.m_CharacterType}
    />    
  )

  const char_list_jsx = character_list.map(char_to_jsx)

  return (
    <div className="flex flex-col items-start mb-4 space-y-4 min-w-min max-w-md h-full m-5">
      <button className='self-center' onClick={HandleLoginCharacter}>
        Log In Character
      </button>
      {char_list_jsx}
    </div>
  )
}

export default CSEAppCharacterList