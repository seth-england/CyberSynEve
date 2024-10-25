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
import MenuMain

client = CSEClient.CSEClient()

def PingThread():
  while True:
    client.PingServer()
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

#client.TransitionMain()
menu = MenuMain.MenuMain()
menu.Start(client)

def StartMenu(next_menu):   
  if next_menu:
    if next_menu.m_NeedsChars:
      client.RetrieveCharacters()
    if next_menu.m_NeedsOpportunities:
      client.RetrieveOpportunities()
    next_menu.Start(client)
    
# Main Loop
while True:
  user_input = input()

  with client.m_Lock:
    menu.Update(user_input)
    next_menu = menu.GetNextMenu()     
    while next_menu:
      StartMenu(next_menu)
      menu = next_menu
      next_menu = menu.GetNextMenu()