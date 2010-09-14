'''
Created on 2010-09-08

@author: nrqm

This script runs on the explorer's netbook.  It spawns the system runner script as an
external process and passes it any messages it receives from a client that connects to it.
It replies to the client with the command result.
'''

# Blowfish encryption code provided by Michael Gilfix under the Artistic license
import socket
import subprocess
import sys
from CryptoJazz import Cryptographer

if not __name__ == '__main__':
    raise Exception("This file must be run as main")

#TODO: next line is offensive programming, should probably be made defensive
#systemRunner = subprocess.Popen("python systemRunner.py", stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    
def doCommand(message):
    if message == "exit":
        return ""
    #systemRunner.stdin.write(message)
    print message.strip()
    #return systemRunner.stdout.read() #TODO: wait for entire message
    return "Success"
    
# should probably change the password in the local copy.  The password must be 8-56 bytes long.
cryptographer = Cryptographer("dummy_password")

HOST = ''
PORT = 64128
while 1:
    print("Listening...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(1)
    conn, (addr, port) = s.accept()
    print 'Establishing connection with %s...'%addr
    data = conn.recv(1024)
    if cryptographer.decrypt(data) == "HELLO":
        conn.send(cryptographer.encrypt("OK"))
        print "OK"
    else:
        print "Client connection failed.  Resetting server."
        conn.close()
        continue
    run = True
    while True:
        try:
            reply = doCommand(cryptographer.decrypt(conn.recv(1024)))
            if reply == "": break
            conn.send(reply)
        except:
            break;
    conn.close()
    print "Connection closed."

