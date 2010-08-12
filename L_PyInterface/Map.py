class Map(object):
    def __init__(self, obstacles=[]):
        self.obstacles = obstacles
    
    def draw(self, cr):
        raise NotImplemented, "Abstract class"
    
    def obstacles(self):    
        raise NotImplemented, "Abstract class"

class GridMap(Map):
    def __init__(self, obstacles=[]):
        super(GridMap, self).__init__(obstacles)
        
    def draw(self, cr):
        # Draw grid
        grid_lims = [200, 300]
        box_size = 25
        
        cr.set_source_rgba(0.7, 1.0, 0.3, 0.5)
        
        for x in range(grid_lims[0]/box_size):
            for y in range(grid_lims[1]/box_size):
                cr.rectangle(x * box_size, y * box_size, box_size, box_size)
        
        cr.stroke()
        
    
    
class LabMap(Map):
    def __init__(self, obstacles=[]):
        super(GridMap, self).__init__(obstacles)
        
    def draw(self, cr):
        pass
        
    def obstacles(self):    
        pass
    
class FloorMap(Map):
    def __init__(self, obstacles=[]):
        super(GridMap, self).__init__(obstacles)
        
    def draw(self, cr):
        pass
        
    def obstacles(self):    
        pass