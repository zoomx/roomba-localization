import threading

class UARTInput(threading.Thread):
    def __init__(self, log=None, debug=False):
        threading.Thread.__init__(self)
        self._input = []
        self._lock = threading.Lock()
        self.debug = debug
        self.log = log
        
    def get_input(self):
        '''
        Retrieves list of all VALID commands that have been processed since last called.
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