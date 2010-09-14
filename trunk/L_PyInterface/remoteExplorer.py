'''
Created on 2010-09-08

@author: nrqm

This script provides a remote interface to the explorer.  The explorer should be running
explorerNetWrapper.py.  This script connects to the server therein and passes any valid
commands on to the explorer.  It waits for the explorer to reply with its output, and
prints the reply to the screen.
'''

import re
import sys
import socket
from CryptoJazz import Cryptographer

if __name__ != '__main__':
    raise Exception("This file must be run as main")
    exit()

# any input line that doesn't match one of these regular expressions is invalid.
moveCmdRE = re.compile(r"^move\s+\d+\s+\d+$")
posCmdRE = re.compile(r"^pos\s+\d+\s+\d+$")
exitCmdRE = re.compile(r"^exit$")

HOST = raw_input("Enter explorer host address: ").strip()    # The remote host
key = raw_input("Enter password: ")

cryptographer = Cryptographer(key)

print "Connecting... ",
PORT = 64128              # The same port as used by the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.send(cryptographer.encrypt("HELLO"))
if (cryptographer.decrypt(s.recv(1024)) == "OK"):
    print "OK"
else:
    print "Failed to connect."

run = True
while run:
    print ">> ",
    line = sys.stdin.readline().strip()
    if not moveCmdRE.match(line) and not posCmdRE.match(line) and not exitCmdRE.match(line):
        print "Invalid command."
        continue
    
    if exitCmdRE.match(line):
        # exit command is not passed to explorer.  The explorer can't be exited with a
        # remote command.
        run = False
    else:
        s.send(cryptographer.encrypt(line))
        print s.recv(1024)
    
# when the client closes the connection the server starts listening for a new connection
s.close()