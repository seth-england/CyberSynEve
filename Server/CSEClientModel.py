import CSEMessages

class CSEClientData:
    def __init__(self) -> None:
        self.m_CharacterId = 0
        self.m_CharacterName = ""
        self.m_AccessToken = ""
        self.m_RefreshToken = ""
        self.m_ExpiresDateString = ""
        self.m_TokenValid = False

class CSEClientModel:
    def __init__(self) -> None:
        self.m_CharacterIdToCharacterData = dict[int, CSEClientData]()
        return

    def GetClientByIndex(self, index : int):
        # Check if key exists
        keys = list(self.m_CharacterIdToCharacterData.keys())
        key_len = len(keys)
        if index >= key_len:
            return None
        
        # Get client data
        key = keys[index]
        client_data = self.m_CharacterIdToCharacterData[key]
        return client_data
        

    def OnNewClientAuth(self, message : CSEMessages.CSEMessageNewClientAuth):
        client_data = self.m_CharacterIdToCharacterData.get(message.m_CharacterId)
        # Client data does not exist, create it
        if client_data is None:
            client_data = CSEClientData()
            self.m_CharacterIdToCharacterData[message.m_CharacterId] = client_data
        
        # Copy client data from message
        client_data.m_CharacterId = message.m_CharacterId
        client_data.m_CharacterName = message.m_CharacterName
        client_data.m_AccessToken = message.m_AccessToken
        client_data.m_RefreshToken = message.m_RefreshToken
        client_data.m_ExpiresDateString = message.m_ExpiresDateString
        client_data.m_TokenValid = True