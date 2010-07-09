'''
Movement.py
@author: River Allen
@date: July 8, 2010
'''

import numpy as np
import util
import copy

class Movement(object):
    def __init__(self, vec, cov, id=None):
        self.vec = vec
        self.cov = cov
        self.id = id

class Move_Explorer(object):
    def __init__(self, explorer_pos, error_tolerance, translation_movement, left_rotation_movement,
                 right_rotation_movement=[], perfect_movement=False):
        '''
        
        '''
        self.explorer_pos = explorer_pos
        self.explorer_cov = error_tolerance
        self.perfect_movement = perfect_movement
        
        if self.perfect_movement:
            # Assume Full Range/Perfect Movement
            # Full/Perfect Translation
            self.translation_movement = Movement(np.array([1,0,0]), np.zeros([3,3]))
            # Full/Perfect Rotation
            self.left_rotation_movement = Movement(np.array([0,0, np.deg2rad(1)]), np.zeros([3,3]))
            self.right_rotation_movement = Movement(np.array([0,0, np.deg2rad(-1)]), np.zeros([3,3]))
        else:
            self.translation_movement = translation_movement
            self.left_rotation_movement = left_rotation_movement
            if right_rotation_movement == []:
                self.right_rotation_movement = copy.deepcopy(left_rotation_movement)
                self.right_rotation_movement.vec[2] = -self.right_rotation_movement.vec[2]
            else:
                self.right_rotation_movement = right_rotation_movement
            
        self._waypoints = []
        
        # Movement / Path history
        # May want to pickle this to a file...read and write contents
        self._movement_history = [] 
        self._waypoints_history = []
        self._true_waypoint_history = [] # Where the explorer actually thought it was
    
    
    def move_to(self, x, y):
        self._waypoints.append([x, y])
    
    
    def get_current_waypoints(self):
        return self._waypoints
    
    def get_old_waypoints(self):
        return self._waypoints_history
    
    def get_next_move(self, explorer_pos):
        if self._waypoints == []:
            return None
        
        # Check if point is within position tolerance
        if self.perfect_movement:
            position_tolerance = [1, 1]
            turn_leniency = np.deg2rad(1)
        else:
            position_tolerance = [50, 50]
            turn_leniency = np.deg2rad(11)
        
        while (util.error(self._waypoints[0][0], explorer_pos[0]) <= position_tolerance[0] and
               util.error(self._waypoints[0][1], explorer_pos[1]) <= position_tolerance[1]):
            # Remove the waypoint and add to history
            self._waypoints_history.append(np.array(self._waypoints.pop(0)))
            self._true_waypoint_history.append(explorer_pos[:2])
            return self.get_next_move(explorer_pos)
        
        point = self._waypoints[0]
        
        # Check if point is within turn tolerance
        x_dist = point[0] - explorer_pos[0]
        y_dist = point[1] - explorer_pos[1] 
        
        angle = np.arctan2(y_dist,x_dist) %(2 * np.pi)
        explorer_angle = explorer_pos[2] %(2 * np.pi)
        id = None
        if util.error(angle, explorer_angle) > turn_leniency:
            angle_diff = angle - explorer_angle
            # Turn Left
            if ((angle_diff > 0 and angle_diff <= np.pi) or 
                (angle_diff > -2*np.pi and angle_diff <= -np.pi)):
                vec, cov = util.affine_transform(explorer_angle, self.left_rotation_movement.vec, 
                                         self.left_rotation_movement.cov)
            # Turn Right
            else:
                vec, cov = util.affine_transform(explorer_angle, self.right_rotation_movement.vec, 
                                         self.right_rotation_movement.cov)
        else:
            # Go Straight
            vec, cov = util.affine_transform(explorer_angle, self.translation_movement.vec, 
                                         self.translation_movement.cov)
            id = 1
        
        self._movement_history.append(vec)
        return Movement(vec, cov, id)
    
    
if __name__ == '__main__':
    print 'Testing Movement and Move_Explorer'
    origin_pos = np.array([200, 300, 0])
    error_tolerance = np.eye(3)
    
    trans_mov = Movement(np.array([104, 3, np.deg2rad(1)]), np.zeros([3,3]))
    left_mov = Movement(np.array([0, 0, np.deg2rad(12)]), np.zeros([3,3]))
    
    #me = Move_Explorer(origin_pos, error_tolerance, [], [], [], perfect_movement=True)
    me = Move_Explorer(origin_pos, error_tolerance, trans_mov, left_mov)
    
    '''
    me.move_to(200, 300)
    me.move_to(100, 150)
    me.move_to(0, 300)
    me.move_to(100, 150)
    me.move_to(0, 0)
    me.move_to(100, 150)
    me.move_to(200, 0)
    '''
    me.move_to(0, 0)
    
    explorer_pos = origin_pos
    import time
    for zz in range(1000000):
        move = me.get_next_move(explorer_pos)
        if move is None:
            break
        explorer_pos = explorer_pos + move.vec
        print '%d\tVec:' % zz, move.vec
        print '%d\tExplorer:' % zz, explorer_pos
        time.sleep(0.1)
    
    print 'Done!'
    print me._waypoints_history
    print me._true_waypoint_history
    #print me._movement_history
    