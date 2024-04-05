import ProjectSettings
ProjectSettings.Init()
import requests
import CSECommon
import webbrowser
import urllib.parse
import uuid
import CSEHTTP
import json
import time
import threading
import CSEClientSettings
import CSEFileSystem
import CSEClient

client = CSEClient.CSEClient()

def PingThread():
  while True:
    client.PingServer()
    #client.RetrieveCharacters()
    time.sleep(CSECommon.PING_PERIOD)

# Read the client serialized values from the disk
CSEFileSystem.ReadObjectFromFileJson(CSECommon.CLIENT_FILE_PATH, client.m_SerializedValues)
# Create UUID if one is not serialized
if client.m_SerializedValues.m_UUID == CSECommon.INVALID_UUID:
  client.m_SerializedValues.m_UUID = str(uuid.uuid4())
client.m_UUID = client.m_SerializedValues.m_UUID
# Write the client serialized values back to the disk
CSEFileSystem.WriteObjectJsonToFilePath(CSECommon.CLIENT_FILE_PATH, client.m_SerializedValues)

# Read client settings
CSEFileSystem.ReadObjectFromFileJson(CSECommon.CLIENT_SETTINGS_FILE_PATH, client.m_ClientSettings)
CSEFileSystem.WriteObjectJsonToFilePath(CSECommon.CLIENT_SETTINGS_FILE_PATH, client.m_ClientSettings)

# Spin up ping thread
client.m_PingThread = threading.Thread(target=PingThread, args=())
client.m_PingThread.start()

client.TransitionMain()

# Main Loop
while True:
  user_input = input()

  match client.m_State:
    case CSEClient.CLIENT_STATE_MAIN:
      client.UpdateMain(user_input)
    case CSEClient.CLIENT_STATE_PROFITABLE:
      client.UpdateProfitable(user_input)
    case CSEClient.CLIENT_STATE_CHAR_TYPE:
      client.UpdateCharType(user_input)