'''
FilterManager.py
@author: River Allen
@date: July 7, 2010

A Manager to control multiple filters in an organised and abstract fashion.
'''

import Filter
import numpy as np

class FilterManagerException(Exception):
    pass

class FilterManager():
    def __init__(self):
        self._filters = {}
        
    def add_filter(self, filt):
        if not isinstance(filt, Filter.Filter):
            raise FilterManagerException, 'Attempted to add non-Filter.'
        self._filters.update({filt.name:filt})
    
    def get_draw(self):
        draw_methods = {}
        for filt in self._filters.values():
            draw_methods.update({filt.name:filt.draw})
        return draw_methods
    
    def move(self, transition_vec, transition_cov):
        for filt in self._filters.values():
            filt.move(transition_vec, transition_cov)
    
    def observation(self, obs, sensor):
        for filt in self._filters.values():
            filt.observation(obs, sensor)

    def get_explorer_pos_mean(self):
        pos = []
        for filt in self._filters.values():
            pos.append(filt.get_explorer_pos())
        
        mean_pos = np.array(pos).mean(axis=0)
        return mean_pos
