#===============================================================================
# General Settings
#===============================================================================
takeInput = True            # True - Windows only, Will take and send input if T

#===============================================================================
# UART Settings
#===============================================================================
serialPort = 'auto'              # Uses Array Numbering (i.e. COM1 is '0'). 
                            # 'auto' can be used to attempt to find the COM port.
baudRate = 100000
joystickPollInterval = 0.7  # The amount of time in seconds between each poll of the joystick
                            # (i.e. 1.5 is 1500 milliseconds)

#===============================================================================
# Log Settings
#===============================================================================
logFilename = 'uart.log'    # Filename for log
logFileMode = 'a'           # 'w' - Overwrite; 'a' - append

# See http://docs.python.org/library/logging.html#formatter
logFormat = '%(asctime)s\t%(levelname)-8s\t%(message)s'

# See http://docs.python.org/library/datetime.html#strftime-and-strptime-behavior
logDateFormat = '%d %b %Y %H:%M:%S'
