class ProfitableSettings:
  def __init__(self) -> None:
    self.m_MinProfit = 5_000_000
    self.m_MinRateOfProfit = 0.05
    self.m_MinOrderCount = 100
    self.m_PctOfRecentVolume = 0.05

class Settings:
  def __init__(self) -> None:
    self.m_ProfitableSettings = ProfitableSettings()
    self.m_PanelsHorzSize = [33.33, 33.33, 33.34],
    self.m_PanelsVertSize = [5, 90, 5], 