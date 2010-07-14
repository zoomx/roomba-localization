--------------------------------------
Author: River Allen
Contact: riverallen@gmail.com
Date: June 08 2010
--------------------------------------
Requirements:
 * Python 2.6
 * PySerial
 * Numpy
 * Scipy
 * Matplotlib


This is known to work on Windows Vista.

You need to install python 2.6 (2.4+ probably works) and pySerial (can be found here: 
http://sourceforge.net/projects/pyserial/files/).

Run uartMain.py.
I would recommend running this in command prompt (you can see errors if program crashes). How
to do this:
 - Start -> Run -> type 'cmd'
 - use 'cd' to navigate to the workspace directory of this project
 - type 'python uartMain.py'

I have not implemented the cleanest exit yet, so just type 'exit' in the input window or Ctrl + C.

Change globalConfig for your needs. If you cannot connect to a device that is plugged in:
 - Did not change globalConfig
 - Not plugged in
 - Not the COM port you think it is
 - Something else is using that port (RealTerm, AVRDude or another uartMain)

This can also be reciprocal. If AVRDude is not working, for example, it may be because uartMain is active.
 