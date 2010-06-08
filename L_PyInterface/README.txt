This works on Windows.

You need to install python 2.6 (2.4+ probably works) and pySerial.

Run uartMain.py.
I would recommend running this in command prompt (you can see errors if program crashes).

I have not implemented a clean exit yet, so just use Ctrl + C.

Change globalConfig for your needs. If you cannot connect to a device that is plugged in:
 - Did not change globalConfig
 - Not plugged in
 - Not the COM port you think it is
 - Something else is using that port (RealTerm, AVRDude or another uartMain)
