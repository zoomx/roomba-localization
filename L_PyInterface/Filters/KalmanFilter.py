'''
KalmanFilter.py
@author: River Allen
@date: July 21, 2010

Kalman Filter implementation for the Roomba localization experiments.
'''
import numpy as np
from numpy import linalg
import Filter
import Sensor
import util

class KalmanFilter(Filter.Filter):
    def __init__(self, explorer_pos, explorer_cov):
        super(KalmanFilter, self).__init__(explorer_pos, explorer_cov, 'Extended Kalman Filter')
        
        
    def move(self, transition_vec, transition_cov):
        '''
        Performs the prediction phase/motion model aspect of the Kalman Filter. 
        After the robot has moved, this function is called to determine the most
        likely new position and accumulate error from the move.
        
        The method for adding the transition vector to the explorer's current position
        as well as determining the predicted explorer covariance is taken from:
            Randell C. Smith and Peter Cheeseman. 1986.
            On the Representation and Estimation of Spatial Uncertainty.
        
        @param tranisition_vec: The transition vector, or the vector the explorer 
        has moved.
        @type tranisition_cov: numpy.array
        @param transition_cov: The error covariance matrix associated with the move.
        @type transition_cov: numpy.array
        '''
        #print self.explorer_pos
        #print self.explorer_cov
        Bu, Q = util.affine_transform(self.explorer_pos[2], transition_vec, transition_cov)
        orig_explorer_pos = self.explorer_pos.copy()
        self.explorer_pos = self.explorer_pos + Bu
        self.explorer_pos[2] = self.explorer_pos[2] % (2*np.pi)
        
        # 'H' here is not the observation model, but a transformation
        # matrix described by Smith and Cheeseman '86.
        H = np.array([[1, 0,-(self.explorer_pos[1] - orig_explorer_pos[1])], 
                      [0, 1, (self.explorer_pos[0] - orig_explorer_pos[0])], 
                      [0, 0, 1]])
        
        self.explorer_cov = np.dot(np.dot(H, self.explorer_cov), H.T) + Q
        
    def _observation_beacon(self, obs, beacon):
        '''
        Fuse beacon range data into the EKF. This is considered part of the update phase.

        This code in this method is based on work in:
            George Kantor and Sanjiv Singh. 2002.
            Preliminary Results in Range Only Localization and Mapping.
            
        @param obs: The range value given by the beacon.
        @type obs: int
        
        @param beacon: The beacon object, which should contain information pertaining to
        its position, covariance and tolerable range.
        @type beacon: Sensor.BeaconSensor 
        '''
        b_angle = np.arctan2((beacon.y_pos - self.explorer_pos[1]),(beacon.x_pos - self.explorer_pos[0]))
        x_obs_pos = beacon.x_pos - ((obs)*np.cos(b_angle))
        y_obs_pos = beacon.y_pos - ((obs)*np.sin(b_angle))
        
        
        obs_pos = np.array([x_obs_pos, y_obs_pos])
        obs_cov = beacon.observation(obs)
        
        # !!!!! Very Important !!!!!!
        # This was taken from Kantor and Singh, and allows us to remain
        # in Cartesian coordinates as opposed to having to convert to polar
        # and back because the beacon only gives us a range as opposed to
        # a position.
        R = np.array([[obs_cov, 0], [0, 10 * obs_cov]])
        
        _,R = util.affine_transform(b_angle, np.array([0,0]), R)
        
        try:
            K = np.dot(R, linalg.inv((R + self.explorer_cov[:2,:2])))
        except linalg.LinAlgError:
            #print '-'*50
            #print 'Explorer Pos:', self.explorer_pos
            #print 'Explorer Cov:', self.explorer_cov
            #print 'Obs position:', obs_pos
            #print 'OBS Variance:', R
            raise
        self.explorer_cov[:2,:2] = R - np.dot(K, R)
        #self.explorer_pos[:2] = self.explorer_pos[:2] + np.dot(K, (self.explorer_pos[:2] - obs_pos))
        self.explorer_pos[:2] = obs_pos + np.dot(K, (self.explorer_pos[:2] - obs_pos))
    
    def _observation_compass(self, obs_heading, sensor):
        '''
        Similar to the beacon, but operates on the compass. What makes the compass
        different is that the prediction phase only affects the explorer's heading and 
        the heading error in the explorer covariance matrix. Thus, it only affects:
        explorer_pos[2]
        explorer_cov[2,2]
        
        @param obs_heading: The observed heading given by the compass (0-3599).
        @type obs_heading: int
        
        @param sensor: The compass responsible for the reading.
        @type sensor: Sensor.CompassSensor
        '''
        obs_variance = sensor.observation(obs_heading)
        k = obs_variance * 1./(obs_variance + self.explorer_cov[2,2])
        self.explorer_cov[2,2] = obs_variance - (k * obs_variance)
        self.explorer_pos[2] = obs_heading + (k * (self.explorer_pos[2] - obs_heading))
        self.explorer_pos[2] = self.explorer_pos[2] % (2*np.pi)
        
    
    def _observation_trilateration(self, beacons, tril_sensor):
        '''
        
        '''
        obs_variance = tril_sensor.observation(None)
        obs_position = tril_sensor.trilateration(beacons, self.get_explorer_pos())
        try:
            K = np.dot(obs_variance, linalg.inv((obs_variance + self.explorer_cov[:2,:2])))
        except linalg.LinAlgError:
            #print '-'*50
            #print 'Explorer Pos:', self.explorer_pos
            #print 'Explorer Cov:', self.explorer_cov
            #print 'Obs position:', obs_pos
            #print 'OBS Variance:', R
            raise
        
        # Position update
        self.explorer_cov[:2,:2] = obs_variance - np.dot(K, obs_variance)
        #self.explorer_pos[:2] = self.explorer_pos[:2] + np.dot(K, (self.explorer_pos[:2] - obs_pos))
        self.explorer_pos[:2] = obs_position + np.dot(K, (self.explorer_pos[:2] - obs_position))
        
        # Heading update
        obs_heading = tril_sensor.trilateration_heading()
        if obs_heading is None:
            # Not enough moves in a row to be used.
            return
        obs_heading_variance = np.deg2rad(2) # Arbitrary value chosen. Not sure how to properly determine this.
        K_heading = obs_heading_variance*((obs_heading_variance + self.explorer_cov[2,2])**-1)
        self.explorer_cov[2,2] = obs_heading_variance - (K_heading*obs_heading_variance)
        self.explorer_pos[2] = obs_heading - K_heading*(self.explorer_pos[2] - obs_heading)
    
    def draw(self, cr):
        '''
        Draws all components associated with the Kalman Filter in the RoombaGUI:
        - Explorer
        - Heading
        - Error Ellipse (Not working properly. The center is off and it seems a bit annoying to fix.)
        
        @param cr: Common drawing area object.
        @type cr: Cairo Context  
        '''
        self._draw_explorer(cr)
        self._draw_heading(cr)
        self._draw_error_ellipse(cr)
    
    def _draw_error_ellipse(self, cr):
        '''
        Draws the error ellipse for the 
        
        @param cr: Common drawing area object.
        @type cr: Cairo Context
        '''
        cr.new_path()
        cr.set_line_width(0.4)
        cr.set_source_rgba(0.7, 0, 0, 0.5)
        cr.set_dash([5])
        x_pts, y_pts = self._error_ellipse_points(self.explorer_cov[:2,:2])
        cr.move_to(self.explorer_pos[0], self.explorer_pos[1]-self.explorer_diam)
        for i in range(len(x_pts)):
            cr.rel_line_to(x_pts[i], y_pts[i])
        cr.stroke()
        cr.set_dash([])
        cr.new_path()
            
        
    def _error_ellipse_points(self, C):
        '''
        This code is taken from:
        http://www.mathworks.com/matlabcentral/fileexchange/4705-errorellipse
        error_ellipse
        by AJ Johnson
        01 Apr 2004 (Updated 13 Apr 2004)
        July 21, 2010 (Converted to Python by River Allen)
        
        Generate x and y points that define a covariance ellipse, given a 2x2
        covariance matrix, C.
        
        @param sigma: 2x2 covariance matrix
        @type sigma: numpy.array
        
        @return: x, y points for the ellipse
        @rtype: (np.array(N), np.array(N))
        '''
        n = 100
        p = np.arange(0, 2 * np.pi, 2 * np.pi/n, dtype=np.float64)
        
        #print 'C:', C
        #print 'e', linalg.eig(C), linalg.eigvals(C)
        [eigval,eigvec] = linalg.eig(C)
        if np.any(eigvec) <= 0 or np.any(eigval) <= 0:
            raise RuntimeError, "Non-Definite Covariance Matrix."
                    
        eigval = np.eye(2) * eigval
        #print 'z', eigval
        p_angles = np.array([np.cos(p), np.sin(p)])
        #print 'j', p_angles.T, '\n', np.sqrt(eigval)
        #print 'kaplah:', np.dot(p_angles.T, np.sqrt(eigval))
        xy = np.dot(np.dot(p_angles.T, np.sqrt(eigval)), eigvec.T)
        #print 'xy:', xy
        x = xy[:,0]
        y = xy[:,1]
        return x, y
    
    def _draw_heading_error(self, cr):
        '''
        NOT WORKING. Attempts to draw a sense of current error heading.
        
        
        @param cr: Common drawing area object.
        @type cr: Cairo Context
        '''
        cr.new_path()
        cr.set_line_width(1)
        cr.set_source_rgba(0, 0, 0.5, 0.8)
        cr.move_to(self.explorer_pos[0], self.explorer_pos[1])
        angle = self.explorer_pos[2]
        cr.rel_line_to(self.explorer_diam * np.cos(angle), self.explorer_diam * np.sin(angle))
        cr.stroke()
        cr.new_path()
    
    
    def get_explorer_pos(self):
        '''
        Retrieve the most likely position of the explorer.

        @rtype: numpy.array
        '''
        return self.explorer_pos
    