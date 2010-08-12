'''
UARTInput.py
@author: River Allen
@date: July 23, 2010

A parent class for objects that will be providing input to be written across UART. 
'''

import threading

class UARTInput(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._input = []
        self._lock = threading.Lock()
        
    def get_input(self):
        '''
        Retrieves list of all VALID data that have been processed since last called.
        '''
        with self._lock:
            ret_data = self._input
            self._input = []
            return ret_data
        
    def add_input(self, dat):
        '''
        Locks, writes to input buffer, then unlocks.
        '''
        with self._lock:
            if type(dat) == type(list):
                self._input.extend(dat)
            else:
                self._input.append(dat)