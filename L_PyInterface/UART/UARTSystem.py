'''
UARTSystem.py
@author: River Allen
@date: July 12, 2010

An all encompassing UART System that allows "easy" mechanisms for interacting with a
microcontroller
'''

import logging
import serial
import threading
import time

import UARTInput

#Based off code from:
#http://eli.thegreenplace.net/2009/07/30/setting-up-python-to-work-with-the-serial-port/

global uart_lock
uart_lock = None

class UART(threading.Thread):
	def __init__(self, serial_port, baud_rate, uart_input=None, approve=False, debug=False):
		'''
		Read/log data from UART, open an input window, and simulate having UART 
		(not fully implemented).
		
		@param serial_port: The number of the port used by UART. Can also use 'auto', which will
		attempt to open a COM port with the first existent COM port. 'auto' runs through
		ports 0-20, attempting trying to open them.
		@type serial_port: int or str
		
		@param baud_rate: The baud_rate for the UART connection.
		@type baud_rate: int
		
		@param uart_input: If None, No input will be used. Otherwise, it will
		poll for new queued commands from a UARTInput child class. The commands it expects
		to get should be in struct.pack format. None by default.
		@type uart_input: UARTInput.UARTInput
		
		@param approve: 
		@type approve: bool
		
		@param debug: 
		@type debug: bool
		'''
		super(UART, self).__init__()
		self.serial_port = serial_port
		self.baud_rate = baud_rate
		self.quit = False
		self.debug = debug
		
		# Locks -- Needed as separate threads can access data.
		self._input_lock = threading.Lock()
		self._output_lock = threading.Lock()
		self._write_lock = threading.Lock()
		
		# Attempt to open the COM port
		if str(self.serial_port).lower() == 'auto':
			self.ser = None
			ports = range(30)
			ports.reverse()
			for i in ports:
				try:
					self.ser = serial.Serial(i, self.baud_rate, timeout=0)
				except:
					continue
				break
			if self.ser is None:
				raise RuntimeError, 'There are no available COM ports.' 
		else:
			try:
				self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=0)
			except:
				print 'Cannot open Port: "%s"' %str(self.serial_port)
				self.quit = True
				raise
	
		self.uo = UARTOutput(self.ser, debug=self.debug)
		
		if uart_input is not None:
			if not isinstance(uart_input, UARTInput.UARTInput):
				raise TypeError, "uart_input must be None or an UARTInput.UARTInput object"
			
			self.ui = uart_input
		else:
			self.ui = None
		
		if self.debug:
			print( '-' * 50 )
			print( 'Starting...' )
			print( 'Device:\t\t\t' + str(self.ser.name) )
			print( 'Baud Rate:\t\t' + str(self.ser.baudrate) )
			print "Hit 'Ctrl + C' or type 'exit' in the input window to exit..."
			print( '-' * 50 )
		
		self._output_data_buffer = []
		self._input_data_buffer = []
		
		self.approve = approve
		self._write_data_buffer = []
		
	def get_output_data(self):
		'''
		Retrieves received UART data since last called.
		'''
		with self._output_lock:
			r_data = self._output_data_buffer
			self._output_data_buffer = []
			return r_data
	
	def set_output_data(self, dat):
		'''
		Locks, writes to out buffer, then unlocks.
		'''
		with self._output_lock:
			if type(dat) == list:
				self._output_lock.extend(dat)
			else:
				self._output_lock.append(dat)
	
	def get_input_data(self):
		'''
		Retrieves all input commands since last called.
		'''
		with self._input_lock:
			r_data = self._input_data_buffer
			self._input_data_buffer = []
			return r_data
	
	def set_input_data(self, dat):
		'''
		Locks, writes to input buffer, then unlocks.
		'''
		with self._input_lock:
			if type(dat) == list:
				self._input_data_buffer.extend(dat)
			else:
				self._input_data_buffer.append(dat)

	def add_data_to_write(self, cmds):
		with self._write_lock:
			if type(cmds) == list:
				self._write_data_buffer.extend(cmds)
			else:
				self._write_data_buffer.append(cmds)
			print self._write_data_buffer

	def exit(self):
		'''
		Safely closes all threads and then closes serial port.
		'''
		self.uo.quit = True
		if self.uo.isAlive():
			self.uo.join(100) # Wait for it to finish
			if self.uo.isAlive():
				raise RuntimeError, 'The UART output thread is not dieing...'
		
		if self.ui is not None:
			# A tricksy way to close/get out of the cmdloop of ui if it is not already closed.
			self.ui.cmdqueue.insert(0, 'exit')
			if self.ui.isAlive():
				self.ui.join(100)
				if self.ui.isAlive():
					raise RuntimeError, 'The UART CLI thread is not dieing...'
				
		self._close_serial()
		if self.debug:
			print "Exiting..."
	
	def _close_serial(self):			
		'''
		Attempt to close the serial connection.
		'''
		if self.ser is not None:
			try:
				self.ser.close()
			except:
				pass

	def run(self):
		'''
		This is UART's main loop and is run when thread.start() is called.
		
		run() attempts to do the following:
		- Start UARTOutput and UARTInput 
		- Log data from UARTOutput
		- if self.approve:
			write any data put into "add_data_to_write"
		- else:
			write any data available from the uart_input buffer 
		'''
		self.uo.start()
		if self.ui is not None:
			self.ui.start()
		
		while not self.quit:
			if self.uo.quit or (self.ui is not None and self.ui.quit):
				if self.debug:
					print 'uo or ui Quit, so Quitting...'
				self.quit = True
				break
			
			# poll uartOut
			uout_data = self.uo.get_data()
			self._output_data_buffer.extend(uout_data)
			
			# poll for new data from CLI
			if self.ui is not None:
				uin_data = self.ui.get_input()
				self._input_data_buffer.extend(uin_data)
			if self.approve:
				if len(self._write_data_buffer) > 0:
					with self._write_lock:
						if self.debug:
							print 'SE:', self._write_data_buffer[0]
						self.ser.write(self._write_data_buffer.pop(0))
			elif self.ui is not None:
				for uin in uin_data:
					if self.debug:
						print 'SE:', uin
					self.ser.write(uin)
				
			time.sleep(0.1)
		
		self.exit()
		

