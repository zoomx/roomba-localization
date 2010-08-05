'''
Filter.py
@author: River Allen
@date: July 2, 2010

'Abstract' class for Filters. 
'''

class Filter(object):
    def __init__(self, explorer_pos, explorer_cov, name='Filter'):
        '''
        @param explorer_pos: The 
        @type explorer_pos: numpy array
        '''
        self.explorer_pos = explorer_pos
        self.explorer_cov = explorer_cov
        self.name = name
        
        self.explorer_diam = 16.75
    
    def draw(self, cr):
        raise NotImplementedError, "Abstract class"
    
    def _draw_explorer(self, cr):
        import numpy as np        
        cr.new_path()
        cr.set_line_width(5)
        cr.set_source_rgba(0, 0, 0.5, 0.8)
        cr.arc(self.explorer_pos[0], self.explorer_pos[1], self.explorer_diam, 0, 2 * np.pi)
        cr.stroke_preserve()
        cr.set_source_rgba(0.3, 0.4, 0.6, 0.8)
        cr.fill()
        cr.new_path()
    
    def _draw_heading(self, cr):
        '''
        A builtin   
        '''
        import numpy as np
        cr.new_path()
        cr.set_line_width(1)
        cr.set_source_rgba(0, 0, 0.5, 0.8)
        cr.move_to(self.explorer_pos[0], self.explorer_pos[1])
        angle = self.explorer_pos[2]
        cr.rel_line_to(self.explorer_diam * np.cos(angle), self.explorer_diam * np.sin(angle))
        cr.stroke()
        cr.new_path()
        
    def motion(self, transition_vec, transition_cov):
        raise NotImplementedError, "Abstract class"
    
    def observation(self, observation, obs_cov):
        raise NotImplementedError, "Abstract class"
    
    def step(self, transition_vec, transition_cov, observation, observation_cov):
        raise NotImplementedError, "Abstract class"
        
    def get_explorer_pos(self):
        raise NotImplementedError, "Abstract class"
