from scipy import io as sio
import numpy as np
import os

def load_data(path=''):
    if path == '':
        path = '.'
    
    pthjoin = os.path.join
    
    f = sio.loadmat(pthjoin(path, 'translation_model.mat'))
    
    translation_model = f['translation_model']
    translation_data = f['translation_data']
    
    f = sio.loadmat(pthjoin(path, 'rotation_model.mat'))
    
    rotation_model = f['rotation_model']
    rotation_data = f['rotation_data']
    
    f = sio.loadmat(pthjoin(path, 'measurement_model.mat'))
    
    measurement_model = f['measurement_model']
    measurement_data = f['measurement_data']
    
    beacons = np.array([[0,300], [200,300], [0,0]])
    
    return (translation_model, translation_data, rotation_model, 
            rotation_data, measurement_model, measurement_data, beacons)