'''
Created on 2010-09-09

@author: nrqm
'''
# Blowfish encryption code provided by Michael Gilfix under the Artistic license
import blowfish
import random

# This isn't supposed to provide robust security, just to deter curious students from
# sending commands to the explorer over the network.


class Cryptographer(object):
    '''Cryptography provider for Roomba explorer project'''
    cryptoProvider = None

    def __init__(self):
        # assuming "secret.key" exists and contains a key between 8 and 56 bytes long
        #TODO: sanity checking (file existence, key length)
        f = open("secret.key", "rb")
        key = f.read()
        self.cryptoProvider = blowfish.Blowfish(key)
        
    def encrypt(self, message):
        """Prepare a message for transmission to the explorer, and encrypt it."""
        # The dummy random numbers in the plaintext ensures each enciphered message is different
        # even if they're for the same commands.
        ciphertext = ""
        block = ""
        i = 0
        for c in message:
            block += c
            i += 1
            if i == 7:
                i = 0
                block += chr(random.randint(0, 255))
                ciphertext += self.cryptoProvider.encrypt(block)
                block = ""
        if len(block) > 0:
            # pad the last block with null bytes
            while len(block) < 7:
                block += "\0"
            block += chr(random.randint(0, 255))
            ciphertext += self.cryptoProvider.encrypt(block)
        return ciphertext
        
    def decrypt(self, ciphertext):
        """    Recover the message content from a complete block of ciphertext that was
        encrypted using encrypt()"""
        message = ""
        block = ""
        for i in range(0, len(ciphertext), 8):
            block = self.cryptoProvider.decrypt(ciphertext[i:i+8])
            message += block[:7]
        return message.strip("\0")


































        