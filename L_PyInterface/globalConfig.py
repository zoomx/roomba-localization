#===============================================================================
# General Settings
#===============================================================================
takeInput = True            # True - Windows only, Will take and send input if T

#===============================================================================
# UART Settings
#===============================================================================
serialPort = 4              # Uses Array Numbering (i.e. COM1 is '0')
baudRate = 100000

#===============================================================================
# Log Settings
#===============================================================================
logFilename = 'uart.log'    # Filename for log
logFileMode = 'a'           # 'w' - Overwrite; 'a' - append

# See http://docs.python.org/library/logging.html#formatter
logFormat = '%(asctime)s\t%(levelname)-8s\t%(message)s'

# See http://docs.python.org/library/datetime.html#strftime-and-strptime-behavior
logDateFormat = '%d %b %Y %H:%M:%S'
