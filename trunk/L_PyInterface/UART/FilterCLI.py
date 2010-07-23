'''
FilterCLI.py
@author: River Allen
@date: July 13, 2010

Filter Command Line Interface.
'''

import UARTCLI
import time
import utilRoomba
import struct

class FilterCLI(UARTCLI.UARTCLI):    
    def __init__(self):
        super(FilterCLI, self).__init__()
    
    def help_move(self):
        print 'syntax: move <angle> <distance>',
        print '-- Turn the Roomba by angle, then move straight for distance.'
        print 'Angle: In degrees. Positive is left and negative is right.'
        print 'Distance: In centimeters.'
        print 'Example: "move 30 100" (Turn left 30 degrees, move 1 meter)'
    
    def do_move(self, args):
        args = args.split( ' ' )
        
        nargs = len(args)
        
        if nargs < 1:
            print 'Not enough arguments.'
            self.help_move()
            return
        elif nargs == 1:
            move_type = int(args[0])
            if move_type == 1:
                args = [0, 100]
            elif move_type == 2:
                args = [10, 0]
            elif move_type == 3:
                args = [-10, 0]
            else:
                args = [0, 0]
        
        angle = 0
        distance = 0
        
        try:
            angle = int( args[0] )
        except:
            print 'Angle argument is invalid.'
            self.help_move()
            return
        
        try:
            distance = int(args[1])
        except:
            print 'Distance argument is invalid.'
            self.help_move()
            return
        
        print angle, distance
        roombaAngle = int( utilRoomba.DegreesToRoombaAngle(angle) )
        roombaDistance = int( utilRoomba.CmToRoombaDistance(distance) )
        fmt = 'hhh' # Unsigned Byte / Short / Short
        self._input.append(('move', fmt, struct.pack(fmt, 0, roombaAngle, roombaDistance)))
    
    def help_stop(self):
        print 'syntax: stop',
        print '-- Stops the Roomba.'
        
    def do_stop(self, args):
        self.do_move('0 0')
    
    def help_pos(self):
        print 'syntax: pos x_pos y_pos'
        print '-- moves the Roomba close to position (x_pos, y_pos)'
    
    def do_pos(self, args):
        args = args.split( ' ' )
        
        nargs = len(args)
        
        if nargs < 2:
            print 'Not enough arguments.'
            self.help_pos()
            return
        
        try:
            x_pos = int( args[0] )
            y_pos = int( args[1] )
        except:
            print 'Arguments are not integers'
            self.help_pos()
            return
    
        self._input.append(('pos', x_pos, y_pos))
    
    def help_wait(self):
        print 'syntax: wait <delay>',
        print '-- Wait approximately <delay> in milliseconds.'
    
    def do_wait(self, arg):
        wait_time = 0
        try:
            wait_time = float(arg) / 1000
        except:
            print 'Delay argument is invalid.'
            self.help_wait()
            return
    
        time.sleep(wait_time)
        
    def emptyline(self):
        self.do_nothing('')