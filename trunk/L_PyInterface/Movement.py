'''
Movement.py
@author: River Allen
@date: July 8, 2010
'''

import numpy as np
import util


class Movement(object):
    def __init__(self, vec, cov, id=None):
        self.vec = vec
        self.cov = cov
        if id is not None:
            self.id = id
        else:
            self.id = hash(str(vec))
        self.straight = vec[0]
        self.offset = vec[1]
        self.heading = vec[2]

class MoveExplorerError(RuntimeError):
    pass

class MoveExplorer(object):
    def __init__(self, explorer_pos, error_leniency, rotation_moves=None, translation_moves=None,
                 debug=False):
        '''
        
        '''
        self.explorer_pos = explorer_pos
        self.error_leniency = error_leniency
        self.debug = debug
#------------------------------------------------------------------------------ 
        self.rotation_moves = {}
        self._sorted_lrot_list = []
        self._sorted_rrot_list = []
        for mov in rotation_moves:
            self.rotation_moves.update({mov.id:mov})
            if mov.heading < 0:
                # Right
                self._sorted_rrot_list.append((abs(mov.heading), mov.id))
            else:
                # Left
                self._sorted_lrot_list.append((mov.heading, mov.id))
        
        # Sort the rotation moves by angle, and place into left and right
        self._sorted_lrot_list.sort()
        self._sorted_rrot_list.sort()
        
        if self.debug:
            print 'Sorted L Rotation List:'
            print self._sorted_lrot_list
            print 'Sorted R Rotation List:'
            print self._sorted_rrot_list
        
#------------------------------------------------------------------------------ 
        self.translation_moves = {}
        self._sorted_trans_list = []
        for mov in translation_moves:
            self.translation_moves.update({mov.id:mov})
            self._sorted_trans_list.append((mov.straight, mov.id))
        
        # Sort translation moves by distance travelled
        self._sorted_trans_list.sort()
        
        if self.debug:
            print 'Sorted Translation List:'
            print self._sorted_trans_list
#------------------------------------------------------------------------------ 
        self._waypoints = []
        
        # Movement / Path history
        # May want to pickle this to a file...read and write contents
        self._movement_history = [] 
        self._waypoints_history = []
        self._true_waypoint_history = [] # Where the explorer actually thought it was
    
    
    def move_to(self, x, y):
        self._waypoints.append([x, y])
    
    def translate(self, explorer_pos):
        explorer_angle = explorer_pos[2] %(2 * np.pi)
        return util.affine_transform(explorer_angle, self.translation_movement.vec, 
                                         self.translation_movement.cov)
    
    def right_rotate(self, explorer_pos):
        explorer_angle = explorer_pos[2] %(2 * np.pi)
        return util.affine_transform(explorer_angle, self.right_rotation_movement.vec, 
                                         self.right_rotation_movement.cov)
    
    def left_rotate(self, explorer_pos):
        explorer_angle = explorer_pos[2] %(2 * np.pi)
        return util.affine_transform(explorer_angle, self.left_rotation_movement.vec, 
                                         self.left_rotation_movement.cov)
        
    def get_current_waypoints(self):
        return self._waypoints
    
    def get_old_waypoints(self):
        return self._waypoints_history
    
    def _find_applicable_rotation(self, angle):
        '''
        
        '''
        if self.debug:
            print 'ANGLE_Difference~', angle
            
        
        sort_list = []
        # Turn Left
        if ((angle > 0 and angle <= np.pi) or 
            (angle > -2*np.pi and angle <= -np.pi)):
            
            sort_list = self._sorted_lrot_list
        
        # Turn Right
        else:
            sort_list = self._sorted_rrot_list

        angle = abs(angle)
        i = 0
        while i < len(sort_list):
            if sort_list[i][0] > angle:
                break
            i += 1
        
        if i <= 0:
            i = 0
        else:
            i = i - 1

        try:
            id = sort_list[i][1] 
        except:
            raise MoveExplorerError, 'No applicable rotation exists.'
        return self.rotation_moves[id]
    
    def _find_applicable_translation(self, distance):
        i = 0
        while i < len(self._sorted_trans_list):
            if self._sorted_trans_list[i][0] > distance:
                break
            i += 1
        
        if i < 0:
            i = 0
        else:
            i = i - 1

        try:
            id = self._sorted_trans_list[i][1] 
        except:
            raise MoveExplorerError, 'No applicable translation exists.'
            
        return self.translation_moves[id]
    
    def get_next_move(self, explorer_pos):
        if self._waypoints == []:
            return None
        
        while (util.error(self._waypoints[0][0], explorer_pos[0]) <= self.error_leniency[0] and
               util.error(self._waypoints[0][1], explorer_pos[1]) <= self.error_leniency[1]):
            # Remove the waypoint and add to history
            self._waypoints_history.append(np.array(self._waypoints.pop(0)))
            self._true_waypoint_history.append(explorer_pos[:2])
            return self.get_next_move(explorer_pos)
        
        current_waypoint = self._waypoints[0]
        
        # Check if point is within turn tolerance
        x_dist = current_waypoint[0] - explorer_pos[0]
        y_dist = current_waypoint[1] - explorer_pos[1] 
        
        angle = np.arctan2(y_dist,x_dist) %(2 * np.pi)
        explorer_angle = explorer_pos[2] %(2 * np.pi)
        
        if self.debug:
            print 'Angle of roomba to waypoint:', angle
            print 'Roomba current angle:', explorer_angle
            print self.error_leniency
            
        if util.error(angle, explorer_angle) > self.error_leniency[2]:
            # We should attempt to turn.
            if self.debug:
                print 'Need to turn!'
            angle_diff = angle - explorer_angle
            _mov = self._find_applicable_rotation(angle_diff)
        else:
            # Go Straight
            distance_diff = np.hypot(x_dist, y_dist)
            _mov = self._find_applicable_translation(distance_diff)

        self._movement_history.append(_mov.vec)
        return _mov
    
    def find_move(self, id):
        if self.translation_moves.has_key(id):
            return self.translation_moves[id]
        elif self.rotation_moves.has_key(id):
            return self.rotation_moves[id]
        else:
            return None
    
    def get_next_move_old(self, explorer_pos):
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
                vec, cov = self.left_rotate(explorer_pos)
                id = 2
            # Turn Right
            else:
                vec, cov = self.right_rotate(explorer_pos)
                id = 3
        else:
            # Go Straight
            vec, cov = self.translate(explorer_pos)
            id = 1
        
        self._movement_history.append(vec)
        return Movement(vec, cov, id)
    
    
