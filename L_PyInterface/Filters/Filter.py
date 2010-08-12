'''
Filter.py
@author: River Allen
@date: July 2, 2010

General 'Abstract' class for Filters. Includes some abstract methods and some convenience
methods. 
'''

class Filter(object):
    def __init__(self, explorer_pos, explorer_cov, name='Filter'):
        '''
        @param explorer_pos: The initial position vector for the explorer. 
        @type explorer_pos: numpy.array
        
        @param explorer_cov: The initial covariance matrix for the explorer.
        @type explorer_cov: numpy.array
        
        @param name: A unique identifying name for the filter.
        @type name: str
        '''
        self.explorer_pos = explorer_pos
        self.explorer_cov = explorer_cov
        self.name = name
        self.explorer_diam = 16.75
    
    def draw(self, cr):
        '''
        This method is called by the Roomba GUI. It is expected that a Filter will draw
        all of the information associated with it.
        '''
        raise NotImplementedError, "Abstract class"
    
    def _draw_explorer(self, cr):
        '''
        Draws a basic explorer using the filter's explorer_pos.
        
        @param cr: Common drawing area object.
        @type cr: Cairo Context
        '''
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
        Draws basic heading based on the Filter's explorer_pos.
        
        @param cr: Common drawing area object.
        @type cr: Cairo Context
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
        
    def move(self, transition_vec, transition_cov):
        '''
        Common function called when explorer performs a motion.
        
        @param transition_vec: A vector of the motion performed.
        @type transition_vec: numpy.array
        
        @param transition_cov: Covariance matrix associated with the error of the motion.
        @type transition_cov: numpy.array 
        '''
        raise NotImplementedError, "Abstract class"
    
    def observation(self, observation, obs_cov):
        '''
        Common function called after "independent" number of motions. Observation data is
        given to the filter to bound the error.
        
        @param observation: The observation value associated with the
        '''
        raise NotImplementedError, "Abstract class"
    
    def step(self, transition_vec, transition_cov, observation, observation_cov):
        '''
        Common function that combines motion and step.
        
        @note: Not currently being used.
        '''
        raise NotImplementedError, "Abstract class"
        
    def get_explorer_pos(self):
        '''
        Retrieve the most likely position of the explorer.
        '''
        raise NotImplementedError, "Abstract class"
