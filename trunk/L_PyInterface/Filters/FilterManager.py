'''
FilterManager.py
@author: River Allen
@date: July 7, 2010
'''

import Filter, KalmanFilter, ParticleFilter
from warnings import warn

import threading
import Sensor
import numpy as np


class FilterManagerException(Exception):
    pass

class FilterManager():
    def __init__(self, origin_pos, origin_cov, use_obs=True, 
                 run_kf=True, run_pf=True, total_particles=1000):
        self._filters = {}
        
        # Do not observe()
        self.use_obs = use_obs
        
        if run_pf:
            self.add_filter(ParticleFilter.ParticleFilter(origin_pos, origin_cov))
        if run_kf:
            self.add_filter(KalmanFilter.KalmanFilter(origin_pos, origin_cov))
        
        if self._filters is {}:
            warn('No Filters are running.')
    
    def add_filter(self, filt):
        if not isinstance(filt, Filter.Filter):
            raise FilterManagerException, 'Attempted to add non-Filter.'
        self._filters.update({filt.name:filt})
    
    def get_draw(self):
        draw_methods = {}
        for filt in self._filters.values():
            draw_methods.update({filt.name:filt.draw})
        return draw_methods
    
    def move(self, transition_vec, transition_cov):
        for filt in self._filters.values():
            filt.move(transition_vec, transition_cov)
    
    def observation(self, obs, sensor):
        if not self.use_obs:
            return
        for filt in self._filters.values():
            filt.observation(obs, sensor)

    def get_explorer_pos_mean(self):
        pos = []
        for filt in self._filters.values():
            pos.append(filt.get_explorer_pos())
        
        mean_pos = np.array(pos).mean(axis=0)
        return mean_pos

class TestGUI():
    
    def delete_event(self, widget, data=None):
        print 'Exit GUI!'
        return False

    def destroy(self, widget, data=None):
        import gtk
        gtk.main_quit()
    
    def _update_clock(self):
        self.window.queue_draw()
        return True
    
    def __init__(self, filter_draw_methods):
        import pygtk
        import cairo
        import gtk
        import gobject
        
        self.init_pos = [50, 475]
        self.transform_mat = cairo.Matrix(1.5, 0, 0, -1.5, self.init_pos[0], self.init_pos[1])
        
        self._filter_draw_methods = filter_draw_methods
        self._draw_methods = []
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        
        self.window.connect('delete_event', self.delete_event)
        self.window.connect('destroy', self.destroy)
        self.window.set_title('Roomba Localization')
        self.window.set_size_request(500, 600)

        self.area = gtk.DrawingArea()
        self.area.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        
        self.area.connect("expose-event", self._expose_cb)
        self.area.connect('button_press_event', self._click_cb)
        
        self.map_frame = gtk.Frame('Map')
        self.map_frame.add(self.area)
        
        #self.window.add(self.area)
        self.window.add(self.map_frame)
        self.window.show_all()
        
        self._click_positions = []
        
        gobject.timeout_add(500, self._update_clock)
    
    def add_draw_method(self, meth):
        self._draw_methods.append(meth)
    
    def _click_cb(self, widget, event):
        import cairo
        cr = widget.window.cairo_create()
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.transform(self.transform_mat)
        #print 'Device Click Coords', event.get_coords()
        self._click_positions.append(cr.device_to_user(*event.get_coords()))
        #print 'Local Click Coords', self._click_positions
        #print self.click_positions
        
    def _expose_cb(self, widget, event):
        import cairo
        
        cr = widget.window.cairo_create()
        cr.set_operator(cairo.OPERATOR_SOURCE)
        #cr.translate(*self.init_pos)
        #cr.scale(1.5, 1.5)
        cr.transform(self.transform_mat)
        #cr.paint()
        
        self._draw_map(cr)
        
        for draw_meth in self._draw_methods:
            draw_meth(cr)
        
        for draw_meth in self._filter_draw_methods.values():
            draw_meth(cr)
        
        

    def _draw_map(self, cr):
        # Draw grid
        grid_lims = [200, 300]
        box_size = 25
        
        cr.set_source_rgba(0.7, 1.0, 0.3, 0.5)
        #cr.arc(50, 50, 10, 0, 2*3.1415)
        
        for x in range(grid_lims[0]/box_size):
            for y in range(grid_lims[1]/box_size):
                cr.rectangle(x * box_size, y * box_size, box_size, box_size)
        
        #cr.fill()
        cr.stroke()
        
    def get_click_positions(self):
        ret_pos = self._click_positions
        self._click_positions = []
        return ret_pos
    
    def mainloop(self):
        import gtk
        gtk.main()