if __name__ == '__main__':
    print 'Testing Movement and Move_Explorer'
    origin_pos = np.array([200, 0, 0])
    error_tolerance = np.eye(3)
    
    trans_mov = Movement(np.array([104, 3, np.deg2rad(1)]), np.zeros([3,3]))
    left_mov = Movement(np.array([0, 0, np.deg2rad(12)]), np.zeros([3,3]))
    
    #me = Move_Explorer(origin_pos, error_tolerance, [], [], [], perfect_movement=True)
    me = MoveExplorer(origin_pos, [12, 12, np.deg2rad(6)], debug=True,
                      translation_moves=[Movement(np.array([1,0,0]), np.identity(3)),
                                         Movement(np.array([10,0,0]), np.identity(3)),
                                         Movement(np.array([100,0,0]), np.identity(3))],
                      rotation_moves=[Movement(np.array([0,0,np.deg2rad(1)]), np.identity(3)),
                                      Movement(np.array([0,0,np.deg2rad(-1)]), np.identity(3)),
                                      Movement(np.array([0,0,np.deg2rad(-10)]), np.identity(3)),
                                      Movement(np.array([0,0,np.deg2rad(10)]), np.identity(3)),
                                      Movement(np.array([0,0,np.deg2rad(-50)]), np.identity(3)),
                                      Movement(np.array([0,0,np.deg2rad(50)]), np.identity(3))])
    #me = Move_Explorer(origin_pos, error_tolerance, trans_mov, left_mov)
    
    #'''
    me.move_to(200, 300)
    me.move_to(100, 150)
    me.move_to(0, 300)
    me.move_to(100, 150)
    me.move_to(0, 0)
    me.move_to(100, 150)
    me.move_to(200, 0)
    #'''
    me.move_to(200, 15)
    
    explorer_pos = origin_pos
    import time
    for zz in range(1000000):
        move = me.get_next_move(explorer_pos)
        if move is None:
            break
        explorer_pos = explorer_pos + util.affine_transform(explorer_pos[2], move.vec, move.cov)[0]
        print '%d\tVec:' % zz, move.vec
        print '%d\tExplorer:' % zz, explorer_pos
        time.sleep(0.1)
    
    print 'Done!'
    print me._waypoints_history
    print me._true_waypoint_history
    #print me._movement_history
    