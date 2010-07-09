'''
Sensor.py
@author: River Allen
@date: July 9, 2010
'''

class Sensor(object):
    def __init__(self, mean, variance, threshold, name='Sensor'):
        self.mean = mean
        self.variance = variance
        self.threshold = threshold
        self.name = name
        
    def observation(self, obs):
        new_obs = obs - self.mean
        if new_obs < self.threshold[0] or new_obs > self.threshold[1]:
            return self.variance + 10000000 # obs should be ignored (i.e. variance of 1000000)
        return self.variance
            
    def draw(self, cr):
        raise NotImplementedError, "abstract class"

class BeaconSensor(Sensor):
    def __init__(self, mean, variance, threshold, x_pos, y_pos):
        super(BeaconSensor, self).__init__(mean, variance, threshold, name='Beacon')
        self.x_pos = x_pos
        self.y_pos = y_pos

class CompassSensor(Sensor):
    def __init__(self, mean, variance, threshold):
        super(CompassSensor, self).__init__(mean, variance, threshold, name='Compass')

class SensorManagerError(Exception):
    pass
    
class SensorManager:
    # @todo: Add a decent __getitem__() method
    def __init__(self, sensors=[]):
        self.sensors = []
        self.sensors_by_type = {}
        for sensor in sensors:
            self.add_sensor(sensor)
        
    def add_sensor(self, sensor):
        if not isinstance(sensor, Sensor):
            raise SensorManagerError, 'Attempted to add non-Sensor.'
        if not self.sensors_by_type.has_key(sensor.name):
            self.sensors_by_type.update({sensor.name:[]})
        self.sensors_by_type[sensor.name].append(sensor)
        
        self.sensors.append(sensor)
    
        
if __name__ == '__main__':
    print 'Simple test of Sensor...'
    se = SensorManager([BeaconSensor(1,2,0,300,[0,10000]), BeaconSensor(1,2,200,300,[0,10000])])
    se.add_sensor(BeaconSensor(1,2,0,0,[0,10000]))
    se.add_sensor(CompassSensor(0,5,[0,3599]))
    print se.sensors
    print se.sensors_by_type['Beacon']
    print se.sensors_by_type['Compass']