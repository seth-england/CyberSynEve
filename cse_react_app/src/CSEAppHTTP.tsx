
export interface PingResponse
{
  m_SessionUUID: string | null,
  m_ClientId: number | null,
  m_CharacterCount: number,
  m_LoggedInCharacterCount: number,
}

export interface Character
{
  m_CharacterID: number
  m_CharacterName: string
  m_CharacterType: string
  m_CharacterLoggedIn: boolean
}

export interface CharactersResponse
{
  m_Characters: Array<Character>
}

export interface PortraitResponse
{
  m_SessionUUID: string
  m_ClientID: number
  m_CharacterID: number
  m_Portrait: string
}