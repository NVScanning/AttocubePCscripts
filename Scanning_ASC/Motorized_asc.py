# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 17:38:03 2024

@author: attocube
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 12:11:11 2024

@author: attocube
"""

import tkinter as tk

import ASC_500.asc500_device as asc

import threading
import time
from tkinter import ttk
import tkinter.messagebox as messagebox

from pl_module import PLModule


class AscStageApp(ttk.Frame):
    
    def __init__(self, master=None):
        super().__init__(master)
        # Initialization of the motors
        #self.master = master
        self.pl_module = PLModule()

        # Initialize the motorized_stage attribute
        
        #title_label = ttk.Label(self, text="Motorized Stage Control")
        #title_label.grid(row=0, column=0, columnspan=3, padx=5, pady=5)
        self.currPos_lock = threading.Lock()
        binPath = "01 ASC500 Installer and Data\\ASC500CL-V2.7.13\\ASC500CL-V2.7.13\\"

        dllPath = "04 ASC500 64bit libraries\\ASC500CL-LIB-WIN64-V2.7.13\\daisybase\\lib\\"
        
        self.asc500 = asc.Device(binPath, dllPath)
        
        self.asc500.base.startServer() #Connect to server - opens a new one if none exists       
        self.asc500.data.setDataEnable(1)
        self.asc500.base.setOutputsWaiting(1)
        self.asc500.scanner.setOutputsActive()
        
        #Check configured channels
        # for chnNo in range(13):
        #     print(chnNo, self.asc500.data.getChannelConfig(chnNo))
        
        #Temperature and Travel limits
        self.asc500.limits.setTemperature(293.2) #kelvin
        self.X_Travel_lim=self.asc500.limits.getXActualTravelLimit()
        self.Y_Travel_lim=self.asc500.limits.getYActualTravelLimit()
        #self.Z_Travel_lim=self.asc500.limits.getZActualTravelLimit()
        self.closed = False
        # self.lock = threading.Lock()
       
        self.currPos = self.asc500.scanner.getPositionsXYRel()
        self.x_pos = self.currPos[0]
        self.y_pos = self.currPos[1]
  
        print(f'first_pos: { self.currPos}')
        

        #self.z_pos = self.currPos[2]

        self.step_x = 1.000
        self.step_y = 1.000
        #self.step_z = 1.000f
        
        # Position label
        self.label_x = tk.Label(self, text=f"X: {self.x_pos:0.5f}", font=("Helvetica", 24), bg="black", fg="green", width=12)
        self.label_y = tk.Label(self, text=f"Y: {self.y_pos:0.5f}", font=("Helvetica", 24), bg="black", fg="green", width=12)
        # self.label_z = tk.Label(self, text=f"Z: {self.z_pos:0.5f}", font=("Helvetica", 24), bg="black", fg="green", width=12)
        
        self.label_x.bind("<Button-1>", lambda event: self.step_length_popup("x"))
        self.label_y.bind("<Button-1>", lambda event: self.step_length_popup("y"))
        # self.label_z.bind("<Button-1>", lambda event: self.step_length_popup("z"))
        
        self.label_x.config(text=f"X: {self.x_pos:0.5f}", relief="raised")
        self.label_y.config(text=f"Y: {self.y_pos:0.5f}", relief="raised")
        # self.label_z.config(text=f"Z: {self.z_pos:0.5f}", relief="raised")
        
        self.label_x.grid(row=0, column=0, pady=10)
        self.label_y.grid(row=0, column=2, pady=10)
        # self.label_z.grid(row=0, column=1, pady=10)
        
        # X-axis frame
        x_frame = tk.Frame(self)
        x_frame.grid(row=1, column=0, padx=20, pady=10)
        
        # Add X-axis widgets like Entry boxes and buttons using grid()
        self.entry_x = tk.Entry(x_frame)
        self.entry_x.grid(row=3, column=0)
        self.entry_x.insert(0, "1.000") # um
        
        self.move_x_button = tk.Button(x_frame, text="Rel. Move", command=lambda: threading.Thread(target=self.move_x).start())

        self.move_x_button.grid(row=3, column=1)
        
        self.entry_x_to = tk.Entry(x_frame)
        self.entry_x_to.grid(row=4, column=0)
        
        self.move_x_to_button = tk.Button(x_frame, text="Move To", command=lambda: threading.Thread(target=self.move_x_to).start())
        self.move_x_to_button.grid(row=4, column=1)
        
        # self.home_x_button = tk.Button(x_frame, text="Home", command=self.home_x)
        # self.home_x_button.grid(row=5, column=0, columnspan=2)
        
        self.up_button = tk.Button(x_frame, text="\u25B6", command=lambda: threading.Thread(target=self.move_x_up).start())
        self.up_button.grid(row=1, column=1)
        
        self.down_button = tk.Button(x_frame, text="\u25C0", command=lambda: threading.Thread(target=self.move_x_down).start())
        self.down_button.grid(row=1, column=0)
        
        # Y-axis frame
        y_frame = tk.Frame(self)
        y_frame.grid(row=1, column=2, padx=20, pady=10)
        
        # Add Y-axis widgets like Entry boxes and buttons using grid()
        self.entry_y = tk.Entry(y_frame)
        self.entry_y.grid(row=3, column=0)
        self.entry_y.insert(0, "1.000") # mikron
        
        self.move_y_button = tk.Button(y_frame, text="Rel. Move", command=lambda: threading.Thread(target=self.move_y).start())

        self.move_y_button.grid(row=3, column=1)
        
        self.entry_y_to = tk.Entry(y_frame)
        self.entry_y_to.grid(row=4, column=0)
        
        self.move_y_to_button = tk.Button(y_frame, text="Move To", command=lambda: threading.Thread(target=self.move_y_to).start())

        self.move_y_to_button.grid(row=4, column=1)
        
        # self.home_y_button = tk.Button(y_frame, text="Home", command=self.home_y)
        # self.home_y_button.grid(row=5, column=0, columnspan=2)
        
        self.up_button = tk.Button(y_frame, text="\u25B6", command=lambda: threading.Thread(target=self.move_y_up).start())

        self.up_button.grid(row=0, column=1)
        
        self.down_button = tk.Button(y_frame, text="\u25C0", command=lambda: threading.Thread(target=self.move_y_down).start())

        self.down_button.grid(row=0, column=0)
        
        # Z-axis frame
        z_frame = tk.Frame(self)
        z_frame.grid(row=1, column=1, padx=20, pady=10, sticky="nsew")
        z_frame.config(width=200, height=200) # Adjust width and height for aesthetic purposes
        
        # The Z-frame is used only as a separator, no widgets needed inside it
        

        self.iterator = 0 

        self.periodic_position_update()
        
        
    
    

     
    def get_xy_position(self):
        
        """
        Get the current X and Z positions of the motorized stage.
    
        Returns:
            tuple: A tuple containing the current X and Z positions (x, z).
            
        """
        pos =  self.asc500.scanner.getPositionsXYRel()
        time.sleep(0.005)
        print(f'x_curr: {pos[0]}')
        return pos[0], pos[1]
    
    def move(self, x, y):
        pos =self.asc500.scanner.getPositionsXYRel()
        # x_const= curr_pos[0]
        x = round(abs(float(x)), 10) #mm convert
        y = round(abs(float(y)), 10) #mm convert
        # print(self.iterator)
        # self.iterator += 1
        #tgt_x=abs(x_const+val)
        tgt = [x , y]
        # print(f'MyxTarget: {tgt}')
        if (0 <= x < self.X_Travel_lim ) and (0 <= y < self.Y_Travel_lim ):
            self.asc500.scanner.setPositionsXYRel(tgt, pos)
            time.sleep(0.0005)
            while(abs(pos[0] - x) > 0.001e-6 or abs(pos[1] - y) > 0.001e-6):
                # print(f'x_while {[abs(x - pos[0]), abs(x - pos[0]) > 1e-7]}')
                # print(f'y_while {[abs(y - pos[0]), abs(y - pos[1]) > 1e-7]}')
                pos = self.asc500.scanner.getPositionsXYRel()
                with self.currPos_lock:
                    self.currPos = pos
                #print(f'while_y1: {pos}')
                time.sleep(0.005)
                # print(f"the iterartor {self.iterator}")
            #with self.lock:
           
        
        #print("done moving!")
        
    def collect_moving(self,velocity, x, y):
        pos =self.asc500.scanner.getPositionsXYRel()
        # x_const= curr_pos[0]
        x = round(abs(float(x)), 10) #mm convert
        y = round(abs(float(y)), 10) #mm convert
        # print(self.iterator)
        # self.iterator += 1
        #tgt_x=abs(x_const+val)
        self.asc500.scanner.setPositioningSpeed(velocity)
        tgt = [x , y]
        # print(f'MyxTarget: {tgt}')
        if (0 <= x < self.X_Travel_lim ) and (0 <= y < self.Y_Travel_lim ):
            self.asc500.scanner.setPositionsXYRel(tgt, pos)
            time.sleep(0.0005)
            while(abs(pos[0] - x) > 0.001e-6 or abs(pos[1] - y) > 0.001e-6):
                # print(f'x_while {[abs(x - pos[0]), abs(x - pos[0]) > 1e-7]}')
                # print(f'y_while {[abs(y - pos[0]), abs(y - pos[1]) > 1e-7]}')
                pos = self.asc500.scanner.getPositionsXYRel()
                with self.currPos_lock:
                    self.currPos = pos
                #print(f'while_y1: {pos}')
                time.sleep(0.005)
                # print(f"the iterartor {self.iterator}")
            #with self.lock:
           
        
        #print("done moving!")

    def move_x_to(self, val=None):
        if val is None:
            try:
                pos =self.asc500.scanner.getPositionsXYRel()
                y_const=pos[1]
               # x_const= curr_pos[0]
                val = round(abs(float(self.entry_x_to.get())*1e-6), 10) #nm convert
                #tgt_x=abs(x_const+val)
                tgt =[val , y_const]
                
                if (0 <= val < self.X_Travel_lim ):
                    
                    self.asc500.scanner.setPositionsXYRel(tgt,pos)
                    time.sleep(0.0005)
                    while (abs(pos[0] - val) > 0.001e-6):
                        pos = self.asc500.scanner.getPositionsXYRel()
                        with self.currPos_lock:
                            
                            self.currPos = pos
                        time.sleep(0.005)
                    
                    
                else:
                    print(f'Xtarget limit= {self.X_Travel_lim}, exceeded!')
                    pass
            except ValueError:
                
                pass
        else:
            try:
                b=time.time()
                pos =self.asc500.scanner.getPositionsXYRel()
                y_const=pos[1]
                # x_const= curr_pos[0]
                val = round(abs(float(val)), 10) #mm convert
                #tgt_x=abs(x_const+val)
                tgt = [val , y_const]
                #print(f'MyxTarget: {tgt}')
                if (0 <= val < self.X_Travel_lim ):
                    self.asc500.scanner.setPositionsXYRel(tgt,pos)
                    time.sleep(0.0005)
                    while (abs(pos[0] - val) > 0.001e-6):
                        pos = self.asc500.scanner.getPositionsXYRel()
                        with self.currPos_lock:
                            self.currPos = pos
                        #print(f'while_x: {pos}')
                        time.sleep(0.005)
                   
                    
        
                else:
                    print(f'Xtarget limit = {self.X_Travel_lim}, exceeded!')
                    pass
                e=time.time()
                print(f'move_x_to time passed= {e- b}')
            except ValueError:
                pass


    def move_y_to(self, val=None):
        if val is None:
            try:
                pos =self.asc500.scanner.getPositionsXYRel()
                y_const=pos[1]
                x_const= pos[0]
                val = round(abs(float(self.entry_y_to.get())*1e-6), 10) #mm convert
                #tgt_y=abs(y_const+val)
                tgt =[x_const, val]
                if (0 <= val < self.Y_Travel_lim ):
                    self.asc500.scanner.setPositionsXYRel(tgt, pos)
                    time.sleep(0.0005)
                    while (abs(pos[1] - val) > 0.001e-6):
                        pos = self.asc500.scanner.getPositionsXYRel()
                        with self.currPos_lock:
                            self.currPos = pos
                       
                        time.sleep(0.005)
        
                    
                    
                else:
                    print(f'Xtarget limit = {self.Y_Travel_lim}, exceeded!')
                    pass
            except ValueError:
                pass
        else:
            try:
                b=time.time()
                pos =self.asc500.scanner.getPositionsXYRel()
                #y_const=curr_pos[1]
                x_const= pos[0]
                val = round(abs(float(val)), 10) #mm convert
                #tgt_y=abs(y_const+val)
                tgt = [x_const, val]
                #print(f'MyyTarget: {tgt}')
                if (0 <= val < self.Y_Travel_lim ):
                    self.asc500.scanner.setPositionsXYRel(tgt,pos)
                    time.sleep(0.0005)
                    while (abs(pos[1] - val) > 0.001e-6):
                        pos = self.asc500.scanner.getPositionsXYRel()
                        with self.currPos_lock:
                            self.currPos = pos
                        #print(f'while_y2: {pos}')
                        time.sleep(0.005)
                
                    

                else:
                    print(f'Ytarget limit = {self.Y_Travel_lim}, exceeded!')
                    pass
                e=time.time()
                print(f'move_y_to time passed= {e- b}')
            except ValueError:
                pass

           
    # X-button actions
    def move_x_up(self):
        pos =self.asc500.scanner.getPositionsXYRel()
    
        #print(curr_pos)
        x_const= pos[0]
        y_const= pos[1]
        val = round(abs(float(self.entry_x.get())*1e-6), 10) #nm convert
        #print(val)
        tgt_x=abs(x_const+val)
        print(f'my target val: {tgt_x}')
        tgt=[tgt_x,y_const]
        if (0 <= tgt_x < self.X_Travel_lim ):
            self.asc500.scanner.setPositionsXYRel(tgt,pos)
            time.sleep(0.0005)
            while (abs(pos[0] - tgt_x) > 0.001e-6):
               
                pos = self.asc500.scanner.getPositionsXYRel()
                with self.currPos_lock:
                    self.currPos = pos   
                time.sleep(0.005)
                
            print(f'New position : {self.currPos}')
        else:
            print(f'Xtarget limit {self.X_Travel_lim} exceeded')
            pass

               
       
        
    def move_x_down(self):
         pos = self.asc500.scanner.getPositionsXYRel()
         print(pos)
         x_const= pos[0]
         y_const= pos[1]
         val = round(-abs(float(self.entry_x.get())*1e-6), 10) #nm convert
         print(val)
         tgt_x=abs(x_const+val)
         tgt=[tgt_x,y_const]
         if (0 <= tgt_x < self.X_Travel_lim ):
             self.asc500.scanner.setPositionsXYRel(tgt,pos)
             time.sleep(0.0005)
             while (abs(pos[0] - tgt_x) > 0.001e-6):
                 pos = self.asc500.scanner.getPositionsXYRel()
                 with self.currPos_lock:
                    self.currPos = pos
                 time.sleep(0.005)
                 #print("Still in loop!")
    
         else:
             print(f'Xtarget limit {self.X_Travel_lim} exceeded')
             pass
       
        
    # Y-button actions
    def move_y_up(self):
         pos =self.asc500.scanner.getPositionsXYRel()
      
         x_const= pos[0]
         y_const= pos[1]
         val = round(abs(float(self.entry_y.get())*1e-6), 10) #nm convert
         print(val)
         tgt_y=abs(y_const+val)
         tgt=[x_const, tgt_y]
         if (0 <= tgt_y < self.Y_Travel_lim ):
             self.asc500.scanner.setPositionsXYRel(tgt,pos)
             time.sleep(0.0005)
             while (abs(pos[1] - tgt_y) > 0.001e-6):
                 pos = self.asc500.scanner.getPositionsXYRel()
                 with self.currPos_lock:
                    self.currPos = pos
                 time.sleep(0.005)
                 print("Still in loop!")
      

         else:
             print(f'Xtarget limit {self.Y_Travel_lim} exceeded')
             pass
   
        
    def move_y_down(self):
         pos =self.asc500.scanner.getPositionsXYRel() 

         x_const= pos[0]
         y_const= pos[1]
         val = round(-abs(float(self.entry_y.get())*1e-6), 10) #nm convert
         tgt_y=abs(y_const+val)
         tgt=[x_const, tgt_y]
         if (0 <= tgt_y < self.Y_Travel_lim ):
             self.asc500.scanner.setPositionsXYRel(tgt,pos)
             time.sleep(0.0005)
             while (abs(pos[1] - tgt_y) > 0.001e-6):
                 pos = self.asc500.scanner.getPositionsXYRel()
                 with self.currPos_lock:
                    self.currPos = pos
                 time.sleep(0.005)
                 print("Still in loop!")


         else:
             print(f'Xtarget limit {self.Y_Travel_lim} exceeded')
             pass


       
    def move_x(self, val):

        b=time.time()
        curr_pos =self.asc500.scanner.getPositionsXYRel()
        y_const=curr_pos[1]
        # x_const= curr_pos[0]
        val = round(abs(float(val)), 10) #mm convert
        #tgt_x=abs(x_const+val)
        tgt = [val , y_const]
        print(f'MyxTarget: {tgt}')
        if (0 <= val < self.X_Travel_lim ):
            self.asc500.scanner.setPositionsXYRel(tgt)
            time.sleep(0.0005)

        else:
            print(f'Xtarget limit = {self.Y_Travel_lim}, exceeded!')
            pass
        e=time.time()
        print(f'move_x time passed= {e- b}')
        

        
    def move_y(self, val):
        b=time.time()
        curr_pos =self.asc500.scanner.getPositionsXYRel()
        x_const= curr_pos[0]
        val = round(abs(float(val)), 10) #mm convert
        tgt = [x_const, val]
        print(f'MyyTarget: {tgt}')
        if (0 <= val < self.Y_Travel_lim ):
            self.asc500.scanner.setPositionsXYRel(tgt)
            time.sleep(0.0005)

        else:
            print(f'Ytarget limit = {self.Y_Travel_lim}, exceeded!')
            pass
        e=time.time()
        print(f'move_y time passed= {e- b}')
     

        
    def close(self):
        #self.asc500.base.stopServer()
        #self.closed = True
        # self.asc500.scanner.closeScanner()
        # self.asc500.base.stopServer()
        self.asc500.scanner.stopScanner()
        self.destroy()
      

            
    def periodic_position_update(self):
     if not self.closed:
         
         with self.currPos_lock:
            
             self.x_pos = round(self.currPos[0] / 1e-6, 3)
             self.y_pos = round(self.currPos[1] / 1e-6, 3)
             #print(f'curr_upd: {self.currPos}')
      
             self.label_x.config(text=f"X: {self.x_pos:0.3f}")
             self.label_y.config(text=f"Y: {self.y_pos:0.3f}")

         self.after(100, self.periodic_position_update)

             
            
if __name__ == "__main__":
    root = tk.Tk()
    app = AscStageApp(root)
    app.grid()
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()  