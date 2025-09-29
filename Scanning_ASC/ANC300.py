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
    ramp: ramp upto a given value in increments of 0.05V, approx 1.5V/s = 1um/s
    step: add a chosen step to the voltage

"""

import telnetlib
import time
import numpy as np
from tkinter import ttk
import tkinter as tk


class ANC300App(ttk.Frame):
    def __init__(self, host, port):
        self.connect(host, port)
        self.abort = None
        self.moving = False

        self.x_pos = self.get_output(1, Print=False) #get initial positions
        self.y_pos = self.get_output(2, Print=False)
        self.z_pos = self.get_output(3, Print=False)
        
        self.limits_RT = 45 #upper limit for room temperature [V]
        self.limits_LT = 112.5 #upper limit for low temperature [V]
        #self.range_xyRT = 30
        #self.range_xyLT = 15
        
        self.update_T(293) #set initial temperature to 293K and update voltage limits accordingly
        #self.conversion_xy = self.limits/self.range_xy
        
    def connect(self, host, port): #connect to the machine
        self.tn = telnetlib.Telnet(host, port)
        self.tn.read_until(b"Authorization code: ")
        self.tn.write(b"123456\n") #returns authorization code
        self.tn.read_until(b"> ")
        self.do("echo off")
        
        for i in range(3):
            self.do(f"setm {i+1} off", sleeptime=0.1) #set all axis to offset mode
        print('connected')
        
    def update_T(self, temp):
        self.T = float(temp)
        self.limits = self.limits_LT + (temp-4)*(self.limits_LT-self.limits_RT)/(4-300) #temperature dependent limit [V]
        #print(self.limits)
        
    def do(self, command, Print=True, sleeptime=0.05): #send a command to the machine
        cmd = command + "\n"
        
        if command.split()[0] == "seta" and float(command.split()[2]) > self.limits: #check if voltage to be set is inside of the range
            print(f"Voltage outside of limits (0, {self.limits}V)")
            return
        
        self.tn.write(cmd.encode('ascii')) #give command to console
        time.sleep(sleeptime) #wait for console output
        output = self.tn.read_very_eager().decode('utf-8') #read output from console
            
        if Print == True:
            print(output) #print console output
        
        return output
    
    def get_output(self, axis, Print=True): #return offset voltage
        output_string = self.do(f"geto {axis}", Print=Print) #change to geto for measured output voltage       
        return float(output_string.split()[2])
            
    def ramp(self, axis, voltage, label=None): #currently approx 0.1V/s
        self.abort = False
        self.moving = True
        t1 = time.time()
    
        #print(f"target: {voltage}")
        if float(voltage) > self.limits or float(voltage) < 0:
            print(f"Voltage outside of limits (0, {self.limits}V)")
            return
        
        self.do("echo off", Print=False)
        V_0 = float(self.do(f"geto {axis}", sleeptime=0.1, Print = False).split()[2]) #starting value
        #print(f"start: {V_0}")
        
        
        #step0 = int(np.ceil((np.absolute(voltage - V_0))/0.2))
        #stepsize = float((np.absolute(voltage - V_0))/(step0+1))
        #print (step0, stepsize)
        #print(np.linspace(V_0, voltage, step0, endpoint = True) )
        
        
        if (V_0 == voltage) != True:
        
            steps = np.arange(V_0, float(voltage), 0.1*np.sign(np.sign(voltage-V_0))) + 0.1*np.sign(voltage-V_0)  #split into steps of 0.05 V
            #print(steps)
            
            for step in steps:
                
                if self.abort == False:
                    self.do(f"seta {axis} {step}", Print=False, sleeptime=0.02)
                    
                    if type(label) != type(None):
                        
                        try:
                            label.set(f"{self.get_output(axis, Print=False)} V")
                            
                        except:
                            #print("second try:")
                            label.set(f"{self.get_output(axis, Print=False)} V") #try again if the output wasn't there yet
                                
                    
                else:
                    break
        
            
        self.do(f"geta {axis}", Print = False)
        self.moving = False
        t2 = time.time()
        
        #if (V_0 == voltage) != True:
        #    print(f"time: {t2-t1}s, avg: {(t2-t1)/(voltage-V_0)}s")
        
        
    def step(self, axis, step):
        self.moving = True
        self.do("echo off")
        V_0 = float(self.do(f"geto {axis}").split()[2]) #starting value
        if float(V_0+step) > self.limits or float(V_0+step) < 0:
            print(f"Voltage outside of limits (0, {self.limits}V)")
            return
        
        self.do(f"seta {axis} {V_0+step}")
        self.moving = False
        
    
    def close(self): #close connection with machine
        self.tn.close()

# host = "192.168.10.2" #ANC 300 IP
# port = 7230 #standard console port

# tn = ANC300App(host, port) #connect to machine

# tn.get_output(1, Print=False)

# print(f"x: {tn.x_pos}, y: {tn.y_pos}, z: {tn.z_pos}")

# for i in range(3):
#     tn.do(f"setm {i+1} gnd") #set all axis to offset mode
    
# for temp in [2, 4, 150, 300]:
#     tn.update_T(temp)
    
# t1 = time.time()

# tn.ramp(1, 0, label=1)
# tn.ramp(2, 20)
# t2 = time.time()

# tn.step(1, 0.1)


# print(f"Ramp time: {t2 -t1}s, avg:{(t2-t1)/20}")

# tn.do("geta 1") #get offset voltage axis 1
# tn.do("seta 1 0.3") #set offset voltage axis 1
# tn.do("geta 1")
# tn.do("geto 1")
# output = tn.get_output(1)
# tn.do("seta 1 0")
# tn.do("getm 3")

# tn.do("seta 1 0")

# for i in range(3):
#     tn.ramp(i+1, 0)
#     tn.do(f"setm {i+1} gnd") #set all axis to offset mode
    
# tn.close()




