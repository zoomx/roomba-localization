'''
systemRunner.py
River Allen
June 7, 2010

@todo: Fix configuration, so it is in a more suitable format (.ini for example)
@todo: Add a timeout where if no beacon data is received...assume beacon ranges are -1...
(i.e. go off motion model)
@todo: Determine a way to better merge user input and Move Explorer's movements.
'''

import threading
import logging
import numpy as np
from warnings import warn
try:
    import gobject
except:
    warn('Cannot import gobject. Thus, the GUI cannot be used.')
import os
import time
import struct
from UART import UARTSystem
from UART import FilterCLI
import roombaGUI
import Map
from Filters import FilterManager, KalmanFilter, ParticleFilter
import Sensor
import Movement
from Data import models
import utilRoomba

class FilterSystemRunner(threading.Thread):

    def __init__(self, serial_port, baud_rate, map_obj, origin_pos, origin_cov, gui=None, 
                 simulation=False, run_pf=True, run_kf=True):
        '''
        @param serial_port: 
        @type serial: 
        
        '''
        super(FilterSystemRunner, self).__init__()
        self.quit = False
        #=======================================================================
        # UART
        #=======================================================================
        self.cli = FilterCLI.FilterCLI()
        self.ua = UARTSystem.UART(serial_port, baud_rate, uart_input=self.cli,
                                  log=logging, approve=True)
        self.uin = [] # uart input from user
        self.uout = [] # uart output from base/roomba
        
        
        #=======================================================================
        # Filter
        #=======================================================================
        self.fm = FilterManager.FilterManager()
        if run_kf:
            self.fm.add_filter(KalmanFilter.KalmanFilter(origin_pos, origin_cov))
        if run_pf:
            self.fm.add_filter(ParticleFilter.ParticleFilter(origin_pos, origin_cov))
        
        #=======================================================================
        # Data
        #=======================================================================
        pthjoin = os.path.join
        (self.translation_model, self.translation_data, self.rotation_model, 
         self.rotation_data, self.measurement_model, self.measurement_data, self.beacons) = models.load_data(pthjoin('Data','001'))
        
        
        #=======================================================================
        # Sensors
        #=======================================================================
        # Kluge fix --  need to fix the .mat file
        measurement_model = self.measurement_model[0]
        self.sm = Sensor.SensorManager()
        # Create Beacons
        # Need to add draw beacon functions
        total_beacons = self.beacons.shape[0]
        for i in range(total_beacons):
            self.sm.add_sensor(Sensor.BeaconSensor(measurement_model[0], measurement_model[1],
                                                      [0,10000], self.beacons[i][0], self.beacons[i][1]))
        
        #=======================================================================
        # Movement
        #=======================================================================
        self._new_moves = []
        self._last_move = None
        
        
        # Move Straight: Vector based on Motion Model measurements
        translation_vec = self.translation_model[:,0]
        translation_vec[:2] = np.array([100.4, 4])
        translation_cov = np.cov(self.translation_data.T)
        translation_mov = Movement.Movement(translation_vec, translation_cov)
        
        # Turn: Vector based on Motion Model measurements
        left_rotation_vec = self.rotation_model[:,0]
        right_rotation_vec = self.rotation_model[:,0] * -1
        
        # May want to change this. This is a guess to get it working.
        # Playing around with cov(rotation_data) may lead to better results.
        rotation_cov = np.zeros([3,3])
        rotation_cov[2,2] = self.rotation_model[2,1]
        
        left_rot_mov = Movement.Movement(left_rotation_vec, rotation_cov)
        right_rot_mov = Movement.Movement(right_rotation_vec, rotation_cov)
        
        explorer_pos = self.fm.get_explorer_pos_mean()
        self.me = Movement.MoveExplorer(explorer_pos, [11, 11, np.deg2rad(6)], 
                                        translation_moves=[],
                                        rotation_moves=[])
        
        #=======================================================================
        # Map
        #=======================================================================
        self.map_obj = map_obj
        
        #=======================================================================
        # GUI
        #=======================================================================
        self.rg = None
        if gui is not None:
            self.rg = gui
            self.rg.add_filter_draw_method(self.fm.get_draw())
                
            for beacon in self.sm.sensors_by_type['Beacon']:
                self.rg.add_draw_method(beacon.draw)
            
            self.rg.add_draw_method(self._draw_all_waypoints)
        
    def exit(self):
        self.quit = True
        #=======================================================================
        # Exit everything and ensure they have all quit.
        #=======================================================================
        if self.rg is not None:
            self.rg.quit = True
            self.rg.destroy(None, None)
        
        self.ua.quit = True
        if self.ua.isAlive():
            self.ua.join(100)
            if self.ua.isAlive():
                raise RuntimeError, "UART is not exiting..."
        print 'Exiting...'
    
    def _draw_all_waypoints(self, cr):
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
            
            waypoints = self.me.get_old_waypoints()[-2:]
            draw_waypoints(cr, -2, waypoints, (0.5, 0, 0, 0.8))
            waypoints = self.me.get_current_waypoints()
            draw_waypoints(cr, 1, waypoints[0:1], (0.4, 0.9, 0.8, 0.8))
            if len(waypoints) > 1:
                draw_waypoints(cr, 2, waypoints[1:], (0, 0, 0.5, 0.8))
                
            cr.new_path()
    
    def _process_out(self, out):
        if 'IPkt' in out:
            sensor_data = out[5:]
            sensor_data.split()
            print sensor_data
            
            #example: data = '0 1006 215|125 321 344 '
            #           angle distance compass| beac1 beac2 beac3 ... 
            move_data, beacon_ranges = sensor_data.split('|')
            move_data = map(int, move_data.split(' '))
            beacon_ranges = map(int, beacon_ranges.split(' ')[:-1])
            if len(beacon_ranges) != len(self.sm.sensors_by_type['Beacon']):
                raise RuntimeError, 'No. of beacon ranges does not match No. of beacons.'
            
            print 'Move Data:', move_data
            if self._last_move is not None:
                # Move filters
                self.fm.move(self._last_move[0], self._last_move[1])
            
                # Add in observational data
                for j in range(len(beacon_ranges)):
                    self.fm.observation(beacon_ranges[j], self.sm.sensors_by_type['Beacon'][j])
            
            print 'Beacon Ranges:', beacon_ranges
            print 'Estimated Explorer Position:', self.fm.get_explorer_pos_mean()
            
            
            return True
        elif 'INITIAL' in out:
            return True
        elif 'Fail' in out:
            print 'Move was unsuccessful.'
            return True
        else:
            # if out_data was split up from line before...combine it
            #@change
            return None
    
    def _process_in(self, inp):
        cmd = inp[0]
        
        if cmd == 'move':
            # This is the iffy part...Essentially need to deal with motion model moves
            # and moves made by a human user.
            _, angle, distance = struct.unpack(inp[1], inp[2])

            move = None            
            if angle == 0 and distance == utilRoomba.CmToRoombaDistance(100):
                # valid translation movement
                move = self.me.translate(self.fm.get_explorer_pos_mean())
            elif distance == 0:
                if angle == int(utilRoomba.DegreesToRoombaAngle(10)):
                    # valid left movement
                    move = self.me.left_rotate(self.fm.get_explorer_pos_mean())
                elif angle == int(utilRoomba.DegreesToRoombaAngle(-10)):
                    # valid right movement
                    move = self.me.right_rotate(self.fm.get_explorer_pos_mean())
            else:
                # Human, non-motion model movement...should not affect filters.
                pass
            
            
            # Store the movement made. Only update the filters' positions with the movement
            # after the roomba has sent the confirmation (in _process_out)
            self._last_move = move
        
            self._new_moves.append(inp[2])
        elif cmd == 'pos':
            print 'POS:', inp[1], inp[2]
            self.me.move_to(inp[1], inp[2])
            print 'Current Waypoints:', self.me.get_current_waypoints()
            
    
    def _convert_move_id_to_move_cmd(self, id):
        if id == 1:
            return '0 100\n'
        if id == 2:
            return '10 0\n'
        if id == 3:
            return '-10 0\n'
        
    
    def run(self):
        #=======================================================================
        # Initialize all threads.
        #=======================================================================
            
        self.ua.start()
        
        if self.rg is not None:
            self.rg.start()
            
        
        waypoints = []
        allow_move = True # only allow movement after beacon readings have come in.
        while not self.quit:
            
            # Check if any threads have exited
            if self.ua.quit or (self.rg is not None and self.rg.quit):
                print 'UART or GUI has quit.'
                self.quit = True
                break
            
            # Poll GUI waypoints
            # Any new? --> put into movement
            if self.rg is not None:
                waypoints = self.rg.get_click_positions()
                for pts in waypoints:
                    self.me.move_to(pts[0], pts[1])
                    
            
            # Poll uartout
            # Any Ipkt? --> process
            # roomba can perform new move
            self.uout.extend(self.ua.get_output_data())
            if len(self.uout) > 0:
                result = self._process_out(self.uout.pop(0))
                if result is not None:
                    allow_move = result
            
            # Poll uartin
            # Any new movements? --> send to roomba
            self.uin.extend(self.ua.get_input_data())
            if len(self.uin) > 0:
                self._process_in(self.uin.pop(0))
            
            # Can roomba move?
            if allow_move:
                # Any new? --> queue command for roomba
                if len(self._new_moves) > 0:
                    move_struct = self._new_moves.pop(0)
                    # send oldest command to base
                    self.ua.add_data_to_write([move_struct])
                    allow_move = False
                else:
                    # Poll Movements
                    move = self.me.get_next_move(self.fm.get_explorer_pos_mean())
                    if move is not None:
                        # This is the most hacked part of the code. I originally wanted
                        # to send it through the CLI, but it would get stuff in the cmdloop's
                        # readline(), thus appending move commands to the CLI cmdqueue failed
                        # because it would not check the cmdqueue until the readline had finished.
                        self.cli.do_move(self._convert_move_id_to_move_cmd(move.id))
                        #time.sleep(0.2)
            
            time.sleep(0.1)
        self.exit()
        
        

if __name__ == '__main__':
    #===========================================================================
    # Configuration
    #===========================================================================
    execfile("globalConfig.py")
    logging.basicConfig(level=logging.DEBUG,
        format=logFormat,
        datefmt=logDateFormat,
        filename=logFilename,
        filemode=logFileMode)
    console = logging.StreamHandler()
    log = logging.getLogger()
    log.addHandler(console)
    
    #gobject.threads_init() # Need to do this, or gtk will not let go of lock
    
    origin_pos = np.array([200,0,np.deg2rad(90)])
    #origin_pos = np.array([200, 300, np.deg2rad(180)])
    origin_cov = np.eye(3) * 3 # Initial Covariance
    origin_cov[2,2] = 0.02
    
    map_obj = Map.GridMap()
    
    #===========================================================================
    # Run
    #===========================================================================
    gui = False
    if gui:
        duh_gui = roombaGUI.RoombaLocalizationGUI(map_obj=map_obj)
    else:
        duh_gui = None
        
    
    sysRunner = FilterSystemRunner(serialPort, baudRate, map_obj, origin_pos, origin_cov, gui=duh_gui,
                                   run_pf=False, run_kf=True)
    sysRunner.start()
    #if gui:
    #    duh_gui.mainloop()