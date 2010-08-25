'''
UARTCLI.py
@author: River Allen
@date: July 12, 2010

Universal Asynchronous Receive/Transmit Command Line Interface (UARTCLI).

Originally based off code from: http://effbot.org/librarybook/cmd.htm
'''

import cmd
import UARTInput

class UARTCLI(cmd.Cmd, UARTInput.UARTInput):
	'''
	UART Command Line Interface.
	'''
	def __init__(self):
		cmd.Cmd.__init__(self)
		UARTInput.UARTInput.__init__(self)
		self.intro = 'Type "help" for additional information...'
		self.prompt = '>> '
		self.quit = False

	def run(self):
		'''
		Overwriting the built-in Thread function. This is essentially the main
		of the thread that initiates after calling self.start() (another Thread() built-in).
		'''
		print 'CLI thread starting...'
		self.cmdloop()
		
	def help_help(self):
		self.do_help('')
		
	def help_exit(self):
		print 'syntax: <exit|quit|bye>',
		print '-- Close main and input window.'
		
	def do_exit(self, args):
		self.quit = True
		return True
		#sys.exit(1)

	def help_nothing(self):
		print 'syntax: nothing'
		print '-- Does absolutely nothing.'
	
	def do_nothing(self, args):
		pass
	
	def help_batch(self):
		self.help_batch_syntax()
		print '-- Runs a file with commands seperated by newlines.'
		print 'Example File test1.txt:'
		print '-'*50
		print 'nothing'
		print 'help'
		print 'nothing'
		print '# This is a comment, "%" must be the first char on the newline'
		print '-'*50
		print 'Thus, running "batch test1.txt" will run all of the commands in test1.txt'
		
	def help_batch_syntax(self):
		print 'syntax: batch <filename>'
		
	def do_batch(self, passed_args):
		args = passed_args.split(' ')
		if args == ['']:
			self.help_batch()
			return
		if len(args) != 1:
			print 'Incorrect number of arguments.'
			self.help_batch_syntax()
			return
	
		filename = args[0]
		# batch ..\batch\test.txt
		try:
			with open(filename, 'r') as batch_file:
				for line in batch_file:
					if line[0] == '#':
						continue
					self.cmdqueue.append(line)
					
		except IOError:
			print 'The file %s could not be opened or does not exist.' %(filename)
		except:
			raise
	
	def run_cmd(self, cmds):
		'''
		Note: Does not fully work yet.
		
		The goal of this method is to allow a separate thread the ability to run commands 
		through the CLI as if it were done by a user. This is great for batching and
		allows for easier creation of systems that can be both automated or user controlled.
		
		@param cmds: the command or commands to be added then run by the CLI. If a str is passed,
		it is interpreted as a single command. If a list is passed, the list is assumed to
		be a list of commands.
		@type cmds: str or list of str 
		'''
		if type(cmds) is str:
			cmds = [cmds]
		elif type(cmds) is list:
			pass
		else:
			raise TypeError, 'cmds is not list or str.'
		
		self.cmdqueue.extend(cmds)
		print 'Before flush', self.cmdqueue
		#self.stdin.flush()
		#print 'After flush', self.cmdqueue
		#self.stdin.write('nothing\n')
	
	# Shortcuts
	do_quit = do_exit
	help_quit = help_exit
	do_bye = do_exit
	help_bye = help_exit
	do_EOF = do_exit
	help_EOF = help_exit

if __name__ == "__main__":
	# Testing out CLI
	try:
		CLI = UARTCLI()
		CLI.cmdloop()
	except KeyboardInterrupt:
		CLI.do_exit('')	
	except:
		raise