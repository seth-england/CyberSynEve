import ProjectSettings
import CSECommon
from math import sqrt

def Clampf(x, min, max):
    if x < min:
        return min
    elif x > max:
        return max
    else:
        return x

def Normalizef(x, min, max):
    t =  (x - min) / (max - min)
    t = Clampf(t, 0.0, 1.0)
    return t

class Vec2:
    def __init__(self, x=0, y=0):
        self.m_X = x
        self.m_Y = y

    def __add__(self, other):
        x = self.m_X + other.m_X
        y = self.m_Y + other.m_Y
        return Vec2(x, y)

    def __sub__(self, other):
        x = self.m_X - other.m_X
        y = self.m_Y - other.m_Y
        return Vec2(x, y)

    def __mul__(self, other : float):
        x = self.m_X * other
        y = self.m_Y * other
        return Vec2(x, y)

    def Length(self):
        c_squared = sqrt(self.m_X * self.m_X + self.m_Y * self.m_Y)
        return c_squared
    
    def Normalized(self):
        length = self.Length()
        if length < CSECommon.ZERO_TOL:
            return Vec2(0,0)
        x = self.m_X / length
        y = self.m_Y / length
        return Vec2(x,y)

    def ToLength(self, length):
        norm = self.Normalized()
        result = norm * length
        return result
        
