from datetime import datetime
import logging
import os
import mmap
import serial
import signal
import struct
import subprocess
import sys
import time


import Roomba

#Based off code from:
#http://eli.thegreenplace.net/2009/07/30/setting-up-python-to-work-with-the-serial-port/

execfile("globalConfig.py")

logging.basicConfig(level=logging.DEBUG,
		format=logFormat,
		datefmt=logDateFormat,
		filename=logFilename,
		filemode=logFileMode)
console = logging.StreamHandler()
log = logging.getLogger()
log.addHandler(console)

childProcess = None
ser = None

def process_packet(packet=''):
	'''
	
	'''
	if packet == '':
		return None
	
	return packet

def init():
	'''
	
	
	'''
	global ser
	global childProcess
	
	# Clean the exit flag.
	sharedMem[exitPoint] = '\x00'
	
	# Attempt to open the COM port
	try:
		ser = serial.Serial(serialPort, baudRate, timeout=0)
	except:
		logging.exception( 'Cannot open Port: "%d"' %(serialPort + 1) )
		exit()
	
	# Log initial information.
	logging.info( '-' * 50 )
	logging.info( 'Starting...' )
	logging.info( 'Device:\t\t\t' + str(ser.name) )
	logging.info( 'Baud Rate:\t\t' + str(ser.baudrate) )
	print "Hit 'Ctrl + C' or type 'exit' in the input window to exit..."
	logging.info( '-' * 50 )
	
	# Windows specific, should be modified.
	if takeInput:
		childProcess = subprocess.Popen('start python uartKeyboardInput.py', shell=True)
	

def exit():
	'''
	
	'''
	# Close COM Port
	# Assumes that if there is a problem closing COM port, COM port was never opened.
	try:
		ser.close()
	except:
		pass
	
	# kill child
	sharedMem[exitPoint] = '\x01'
	print "EXITING..."
	sys.exit()

def log_filter(logVal):
	'''
	
	'''
	
	if 'IPkt' in  logVal:
		try:
			fil = open( 'RoombaMoveMetrics.log', 'a' )
		except:
			logging.exception("Could not open Metrics log file.")
			return
		
		data_row = logVal[5:]
		data_vals = data_row.split('|')
		if int(data_vals[0]) == 2:
			print 'DONE!'
			
		data_vals[2] = str(Roomba.RoombaAngleToDegrees(int(data_vals[2])))
		data_row = ' | '.join(data_vals)
		fil.write(data_row + '\n')
		fil.close()
	

def main():
	'''
	
	'''
	init()
	global ser
	
	try:
		while True:
			val = ser.read(999)
			
			if len(val) > 0:
				logging.info( val )
			
			#log_filter(val)
			
			#@todo: Should create a clean way to show exit to other
			# process. Perhaps use specified point in shared memory,
			# and write to it. If that point in mem is written,
			# know other has exited.
			
			time.sleep(0.1)
			
			if takeInput:
				# Simple locking mechanism
				#@todo: Needs to be done cleaner, the first value 
				# should be the length of the data sent. It is type
				# now.
				if sharedMem[0] != '\0':
					dat = sharedMem[1:5] # Remove '\n'
					sharedMem[0] = '\0'
					packet = process_packet(dat)
					if packet is not None:
						logging.debug( "SE: " + str(dat) )
						ser.write(dat) # Write the packet to uart
					time.sleep(0.1)
					
			if sharedMem[exitPoint] == '\x01':
				exit()
	except KeyboardInterrupt:
		pass
	except:
		raise
	finally:
		exit()

if __name__ == "__main__":
	main();