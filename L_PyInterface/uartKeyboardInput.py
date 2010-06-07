import cmd
import datetime
import os
import math
import mmap
import struct
import sys
import time
import Roomba

# Load the common vars
execfile("globalConfig.py")
global first_run
first_run = True

def send_struct(strct=None, fmt=''):
	'''
	Prepare and "send" struct to uartMain. "Sending" involves IPC by 
	shared memory.
	
	send_struct() will ONLY return after uartMain has read the data.
	
	@param strct: A C struct to be sent to uartMain to be interpreted.
	@type strct: str (struct string)
	'''
	if strct is None or strct == '':
		return
	
	global first_run
	'''
	fmt = 'Bhh'
	print 'TESTING', len(strct), strct
	zz = struct.calcsize(fmt)
	print len(fmt), fmt, struct.calcsize(fmt), struct
	
	'''
	if first_run:
		sharedMem[0] = 'x'
		sharedMem.seek(1)
		sharedMem.write(strct + '\n')
		first_run = False
	else:
	    while sharedMem[0] != '\0':
	        pass
	    sharedMem[0] = 'x'
	    sharedMem.seek(1)
	    sharedMem.write(strct + '\n')
	    sharedMem.flush()
	#'''

def send_exit():
	'''
	Warn uartMain that uartKeyboardInput has closed.
	'''
	pass

class UartCLI(cmd.Cmd):
	'''
	UART Command Line Interface.
	'''
	def __init__(self):
		cmd.Cmd.__init__(self)
		self.intro = 'Type "help" for additional information...'
		self.prompt = '>> '
		
	def help_help(self):
		self.do_help('')
		
	def help_exit(self):
		print 'syntax: <exit|quit|bye>',
		print '-- Close main and input window.'
		
	def do_exit(self, args):
		#@todo: Signal or leave message for UartMain process
		sys.exit(1)
	
	def help_move(self):
		print 'syntax: move <angle> <distance>',
		print '-- Turn the Roomba by angle, then move straight for distance.'
		print 'Angle: In degrees. Positive is left and negative is right.'
		print 'Distance: In centimeters.'
		print 'Example: "move 30 100" (Turn left 30 degrees, move 1 meter)'
	
	def do_move(self, args):
		args = args.split( ' ' )
		
		if len(args) < 2:
			print 'Not enough arguments.'
			self.help_move()
			return
		
		angle = 0
		distance = 0
		
		try:
			angle = int( args[0] )
		except:
			print 'Angle argument is invalid.'
			self.help_move()
			return
		
		try:
			distance = int(args[1])
		except:
			print 'Distance argument is invalid.'
			self.help_move()
			return
		
		print angle, distance
		roombaAngle = int( Roomba.DegreesToRoombaAngle(angle) )
		roombaDistance = int( Roomba.CmToRoombaDistance(distance) )
		fmt = 'hh' # Unsigned Byte / Short / Short
		send_struct(struct.pack(fmt, roombaAngle, roombaDistance), fmt)
	
	def help_stop(self):
		print 'syntax: stop',
		print '-- Stops the Roomba.'
		
	def do_stop(self, args):
		self.do_move('0 0')
	
	def help_wait(self):
		print 'syntax: wait <delay>',
		print '-- Wait approximately <delay> milliseconds.'
	
	def do_wait(self, arg):
		wait_time = 0
		try:
			wait_time = float(arg) / 1000
		except:
			print 'Delay argument is invalid.'
			self.help_wait()
			return
	
		print wait_time
		sleep(wait_time)
	
	# Shortcuts
	do_quit = do_exit
	help_quit = help_exit
	do_bye = do_exit
	help_bye = help_exit
	do_eof = do_exit


def main():
	CLI = UartCLI()
	CLI.cmdloop()

if __name__ == "__main__":
	main();