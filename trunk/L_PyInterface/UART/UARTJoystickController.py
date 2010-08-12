'''
UARTJoystickController.py
@author: River Allen
@date: July 15, 2010

A simple piece of code that uses pygame to poll a usb ps2 joystick for button and 
axes information. It's main design goal was for providing a simple 19 byte integer packet
to be sent through UART to a microcontroller to provide human control of an embedded system. 
'''

import pygame
import struct
import time
from UART import UARTInput
from UART import UARTSystem

class UARTJoystickController(UARTInput.UARTInput):
    def __init__(self, button_toggle=False, poll_interval=0.07, debug=True):
        '''
        Built for the Average Logitech USB (PS2) controller.
        
        Buttons:
        (Note: these numbers are array index in code...i.e. button 1 is get_button(0))
         * 1 - 10 are labelled.
         * 11 - left stick button. (Press the left joystick button down until it makes a 'click' noise)
         * 12 - right stick button. (Press the Right joystick button down)
        Axes:
         * 0 - Left Stick X-axis (-ve: Left, +ve: Right)
         * 1 - Left Stick Y-axis (-ve: Up, +ve: Down)
         * 2 - Right Stick X-axis (-ve: Left, +ve: Right)
         * 3 - Right Stick Y-axis (-ve: Up, +ve: Down)
        Hat(s):
         * This is the D-Pad.
        
        @param button_toggle: If True, Pressing and holding down a button will look like this:
        0001000000
           ^ - button pressed and held at this moment.
        
        '''
        UARTInput.UARTInput.__init__(self)
        self.quit = False

        self.struct_fmt = 'b' * 19 + '\r\n' # 12 buttons + 2 (xyaxis1) + 2 (xyaxis2) + 2 (hat)
        self._debug = debug
        self._button_toggle = False
        pygame.init()
        self.joysticks = []
        
        self.poll_interval = poll_interval
        
        try:
            self.joysticks.append(pygame.joystick.Joystick(0))
        except:
            print 'No joystick(s) plugged in.'
        
        try:
            self.joysticks.append(pygame.joystick.Joystick(1))
        except:
            self.joysticks.append(self.joysticks[0])
        
        for joy in self.joysticks:
            joy.init()
            if self._debug:
                print('-' * 50)
                print(str(joy.get_name()))
                print('-' * 50)
    
        self._packets = []
    
    def run(self):
        '''
        This method is used by threading, and is essentially the UARTJoystickControl's main
        thread. Here, it polls the joystick and queues data that can be viewed by other threads
        (most probably UARTSystem).
        '''
        try:
            button_history = []
            for joy in self.joysticks:
                button_history.append([0,0,0,0,0,0,0,0,0,0,0,0])
            
            while not self.quit:
                pygame.event.pump()
                joy_num = 0
                for joy in self.joysticks:
                    # Buttons
                    buttons = []
                    for i in range(joy.get_numbuttons()):
                        button_value = joy.get_button(i)
                        if self._button_toggle:
                            # Button will send only a single '1' then '0's until 
                            # button is released and pressed again.
                            # Stops button holding and button tapping timing issues.
                            if button_history[joy_num][i] and button_value:
                                buttons.append(0)
                            else:
                                buttons.append(button_value)
                                button_history[joy_num][i] = button_value
                        else:
                            # Send the button value as is. (i.e. allows holding)
                            buttons.append(button_value)
                    
                    # Axes
                    axes = []
                    for i in range(joy.get_numaxes()):
                        axes.append(int(joy.get_axis(i)*100)) # Normalize axes to 100 (fit in byte)
                    
                    # Hat (aka D-Pad)
                    hat = list(joy.get_hat(0))
                    
                    all_data = []
                    all_data.extend(buttons)
                    all_data.extend(axes)
                    all_data.extend(hat)
                    all_data.append(joy_num)
                    
                    packet = struct.pack(self.struct_fmt, *tuple(all_data))
                    # Allow another thread (probably UARTSystem) to get queued data
                    self.add_input(packet)
                    
                    if self._debug:
                        print('Buttons:\t' + str(buttons))
                        print('Axes\t\t' + str(axes))
                        print('Hat:\t\t' + str(hat))
                        print('-' * 50)
                    
                    time.sleep(self.poll_interval)
                    joy_num += 1

        except:
            print 'Crashed...'
            raise

if __name__ == '__main__':
    # Loads in variables from the globalConfig file.
    execfile("..\\globalConfig.py")
    
    
    joy = UARTJoystickController(button_toggle=False, poll_interval=joystickPollInterval, debug=False)
    # Uncomment next line if you want to ONLY test the joystick.
    #joy.run() 
    
    ua = UARTSystem.UART(serialPort, baudRate, uart_input=joy, approve=False, debug=True)
    ua.start()
