'''
KalmanFilter.py
@author: River Allen
@date: 21-06-2010

The Module relating to Kalman Filters.
Contains KalmanFilter obj.
Use getKalmanFilter() for a static KalmanFilter obj
'''
import numpy as np
from numpy import linalg
import Filter
import Sensor # This should be up a level...(Sensor stuff needs to be put somewhere nicer)

global KF
KF = None

class KalmanFilter(Filter.Filter):
    '''
    
    
    '''
    def __init__(self, explorer_pos, explorer_cov):
        super(KalmanFilter, self).__init__(explorer_pos, explorer_cov, 'Extended Kalman Filter')
        
        
    def move(self, transition_vec, transition_cov):
        orig_explorer_pos = self.explorer_pos.copy()
        self.explorer_pos = self.explorer_pos + transition_vec
        
        # 'H' here is not the observation model, but a transformation
        # matrix described by Smith and Cheeseman '86.
        H = np.array([[1, 0,-(self.explorer_pos[1] - orig_explorer_pos[1])], 
                      [0, 1, (self.explorer_pos[0] - orig_explorer_pos[0])], 
                      [0, 0, 1]])
        
        self.explorer_cov = np.dot(np.dot(H, self.explorer_cov), H.T) + transition_cov
        
    def observation(self, obs, sensor):
        if isinstance(sensor, Sensor.BeaconSensor):
            self._observation_beacon(obs, sensor) 
        elif isinstance(sensor, Sensor.CompassSensor):
            self._observation_compass(obs, sensor)
    
    def _observation_beacon(self, obs, sensor):
        '''
        Run EKF update phase for beacon sensor.

        Run a modified Update Phase Kalman Filter
        This is based off how it was done in:
            Preliminary Results in Range Only Localization and Mapping
            George Kantor + Sanjiv Singh
        
        '''
        b_angle = np.arccos((sensor.x_pos - self.explorer_pos[0])/obs)
        x_obs_pos = sensor.x_pos - ((obs)*np.cos(b_angle))
        y_obs_pos = sensor.y_pos - ((obs)*np.sin(b_angle))
        
        
        obs_pos = np.array([x_obs_pos, y_obs_pos])
        obs_cov = sensor.observation(obs)
        R = np.array([[obs_cov, 0], [0, 10 * obs_cov]])
        
        #print 'OBS Variance:', R
        
        K = np.dot(R, linalg.inv((R + self.explorer_cov[:2,:2])))
        self.explorer_cov[:2,:2] = R - np.dot(K, R)
        #self.explorer_pos[:2] = obs_pos + np.dot(K, (self.explorer_pos[:2] - obs_pos))
        
    
    def _observation_compass(self, obs, sensor):
        '''
        
        '''
        raise NotImplementedError
    
    def draw(self, cr):
        '''
        
        '''
        self._draw_explorer(cr)
        self._draw_heading(cr)
        #self._draw_error_ellipse(cr)
    
    def _draw_error_ellipse(self, cr):
        '''
        
        '''
        cr.new_path()
        cr.set_line_width(0.4)
        cr.set_source_rgba(0.7, 0, 0, 0.5)
        cr.set_dash([5])
        x_pts, y_pts = self._error_ellipse_points(self.explorer_cov[:2,:2])
        cr.move_to(self.explorer_pos[0], self.explorer_pos[1])
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
    
    def get_explorer_pos(self):
        return self.explorer_pos
    
    def step(self, X, P, F, H, B, Q, R, u, z):
        '''
        See the Wikipedia article on the Kalman Filter. 
        This function is essentially the Kalman Filter.
        
        First, the prediction phase is computed.
            Xk|k-1 = F*Xk-1 + B*u
            ...
        Second, the update phase is computed.
            ...
            ...
            ...
            ...
        Finally, the results of the update phase are returned.
        
        @param X: The mean vector describing state at k-1 (last state). For example, in a 2-D system this might
        encompass [x, y, vx, vy] where vx and vy are the velocities for x and y.
        @type X: Vector or 1-D matrix/list [n x 1]
        @param P: The filter's covariance matrix at state k-1.
        @type P: Matrix [n x n]
        @param F: The Transition model at state k. This your motion model. When this is
        multiplied against X, it should create a new X that describes your movement. For example,
        
        F =[1 0 t 0;
            0 1 0 t;
            0 0 1 0;
            0 0 0 1]
        
        
        @return: X (Current state vector) and P (current covariance matrix).
        @rtype: Tuple [X, P]
        '''
        # Prediction Phase
        X = np.dot(F, X) + np.dot(B, u)
        P = np.dot(np.dot(F, P), F.T) + Q
        
        # Update Phase
        # Measurement Residual
        y = z - np.dot(H, X)
        # Measurement cov
        S = np.dot(np.dot(H, P), H.T) + R      
        #  Optimal Kalman gain
        K = np.dot(np.dot(P, H.T), (linalg.inv(S)))
        #  Updated state estimate
        X = X + np.dot(K, y)       
        d = X.shape[0]
        #  Updated state cov
        P = np.dot((np.eye(d) - np.dot(K, H)), P)
        
        return X, P

    def modified_prediction_phase(self, X, P, Q, B, u):
        '''
        Modified KF Prediction Phase taken from
        Singh / Kantor 2002 paper.
        Smith / Cheeseman 1986 paper.
        
        '''
        theta = X[2];
        transform = np.array([[np.cos(theta), -np.sin(theta), 0], 
                              [np.sin(theta), np.cos(theta), 0],
                              [0, 0, 1]])
    
        control_vector = np.dot(transform, u.T)
    
        transition_cov = np.dot(np.dot(transform, Q), transform.T)
        orig_explorer_pos = X
        explorer_pos = X + control_vector
        
        # 'H' here is not the observation model, but a transformation
        # matrix described by smith and cheeseman.
        H = np.array([[1, 0, -(explorer_pos[1] - orig_explorer_pos[1])], 
             [0, 1, (explorer_pos[0] - orig_explorer_pos[0])], 
             [0, 0, 1]])
        
        explorer_cov = np.dot(np.dot(H, P), H.T) + transition_cov
    
        return (explorer_pos, explorer_cov)
        
    def modified_update_phase(self, X, P, R, z):
        '''
        Run a modified Update Phase Kalman Filter
        This is based off how it was done in:
            Preliminary Results in Range Only Localization and Mapping
            George Kantor + Sanjiv Singh
        
        '''
        
        K = np.dot(R, linalg.inv((R + P)))
        P = R - np.dot(K, R)
        X = z + np.dot(K, (X - z))
        
        return X, P

def getKalmanFilter():
    '''
    Return a static Kalman Filter Object. This should be used over creating a separate one, 
    unless a separate, unique KF is desired.
    
    @return: Static KF
    @rtype: KalmanFilter
    '''
    global KF
    if KF is None:
        KF = KalmanFilter()
    return KF
    