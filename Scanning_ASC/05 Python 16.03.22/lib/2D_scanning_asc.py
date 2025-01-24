# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 15:37:36 2024

@author: attocube
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from motorized_stage import AscStageApp
import asc500_device as asc
import threading
from qualang_tools.control_panel import ManualOutputControl
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
from qm import SimulationConfig
import matplotlib.pyplot as plt
from configuration import *
from qm import LoopbackInterface
from qm import generate_qua_script
from qm.octave import *
from qm.octave.octave_manager import ClockMode
###################
# The QUA program #
###################

single_integration_time_ns = int(60 * u.ms) 

print(single_integration_time_ns)

with program() as counter:
    times = declare(int, size=16000)
    counts = declare(int)
    total_counts = declare(int)
    counts_st = declare_stream()

    with infinite_loop_():
        measure("readout", "SPCM", None, time_tagging.analog(times, single_integration_time_ns, counts))
        save(counts, counts_st)
    with stream_processing():
        counts_st.with_timestamps().save("counts")
        
with program() as idle:
    with infinite_loop_():
        play('const','AOM')

#####################################
#  Open Communication with the QOP  #
#####################################

octave_ip = "192.168.88.50"
octave_port = 80  # Must be 11xxx, where xxx are the last three digits of the Octave IP address
con = "con1"
octave = "octave1"
cluster_name = 'my_cluster'
octave_config = QmOctaveConfig()
octave_config.add_device_info(octave, octave_ip, octave_port)

qmm = QuantumMachinesManager(host='192.168.88.10', port='80',cluster_name=cluster_name, octave=octave_config)



qm = qmm.open_qm(config)

job = qm.execute(counter)

# sourceFile = open('debug.py', 'w')
# print(generate_qua_script(counter, config), file=sourceFile)
# sourceFile.close()


# new_counts = counts_handle.fetch("counts")["value"] # counts exports
# print(new_counts)
class ScannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("2D ASC500 Scanner")
        self.my_app = AscStageApp()
    
        # Set velocity parameters for the motors
        self.my_app.motor_x.set_velocity_parameters(0, 0.3, 0.05)
        self.my_app.motor_y.set_velocity_parameters(0, 0.3, 0.05)
        self.my_app.motor_z.set_velocity_parameters(0, 0.3, 0.05)
        
        # Add this line to define the scanning attribute
        self.scanning = False
        
        # Configure main window weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
    
        # Graph Frame
        self.graph_frame = ttk.Frame(self)
        self.graph_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
    
        # Motorized Stage App Frame
        self.motorized_stage_frame = ttk.Frame(self)
        self.motorized_stage_frame.grid(row=0, column=1, sticky="nsew")
    
        self.motorized_stage_app = AscStageApp(self.motorized_stage_frame)
        self.motorized_stage_app.grid(column=0, row=0, sticky="nsew")
    
        # Control Panel Frame
        self.control_frame = ttk.Frame(self)
        self.control_frame.grid(row=1, column=1, sticky="nsew")
    
        # Graph
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Control Panel
        self.create_control_panel()
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Line Graph Frame
        self.line_graph_frame = ttk.Frame(self)
        self.line_graph_frame.grid(row=0, column=2, rowspan=2, sticky="nsew")
        # Put the line graph in the frame
        self.fig2, self.ax2 = plt.subplots()
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.line_graph_frame)
        self.canvas2.get_tk_widget().config(width=500)
        self.canvas2.draw()
        self.canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=False)






if __name__ == "__main__":
    app = ScannerApp()
    app.mainloop()
