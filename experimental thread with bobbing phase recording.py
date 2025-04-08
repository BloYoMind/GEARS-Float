import socket
from utime import sleep, ticks_ms
from machine import Pin, SoftI2C
from _thread import start_new_thread
from ads1x15 import ADS1115

# Defaults
html = ''
start_time = 0

# DEBUG MODE
debugMode = False

if debugMode == True:
    from random import uniform

# HTTP webserver code (It WORKS. Don't ask how.)
def webserver():
    global html
    
    addr = socket.getaddrinfo('192.168.4.1', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)

    print('Listening on ' + str(addr) + '.')
    try:
        while True:
            cl, addr = s.accept()
            print('Client connected from ' + str(addr) + '.')
            cl_file = cl.makefile('rwb', 0)
            while True:
                line = cl_file.readline()
                if not line or line == b'\r\n':
                    break
            cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            cl.send(html)
            cl.close()
    except OSError as e:
            print(e)
    
# Ported Arduino map function for later use
def _map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

# Class that controls all the hardware functions
class SquidControl():

    # Initialize variables
    def __init__(self):
        global debugMode
        self.light = Pin(33, Pin.OUT)
        self.light.off()
        if debugMode == False:
            self.pressure = ADS1115(SoftI2C(scl = Pin(2, Pin.IN, Pin.PULL_UP), sda = Pin(4, Pin.IN, Pin.PULL_UP)))
        self.syringeOut = Pin(25, Pin.OUT)
        self.syringeOut.off()
        self.syringeIn = Pin(5, Pin.OUT)
        self.syringeIn.off()
        
    # Compress syringe and push water out
    def surface(self, seconds = 1):
        self.syringeOut.on()
        sleep(seconds)
        self.syringeOut.off()
    
    # Do that in a non-blocking way
    def surfaceThread(self, seconds = 1):
        def action(seconds):
            self.syringeOut.on()
            sleep(seconds)
            self.syringeOut.off()
        start_new_thread(action, (seconds,))
    
    # Extend syringe and pull water in
    def sink(self, seconds = 1):
        self.syringeIn.on()
        sleep(seconds)
        self.syringeIn.off()
        
    # Do that in a non-blocking way
    def sinkThread(self, seconds = 1):
        def action(seconds):
            self.syringeIn.on()
            sleep(seconds)
            self.syringeIn.off()
        start_new_thread(action, (seconds,))

    # Toggle the LED light on or off
    def toggleLight(self):
        self.light.value(int(not self.light.value()))
        
    # Blink the light a specified number of times at a specified speed
    def blinkLight(self, times, rate):
        def action(times, rate):
            for i in range(times):
                self.light.on()
                sleep(rate)
                self.light.off()
                sleep(rate)
        start_new_thread(action, (times, rate))
        
    # Get the current pressure reading from the pressure sensor
    def getPressure(self):
        if debugMode == False:
            return round(_map(self.pressure.raw_to_v(self.pressure.read()), 0.5, 4.5, 0, 30) * 6.89476 + 101.325 + 4.56, 2)
        else:
            return round(uniform(100.000, 130.000), 2)
    
    # Record data going either up or down
    def record(self, direction):
        global startTime
        print('Going ' + direction + '.')
        profileData = []
        for i in range(8):
            dataPoint = []
            dataPoint.append(str(round((ticks_ms() - startTime)/1000, 2)))
            currentPressure = self.getPressure()
            dataPoint.append(str(currentPressure))
            dataPoint.append(str(round((currentPressure - 101.325) / 9.78, 2)))
            print('Data packet:', dataPoint)
            profileData.append(dataPoint)
            sleep(5)
        return profileData
    
    # Handle the bobbing action in a separate thread
    def bobbingThread(self, bobbingDuration):
        def action():
            endTime = ticks_ms() + (bobbingDuration * 1000)
            while ticks_ms() < endTime:
                self.surface(seconds=1)
                self.sink(seconds=1)
        start_new_thread(action, ())

def main():
    # Declare global variables
    global startTime, html
    
    # Record the start time
    startTime = ticks_ms()
    
    # Constants for easily changing the timing of the float
    sinkSec = 6
    surfaceSec = 6
    waitSurfaceSec = 45
    bobbingDuration = 45 # Duration to bob up and down
    numProfiles = 3
    
    # Create an instance of the SquidControl class
    squid = SquidControl()
    
    # Blink the light so the operator knows the float is alive
    squid.blinkLight(3, 0.5)
    
    # Bring in the HTML files
    with open('head.html','r') as h:
        with open('profileStart.html','r') as pS:
            with open('row.html','r') as r:
                with open('profileEnd.html','r') as pE:
                    with open('foot.html','r') as f:
                        head = h.read()
                        profileStart = pS.read()
                        row = r.read()
                        profileEnd = pE.read()
                        foot = f.read()
    
    # Craft an initial transmission
    initialPressure = squid.getPressure()
    head = head % (str(round((ticks_ms() - startTime) / 1000, 2)), initialPressure, round((initialPressure - 101.325) / 9.78, 2))
    html = head + foot
    
    # Start the webserver thread
    start_new_thread(webserver, ())
    
    # Run a quick motor test
    squid.sink(seconds=0.5)
    sleep(0.2)
    squid.surface(seconds=0.5)
    
    # Give the operator time to establish a connection
    sleep(waitSurfaceSec)
    
    profiles = []
    for i in range(numProfiles):
        print('Starting profile ' + str(i + 1) + '.')
        
        # Sink the float
        squid.sinkThread(seconds=sinkSec)
        
        # Record until it hits bottom
        profileData = squid.record('down')
        
        # Check if it has reached 2.5 meters depth
        currentDepth = (squid.getPressure() - 101.325) / 9.78
        if currentDepth >= 2.5:
            print("Reached 2.5 meters, bobbing up and down for 45 seconds.")
            
            # Start bobbing in a separate thread
            squid.bobbingThread(bobbingDuration)
        
        # Continue sinking until the bottom
        squid.sinkThread(seconds=sinkSec)
        profileData += squid.record('down')
        
        # Float the float
        squid.surfaceThread(seconds=surfaceSec)
        
        # Record until it hits the surface
        profileData += squid.record('up')
        
        # Add the new data to the list of profiles
        profiles.append(profileData)
        
        # Generate the HTML for the webpage
        number = 1
        profilesHTML = ''
        for z in profiles:
            profileBody = ''
            for x in z:
                profileBody += row % tuple(x)
            profilesHTML += ((profileStart % str(number)) + profileBody + profileEnd)
            number += 1
            
        html = head + profilesHTML + foot
        print('Completed profile ' + str(i + 1) + '.')
        print('New HTML posted.')
        
        # Blink the light to indicate progress
        squid.blinkLight(5, 0.25)
        
        # Give the operator time to establish a connection
        sleep(waitSurfaceSec)
    
    print('Completed ' + str(numProfiles) + ' profiles.')

# Run main function
main()
