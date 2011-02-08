'''
ParticleFilter.py
@author: River Allen
@date: June 21, 2010

The Module relating to a vanilla Particle Filter.
This particle filter may be written a little to specifically for your
desired problem domain. If so, change it or create a new Filter.Filter and add it
to the FilterManager. 

Use getParticleFilter() for a static ParticleFilter obj
'''
import numpy as np
import scipy.stats as stats
import util
import Filter
import Sensor

global pf
pf = None


class ParticleFilter(Filter.Filter):
    '''
    This was designed in haste and will hopefully be cleaned up in the future.
    
    '''
    
    #@todo: Get rid of defaults, except for total_particles once everything works...
    # implies the wrong thing.
    def __init__(self, explorer_pos=[], explorer_cov=[], total_particles=250):
        '''
        Does nothing for now.
        '''
        super(ParticleFilter, self).__init__(explorer_pos, explorer_cov, name='Vanilla Particle Filter')
        self.total_particles = total_particles

        if explorer_pos is not []:
            self.generateParticles(total_particles, explorer_pos, explorer_cov)
            self.weight = self.equal_weight(self.total_particles)
        

    def generateParticles(self, N, mean, covariance): 
        '''
        
        '''
        particles = np.zeros([N, 3])
        for i in range(N):
            particles[i,:] = util.mvnrnd(mean, covariance)
        self.particles = particles
        return particles
    
    def move_particles(self, particles, transition_vec, transition_cov):
        '''
        
        '''
        num_of_particles = particles.shape[0]
        for L in range(num_of_particles):
            transition_sample = util.mvnrnd(transition_vec, transition_cov)
            # Xk(L) = p(Xk-1(L),yk) // ignoring the ',yk' for now
            particles[L,:] = particles[L,:] + transition_sample
        return particles
    
    def move(self, transition_vec, transition_cov):
        for L in range(self.total_particles):
            p_move_vec, p_move_cov = util.affine_transform(self.particles[L][2], transition_vec, transition_cov)
            transition_sample = util.mvnrnd(p_move_vec, p_move_cov)
            # Xk(L) = p(Xk-1(L),yk) // ignoring the ',yk' for now
            self.particles[L,:] = self.particles[L,:] + transition_sample
            #self.particles[L,2] = self.particles[L,2] % (2 * np.pi)
        
    def _observation_beacon(self, obs, beacon):
        #=======================================================================
        # Weight samples against observation model
        #=======================================================================
        # This could potentially be optimized
        self.weight = self.equal_weight(self.total_particles)
        for L in range(self.total_particles):
            # ~wk(L) = wk-1(L) * p(yk|xk(L))
            # In other words, compute a new weight based on the particles
            # current normalized weight, and the probability of the 
            # evidence (yk|observation) given the current state 
            # (xk(L)|particle(L)).
            distance = np.sqrt((beacon.x_pos-self.particles[L,0])**2 + (beacon.y_pos-self.particles[L,1])**2)
            dis_error = obs - distance
            self.weight[L] = self.weight[L] * stats.norm.pdf(dis_error, beacon.mean, beacon.observation(obs))
        
        self._resample()
        
    
    
    def _observation_compass(self, obs_heading, compass):
        '''
        obs_variance = compass.observation(obs_heading)
        k = obs_variance * 1./(obs_variance + self.explorer_cov[2,2])
        self.explorer_cov[2,2] = obs_variance - (k * obs_variance)
        self.explorer_pos[2] = obs_heading + (k * (self.explorer_pos[2] - obs_heading))
        self.explorer_pos[2] = self.explorer_pos[2] % (2*np.pi)
        '''
        
        for L in range(self.total_particles):
            # ~wk(L) = wk-1(L) * p(yk|xk(L))
            # In other words, compute a new weight based on the particles
            # current normalized weight, and the probability of the 
            # evidence (yk|observation) given the current state 
            # (xk(L)|particle(L)).
            heading_error = obs_heading - self.particles[L][2]
            self.weight[L] = self.weight[L] * stats.norm.pdf(heading_error, compass.mean, compass.observation(obs_heading))
        
        self._resample()
    
    def _observation_trilateration(self, beacons, tril_sensor):
        obs_variance = tril_sensor.observation(None)
        obs_position = tril_sensor.trilateration(beacons, self.get_explorer_pos())
        if np.any(map(np.isnan, obs_position)):
            # If is testing if any of the values are nan.
            # Bug that can occur when ranges don't intersect, hacky fix (apologies).
            tril_sensor._pos_history = []
            return
        
        self.weight = self.equal_weight(self.total_particles)
        
        # Heading update
        obs_heading = tril_sensor.trilateration_heading()
        obs_heading_variance = np.deg2rad(2) # Arbitrary value chosen. Not sure how to properly determine this.
        for L in range(self.total_particles):
            # ~wk(L) = wk-1(L) * p(yk|xk(L))
            # In other words, compute a new weight based on the particles
            # current normalized weight, and the probability of the 
            # evidence (yk|observation) given the current state 
            # (xk(L)|particle(L)).
            dis_error = np.hypot(obs_position[0] - self.particles[L][0], obs_position[1] - self.particles[L][1]) 
            self.weight[L] = self.weight[L] * stats.norm.pdf(dis_error, 0, obs_variance[0][0])
            if obs_heading is not None:
                heading_error = self.particles[L][2] - obs_heading
                self.weight[L] = self.weight[L] * stats.norm.pdf(heading_error, 0, obs_heading_variance)
        
        self._resample()
    
    def _resample(self):
        #=======================================================================
        # Resample
        #=======================================================================
        # Normalize
        weightSum = np.sum(self.weight)
        self.weight = self.weight / weightSum

        # Estimate Neff (Effective number of samples)
        Neff =  1 / np.sum(self.weight ** 2)

        # Do we need to resample?
        if Neff < self.total_particles:
            #index_set = []
            # Copy size-> can this be optimized?
            new_particles = np.zeros([self.total_particles, 3])
            # Now resample...
            for p in range(self.total_particles):
                # Sample from our weights 
                index = util.sample_from_dist(self.weight)
                #index_set = unique( [index_set index])
                new_particles[p,:] = self.particles[index,:]

            #index_set = unique( index );
            #self.particles[index_set,:]
            self.particles = new_particles
    
    def get_explorer_pos(self):
        #print 'PF168: (PARTICLES VARIANCE):', self.particles.var(axis=0)
        return self.particles.mean(axis=0)
        #return np.average(self.particles, axis=0, weights=self.weight)
    
    def equal_weight(self, N):
        '''
        
        '''
        return (np.ones(N, dtype=np.float64) * 1/float(N)) # Equal weight for all samples
    

    def weight_particles(self, weight, particles, x_beacon, y_beacon, z, mu, sigma):
        '''
        
        '''
        total_particles = particles.shape[0]
        
        # Weight samples against observation model
        # This could potentially be optimized
        for L in range(total_particles):
            # ~wk(L) = wk-1(L) * p(yk|xk(L))
            # In other words, compute a new weight based on the particles
            # current normalized weight, and the probability of the 
            # evidence (yk|observation) given the current state 
            # (xk(L)|particle(L)).
            distance = np.sqrt((x_beacon-particles[L,0])**2 + (y_beacon-particles[L,1])**2)
            dis_error = z - distance
            weight[L] = weight[L] * stats.norm.pdf(dis_error, mu, sigma)
        return weight
    
    def SIR(self, weight, particles):
        '''
        
        '''
        total_particles = particles.shape[0]
        # Normalize
        weightSum = np.sum(weight)
        weight = weight / weightSum

        # Estimate Neff (Effective number of samples)
        Neff =  1 / np.sum(weight ** 2)

        # Do we need to resample?
        if Neff < total_particles:
            index_set = []
            # Copy size-> can this be optimized?
            new_particles = np.zeros([total_particles, 3])
            # Now resample...
            for p in range(total_particles):
                # Sample from our weights 
                index = util.sample_from_dist(weight)
                #index_set = unique( [index_set index])
                new_particles[p,:] = particles[index,:]

            #index_set = unique( index );
            particles[index_set,:]
            particles = new_particles
        
        return particles
    
    def draw(self, cr):
        cr.set_line_width(2)
        cr.set_source_rgba(0.4, 0, 0, 0.3)
        #'''
        for part in self.particles:
            cr.move_to(part[0], part[1])
            cr.rel_line_to(0.1, 0.1)
            cr.stroke()
        #'''
        print 'D.PF.237: Draw'
        self.explorer_pos = self.get_explorer_pos()
        #self._draw_explorer(cr)
        self._draw_heading(cr)
        
    
def getParticleFilter():
    global pf
    if pf is None:
        pf = ParticleFilter()
    return pf
