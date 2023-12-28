import ProjectSettings
import sys
import CSEMapModel
import CSEMath
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class CSESystemView:
    def __init__(self) -> None:
        self.m_SystemModel = CSEMapModel.CSESystemData()
        self.m_Width = 10
        self.m_Height = 10
        self.MapCoordinates = CSEMath.Vec2()

    def Init(self, system_model : CSEMapModel.CSESystemData):
        self.m_SystemModel = system_model

    def Activate(self, coordinates : CSEMath.Vec2):
        start = coordinates - CSEMath.Vec2(self.m_Width, self.m_Height) * .5
        end = coordinates + CSEMath.Vec2(self.m_Width, self.m_Height) * .5
        self.m_MapCoordinates = coordinates
        return


class CSEMapView(QWidget):
    def UniverseToMapCoords(self, universe_x, universe_z) -> CSEMath.Vec2:
        t_x = CSEMath.Normalizef(universe_x, self.m_MinUniverseX, self.m_MaxUniverseX)
        map_x = t_x * self.m_MapWidth
        t_z = CSEMath.Normalizef(universe_z, self.m_MinUniverseZ, self.m_MaxUniverseZ)
        map_z = t_z * self.m_MapHeight
        result = CSEMath.Vec2()
        result.m_X = map_x
        result.m_Y = map_z
        return result

    def MapCoordsToNormalizedMapCoords(self, map_x, map_y) -> CSEMath.Vec2:
        result = CSEMath.Vec2()
        result.m_X = CSEMath.Normalizef(map_x, 0.0, self.m_MapWidth)
        result.m_Y = CSEMath.Normalizef(map_y, 0.0, self.m_MapHeight)
        return result

    def NormalizedMapCoordsToMapCoords(self, norm_x, norm_y) -> CSEMath.Vec2:
        result = CSEMath.Vec2()
        result.m_X = norm_x * self.m_MapWidth
        result.m_Y = norm_y * self.m_MapHeight
        return result
        
    def Draw(self):
        self.m_SystemViews.clear()
        visited_systems = {}
        neighbors_to_eval = []
        if len(self.m_Model.m_Systems) == 0:
            return
        neighbors_to_eval.append(self.m_Model.m_Systems[0])

        for system in neighbors_to_eval:
            previous_system_view = None
            if visited_systems.get(system.m_Id) == None:
                map_coords = self.UniverseToMapCoords(system.m_X, system.m_Z)
                previous_system_view = CSESystemView()
                previous_system_view.Init(system)
                previous_system_view.Activate(map_coords)
                self.m_SystemViews.append(previous_system_view)
                visited_systems[system.m_Id] = previous_system_view
            previous_system_view = visited_systems[system.m_Id]
            for neighbor_system_id in system.m_AdjcentSystemsIds:
                if visited_systems.get(neighbor_system_id) != None:
                    continue
                neighbor_system = self.m_Model.GetSystemById(neighbor_system_id)
                map_coords = self.UniverseToMapCoords(neighbor_system.m_X, neighbor_system.m_Z)
                from_previous = map_coords - previous_system_view.m_MapCoordinates
                new_from_previous = from_previous.ToLength(self.m_SystemDistance)
                map_coords = previous_system_view.m_MapCoordinates + new_from_previous
                system_view = CSESystemView()
                system_view.Init(neighbor_system)
                system_view.Activate(map_coords)
                self.m_SystemViews.append(system_view)
                visited_systems[neighbor_system.m_Id] = system_view
                neighbors_to_eval.append(neighbor_system)
        return

    def __init__(self):
        QWidget.__init__(self)
        self.m_Model = CSEMapModel.MapModel()
        self.m_MinUniverseX = 0
        self.m_MinUniverseZ = 0
        self.m_MaxUniverseX = 0
        self.m_MaxUniverseZ = 0
        self.m_MapWindowWidth = 0
        self.m_MapWindowHeight = 0
        self.m_MapWidth = 0
        self.m_MapHeight = 0
        self.m_MapCenterX = 0
        self.m_MapCenterY = 0
        self.m_Scale = 1.0
        self.m_ZoomX = 1.0
        self.m_ZoomY = 1.0
        self.m_ZoomSpeed = 1
        self.m_SystemViews = []
        self.m_SystemDistance = 0

    def Init(self, parent, model : CSEMapModel.MapModel):
        self.m_Model = model
        self.m_MinUniverseX = sys.float_info.max
        self.m_MinUniverseZ = sys.float_info.max
        self.m_MaxUniverseX = sys.float_info.min
        self.m_MaxUniverseZ = sys.float_info.min
        self.m_MapWindowWidth = 720
        self.m_MapWindowHeight = 480
        self.m_MapWidth = 8000
        self.m_MapHeight = 8000
        self.m_MapCenterX = self.m_MapWidth * .5
        self.m_MapCenterY = self.m_MapHeight * .5
        self.m_Scale = 1.0
        self.m_ZoomX = self.m_MapCenterX
        self.m_ZoomY = self.m_MapCenterY
        self.m_ZoomSpeed = 1.1
        self.m_SystemViews = []
        self.m_SystemDistance = 100

        # Figure out how big the universe is
        min_universe_x = sys.float_info.max
        min_universe_z = sys.float_info.max
        max_universe_x = sys.float_info.min
        max_universe_z = sys.float_info.min
        for system in self.m_Model.m_Systems:
            # Skip unconnected
            if len(system.m_AdjcentSystemsIds) == 0:
                continue
            self.m_MinUniverseX = min(self.m_MinUniverseX, system.m_X)
            self.m_MinUniverseZ = min(self.m_MinUniverseZ, system.m_Z)
            self.m_MaxUniverseX = max(self.m_MaxUniverseX, system.m_X)
            self.m_MaxUniverseZ = max(self.m_MaxUniverseZ, system.m_Z)         
        self.m_UniverseCenterX = (self.m_MaxUniverseX - self.m_MinUniverseX) * .5 + self.m_MinUniverseX
        self.m_UniverseCenterZ = (self.m_MaxUniverseZ - self.m_MinUniverseZ) * .5 + self.m_MinUniverseZ
        self.setParent(parent)
        for i in range(1,50):
            object = QLabel("TextLabel: "+str(i))
            object.setParent(self)
            object.move(i, i)
        self.show()