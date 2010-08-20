'''
Sensor.py
@author: River Allen
@date: July 9, 2010
'''
import Queue

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

class Trilateration2DSensor(Sensor):
    def __init__(self, mean, variance, threshold):
        super(Trilateration2DSensor, self).__init__(mean, variance, threshold, name='Trilateration2D')
        self._pos_history = []
        self._pos_history_size = 4 # only keep this many records.

    def trilateration(self, beacons, pos):
        '''
        Performs 2-D trilateration.
        
        Essentially solving:
        
        R1^2 = x^2 + y^2
        R2^2 = x^2 + (y-d)^2
        (if there is more than 2 beacons...)
        R3^2 = (x-a)^2 + (y-b)^2
        
        Thus,
        y = ((d^2)/2*d) + R2 - R1
        
        2 beacons -->
        x^2 + y^2 - R1 = 0
        x = (-sqrt(y^2 - R1), sqrt(y^2 - R1))
        
        3 beacons -->
        x = (a^2 + (y - b)^2 - y - R3 + R1) / 2*a
        
        Will return a value for the closer position if there are only two observations.
        '''
        import numpy as np
        observations = []
        for beacon in beacons:
            observations.append(beacon.obs)
        
        if len(observations) < 2:
            raise ValueError, "2D Trilateration requires at least 2 observations."
        
        # Convert to a local coordinate system to solve the intersection points
        # @todo: Optimize: include a way for the sensor manager to cache this, so it is not
        # computed every time trilateration is called.
        # Make the first beacon the origin.
        origin_pos = (beacons[0].x_pos, beacons[0].y_pos)
        print 'Debug, Origin Pos:', origin_pos
        
        local_beacon_positions = []
        for i in range(len(beacons)):
            local_beacon_positions.append([beacons[i].x_pos-origin_pos[0], beacons[i].y_pos-origin_pos[1]])
        
        print 'Debug, local_beacon_position:', local_beacon_positions
        
        # Find the angle to rotate the beacon points such that beacon 2's local_x_pos = 0. This allows
        # us to solve R1 - R2.
        b2_hyp = np.hypot(local_beacon_positions[1][0], local_beacon_positions[1][1])
        
        # We want the second beacon to be at position (0, b2_hyp). To use the cosine rule, we need
        # to find the distance between this beacon's new point and the beacon's current point.
        b2_diff_hyp = np.hypot(local_beacon_positions[1][0], (local_beacon_positions[1][1]-b2_hyp))
        print 'Debug, hyp:', b2_hyp, b2_diff_hyp
        
        # Cosine Rule
        rotation_angle = np.arccos((2*((b2_hyp)**2) - (b2_diff_hyp**2))/(2*(b2_hyp**2)))
        print 'Debug, rotation angle:', rotation_angle, np.rad2deg(rotation_angle)
        for i in range(1, len(local_beacon_positions)):
            # Rotate counter-clockwise about origin
            x, y = local_beacon_positions[i]
            print 'Debug:', x, y
            print 'Debug:', local_beacon_positions
            local_beacon_positions[i][0] = (x * np.cos(rotation_angle)) - (y * np.sin(rotation_angle))
            local_beacon_positions[i][1] = (x * np.sin(rotation_angle)) + (y * np.cos(rotation_angle))
        
        print 'Debug, local_positions:', local_beacon_positions
        
        # Now we solve:
        R1_sq = observations[0] ** 2 
        R2_sq = observations[1] ** 2
        d = local_beacon_positions[1][1]
        y = (d**2 + R1_sq - R2_sq) / (2*d)
        if len(observations) == 2:
            print 'Debug, y, d, R1, R2:', y, d, np.sqrt(R1_sq), np.sqrt(R2_sq)
            x1 = -np.sqrt(R1_sq - y**2)
            x2 = np.sqrt(R1_sq - y**2)
            print 'Debug, x1 and x2:', x1, x2
            possible_positions = [[x1, y], [x2, y]]
            #Convert b
        else:
            # Can return a position without needing position.
            R3_sq = observations[2] ** 2
            a = local_beacon_positions[2][0]
            b = local_beacon_positions[2][1]
            x = (a**2 + (y-b)**2 - y**2 - R3_sq + R1_sq) / (2*a)
            possible_positions = [[x,y]]
            # x = (a^2 + (y - b)^2 - y - R3 + R1) / 2*a
        
        for i in range(len(possible_positions)):
            # convert positions
            x = possible_positions[i][0]
            y = possible_positions[i][1]
            possible_positions[i][0] = (x*np.cos(rotation_angle)) + (y*np.sin(rotation_angle)) + origin_pos[0]
            possible_positions[i][1] = (-x*np.sin(rotation_angle)) + (y*np.cos(rotation_angle)) + origin_pos[1]
            
        print 'Debug, Possible positions:', possible_positions
        
        if len(possible_positions) > 1:
            # Select the one closer to possible position that is closest to pos.
            hyp1 = np.hypot((pos[0] - possible_positions[0][0]), (pos[1] - possible_positions[0][1]))
            hyp2 = np.hypot((pos[0] - possible_positions[1][0]), (pos[1] - possible_positions[1][1]))
            if hyp1 <= hyp2:
                ret_pos = possible_positions[0]
            else:
                ret_pos = possible_positions[1]
        else:
            ret_pos = possible_positions[0]
    
        self._pos_history.append(ret_pos)
        if len(self._pos_history) > self._pos_history_size:
            self._pos_history.pop(0)
        return ret_pos
    
    def trilateration_heading(self):
        import numpy as np
        return None
        if len(self._pos_history) < 2:
            return None

        # Some sort of sophisticated smoothing algorithm could be put here, for now just use
        # the last and current position to determine an approximate heading.
        positions = self._pos_history[-2:]
        possible_heading = np.arctan2(positions[1][1] - positions[0][1], positions[1][0] - positions[0][0])
        
        return possible_heading
    
    def observation(self, obs):
        return self.variance


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
    import numpy as np
    '''
    se = SensorManager([BeaconSensor(1,2,0,300,[0,10000]), BeaconSensor(1,2,200,300,[0,10000])])
    se.add_sensor(BeaconSensor(1,2,0,0,[0,10000]))
    se.add_sensor(CompassSensor(0,5,[0,3599]))
    print se.sensors
    print se.sensors_by_type['Beacon']
    print se.sensors_by_type['Compass']
    '''
    # Test Trilateration
    tri = Trilateration2DSensor(0, np.eye(2) * 3, None)
    # o (-10, 15)    x (45, 15)     o (113, 15)
    pos = (45, 15)
    beac1 = BeaconSensor(0, 3, [1, 1000], -10, 15)
    beac1.obs = 55
    beac2 = BeaconSensor(0, 3, [1, 1000], 113, 15)
    beac2.obs = 68
    #new_pos = tri.trilateration([beac1, beac2], pos)
    #print 'Trilateration Position(%s):' %str(pos), new_pos
    
    #                            o (113, 48)
    # o (-10, 15)         
    #                    x (47, -25)
    pos = (47, -25)
    beac1 = BeaconSensor(0, 3, [1, 1000], -10, 15)
    beac1.obs = np.hypot(pos[0] - beac1.x_pos, pos[1] - beac1.y_pos)
    beac2 = BeaconSensor(0, 3, [1, 1000], 113, 48)
    beac2.obs = np.hypot(pos[0] - beac2.x_pos, pos[1] - beac2.y_pos)
    #new_pos = tri.trilateration([beac1, beac2], pos)
    #print 'Trilateration Position(%s):' %str(pos), new_pos
    
    #                            o (113, 48)
    # o (-10, 15)                         o (150, 20)
    #                    x (47, -25)
    beac3 = BeaconSensor(0, 3, [1, 1000], 150, 20)
    beac3.obs = np.hypot(pos[0] - beac3.x_pos, pos[1] - beac3.y_pos)
    new_pos = tri.trilateration([beac1, beac2, beac3], pos)
    print 'Trilateration Position(%s):' %str(pos), new_pos
    
    # Test trilateral heading
    pos = (47, 30)
    beac1.obs = np.hypot(pos[0] - beac1.x_pos, pos[1] - beac1.y_pos)
    beac2.obs = np.hypot(pos[0] - beac2.x_pos, pos[1] - beac2.y_pos)
    beac3.obs = np.hypot(pos[0] - beac3.x_pos, pos[1] - beac3.y_pos)
    new_pos = tri.trilateration([beac1, beac2, beac3], pos)
    print 'Trilateration Position(%s):' %str(pos), new_pos
    new_angle = tri.trilateration_heading()
    print 'New heading:', new_angle, np.rad2deg(new_angle)
    
    