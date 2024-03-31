
import CSECommon


class CSEUndercutResultEntry:
  def __init__(self) -> None:
    self.m_ItemId = 0
    self.m_ItemName = ""
    self.m_RegionId = 0
    self.m_RegionName = ""
    self.m_LowestPrice = CSECommon.INF
    self.m_ItemCount = 0
    self.m_SelfVolume = 0
    self.m_SelfPrice = 0
    self.m_RecentSellVolumeEst = 0

class CSEUndercutResult:
  def __init__(self) -> None:
    self.m_Valid = False
    self.m_ResultsSameStationValueType = CSEUndercutResultEntry
    self.m_ResultsSameStation = list[self.m_ResultsSameStationValueType]()