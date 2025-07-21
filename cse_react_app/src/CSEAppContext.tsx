import React from 'react'
import * as CSEAppClientSettings from './CSEAppClientSettings'
import { create } from 'zustand'
import * as CSEAppCommon from './CSEAppCommon'
import * as CSEClientSettings from './CSEAppClientSettings'

interface CSEAppContextType
{
    m_SessionUUID: string,
    m_ClientSettings: CSEAppClientSettings.CSEAppClientSettings, 
    m_SetClientSettings: any, 
    m_ConnectedToServer: boolean, 
    m_SetConnectedToServer: any,
    m_PingErrorMessage: string,
    m_SetPingErrorMessage: any,
    m_HasPingErrorMessage: boolean,
    m_SetHasPingErrorMessage: any,
    m_AppState: number,
    m_SetAppState: any,
    m_ClientID: number | undefined,
    m_SetClientId: any,
    m_RequestPing: boolean,
    m_SetRequestPing: any,
}

function CreateOrGetSessionUUID(): string
{
  //type context_keys = keyof CSEAppContextType;
  //const uuid_key_name: context_keys = "m_SessionUUID";
  const key_name = "CSE Session UUID"
  const current_uuid = localStorage.getItem(key_name)
  if (current_uuid)
  {
    return current_uuid
  }
  else
  {
    let uuid = crypto.randomUUID()
    try
    {
      localStorage.setItem(key_name, uuid)
    }
    catch(err)
    {
      console.log(`CreateOrGetSessionUUID ${err}`)
    }
    return uuid
  }
}

export const CSEAppContext = create<CSEAppContextType>((set) => 
({
  m_SessionUUID: CreateOrGetSessionUUID(),
  m_ClientSettings: CSEAppClientSettings.CreateCSEAppClientSettings({}),
  m_SetClientSettings: (m_ClientSettings: CSEAppClientSettings.CSEAppClientSettings) => set({m_ClientSettings}),
  m_ConnectedToServer: false,
  m_SetConnectedToServer: (m_ConnectedToServer: boolean) => set({m_ConnectedToServer}),
  m_PingErrorMessage: "Unknown",
  m_SetPingErrorMessage: (m_PingErrorMessage: string) => set({m_PingErrorMessage}),
  m_HasPingErrorMessage: false,
  m_SetHasPingErrorMessage: (m_HasPingErrorMessage: boolean) => set({m_HasPingErrorMessage}),
  m_AppState: CSEAppCommon.CSE_STATE_WELCOME,
  m_SetAppState: (m_AppState: number) => set({m_AppState}),
  m_ClientID: undefined,
  m_SetClientId: (m_ClientId: number) => set({m_ClientID: m_ClientId}),
  m_RequestPing: false,
  m_SetRequestPing: (m_RequestPing: boolean) => set({m_RequestPing}),
}));
