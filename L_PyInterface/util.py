
def affine_transform(angle, vec, covar):
    '''
    
    '''
    import numpy as np
    transform = np.array([[np.cos(angle), -np.sin(angle), 0], [np.sin(angle), np.cos(angle), 0],
                          [0, 0, 1]])
    if vec.shape == (2,) and covar.shape == (2,2):
        transform = transform[:2,:2]
    transition_vec = np.dot(transform, vec)
    transition_cov = np.dot(np.dot(transform, covar), transform.T)
    return transition_vec, transition_cov


def error(val1, val2):
    return abs(val1 - val2)


def mvnrnd(mu, Sigma):
    '''
    function s = mvnrnd( mu,Sigma)
            nxd         nxd  dxd
    Draw n random d-dimensional vectors from a multivariate Gaussian distribution
    with mean mu and covariance matrix Sigma.
    
    Iain Murray 2003 -- I got sick of this simple thing not being in Octave and
                        locking up a stats-toolbox license in Matlab for no good
                        reason.
    River Allen 2010 -- Converted to Python.
    '''
    import numpy as np
    from numpy.random import randn
    from numpy import linalg
    from random import random
    
    d = mu.T.shape[0]
    if Sigma.shape != (d,d):
        raise 'Sigma must have dimensions dxd where mu is nxd.'
    
    try:
        U = linalg.cholesky(Sigma).T
    except:
        E, Lambda = linalg.eig(Sigma)
        if (min(np.diag(Lambda)) < 0):
            raise 'Sigma must be positive semi-definite.'
        U = np.dot(np.sqrt(Lambda), E.T)
    
    s = np.dot(randn(1,d), U) + mu
    return s
    
    # Explanation (by original author):
    # 
    # We can draw from axis aligned unit Gaussians with randn(d)
    #     x ~ A*exp(-0.5*x'*x)
    # We can then rotate this distribution using
    #     y = U'*x
    # Note that
    #     x = inv(U')*y
    # Our new variable y is distributed according to:
    #     y ~ B*exp(-0.5*y'*inv(U'*U)*y)
    # or
    #     y ~ N(0,Sigma)
    # where
    #     Sigma = U'*U
    # For a given Sigma we can use the chol function to find the corresponding U,
    # draw x and find y. We can adjust for a non-zero mean by just adding it on.
    # 
    # But the Cholsky decomposition function doesn't always work...
    # Consider Sigma=[1 1;1 1]. Now inv(Sigma) doesn't actually exist, but Matlab's
    # mvnrnd provides samples with this covariance st x(1)~N(0,1) x(2)=x(1). The
    # fast way to deal with this would do something similar to chol but be clever
    # when the rows aren't linearly independent. However, I can't be bothered, so
    # another way of doing the decomposition is by diagonalising Sigma (which is
    # slower but works).
    # if
    #     [E,Lambda]=eig(Sigma)
    # then
    #     Sigma = E*Lambda*E'
    # so
    #     U = sqrt(Lambda)*E'
    # If any Lambdas are negative then Sigma just isn't even positive semi-definite
    # so we can give up.
    # }}}

def sample_from_dist(weight):
    '''
    Not written by me (probably Dimitri or Yannis). Converted from matlab to
    python 2010 by River Allen.
    
    Return the index of a sample from a distribution weight.
    
    @param weight: A normalized array of weights (or probabilites)
    @type weight: numpy.array

    @return: The sample index from weight
    @rtype: int 
    '''
    from random import random
    p = random() # A number between 0 and 1 
    probsum = 0
    for i in range(weight.shape[0]):
        probsum = probsum + weight[i]
        if (p < probsum):
            return i

