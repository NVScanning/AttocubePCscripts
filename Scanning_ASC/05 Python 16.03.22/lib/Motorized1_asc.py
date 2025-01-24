# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 12:11:11 2024

@author: attocube
"""

import tkinter as tk
#import thorlabs_apt as apt
import asc500_device as asc


import threading
import time
from tkinter import ttk
import tkinter.messagebox as messagebox


class MotorizedStageApp(ttk.Frame):
    
    def __init__(self, master=None):
        super().__init__(master)
        # Initialization of the motors
        
        # Initialize the motorized_stage attribute
        
        title_label = ttk.Label(self, text="Motorized Stage Control")
        title_label.grid(row=0, column=0, columnspan=3, padx=5, pady=5)
        
        binPath = "01 ASC500 Installer and Data\\ASC500CL-V2.7.13\\ASC500CL-V2.7.13\\"
        
        dllPath = "04 ASC500 64bit libraries\\ASC500CL-LIB-WIN64-V2.7.13\\daisybase\\lib\\"
        
        asc500 = asc.Device(binPath, dllPath)
        
        
        asc500.base.startServer()
        
        asc500.base.sendProfile(binPath + 'AFM_SampleScan_Daisy-Profil.ngp')
        
        asc500.data.setDataEnable(1)
        asc500.base.setOutputsWaiting(1)
        
        sampTime = 1e-3
        average = 0
        chnNo = 0
        bufSize = 256
        
        asc500.data.configureChannel(chnNo,
                                      asc500.base.getConst('CHANCONN_PERMANENT'),
                                      asc500.base.getConst('CHANADC_AFMAMPL'),
                                      average,
                                      sampTime)
        
        print(asc500.data.getChannelConfig(chnNo))
        
        asc500.data.configureDataBuffering(chnNo, bufSize)
        
        
        asc500.scanner.setOutputsActive()
        
        self.x_pos = self.asc500.scanner.getPositionsXYZRel[0]
        self.y_pos = self.asc500.scanner.getPositionsXYZRel[1]
        self.z_pos = self.asc500.scanner.getPositionsXYZRel[2]

        self.step_x = 0.001
        self.step_y = 0.001
        self.step_z = 0.001
        
        # Position label
        self.label_x = tk.Label(self, text=f"X: {self.x_pos:0.5f}", font=("Helvetica", 24), bg="black", fg="green", width=12)
        self.label_y = tk.Label(self, text=f"Y: {self.y_pos:0.5f}", font=("Helvetica", 24), bg="black", fg="green", width=12)
        self.label_z = tk.Label(self, text=f"Z: {self.z_pos:0.5f}", font=("Helvetica", 24), bg="black", fg="green", width=12)

        self.label_x.bind("<Button-1>", lambda event: self.step_length_popup("x"))
        self.label_y.bind("<Button-1>", lambda event: self.step_length_popup("y"))
        self.label_z.bind("<Button-1>", lambda event: self.step_length_popup("z"))

        self.label_x.config(text=f"X: {self.x_pos:0.5f}", relief="raised")
        self.label_y.config(text=f"Y: {self.y_pos:0.5f}", relief="raised")
        self.label_z.config(text=f"Z: {self.z_pos:0.5f}", relief="raised")

        self.label_x.grid(row=0, column=0, pady=10)
        self.label_y.grid(row=0, column=1, pady=10)
        self.label_z.grid(row=0, column=2, pady=10)

        # X-axis frame
        x_frame = tk.Frame(self)
        x_frame.grid(row=1, column=0, padx=20, pady=10)

        # Add X-axis widgets like Entry boxes and buttons using grid()
        self.entry_x = tk.Entry(x_frame)
        self.entry_x.grid(row=3, column=0)
        self.entry_x.insert(0, "0.001")
        
        self.move_x_button = tk.Button(x_frame, text="Rel. Move", command=self.move_x)
        self.move_x_button.grid(row=3, column=1)

        self.entry_x_to = tk.Entry(x_frame)
        self.entry_x_to.grid(row=4, column=0)

        self.move_x_to_button = tk.Button(x_frame, text="Move To", command=self.move_x_to)
        self.move_x_to_button.grid(row=4, column=1)

        self.home_x_button = tk.Button(x_frame, text="Home", command=self.home_x)
        self.home_x_button.grid(row=5, column=0, columnspan=2)

        self.up_button = tk.Button(x_frame, text="\u25B2", command= self.move_x_up)
        self.up_button.grid(row=1, column=0, columnspan=2)


        self.down_button = tk.Button(x_frame, text="\u25BC", command= self.move_x_down)
        self.down_button.grid(row=2, column=0, columnspan=2)

        # Y-axis frame
        y_frame = tk.Frame(self)
        y_frame.grid(row=1, column=1, padx=20, pady=10)

        # Add Y-axis widgets like Entry boxes and buttons using grid()
        self.entry_y = tk.Entry(y_frame)
        self.entry_y.grid(row=3, column=0)
        self.entry_y.insert(0, "0.001")
        
        
        self.move_y_button = tk.Button(y_frame, text="Rel. Move", command=self.move_y)
        self.move_y_button.grid(row=3, column=1)

        self.entry_y_to = tk.Entry(y_frame)
        self.entry_y_to.grid(row=4, column=0)

        self.move_y_to_button = tk.Button(y_frame, text="Move To", command=self.move_y_to)
        self.move_y_to_button.grid(row=4, column=1)

        self.home_y_button = tk.Button(y_frame, text="Home", command=self.home_y)
        self.home_y_button.grid(row=5, column=0, columnspan=2)

        self.up_button = tk.Button(y_frame, text="\u25B2",  command=self.move_y_up)
        self.up_button.grid(row=1, column=0, columnspan=2)


        self.down_button = tk.Button(y_frame, text="\u25BC", command=self.move_y_down)
        self.down_button.grid(row=2, column=0, columnspan=2)

        

        # Z-axis frame
        z_frame = tk.Frame(self)
        z_frame.grid(row=1, column=2, padx=20, pady=10)

        # Add Z-axis widgets like Entry boxes and buttons using grid()
        self.entry_z = tk.Entry(z_frame)
        self.entry_z.grid(row=3, column=0)
        self.entry_z.insert(0, "0.001")
        
        self.move_z_button = tk.Button(z_frame, text="Rel. Move", command=self.move_z)
        self.move_z_button.grid(row=3, column=1)

        self.entry_z_to = tk.Entry(z_frame)
        self.entry_z_to.grid(row=4, column=0)

        self.move_z_to_button = tk.Button(z_frame, text="Move To", command=self.move_z_to)
        self.move_z_to_button.grid(row=4, column=1)

        self.home_z_button = tk.Button(z_frame, text="Home", command=self.home_z)
        self.home_z_button.grid(row=5, column=0, columnspan=2)

        self.up_button = tk.Button(z_frame, text="\u25B2", command=self.move_z_up)
        self.up_button.grid(row=1, column=0, columnspan=2)
        
        self.down_button = tk.Button(z_frame, text="\u25BC", command=self.move_z_down)
        self.down_button.grid(row=2, column=0, columnspan=2)
        

        self.closed = False

        self.periodic_position_update()
    
    
    
    def get_yz_position(self):
        
         """
         Get the current Y and Z positions of the motorized stage.
    
         Returns:
             tuple: A tuple containing the current Y and Z positions (y, z).
             
         """
         
         return self.asc500.scanner.getPositionsXYZRel[1], self.asc500.scanner.getPositionsXYZRel[2]
     
    def get_xz_position(self):
        
        """
        Get the current X and Z positions of the motorized stage.
    
        Returns:
            tuple: A tuple containing the current X and Z positions (x, z).
            
        """
        return self.asc500.scanner.getPositionsXYZRel[0], self.asc500.scanner.getPositionsXYZRel[2]

    def move_x_to(self):
        
        try:
            y_const=self.asc500.scanner.getPositionsXYZRel[1]
            x_target = round(float(self.entry_x_to.get()), 5)
            tgt=[x_target,y_const]
            self.asc500.scanner.setPositionsXYRel(tgt)
        except ValueError:
            pass


    def move_y_to(self):
        try:
            x_const=self.asc500.scanner.getPositionsXYZRel[0]
            y_target = round(float(self.entry_y_to.get()), 5)
            tgt=[x_const,y_target]
            self.asc500.scanner.setPositionsXYRel(tgt)
        except ValueError:
            pass

    def move_z_to(self):
        try:
            x_const=self.asc500.scanner.getPositionsXYZRel[0]
            y_const=self.asc500.scanner.getPositionsXYZRel[1]
            Z_target = round(float(self.entry_Z_to.get()), 5)
            tgt=[x_const,y_const,Z_target]
            self.asc500.scanner.setPositionsXYZRel(tgt)
        except ValueError:
            pass
           
    # X-button actions
    def move_x_up(self):
        y_const=self.asc500.scanner.getPositionsXYZRel[1]
        x_movement = round(abs(float(self.entry_x.get())),5)
        tgt=[x_movement,y_const]
        self.asc500.scanner.setPositionsXYRel(tgt)
   
        
    def move_x_down(self):
        y_const=self.asc500.scanner.getPositionsXYZRel[1]
        x_movement = round(-abs(float(self.entry_x.get())),5)
        tgt=[x_movement,y_const]
        self.asc500.scanner.setPositionsXYRel(tgt)
        
    # Y-button actions
    def move_y_up(self):
        x_const=self.asc500.scanner.getPositionsXYZRel[0]
        y_movement = round(abs(float(self.entry_y.get())),5)
        tgt=[y_movement,x_const]
        self.asc500.scanner.setPositionsXYRel(tgt)
   
        
    def move_y_up(self):
        x_const=self.asc500.scanner.getPositionsXYZRel[0]
        y_movement = round(-abs(float(self.entry_y.get())),5)
        tgt=[y_movement,x_const]
        self.asc500.scanner.setPositionsXYRel(tgt)
        
    def move_x(self):
        try:
            self.asc500.scanner.stopScanner
            currPos = self.asc500.positionXYZRel
            x_movement = round(float(self.entry_x.get()),5)
            self.asc500.base.setParameter(self.asc500.base.getConst('ID_PATH_GUI_X'), currPos[0], index=0)  # start point is current position
            self.asc500.base.setParameter(self.asc500.base.getConst('ID_PATH_GUI_X'), x_movement, index=1)    # target point
            time.sleep(0.05)
        except ValueError:
            pass
        
    def move_y(self):
        try:
            self.asc500.scanner.stopScanner
            currPos = self.asc500.positionXYZRel
            y_movement = round(float(self.entry_y.get()),5)
            self.asc500.base.setParameter(self.asc500.base.getConst('ID_PATH_GUI_Y'), currPos[1], index=0)  # start point is current position
            self.asc500.base.setParameter(self.asc500.base.getConst('ID_PATH_GUI_y'), y_movement, index=1)    # target point
            time.sleep(0.05)
        except ValueError:
            pass
    def move_z(self):
        try:
            self.asc500.scanner.stopScanner
            currPos = self.asc500.positionXYZRel
            z_movement = round(float(self.entry_z.get()),5)
            self.asc500.base.setParameter(self.asc500.base.getConst('ID_PATH_GUI_Y'), currPos[2], index=0)  # start point is current position
            self.asc500.base.setParameter(self.asc500.base.getConst('ID_PATH_GUI_y'), z_movement, index=1)    # target point
            time.sleep(0.05)
        except ValueError:
            pass
    def on_close(self):
        
        self.closed = True
        self.destroy()
        
if __name__ == "__main__":
    root = tk.Tk()
    app = MotorizedStageApp(root)
    app.grid()
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()  
self.asc500.scanner.setPositionsXYRel(tgt)
        


        
        
        
        
        
        
        asc500.base.stopServer()