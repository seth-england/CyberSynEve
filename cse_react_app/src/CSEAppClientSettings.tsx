export interface CSEAppProfitableSettings
{
  m_MinProfit: Number
  m_MinRateOfProfit: Number
  m_MinOrderCount: Number
  m_PctOfRecentVolume: Number
}

export interface CSEAppClientSettings
{
  m_PanelsHorzSize: [number, number, number]
  m_PanelsVertSize: [number, number, number]
  m_ProfitableSettings: CSEAppProfitableSettings
}

function CreateCSEAppProfitableSettings(data: Partial<CSEAppProfitableSettings> = {}): CSEAppProfitableSettings
{
  const defaults: CSEAppProfitableSettings = 
  {
    m_MinProfit: 5_000_000,
    m_MinRateOfProfit: 0.05,
    m_MinOrderCount: 100,
    m_PctOfRecentVolume: 0.05,
  }

  let ret_val = 
  {
    ...defaults,
    ...data
  }

  return ret_val
}

export function CreateCSEAppClientSettings(data: Partial<CSEAppClientSettings> = {}): CSEAppClientSettings
{
  const defaults: CSEAppClientSettings = 
  {
    m_PanelsHorzSize: [33.33, 33.33, 33.34],
    m_PanelsVertSize: [5, 90, 5],
    m_ProfitableSettings: CreateCSEAppProfitableSettings({})
  }

  let ret_value: CSEAppClientSettings =
  {
    ...defaults,
    ...data,
    m_ProfitableSettings: data.m_ProfitableSettings ? CreateCSEAppProfitableSettings(data.m_ProfitableSettings) : defaults.m_ProfitableSettings
  }

  return ret_value
}