class TestThread(threading.Thread):
    def __init__(self, fm, tg, auto=False):
        super(TestThread, self).__init__()
        self.fm = fm
        # Need the Gui in order to get the click positions...
        self.tg = tg
        self.quit = False
        self.auto = auto
        
    def _auto_run(self):
        from Data import models
        import os
        from numpy.random import randn
        pthjoin = os.path.join
        
        (translation_model, translation_data, rotation_model, 
         rotation_data, measurement_model, measurement_data, beacons) = models.load_data(pthjoin('Data','001'))
    
        # Kluge fix --  need to fix the .mat file
        measurement_model = measurement_model[0]
        
        total_beacons = beacons.shape[0]
        
        # Move Straight: Vector based on Motion Model measurements
        #translation_vec = [dist_hypot, dist_hypot, translation_model[2,0]]
        translation_vec = translation_model[:,0]
        translation_cov = np.cov(translation_data.T)
        
        # Turn: Vector based on Motion Model measurements
        left_rotation_vec = rotation_model[:,0]
        right_rotation_vec = rotation_model[:,0] * -1
        
        # May want to change this. This is a guess to get it working.
        # Playing around with cov(rotation_data) may lead to better results.
        rotation_cov = np.zeros([3,3])
        rotation_cov[2,2] = rotation_model[2,1]
        
        still_vec = np.array([0, 0, 0])
        still_cov = np.zeros([3,3])
        
        turn_leniency = np.deg2rad(10) # Used as an error judgement for deciding when to turn
        
        moves = []
        
        explorer_pos = self.fm.get_explorer_pos_mean()
        while True:
            if self.quit:
                print 'Exiting Thread!'
                return # Defaults -- Do not move.
            transition_vec = still_vec
            transition_cov = still_cov
            
            movement_type = 0 #0 - still, 1 - straight, 2 - left, 3 - right
            
            #print 'explorer_pos', explorer_pos
            
            if (explorer_pos[0] >= 100 and explorer_pos[1] <= 100 and abs((explorer_pos[2] % (2*np.pi)) - np.pi/2) > turn_leniency):
                # Bottom Right Corner
                #print 'BR'
                movement_type = 2
            elif (explorer_pos[0] >= 100 and explorer_pos[1] >= 200 and abs((explorer_pos[2] % (2*np.pi)) - np.pi) > turn_leniency):
                # Top Right Corner
                #print 'TR'
                movement_type = 2
            elif (explorer_pos[0] <= 100 and explorer_pos[1] >= 200 and abs((explorer_pos[2] % (2*np.pi)) - (3*np.pi)/2) > turn_leniency):
                # Top Left Corner
                #print 'TL'
                movement_type = 2
            # Slight error here: can only turn if angle is greater than or equal to zero    
            elif (explorer_pos[0] <= 100 and explorer_pos[1] <= 100 and abs((explorer_pos[2] % (2*np.pi)) - 0) > turn_leniency):
                # Bottom Left Corner
                #print 'BL'
                movement_type = 2
            else:
                # Straight
                movement_type = 1
                
            moves.append(movement_type) # Keep track of moves taken
            
            if movement_type == 1:
                # Drive Straight
                transition_vec = translation_vec
                transition_cov = translation_cov
            elif  movement_type == 2:
                # Rotate Left
                transition_vec = left_rotation_vec
                transition_cov = rotation_cov
            elif movement_type == 3:
                # Rotation Right
                transition_vec = right_rotation_vec
                transition_cov = rotation_cov
            else:
                # Motionless
                pass
            
            theta = explorer_pos[2]
            
            transform = np.array([[np.cos(theta), -np.sin(theta), 0], [np.sin(theta), np.cos(theta), 0],
                                  [0, 0, 1]])
            
            transition_vec = np.dot(transform, transition_vec)
            transition_cov = np.dot(np.dot(transform, transition_cov), transform.T) 
    
            # For plotting later
            #old_particles = particles.copy()
            
            # Perform motion model on samples
            self.fm.move(transition_vec, transition_cov)
            
            # For plotting later
            #particles_before_resample = particles.copy()
            
            beacon_ranges = []
            for j in range(total_beacons):
                prob_pos = self.fm.get_explorer_pos_mean()
                obs_dis = np.sqrt((beacons[j][0] - prob_pos[0])**2 + (beacons[j,1] - prob_pos[1])**2) + (randn() * measurement_model[1]) + measurement_model[0]
                beacon_ranges.append(obs_dis)
                
                # Only Perform particle filter when translating straight.
                # Doing it while it is stationary / rotating will make it too 
                # confident.
                if movement_type == 1:
                    self.fm.observation(obs_dis, measurement_model[0], measurement_model[1], 
                                    beacons[j][0], beacons[j][1])
            
            explorer_pos = self.fm.get_explorer_pos_mean()
    
    def _manual_run(self):
        from Data import models
        import os
        from numpy.random import randn
        import Movement
        pthjoin = os.path.join
        
        (translation_model, translation_data, rotation_model, 
         rotation_data, measurement_model, measurement_data, beacons) = models.load_data(pthjoin('..','Data','001'))
    
        # Kluge fix --  need to fix the .mat file
        measurement_model = measurement_model[0]
        sm = Sensor.SensorManager()
        # Create Beacons
        # Need to add draw beacon functions
        total_beacons = beacons.shape[0]
        for i in range(total_beacons):
            sm.add_sensor(Sensor.BeaconSensor(measurement_model[0], measurement_model[1],
                                                      [0,10000], beacons[i][0], beacons[i][1]))
        
        # Move Straight: Vector based on Motion Model measurements
        #translation_vec = [dist_hypot, dist_hypot, translation_model[2,0]]
        translation_vec = translation_model[:,0]
        translation_cov = np.cov(translation_data.T)
        translation_mov = Movement.Movement(translation_vec, translation_cov)
        
        # Turn: Vector based on Motion Model measurements
        left_rotation_vec = rotation_model[:,0]
        right_rotation_vec = rotation_model[:,0] * -1
        
        # May want to change this. This is a guess to get it working.
        # Playing around with cov(rotation_data) may lead to better results.
        rotation_cov = np.zeros([3,3])
        rotation_cov[2,2] = rotation_model[2,1]
        
        left_rot_mov = Movement.Movement(left_rotation_vec, rotation_cov)
        right_rot_mov = Movement.Movement(right_rotation_vec, rotation_cov)
        
        
        #turn_leniency = np.deg2rad(10) # Used as an error judgement for deciding when to turn
        
        explorer_pos = self.fm.get_explorer_pos_mean()
        me = Movement.Move_Explorer(explorer_pos, [], translation_mov, left_rot_mov, 
                                    right_rot_mov, perfect_movement=False)
        
        def draw_all_waypoints(cr):
            import cairo
            #cr.select_font_face('arial')
            cr.set_font_size(15)
            
            #cr.set_font_matrix(cairo.Matrix(1, 0, 0, -1, 0, 0))
            cr.new_path()
            def draw_waypoints(cr, i, waypoints, rgba_color):
                for pnt in waypoints:
                    cr.set_source_rgba(*rgba_color)
                    cr.arc(pnt[0], pnt[1], 6, 0, 2 * np.pi)
                    cr.stroke()
                    cr.move_to(pnt[0], pnt[1])
                    #cr.show_text(str(i))
                    #i += 1
            
            waypoints = me.get_old_waypoints()[-2:]
            draw_waypoints(cr, -2, waypoints, (0.5, 0, 0, 0.8))
            waypoints = me.get_current_waypoints()
            draw_waypoints(cr, 1, waypoints[0:1], (0.4, 0.9, 0.8, 0.8))
            if len(waypoints) > 1:
                draw_waypoints(cr, 2, waypoints[1:], (0, 0, 0.5, 0.8))
                
            cr.new_path()
            
        #=======================================================================
        # Add Drawing Methods
        #=======================================================================
        self.tg.add_draw_method(draw_all_waypoints)
        for beacon in sm.sensors_by_type['Beacon']:
            self.tg.add_draw_method(beacon.draw)
        
        while True:
            waypoints = []
            explorer_pos = self.fm.get_explorer_pos_mean()
            import time
            if self.quit:
                print 'Exiting Thread!'
                return # Defaults -- Do not move.
    
            # Poll for any new user input.
            waypoints.extend(tg.get_click_positions())
            
            for pnt in waypoints:
                me.move_to(pnt[0], pnt[1])
            
            transition_mov = me.get_next_move(explorer_pos)
            if transition_mov is not None:
                #explorer_pos += transition_mov.vec
                self.fm.move(transition_mov.vec, transition_mov.cov)
                time.sleep(0.5)
            
                beacon_ranges = []
                for j in range(total_beacons):
                    prob_pos = self.fm.get_explorer_pos_mean()
                    obs_dis = np.sqrt((beacons[j][0] - prob_pos[0])**2 + (beacons[j,1] - prob_pos[1])**2) + (randn() * measurement_model[1]) + measurement_model[0]
                    beacon_ranges.append(obs_dis)
                    
                    # Only Perform particle filter when translating straight.
                    # Doing it while it is stationary / rotating will make it too 
                    # confident.
                    if transition_mov.id == 1:
                        
                        self.fm.observation(obs_dis, sm.sensors_by_type['Beacon'][j])
                        
            time.sleep(0.1)
            
    
    def run(self):
        if self.auto:
            self._auto_run()
        else:
            self._manual_run()

if __name__ == '__main__':
    print 'Testing FilterManager...'
    import numpy as np
    import gobject
    
    origin_pos = np.array([200, 0, np.pi/2])
    origin_cov = np.eye(3) * 3 # Initial Covariance
    origin_cov[2,2] = 0.02
    
    # Need to call this or gtk will never release locks
    gobject.threads_init()
    
    fm = FilterManager(origin_pos, origin_cov, use_gui=True, run_pf=False)
    tg = TestGUI(fm.get_draw())
    
    #tt = TestThread(fm, tg, auto=True)
    tt = TestThread(fm, tg, auto=False)
    tt.start()
    tg.mainloop()
    tt.quit = True