'''
KalmanFilter.py
River Allen
21-06-2010

The Module relating to Kalman Filters.
Contains KalmanFilter obj.
Use getKalmanFilter() for a static KalmanFilter obj
'''
import numpy as np
from numpy import linalg
import Filter


global KF
KF = None

class KalmanFilter(Filter.Filter):
    '''
    
    
    '''
    
    def __init__(self, explorer_pos, explorer_cov):
        super(KalmanFilter, self).__init__(explorer_pos, explorer_cov, 'Extended Kalman Filter')
        
        
    def move(self, transition_vec, transition_cov):
        
        
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
    