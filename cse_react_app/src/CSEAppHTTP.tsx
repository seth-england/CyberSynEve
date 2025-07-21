
export interface PingResponse
{
  m_SessionUUID: string | null,
  m_ClientId: number | null,
}

export interface Character
{
  m_CharacterID: number
  m_CharacterName: string
  m_CharacterType: string
  m_LoggedIn: boolean
}

export interface CharactersResponse
{
  m_Characters: Array<Character>
}