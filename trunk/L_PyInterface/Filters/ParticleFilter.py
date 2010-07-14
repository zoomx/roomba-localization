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
    def __init__(self, explorer_pos=[], explorer_cov=[], total_particles=1000):
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
            transition_sample = util.mvnrnd(transition_vec, transition_cov)
            # Xk(L) = p(Xk-1(L),yk) // ignoring the ',yk' for now
            self.particles[L,:] = self.particles[L,:] + transition_sample
        
        
    def observation(self, obs, sensor):
        if isinstance(sensor, Sensor.BeaconSensor):
            self._observation_beacon(obs, sensor) 
        elif isinstance(sensor, Sensor.CompassSensor):
            self._observation_compass(obs, sensor)
        
        
    def _observation_beacon(self, obs, beacon):
        #=======================================================================
        # Weight samples against observation model
        #=======================================================================
        # This could potentially be optimized
        for L in range(self.total_particles):
            # ~wk(L) = wk-1(L) * p(yk|xk(L))
            # In other words, compute a new weight based on the particles
            # current normalized weight, and the probability of the 
            # evidence (yk|observation) given the current state 
            # (xk(L)|particle(L)).
            distance = np.sqrt((beacon.x_pos-self.particles[L,0])**2 + (beacon.y_pos-self.particles[L,1])**2)
            dis_error = obs - distance
            self.weight[L] = self.weight[L] * stats.norm.pdf(dis_error, beacon.mean, beacon.variance)
        
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
            index_set = []
            # Copy size-> can this be optimized?
            new_particles = np.zeros([self.total_particles, 3])
            # Now resample...
            for p in range(self.total_particles):
                # Sample from our weights 
                index = util.sample_from_dist(self.weight)
                #index_set = unique( [index_set index])
                new_particles[p,:] = self.particles[index,:]

            #index_set = unique( index );
            self.particles[index_set,:]
            self.particles = new_particles
    
    def _observation_compass(self, observation, compass):
        raise NotImplementedError
    
    def get_explorer_pos(self):
        return self.particles.mean(axis=0)
    
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
        for part in self.particles:
            cr.move_to(part[0], part[1])
            cr.rel_line_to(0.1, 0.1)
            cr.stroke()
        self.explorer_pos = self.get_explorer_pos()
        self._draw_explorer(cr)
        self._draw_heading(cr)
        
    
def getParticleFilter():
    global pf
    if pf is None:
        pf = ParticleFilter()
    return pf
