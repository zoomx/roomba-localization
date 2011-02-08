'''
models.py
@author: River Allen
@date: May 27, 2010

A convenience module for dealing with motion and measurement model data.
'''

from scipy import io as sio # Load matlab/octave files
import numpy as np # For beacons 
import os # File manipulation

def load_data(path=''):
    '''
    A convenience function for loading the various motion and measurement
    models.
    
    @param path: Filesystem path where models are located. Default, path 
    will be current directory.
    @type path: str
    
    @return: (translation_model, translation_data, rotation_model, 
            rotation_data, measurement_model, measurement_data, beacons)
    @rtype: tuple of numpy.arrays
    '''
    if path == '':
        path = '.'
    
    pthjoin = os.path.join # For convenience...
    
    f = sio.loadmat(pthjoin(path, 'eow_tran_mod.mat'))
    #f = sio.loadmat(pthjoin(path, 'translation_model.mat'))
    translation_model = f['translation_model']
    translation_data = f['translation_data']
    
    f = sio.loadmat(pthjoin(path, 'eow_rot_mod.mat'))
    #f = sio.loadmat(pthjoin(path, 'rotation_model.mat'))
    rotation_model = f['rotation_model']
    rotation_data = f['rotation_data']
    
    f = sio.loadmat(pthjoin(path, 'measurement_model.mat'))
    measurement_model = f['measurement_model']
    measurement_data = f['measurement_data']
    
    beacons = np.array([[100,500], [227,400], [300,-30]])
    
    return (translation_model, translation_data, rotation_model, 
            rotation_data, measurement_model, measurement_data, beacons)