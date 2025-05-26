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
from ANC300 import ANC300App
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
  
        print(f'first_pos: {self.currPos}')
        
        self.step_x = 1.000
        self.step_y = 1.000
        
        host = "192.168.10.2" #ANC 300 IP
        port = 7230 #standard console port
        self.ANC = ANC300App(host, port) #connect to machine
        
        style = ttk.Style()
        style.theme_use("vista")
        
        style.configure(
            "Std.TLabel",
            foreground="#000",
            background="#EDECEC",
            anchor="tk.center",
            font=("Helvetica", 11)
        )
        style.configure(
            "Txt.TLabel",
            foreground="#000",
            background="#fff",
            anchor="center",
            font=("Helvetica", 10),
            borderwidth=2,
            relief="groove"
        )

        style.configure(
            "Std.TButton",
            foreground="#000",
            background="#E4E2E2",
            width=3,
            font=("Helvetica", 10)
        )
        
        
        #create frame for ASC scanning
        ASC_frame = tk.Frame(self, highlightbackground="#99b3e6", highlightthickness=1, padx=20, pady=5)
        ASC_frame.grid(row=0, column=0, pady=(0,20), ipady=5)
        ASC_frame.grid_columnconfigure(0, weight=1)
        ASC_title = ttk.Label(master=ASC_frame, text="Sample motors", font=("Helvetica",12))
        ASC_title.grid(row=0, columnspan=7, padx=10, pady=(0,5))
        
        #create frame for ANC
        ANC_frame = tk.Frame(self, highlightbackground="#99b3e6", highlightthickness=1, padx=20, pady=5)
        ANC_frame.grid(row=1, column=0, ipady=5)
        ANC_title = ttk.Label(master=ANC_frame, text="Tip motors", font=("Helvetica",12))
        ANC_title.grid(row=0, columnspan=7, padx=10)
        
                
        #Labels
        ASC_label = ttk.Label(master=ASC_frame, text="Step [um]", style="Std.TLabel", width=12)
        ASC_label1 = ttk.Label(master=ASC_frame, text="Move To [um]", style="Std.TLabel", width=12)
        ASC_label2 = ttk.Label(master=ASC_frame, text="Position [um]", style="Std.TLabel", width=12)
        ASC_label3 = ttk.Label(master=ASC_frame, text="X", style="Std.TLabel", padding=[10,0])
        ASC_label4 = ttk.Label(master=ASC_frame, text="Y", style="Std.TLabel", padding=[10,0])
        ASC_label.grid(column=4, row=1, padx=10, pady=5)
        ASC_label1.grid(column=2, row=1, padx=10, pady=5)
        ASC_label2.grid(column=1, row=1, padx=10, pady=5)
        ASC_label3.grid(column=0, row=2, padx=10, pady=5)
        ASC_label4.grid(column=0, row=3, padx=10, pady=5)
        
        #Position lables
        ASC_PosX_var = tk.StringVar() #Dynamic tk variable to update the position lable
        ASC_PosY_var = tk.StringVar()
        self.ASC_dynamiclabels = [ASC_PosX_var, ASC_PosY_var] #Initialize variables
        for i in range(2):
            self.ASC_dynamiclabels[i].set(f"{round(self.currPos[i]/1e-6,3)} um")

        ASC_PosX = ttk.Label(master=ASC_frame, textvar=ASC_PosX_var, style="Txt.TLabel", width=12, anchor="center")
        ASC_PosY = ttk.Label(master=ASC_frame, textvar=ASC_PosY_var, style="Txt.TLabel", width=12, anchor="center")
        ASC_PosX.grid(column=1, row=2, padx=10, pady=5)       
        ASC_PosY.grid(column=1, row=3, padx=10, pady=5) 
        
        #Entries to enter movements and steps etc. 
        self.ASC_MoveX = ttk.Entry(master=ASC_frame, width=12)
        self.ASC_MoveY = ttk.Entry(master=ASC_frame, width=12)
        self.ASC_StepX = ttk.Entry(master=ASC_frame, width=12)
        self.ASC_StepY = ttk.Entry(master=ASC_frame, width=12)
        self.ASC_MoveX.grid(column=2, row=2, padx=10, pady=5)
        self.ASC_MoveY.grid(column=2, row=3, padx=10, pady=5)
        self.ASC_StepX.grid(column=4, row=2, padx=10, pady=5)
        self.ASC_StepY.grid(column=4, row=3, padx=10, pady=5)
        
        for i, entry in enumerate([self.ASC_MoveX, self.ASC_MoveY, self.ASC_StepX, self.ASC_StepY]):
            if i<2:
                entry.insert(0, "20")
            else:
                entry.insert(0, "0.5")
        
        #Buttons to set movements
        ASC_Button_MoveX = ttk.Button(master=ASC_frame, text="\u2713", style="Std.TButton", command= lambda: threading.Thread(target=self.move_x_to).start())
        ASC_Button_MoveY = ttk.Button(master=ASC_frame, text="\u2713", style="Std.TButton", command= lambda: threading.Thread(target=self.move_y_to).start())
        ASC_X_smaller = ttk.Button(master=ASC_frame, text="\u2BC7", style="Std.TButton", command= lambda: threading.Thread(target=self.move_x_down).start())
        ASC_X_larger = ttk.Button(master=ASC_frame, text="\u2BC8", style="Std.TButton", command= lambda: threading.Thread(target=self.move_x_up).start())
        ASC_Y_smaller = ttk.Button(master=ASC_frame, text="\u2BC7", style="Std.TButton", command= lambda: threading.Thread(target=self.move_y_down).start())
        ASC_Y_larger = ttk.Button(master=ASC_frame, text="\u2BC8", style="Std.TButton", command=lambda: threading.Thread(target=self.move_y_up).start())
        ASC_Button_MoveX.grid(column=3,row=2)
        ASC_Button_MoveY.grid(column=3,row=3)
        ASC_X_smaller.grid(column=5, row=2)
        ASC_X_larger.grid(column=6, row=2)
        ASC_Y_smaller.grid(column=5, row=3)
        ASC_Y_larger.grid(column=6, row=3)
        
        #Title labels
        label = ttk.Label(master=ANC_frame, text="Step [V]", style="Std.TLabel", width=12)
        label1 = ttk.Label(master=ANC_frame, text="Move To [V]", style="Std.TLabel", width=12)
        label2 = ttk.Label(master=ANC_frame, text="Position [V]", style="Std.TLabel", width=12, anchor="center")
        label3 = ttk.Label(master=ANC_frame, text="X", style="Std.TLabel", padding=[10,0])
        label4 = ttk.Label(master=ANC_frame, text="Y", style="Std.TLabel", padding=[10,0])
        label5 = ttk.Label(master=ANC_frame, text="Z", style="Std.TLabel", padding=[10,0])
        label.grid(column=4, row=1, padx=10, pady=5)
        label1.grid(column=2, row=1, padx=10, pady=5)
        label2.grid(column=1, row=1, padx=10, pady=5)
        label3.grid(column=0, row=2, padx=10, pady=5)
        label4.grid(column=0, row=3, padx=10, pady=5)
        label5.grid(column=0, row=4, padx=10, pady=5)


        #Dynamic position labels
        PosX_var = tk.StringVar()
        PosY_var = tk.StringVar()
        PosZ_var = tk.StringVar()

        self.ANC_dynamiclabels = [PosX_var, PosY_var, PosZ_var]
        for i in range(3):
            self.ANC_dynamiclabels[i].set(f"{self.ANC.get_output(i+1, Print=False)} V")

        PosX = ttk.Label(master=ANC_frame, textvar=PosX_var, style="Txt.TLabel", width=12, anchor="center")
        PosY = ttk.Label(master=ANC_frame, textvar=PosY_var, style="Txt.TLabel", width=12, anchor="center")
        PosZ = ttk.Label(master=ANC_frame, textvar=PosZ_var, style="Txt.TLabel", width=12, anchor="center")
        PosX.grid(column=1, row=2, padx=10, pady=5)
        PosY.grid(column=1, row=3, padx=10, pady=5)
        PosZ.grid(column=1, row=4, padx=10, pady=5)

        #User entries for movement
        MoveX = ttk.Entry(master=ANC_frame, width=12)
        MoveY = ttk.Entry(master=ANC_frame, width=12)
        MoveZ = ttk.Entry(master=ANC_frame, width=12)
        StepX = ttk.Entry(master=ANC_frame, width=12)
        StepY = ttk.Entry(master=ANC_frame, width=12)
        StepZ = ttk.Entry(master=ANC_frame, width=12)
        MoveX.grid(column=2, row=2, padx=10, pady=5)
        MoveY.grid(column=2, row=3, padx=10, pady=5)
        MoveZ.grid(column=2, row=4, padx=10, pady=5)
        StepX.grid(column=4, row=2, padx=10, pady=5)
        StepY.grid(column=4, row=3, padx=10, pady=5)
        StepZ.grid(column=4, row=4, padx=10, pady=5)
        self.Moves = [MoveX, MoveY, MoveZ]           
        self.Steps = [StepX, StepY, StepZ]
        
        for entry in self.Moves:
            entry.insert(0, "20")
        for entry in self.Steps:
            entry.insert(0, "0.5")
            
        #Buttons to set movements
        Button_MoveX = ttk.Button(master=ANC_frame, text="\u2713", style="Std.TButton", command= lambda: threading.Thread(target=self.ANC_set_move, args=[1]).start())
        Button_MoveY = ttk.Button(master=ANC_frame, text="\u2713", style="Std.TButton", command= lambda: threading.Thread(target=self.ANC_set_move, args=[2]).start())
        Button_MoveZ = ttk.Button(master=ANC_frame, text="\u2713", style="Std.TButton", command= lambda: threading.Thread(target=self.ANC_set_move, args=[3]).start())
        X_smaller = ttk.Button(master=ANC_frame, text="\u2BC7", style="Std.TButton", command= lambda: threading.Thread(target=self.ANC_set_step(1,-1)).start())
        X_larger = ttk.Button(master=ANC_frame, text="\u2BC8", style="Std.TButton", command= lambda: threading.Thread(target=self.ANC_set_step(1,1)).start())
        Y_smaller = ttk.Button(master=ANC_frame, text="\u2BC7", style="Std.TButton", command= lambda: threading.Thread(target=self.ANC_set_step(2,-1)).start())
        Y_larger = ttk.Button(master=ANC_frame, text="\u2BC8", style="Std.TButton", command=lambda: threading.Thread(target= self.ANC_set_step(2,1)).start())
        Z_smaller = ttk.Button(master=ANC_frame, text="\u2BC7", style="Std.TButton", command=lambda: threading.Thread(target=self.ANC_set_step(3,-1)).start())
        Z_larger = ttk.Button(master=ANC_frame, text="\u2BC8", style="Std.TButton", command=lambda: threading.Thread(target=self.ANC_set_step(3,1)).start())
        Button_abort = ttk.Button(master=ANC_frame, text="Abort move", style = 'Std.TButton', width=10, command=self.ANC_abort_move)
        Button_MoveX.grid(column=3,row=2)
        Button_MoveY.grid(column=3,row=3)
        Button_MoveZ.grid(column=3,row=4)
        X_smaller.grid(column=5, row=2)
        X_larger.grid(column=6, row=2)
        Y_smaller.grid(column=5, row=3)
        Y_larger.grid(column=6, row=3)
        Z_smaller.grid(column=5, row=4)
        Z_larger.grid(column=6, row=4)
        Button_abort.grid(column=7, row=3, padx=10)

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
                 val = round(abs(float(self.ASC_MoveX.get())*1e-6), 10) #nm convert
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
                val = round(abs(float(self.ASC_MoveY.get())*1e-6), 10) #mm convert
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
    # X-button actions
    def move_x_up(self):
        pos =self.asc500.scanner.getPositionsXYRel()

        #print(curr_pos)
        x_const= pos[0]
        y_const= pos[1]
        val = round(abs(float(self.ASC_StepX.get())*1e-6), 10) #nm convert
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
         val = round(-abs(float(self.ASC_StepX.get())*1e-6), 10) #nm convert
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
         val = round(abs(float(self.ASC_StepY.get())*1e-6), 10) #nm convert
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
         val = round(-abs(float(self.ASC_StepY.get())*1e-6), 10) #nm convert
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
                
                for i in range(2):
                    self.ASC_dynamiclabels[i].set(f"{round(self.currPos[i]/1e-6,3)} um")
                    
                if not self.ANC.moving:
                    for i in range(3):
                        self.ANC_dynamiclabels[i].set(f"{self.ANC.get_output(i+1, Print=False)} V")
      
            self.after(1000, self.periodic_position_update)
         
    def ANC_set_move(self, axis): 
        pos = float(self.Moves[axis-1].get())
        self.ANC.ramp(axis, pos, label=self.ANC_dynamiclabels[axis-1])
        self.ANC_dynamiclabels[axis-1].set(f"{self.ANC.get_output(axis, Print=False)} V")
        
    def ANC_set_step(self,axis, direction): 
        step = abs(float(self.Steps[axis-1].get()))*direction
        self.ANC.step(axis, step)
        self.ANC_dynamiclabels[axis-1].set(f"{self.ANC.get_output(axis, Print=False)} V")
        
    def ANC_abort_move(self):
        self.ANC.abort = True
        self.ANC.moving = False
        