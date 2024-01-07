class ProfitableSettings:
  def __init__(self) -> None:
    self.m_MinProfit = 5_000_000
    self.m_MinRateOfProfit = 0.05
    self.m_MinOrderCount = 100

class Settings:
  def __init__(self) -> None:
    self.m_ProfitableSettings = ProfitableSettings() 