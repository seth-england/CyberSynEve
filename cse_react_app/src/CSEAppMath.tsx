export interface BoundingBox
{
  m_Left: number,
  m_Right: number,
  m_Top: number,
  m_Bottom: number,
}

export interface Point
{
  m_X: number,
  m_Y: number,
}

export function BoundingBoxFromDomRect(rect: DOMRect): BoundingBox
{
  return {
    m_Left: rect.left,
    m_Right: rect.right,
    m_Top: rect.top,
    m_Bottom: rect.bottom,
  }
}

export function BoundingBoxesIntersects(bounds1: BoundingBox, bounds2: BoundingBox): boolean
{
  if (bounds1.m_Left > bounds2.m_Right)
  {
    return false
  }
  if (bounds1.m_Right < bounds2.m_Left)
  {
    return false
  }
  if (bounds1.m_Top > bounds2.m_Bottom)
  {
    return false
  }
  if (bounds1.m_Bottom < bounds2.m_Top)
  {
    return false
  }
  return true
}

export function PointInBoundingBox(point: Point, bounds: BoundingBox): boolean
{
  if (point.m_X < bounds.m_Left)
  {
    return false
  }
  if (point.m_X > bounds.m_Right)
  {
    return false
  }
  if (point.m_Y < bounds.m_Top)
  {
    return false
  }
  if (point.m_Y > bounds.m_Bottom)
  {
    return false
  }
  return true
}

export function CalculateIntersection(bounds1: BoundingBox, bounds2: BoundingBox): BoundingBox | null
{
  const left = Math.max(bounds1.m_Left, bounds2.m_Left)
  const right = Math.min(bounds1.m_Right, bounds2.m_Right)
  const top = Math.max(bounds1.m_Top, bounds2.m_Top)
  const bottom = Math.min(bounds1.m_Bottom, bounds2.m_Bottom)

  if (left > right || top > bottom)
  {
    return null
  }
  return {m_Left: left, m_Right: right, m_Top: top, m_Bottom: bottom}
}

export function CalculateIntersectionArea(bounds1: BoundingBox, bounds2: BoundingBox): number
{
  const intersection = CalculateIntersection(bounds1, bounds2)
  if (!intersection)
  {
    return 0
  }
  return (intersection.m_Right - intersection.m_Left) * (intersection.m_Bottom - intersection.m_Top)
}
