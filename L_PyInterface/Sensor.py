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
        self.obs = None
        self.color = (0,0,0,0)
        
    def observation(self, obs):
        new_obs = obs - self.mean
        if new_obs < self.threshold[0] or new_obs > self.threshold[1]:
            return self.variance + 10000000 # obs should be ignored (i.e. variance of 1000000)
        self.obs = obs
        return self.variance
            
    def draw(self, cr):
        #raise NotImplementedError, "abstract class"
        pass

class BeaconSensor(Sensor):
    def __init__(self, mean, variance, threshold, x_pos, y_pos):
        super(BeaconSensor, self).__init__(mean, variance, threshold, name='Beacon')
        self.x_pos = x_pos
        self.y_pos = y_pos
        
    def draw(self, cr):
        cr.new_path()
        cr.set_source_rgba(*self.color)
        cr.set_line_width(3)
        beacon_size = 10
        cr.rectangle(self.x_pos-beacon_size/2., self.y_pos-beacon_size/2., beacon_size, beacon_size)
        cr.stroke()

        # Draw Range if available
        if self.obs is not None:
            cr.new_path()
            import numpy as np
            cr.set_line_width(2)
            cr.set_dash([1])
            cr.set_source_rgba(*self.color)
            cr.arc(self.x_pos, self.y_pos, self.obs, 0, 2 * np.pi)
            cr.stroke()
            cr.set_dash([])

        cr.new_path()

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
        self.sensors[-1].color = self._get_color(len(self.sensors))
        
    def _get_color(self, i):
        return ( ((((i+1)*50)%256)/255.), ((((i+1)*200)%256)/255.), ((((i+1)*130)%256)/255.), 0.8 ) 
        
        
if __name__ == '__main__':
    print 'Simple test of Sensor...'
    se = SensorManager([BeaconSensor(1,2,0,300,[0,10000]), BeaconSensor(1,2,200,300,[0,10000])])
    se.add_sensor(BeaconSensor(1,2,0,0,[0,10000]))
    se.add_sensor(CompassSensor(0,5,[0,3599]))
    print se.sensors
    print se.sensors_by_type['Beacon']
    print se.sensors_by_type['Compass']