class UARTOutput(threading.Thread):
	'''
	'''
	def __init__(self, ser, debug=False):
		'''
		@param ser: Open and ready to go serial.
		@type ser: serial.Serial
		
		'''
		super(UARTOutput, self).__init__()
		self.quit = False
		self.debug = debug
		self._lock = threading.Lock()
		self.ser = ser
		self._received_data = []

		
	def exit(self):
		'''
		
		'''
		self.quit = True
		#sys.exit()
		
	def get_data(self):
		with self._lock:
			ret_data = self._received_data
			self._received_data = []
			return ret_data
	
	def run(self):
		'''
		
		'''
		try:
			temp_buffer = ''
			newline = '\r\n'
			while not self.quit:
				val = self.ser.read(400)
				if len(val) > 0:
					temp_buffer += val

				# Need to do this as incomplete lines can be read.
				# In addition, may read complete line + incomplete line
				# or two complete lines.
				if newline in temp_buffer:
					# Get the index of the point where to cut data+newline
					n_index = temp_buffer.index(newline) + len(newline)
					# Store/Log new data
					newest_data = temp_buffer[:n_index]
					with self._lock:
						if self.debug:
							print 'RE:', newest_data
						self._received_data.append(newest_data)
					temp_buffer = temp_buffer[n_index:]
				else:
					pass
				
				time.sleep(0.01)
		finally:
			self.exit()


if __name__ == "__main__":
	execfile("..\globalConfig.py")
	logging.basicConfig(level=logging.DEBUG,
		format=logFormat,
		datefmt=logDateFormat,
		filename=logFilename,
		filemode=logFileMode)
	console = logging.StreamHandler()
	log = logging.getLogger()
	log.addHandler(console)
	ua = UART(serialPort, baudRate, debug=True)
	ua.start()
	
	