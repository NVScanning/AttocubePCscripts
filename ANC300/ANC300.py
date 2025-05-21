# -*- coding: utf-8 -*-
"""
Created on Fri May 16 13:33:32 2025

@author: Lotte

Connect to ANC300 via telnet

commands:
    getm/setm <Axis>: get/set the mode of the axis - gnd (disables all outputs), off (offset mode), more (see manual)
    geta/seta <Axis>: get/set offset voltage on the axis (range between 0-3V at RT and 0-7.5V at LT)
    echo <on/off>: turn console echo on/off
    See manual for other commands

Class functions:
    do: give a direct command to the console
    ramp: ramp upto a given value in increments of 50nm, approx 0.1V/s
    step: add a chosen step to the voltage

"""

import telnetlib
import time
import numpy as np

class TelnetFunction:
    def __init__(self, host, port):
        self.connect(host, port)
        
    def connect(self, host, port): #connect to the machine
        self.tn = telnetlib.Telnet(host, port)
        self.tn.read_until(b"Authorization code: ")
        self.tn.write(b"123456\n") #returns authorization code
        self.tn.read_until(b"> ")
        print('connected')
        
    def do(self, command, Print=True, sleeptime=0.05): #send a command to the machine
        cmd = command + "\n" 
        self.tn.write(cmd.encode('ascii')) #give command to console
        time.sleep(sleeptime) #wait for console output
        output = self.tn.read_very_eager().decode('utf-8') #read output from console
        # for i, out in enumerate(output.split()):
        #     print(f"{i}: {out}")
            
        if Print == True:
            print(output) #print console output
        
        return output
            
    def ramp(self, axis, voltage): #currently approx 0.1V/s
        self.do("echo off")
        V_0 = float(self.do(f"geta {axis}").split()[2]) #starting value
        print(V_0)
        steps = np.arange(V_0, float(voltage), 0.005) + 0.005 #split into steps of 50nm
        print(steps)
        for step in steps:
            self.do(f"seta {axis} {step}", Print=False, sleeptime=0.04)
            
        self.do(f"geta {axis}")
        
    def step(self, axis, step):
        self.do("echo off")
        V_0 = float(self.do(f"geta {axis}").split()[2]) #starting value
        self.do(f"seta {axis} {V_0+step}")
        
    
    def close(self): #close connection with machine
        self.tn.close()

host = "192.168.10.2" #ANC 300 IP
port = 7230 #standard console port

tn = TelnetFunction(host, port) #connect to machine
for i in range(3):
    tn.do(f"setm {i+1} off") #set all axis to offset mode
    
t1 = time.time()
tn.ramp(1, 0.5)
t2 = time.time()

tn.step(1, 0.1)

tn.do("echo on")

print(f"Ramp time: {t2 -t1}s, avg:{(t2-t1)/20}")

tn.do("geta 1") #get offset voltage axis 1
tn.do("seta 1 0.1") #set offset voltage axis 1
tn.do("geta 1")
tn.do("seta 1 0")
tn.do("getm 3")

for i in range(3):
    tn.ramp(i, 0)
    tn.do(f"setm {i+1} gnd") #set all axis to offset mode
    
tn.close()




