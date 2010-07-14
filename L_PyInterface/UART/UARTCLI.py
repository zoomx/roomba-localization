'''
UARTCLI.py
@author: River Allen
@date: July 12, 2010

Universal Asynchronous Receive/Transmit Command Line Interface (UARTCLI)
'''

import cmd
import threading

class UARTCLI(cmd.Cmd, threading.Thread):
	'''
	UART Command Line Interface.
	'''
	def __init__(self):
		cmd.Cmd.__init__(self)
		threading.Thread.__init__(self)
		self.intro = 'Type "help" for additional information...'
		self.prompt = '>> '
		self._commands = []
		self.quit = False

	def run(self):
		'''
		Overwriting the built-in Thread function. This is essentially the main
		of the thread that initiates after calling self.start() (another Thread() built-in).
		'''
		print 'CLI thread starting...'
		self.cmdloop()
		
	def get_commmands(self):
		'''
		Retrieves list of all VALID commands that have been processed since last called.
		'''
		ret_data = self._commands
		self._commands = []
		return ret_data
		
	
	def help_help(self):
		self.do_help('')
		
	def help_exit(self):
		print 'syntax: <exit|quit|bye>',
		print '-- Close main and input window.'
		
	def do_exit(self, args):
		self.quit = True
		return True
		#sys.exit(1)

	
	# Shortcuts
	do_quit = do_exit
	help_quit = help_exit
	do_bye = do_exit
	help_bye = help_exit
	do_EOF = do_exit
	help_EOF = help_exit


def main():
	try:
		CLI = UARTCLI()
		CLI.cmdloop()
	except KeyboardInterrupt:
		CLI.do_exit('')	
	except:
		raise
	
if __name__ == "__main__":
	main();