

import tkinter as tk
from tkinter import ttk
from tkinter import StringVar

import numpy as np
from scipy.optimize import curve_fit
import scipy.stats
import time
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector
import os


from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from Motorized_asc import AscStageApp
from ANC300 import ANC300App

import threading
from qualang_tools.control_panel import ManualOutputControl
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
from qm import SimulationConfig
#from configuration_octave_scan import *
from configuration_with_octave_Last import *
from qm import LoopbackInterface
from qm import generate_qua_script
from qm.octave import *
from qm.octave.octave_manager import ClockMode
#Modules used
from odmr_popup import ODMRPopup
from rabi_popup import RabiPopup
from ODMRFitPopup import ODMRFitPopup
from RabiFitPopup import RabiFitPopup

from pl_module import PLModule
from pl_module_linescan import PLModuleLinescan
from odmr_module import ODMRModule
from rabi_module import RabiModule
##Optimization functions##
import threading
data_lock = threading.Lock()


class ScannerApp(tk.Tk):
    """
    A GUI application for controling a scanner, built with Tkinter.
    
    Inherits from:
         tk.Tk:The main Tkinter window class, providing the base for GUI.
    
    Attributes:
        None

    """
    def __init__(self):
        """
        Initializes the main application window.

        """
        
        super().__init__()
        self.title("2D Photoluminescence Scanner") #Title of the application window.
      
        
        # Initialize other modules
        self.pl_module = PLModule()#Submodule for photoluminescence
        self.pl_module_linescan = PLModuleLinescan()
        self.odmr_module = ODMRModule()#Submodule for ODMR
        

        # Initialize fast\slow positions 
        self.f_pos = 0.0
        self.s_pos = 0.0
        ### Why does ^this exist? ###
        
        # Initialise for dropdown bottons
        self.scan_type = StringVar()
        self.scan_type.set("Select Scan Type")  
        
        
        # Add this line to define the scanning attribute
        self.scanning = False
        self.odmr_params_confirmed = False
        ### Can we reorder these lines so that all of the initializes happen
        ### then all of the scanning things? ###
        
       
        # Configure main window weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        ### What does this do? ###
      
        # Motorized Stage App Frame
        self.motorized_stage_frame = ttk.Frame(self)
        self.motorized_stage_frame.grid(row=0, column=1)

        self.my_app = AscStageApp(self.motorized_stage_frame)
        self.motorized_stage_app = self.my_app
        
        self.motorized_stage_app.grid(column=0, row=0)
            
        # Control Panel Frame
        self.control_frame = ttk.Frame(self)
        self.control_frame.grid(row=1, column=1, sticky="nsew")
        
        # Graph Frame
        self.graph_frame = ttk.Frame(self)
        self.graph_frame.grid(row=0, column=0, rowspan=1, sticky="nsew")
        
        # Graph
        self.fig = Figure(figsize=(5, 4))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=False)
        self.canvas.draw()
        
        # ODMR Frame
        self.ODMR_frame = ttk.Frame(self)
        self.ODMR_frame.grid(row=1, column=0, rowspan=2, sticky="nsew")
        
        # Graph
        self.fig5 =  Figure(figsize=(5, 4))
        self.ax5 = self.fig5.add_subplot(111)
        self.canvas5 = FigureCanvasTkAgg(self.fig5, master=self.ODMR_frame)   
        self.canvas5.get_tk_widget().config(width=200, height=200)
        self.canvas5.get_tk_widget().pack(fill=tk.BOTH, expand=False)
        self.canvas5.draw()
        
        #odmr heatmap selection
        # Initialize heatmap data dictionaries
        self.heatmap_data_dict = {
            'x [um]': None,
            'y [um]': None,
            'AFM height [um]' : None,
            'counts [kc/s]': None,           
        }

        # Selected value variable
        self.selected_value_var = tk.StringVar(value='counts [kc/s]')

        # # Buttons for switching heatmaps
        # self.button_frame = ttk.Frame(self.graph_frame)
        # self.button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # buttons = ['AFM height [um]', 'counts [kc/s]', 'freq_center', 'fwhm', 'contrast', 'sensitivity','rabi_freq', 'rabi_decay', 'rabi_contrast']
        # for key in buttons:
        #     button = ttk.Radiobutton(
        #         self.button_frame, 
        #         text=key.capitalize(), 
        #         variable=self.selected_value_var, 
        #         value=key, 
        #         command=self.update_displayed_heatmap
        #     )
        #     button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # # Add popup button in the same row
        # self.popup_button = ttk.Button(self.button_frame, text="Popup", command=self.popup_heatmap)
        # self.popup_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Create a unified button frame under the graph frame
        self.button_frame = ttk.Frame(self.graph_frame)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Sub-frames for arranging two rows of buttons
        self.odmr_button_row = ttk.Frame(self.button_frame)
        self.odmr_button_row.pack(side=tk.TOP, fill=tk.X)
        
        self.rabi_button_row = ttk.Frame(self.button_frame)
        self.rabi_button_row.pack(side=tk.TOP, fill=tk.X)
        
        # Make sure the shared selection variable is initialized
        self.selected_value_var = tk.StringVar(value='counts [kc/s]')
        
        # ODMR-related buttons
        odmr_keys = ['AFM height [um]', 'counts [kc/s]', 'freq_center', 'fwhm', 'contrast', 'sensitivity']
        for key in odmr_keys:
            button = ttk.Radiobutton(
                self.odmr_button_row,
                text=key.capitalize(),
                variable=self.selected_value_var,
                value=key,
                command=self.update_displayed_heatmap
            )
            button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Rabi-related buttons (second line)
        rabi_keys = ['rabi_freq', 'rabi_decay', 'rabi_contrast']
        for key in rabi_keys:
            button = ttk.Radiobutton(
                self.rabi_button_row,
                text=key.capitalize(),
                variable=self.selected_value_var,
                value=key,
                command=self.update_displayed_heatmap
            )
            button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Popup button placed on the right
        self.popup_button = ttk.Button(self.button_frame, text="Popup", command=self.popup_heatmap)
        self.popup_button.pack(side=tk.RIGHT, padx=5, pady=5)

        
        # Initialize the selected heatmap
        self.update_displayed_heatmap()
        
        # Add ODMR Fit Popup Button
        self.odmr_fit_button = ttk.Button(self.ODMR_frame, text="ODMR", command=self.open_odmr_fit_popup)
        self.odmr_fit_button.pack(pady=10)
        
        # Add Rabi Fit Popup Button
        self.rabi_fit_button = ttk.Button(self.ODMR_frame, text="Rabi", command=self.open_rabi_fit_popup)
        self.rabi_fit_button.pack(pady=10)

        
        
        # Control Panel
        self.create_control_panel()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        
        # Line Graph Frame
        self.line_graph_frame = ttk.Frame(self)
        self.line_graph_frame.grid(row=0, column=2, rowspan=2, sticky="nsew")
        
        # Put the line graph in the frame
        self.fig2 = Figure(figsize=(5, 4))
        self.ax2 = self.fig2.add_subplot(111)
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.line_graph_frame)
        self.canvas2.get_tk_widget().config(width=500)
        self.canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=False)
        self.canvas2.draw()
        

        
        # Put the Optimise graph in the frame
        self.fig3 = Figure(figsize=(6, 5))
        self.ax3 = self.fig3.add_subplot(111)

        self.canvas3 = FigureCanvasTkAgg(self.fig3, master=self.line_graph_frame)
        self.canvas3.get_tk_widget().config(width=500, height=450)
        self.canvas3.draw()
        self.canvas3.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.initialize_optimize_graph()
        self.fig3.tight_layout()

        # calls on the click function when selecting a rectangular area in the optimization heat plot
        self.rect_selector = RectangleSelector(self.ax3, self.rectselect)
        

        self.fig4 = Figure(figsize=(6, 2))
        self.ax4 = self.fig4.add_subplot(111)
#        self.ax4.tick_params("y", rotation=270)      
        self.canvas4 = FigureCanvasTkAgg(self.fig4, master=self.line_graph_frame)
        self.canvas4.get_tk_widget().config(width=500,height=100)
        self.canvas4.draw()
        self.canvas4.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=False)
        self.fig4.tight_layout()

    def on_close(self):
        """
        Closing the motorised stage app.
        
        
        Args:
            None

        """
        
        self.my_app.asc500.scanner.pauseScanner() # Stop the motors
        self.my_app.close()
        self.destroy()
        

    def create_control_panel(self):
        """
        Create and places all the widgets in the main application window.

        """
        control_frame = self.control_frame

        style = ttk.Style()
        style.theme_use('vista')
        style.configure('Large.TButton', font=("Helvetica", 12, "bold"), padding=(20, 10))
        #style.configure('TCombobox', font=('Helvetica', 12), padding=(20, 10))

        # Create a new frame for the control panel elements
        scanning_control_frame = ttk.Frame(control_frame)
        scanning_control_frame.grid(row=1, column=1)

        ttk.Label(scanning_control_frame, text="X Length (um or V)").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.total_X_length = ttk.Entry(scanning_control_frame, width=10)
        self.total_X_length.insert(0, "10")
        self.total_X_length.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(scanning_control_frame, text="Y Length (um or V)").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.total_Y_length = ttk.Entry(scanning_control_frame, width=10)
        self.total_Y_length.insert(0, "10")
        self.total_Y_length.grid(row=2, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(scanning_control_frame, text="Step X (um or V)").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.delta_X = ttk.Entry(scanning_control_frame, width=10)
        self.delta_X.insert(0, "1")
        self.delta_X.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(scanning_control_frame, text="Step Y (um or V)").grid(row=3, column=2, padx=5, pady=5, sticky="w")
        self.delta_Y = ttk.Entry(scanning_control_frame, width=10)
        self.delta_Y.insert(0, "1")
        self.delta_Y.grid(row=3, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(scanning_control_frame, text="Fast Delay (sec)").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.delay_fast = ttk.Entry(scanning_control_frame, width=10)
        self.delay_fast.insert(0, "0.1")
        self.delay_fast.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(scanning_control_frame, text="Slow Delay (sec)").grid(row=4, column=2, padx=5, pady=5, sticky="w")
        self.delay_slow = ttk.Entry(scanning_control_frame, width=10)
        self.delay_slow.insert(0, "0.1")
        self.delay_slow.grid(row=4, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(scanning_control_frame, text="File Name").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.file_name = ttk.Entry(scanning_control_frame, width=20)
        self.file_name.insert(0, "test")
        self.file_name.grid(row=6, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(scanning_control_frame, text="Probe").grid(row=7, column=2, padx=5, pady=5, sticky="w")
        self.probe = ttk.Entry(scanning_control_frame, width=20)
        self.probe.insert(0, "")
        self.probe.grid(row=7, column=3, padx=5, pady=5, sticky="w")
        
        ttk.Label(scanning_control_frame, text="Sample").grid(row=7, column=0, padx=5, pady=5, sticky="w")
        self.sample = ttk.Entry(scanning_control_frame, width=20)
        self.sample.insert(0, "")
        self.sample.grid(row=7, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(scanning_control_frame, text="Temp (K)").grid(row=0, column=2, padx=0, pady=0, sticky="w")
        self.temp = ttk.Entry(scanning_control_frame, width=10)
        self.temp.insert(0, "300")
        self.temp.grid(row=0, column=2, padx=80, pady=0, sticky="w")        
        
        #self.file_name = ttk.Entry()  # File name input entry
        current_directory = os.getcwd()
        probe = "FR067-9C-1R2"
        sample = "AFM_grid"
        
       
        self.save_flag = tk.BooleanVar(value=False)  # Track the switch state

        # Save switch button (styled like a switch) next to the file name entry
        self.save_switch = ttk.Checkbutton(scanning_control_frame, text="Auto-Save", variable=self.save_flag, style='Switch.TCheckbutton')
        self.save_switch.grid(row=6, column=3, padx=5, pady=5, sticky="w")
        
        # Create the "Scan" button that executes the selected scan type
        self.SCAN_button = ttk.Button(scanning_control_frame, text="Start Scan", command= self.start_selected_scan, style='Large.TButton')
        self.SCAN_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # Style the Combobox (if desired)
        style.configure('Large.TCombobox', font=('Arial', 10))
        ### what is a combobox ###

        
        ttk.Label(scanning_control_frame, text="Integration Time (ms)").grid(row=5, column=2, padx=5, pady=5, sticky="w")
        self.integration_time = ttk.Entry(scanning_control_frame, width=10)
        self.integration_time.insert(0, "100")
        self.integration_time.grid(row=5, column=3, padx=5, pady=5, sticky="w")
        
        
        # self.start_button = ttk.Button(scanning_control_frame, text="2D Scan", command=self.start_scan, style='Large.TButton')
        # self.start_button.grid(row=7, column=0, columnspan=1, padx=10, pady=10, sticky="ew")
        # Create a variable to hold the selected scan type

        
        # Create the drop-down list (Combobox) for scan types
        self.scan_dropdown = ttk.Combobox(scanning_control_frame, textvariable=self.scan_type
                                          , values=["2D Scan", "2D F_Line Scan", "2D Scan Tip"], state="readonly", style='Large.TCombobox')
        self.scan_dropdown.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
     
        
        self.start_button = ttk.Button(scanning_control_frame, text="Start Time Trace"
                                       , command=self.start_time_trace, style='Large.TButton')
        self.start_button.grid(row=0, column=3, columnspan=1, padx=10, pady=10, sticky="ew")
        
        
        self.abort_button = ttk.Button(scanning_control_frame, text="Abort"
                                       , command=self.abort_scan, style='Large.TButton')
        self.abort_button.grid(row=0, column=1, columnspan=1, padx=10, pady=10, sticky="ew")


        # ttk.Label(scanning_control_frame, text="Slow Axis").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        # self.slow_axis = ttk.Entry(scanning_control_frame, width=10)
        # self.slow_axis.insert(0, "X")
        # self.slow_axis.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(scanning_control_frame, text="Scanning Direction (Fast Axis)").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.fast_axis = tk.StringVar()
        self.scan_dropdown = ttk.Combobox(scanning_control_frame, textvariable=self.fast_axis
                                          , values=["X","Y"], state="readonly")
        self.scan_dropdown.grid(row=1, column=1, padx=5, pady=5, sticky="w") 
        
        
        
        # Add a label for the APD signal value
        status_frame = ttk.Frame(control_frame)
        status_frame.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        ttk.Label(status_frame, text="APD Signal", font=("Helvetica", 20)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.apd_signal_label = ttk.Label(status_frame, text="N/A"
                                          , font=("Helvetica", 24), foreground="#0077FF", background="black", width=12)
        self.apd_signal_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        ttk.Label(status_frame, text="Status", font=("Helvetica", 20)).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.status_label = ttk.Label(status_frame, text="Idle", font=("Helvetica", 24), foreground="#0077FF", background="black", width=12)
        self.status_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(status_frame, text="Time Left(m)", font=("Helvetica", 20)).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.time_left_label = ttk.Label(status_frame, text="Idle", font=("Helvetica", 24), foreground="#0077FF", background="black", width=12)
        self.time_left_label.grid(row=1, column=2, padx=5, pady=5, sticky="w")

        self.Line_scan_velocity = ttk.Entry(scanning_control_frame)
        self.Line_scan_velocity.grid(row=5,column =1, padx=5, pady = 5, sticky = "ew")
        ttk.Label(scanning_control_frame, text="Velocity (um/s)").grid(row=5,column=0, padx=3, pady = 5, sticky = "w")

        
        # Add other text boxes and labels as needed
        self.optimize_button= ttk.Button(scanning_control_frame, text="Optimize", command=self.start_optimize, style='Large.TButton')
        self.optimize_button.grid(row=8, column=0, columnspan=1, padx=5, pady=5, sticky="nsew")
        
        
        #ttk.Label(Opt_frame, text="FC", font=("Helvetica", 20)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.Optfast_label = ttk.Label(scanning_control_frame, text=f"F: {self.f_pos:0.5f}",font=("Helvetica", 20), foreground="ghost white", background="red3", width=9)
        self.Optfast_label.grid(row=8, column=1, padx=5, pady=5, sticky="w")

        #ttk.Label(Opt_frame, text="SC", font=("Helvetica", 20)).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.OptSlow_label = ttk.Label(scanning_control_frame, text=f"S: {self.s_pos:0.5f}",font=("Helvetica", 20), foreground="ghost white", background="#0077FF", width=9)
        self.OptSlow_label.grid(row=8, column=2, padx=5, pady=5, sticky="w")
        
        
        #ttk.Label(Opt_frame, text="SC", font=("Helvetica", 20)).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.focal_label = ttk.Label(scanning_control_frame, text=f"f: {self.s_pos:0.5f}",font=('italic',20), foreground="ghost white", background="green", width=9)
        self.focal_label.grid(row=8, column=3, padx=5, pady=5, sticky="w")
        # Additional Frame to contain the switch and the entry box
        self.switch_frame = ttk.Frame(scanning_control_frame)
        self.switch_frame.grid(row=8, column=2, padx=5, pady=5, sticky="w")

        # # Step 1: Define the variable for the switch
        # self.switch_var = tk.BooleanVar(value=False)  # default to OFF
        
        # # Step 2: Create the Checkbutton as a switch inside the new frame
        # self.switch_button = ttk.Checkbutton(self.switch_frame, text="Period(sec)", variable=self.switch_var, style='Switch.TCheckbutton', command=self.toggle_entry)
        # self.switch_button.pack(side="left", padx=(0, 10))  # Pack to the left side of the frame
        
        # # Step 3: Create the Entry box inside the new frame
        # self.entry_box = ttk.Entry(self.switch_frame, font=("Helvetica", 16), width=4)
        # self.entry_box.pack(side="left")  # Pack next to the switch
       
        # # Set default value for the entry box
        # self.entry_box.insert(0, "100")  # Default value set to "100"
        
        # # Initially disable the entry box
        # self.entry_box.configure(state='disabled')
        
        # Drop-Down Menu (ComboBox)
        self.dropdown_var = tk.StringVar()
        self.dropdown_menu = ttk.Combobox(scanning_control_frame, textvariable=self.dropdown_var, values=["PL", "ODMR","Rabi"], state="readonly", style='TCombobox')
        self.dropdown_menu.grid(row=1, column=3, padx=(6, 0), pady=(8,0), sticky="w")
        self.dropdown_menu.current(0)  # Set default selection to the first option    
        self.initialize_graph()
    # def toggle_entry(self):
        
    #     if self.switch_var.get():
    #         self.entry_box.configure(state='normal')
    #     else:
    #         self.entry_box.configure(state='disabled')
    
 
            
    # Function to handle the selected scan and execute it
    def start_selected_scan(self, event=None):
        """
        Handles the logic to execute the selected scan type.

        """
        
        
        selected_scan = self.scan_type.get()
        print(f'ss: {selected_scan}')
        if selected_scan == "2D Scan":
            self.start_scan()  # Execute the fast axis scan
        elif selected_scan == "2D F_Line Scan":
            self.start_2D_line_scan()  # Execute the 2D line scan
        elif selected_scan == "2D Scan Tip":
            self.start_tip_scan() # Execute Tip scan
            
        ### Comments on 2D Scan and 1D F_Line Scan seem switched?? ###
            
            
    def open_odmr_fit_popup(self):
        """
        The command for ODMR fit botton, which executes the ODMRFitPopup submodule.

        """

            # Open the ODMR Fit Popup
        ODMRFitPopup(self)
        
    def open_rabi_fit_popup(self):
        """
        The command for ODMR fit botton, which executes the ODMRFitPopup submodule.

        """

            # Open the ODMR Fit Popup
        RabiFitPopup(self)
        
    def update_displayed_heatmap(self, selection='PL'):
        """
        Updates the heatmap data for all key elements with the logic to distinguish PL and ODMR module.

        """
        selected_scan = self.scan_type.get()
        selected_value_key = self.selected_value_var.get()
       
        if selected_value_key not in ["counts [kc/s]", "AFM height [um]"] and self.dropdown_var.get() == 'PL':
            print(f"PL module does not contain {selected_value_key} measurement.")
            self.selected_value_var.set("counts [kc/s]")
            return
                
        # elif selected_value_key != 'counts [kc/s]' and selected_scan == '2D F_Line Scan':
        #     print(f"Linescan cannot show {selected_value_key} measurement.")
        #     self.selected_value_var.set("counts [kc/s]")
        #     return
        
        if self.heatmap_data_dict[selected_value_key] is not None:
            self.im.set_data(self.heatmap_data_dict[selected_value_key])
            
            if selection == 'ODMR' and selected_value_key == 'freq_center':
                self.im.set_clim(np.min(self.odmr_frequencies), np.max(self.odmr_frequencies))
            
            else:
                self.im.set_clim(np.nanmin(self.heatmap_data_dict[selected_value_key]), np.nanmax(self.heatmap_data_dict[selected_value_key]))
            self.canvas.draw_idle()

    def update_displayed_heatmap_opt(self, selection='PL'):
        """
        Updates the heatmap data for all key elements with the logic to distinguish PL and ODMR module.

        """
        selected_scan = self.scan_type.get()
        selected_value_key = self.selected_value_var.get()
       
        if selected_value_key not in ["counts [kc/s]", "AFM height [um]"] and self.dropdown_var.get() == 'PL':
            print(f"PL module does not contain {selected_value_key} measurement.")
            self.selected_value_var.set("counts [kc/s]")
            return
                
        # elif selected_value_key != 'counts [kc/s]' and selected_scan == '2D F_Line Scan':
        #     print(f"Linescan cannot show {selected_value_key} measurement.")
        #     self.selected_value_var.set("counts [kc/s]")
        #     return
        
        if self.heatmap_data_dict[selected_value_key] is not None:
            self.im3.set_data(self.heatmap_data_dict[selected_value_key])
            
            if selection == 'ODMR' and selected_value_key == 'freq_center':
                self.im3.set_clim(np.min(self.odmr_frequencies), np.max(self.odmr_frequencies))
            
            else:
                self.im3.set_clim(np.nanmin(self.heatmap_data_dict[selected_value_key]), np.nanmax(self.heatmap_data_dict[selected_value_key]))
            self.canvas3.draw_idle()


    def popup_heatmap(self):
        """
        This function pops up the selected heatmap using the similar structure of update_displayed_heatmap, but with update_popup fuction .

        """
        selected_value_key = self.selected_value_var.get()
        if self.heatmap_data_dict[selected_value_key] is not None:
            popup = tk.Toplevel(self)
            fig_popup = Figure(figsize=(5, 4))
            ax_popup = fig_popup.add_subplot(111)
    
            # Set the same extent as the main heatmap
            extent = self.im.get_extent()
    
            im_popup = ax_popup.imshow(
                self.heatmap_data_dict[selected_value_key], 
                aspect='auto', 
                origin='lower',
                extent=extent  # Set the extent
            )
    
            colorbar_popup = fig_popup.colorbar(im_popup, ax=ax_popup)
            canvas_popup = FigureCanvasTkAgg(fig_popup, master=popup)
            canvas_popup.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            canvas_popup.draw()
            
            self.update_popup(popup, im_popup, canvas_popup, selected_value_key)

            

            
    def save_heatmap_data(self, selection='PL', fixed_path=None):
        """
        Saves heatmap data to a single file.
        If `fixed_path` is provided (or persistent_save_path exists), reuse it.
        Otherwise, generate a new timestamped file (e.g. at end of scan).
        """
        # Determine save path
        if fixed_path:
            full_path = fixed_path
        elif hasattr(self, 'persistent_save_path'):
            full_path = self.persistent_save_path
        else:
            base_filename = self.file_name.get()
            directory = os.path.join(f"//WXPC724/Share/Data/{self.probe.get()}/{self.sample.get()}", time.strftime('%Y%m%d'))
            os.makedirs(directory, exist_ok=True)
            full_path = os.path.join(directory, f"{time.strftime('%Y%m%d-%H%M-%S')}_{base_filename}.txt")
            self.persistent_save_path = full_path  # store for later use
        # Flatten and collect heatmap data
        save_data = []
        for key, data in self.heatmap_data_dict.items():
            if data is not None:
                save_data.append(data.flatten())
        data_for_file = np.array(save_data).T
        # Save .txt and .npz
        with open(full_path, 'w') as f:
            f.writelines(self.headerlines)
            # Save the heatmap data as a text file in float format
            np.savetxt(f, data_for_file, delimiter='\t')
        print(f"Heatmap data saved at {full_path}")
        np.savez(full_path.replace('.txt', ''), **self.heatmap_data_dict)
        print(selection)
        if selection == 'ODMR':
            np.savez(full_path.replace('.txt', '') + '_ODMRData',
                     counts=self.odmr_data, frequencies=self.odmr_frequencies, f_center = self.freq_centers)
            # Write pointer to last ODMR path
            odmr_path = full_path.replace('.txt', '') + '_ODMRData.npz'
            pointer_file = os.path.join("//WXPC724/Share/Data", "last_odmr_path.txt")
            with open(pointer_file, 'w') as f:
                f.write(odmr_path)
        print(f"Heatmap data saved at {full_path}")

            
          
  
        
    def update_popup(self, popup, im_popup, canvas_popup, selected_value_key):
        """
        Updates the popped up heatmap with its own thread.
        """
        if self.scanning:
            if self.heatmap_data_dict[selected_value_key] is not None:
                im_popup.set_data(self.heatmap_data_dict[selected_value_key])
                im_popup.set_clim(np.min(self.heatmap_data_dict[selected_value_key]), np.max(self.heatmap_data_dict[selected_value_key]))
                canvas_popup.draw_idle()
            self.after(100, self.update_popup, popup, im_popup, canvas_popup, selected_value_key) # Thread-safe update of the heatmap in every 0.1 sec. 
                
                ### Don't you already have the second if statement before
                ### the function is called? ###


    def start_time_trace(self):
        
        
        """
        Command function for start_time_trace button, starts threading for its run_time_trace function.
        """
    
        
        self.scanning = True
        self.status_label.config(text="Scanning")
        f_idx = 0
        self.pl_module.total_integration_time = int(float(self.integration_time.get()) * u.ms)
    
        def run_time_trace():
            """
            Counts wrt timestamps plotted in real time.
            """
            self.pl_module.connect()
            self.pl_module.start_job()
            self.pl_module.start_fetching()   # Initialize data handles
            self.pl_module.z_control = self.my_app.asc500.zcontrol
            self.pl_module.scannerpos = self.my_app.asc500.scanner
            
            Time = []
            counts = []
            self.ax2.set_xlabel("time [s]")
            self.ax2.set_ylabel("counts [kcps]")
            self.ax2.set_title("Counter")
    
            while self.scanning:
                self.pl_module.get_data(f_idx)
                data_dict = self.pl_module.data_dict
                new_counts = data_dict.get('counts [kc/s]')
                timestamp = data_dict.get('timestamp')
                counts.append(new_counts)
                Time.append(timestamp)
    
                self.ax2.cla()
                self.ax2.set_xlabel("time [s]")
                self.ax2.set_ylabel("counts [kcps]")
                self.ax2.set_title("Counter")
    
    
                if len(Time) > 200:
                    self.ax2.plot(Time[-200:], counts[-200:])
                else:
                    self.ax2.plot(Time, counts)
    
                self.canvas2.draw_idle()
                self.update_idletasks()
                time.sleep(0.1)
    
            self.status_label.config(text="Idle")
   
        # Create and start a separate thread for the time trace
        self.time_trace_thread = threading.Thread(target=run_time_trace)
        self.time_trace_thread.start()

        
        
    def start_2D_line_scan(self): 
        
        """
        Button command function using pl_module. Also starts the threading for its line_scan_2D function.
        
        Important elements:
            velocity: To set the speed of the XY scanner in [um/s]

        """
        start_time_0 = time.time()
        
        self.scanning = True
        module = self.pl_module_linescan #Photoluminescence sub_module is used.
        self.status_label.config(text="Scanning")
        
        module.z_control = self.my_app.asc500.zcontrol
        module.scannerpos = self.my_app.asc500.scanner
        #Getting the inserted values from control frame.
        total_X_length = float(self.total_X_length.get())*1e-6
        total_Y_length = float(self.total_Y_length.get())*1e-6
        delta_X = float(self.delta_X.get())*1e-6
        delta_Y = float(self.delta_Y.get())*1e-6
        delay_fast = float(self.delay_fast.get())
        delay_slow = float(self.delay_slow.get())
        file_name = self.file_name.get()
        integration_time = float(self.integration_time.get())
        module.total_integration_time = int(float(self.integration_time.get()) * u.ms)
        
        #corrected stepsizes to ensure an integer number of pixels in the scan
        steps = [int(round(total_X_length/delta_X)), int(round(total_Y_length/delta_Y))]
        stepsize = [total_X_length/steps[0], total_Y_length/steps[1]]
       
        fast_axis = self.fast_axis.get() # 'X' or 'Y'
                
        if fast_axis == 'X':
            [module.fast_steps, module.slow_steps] = steps
            [delta_fast, delta_slow] = stepsize
                        
        elif fast_axis == 'Y':
            [module.fast_steps, module.slow_steps] = [steps[1], steps[0]]
            [delta_fast, delta_slow] = [stepsize[1], stepsize[0]]
            
        
        
        #Taking the speed value
        velocity = abs(float(self.Line_scan_velocity.get())*1e-6) #um convert
        print(f'v:{velocity}')
       
        self.my_app.asc500.scanner.setPositioningSpeed(velocity) #speed of the XY scanner in [um/s]
        print("Before line_scan")
        
        
        # Calculate how many data points per pixel
        time_per_pixel = delta_fast / velocity  # in seconds
        
        #Taking the single_integration_time_ns into account number of data points per pixel is calculated
        #module.n_data_points_per_pixel = int(time_per_pixel / (module.single_integration_time_ns  / 1e9)) 
        module.n_data_points_per_pixel = int(time_per_pixel / 5.225e-6) 
       
        print(f"single_int_time {module.single_integration_time_ns / 1e9}")
        print(f'Number of data points per pixel: {module.n_data_points_per_pixel}')
        print(f'Number of pixels: {module.fast_steps}')
       
        def line_scan_2D():
            """
            2D Fast-Line scan function averages the n_data_points_per_pixel for every pixel and updates the heat-map.
            Also contains the logic to operate whether X or Y as a fast_axis.
            
            """           
            #Linear transition state-machinary to prepare OPX for getting data
            module.connect()   
            module.start_job()
            module.start_fetching() 
            
            #Initialising the time and counts lists
            Time = []
            Time_b= []
            counts = []
        
            x0, y0 = self.my_app.asc500.scanner.getPositionsXYRel()
            print(f'pos: x: {x0}, y: {y0}')
            
            #bottom left of center scan
            X_start = x0 - total_X_length/2
            Y_start = y0 - total_Y_length/2
            
            x_start = x0 - total_X_length/2 + stepsize[0]/2
            x_end = x0 + total_X_length/2
            y_start = y0 - total_Y_length/2 + stepsize[1]/2
            y_end = y0 + total_Y_length/2
            
            self.x_array = np.arange(x_start, x_end, stepsize[0])*1e6
            self.y_array = np.arange(y_start, y_end, stepsize[1])*1e6
            x_flat = np.tile(self.x_array, np.size(self.y_array))
            y_flat = np.repeat(self.y_array, np.size(self.x_array))
            self.heatmap_data_dict['x [um]'] = x_flat
            self.heatmap_data_dict['y [um]'] = y_flat
                
            a = np.zeros([steps[1], steps[0]])
            a[:,:] = np.nan
            
            self.heatmap_data_dict['counts [kc/s]'] = np.copy(a) # y, x
            self.heatmap_data_dict['AFM height [um]'] = np.copy(a) # y, x
            self.im.set_extent(np.array([x0 - total_X_length / 2, x0 + total_X_length / 2, y0 - total_Y_length / 2, y0 + total_Y_length / 2])/1e-6)
            
            for i in range(module.slow_steps): 
            
              
                print('Move to new line')
                
                pos = self.my_app.asc500.scanner.getPositionsXYRel()
                with self.my_app.currPos_lock:
                    self.my_app.currPos=pos
                print(f'pos_check {pos}')

                if fast_axis == 'X':
                    X = X_start #start of line
                    X_tgt = X + total_X_length #end of line
                    Y = y_start + i * stepsize[1] #constant Y for line
                    Y_tgt = Y
                    
                    
                elif fast_axis == 'Y':
                    X = x_start + i * stepsize[0] #constant X for line
                    X_tgt = X
                    Y = Y_start #start of line
                    Y_tgt = Y + total_Y_length #end of line
                     
                else:
                    print("Invalid Axis Entered")
                    
                #move to the beginning of the next line
                tgt_start = [X,Y]
                
                if not self.scanning:
                    break
                
                self.my_app.asc500.scanner.setPositionsXYRel(tgt_start, pos)
                time.sleep(0.0005)
                #print("Start moving")
            
                
                while (abs(pos[0] - tgt_start[0]) > 0.001e-6 or abs(pos[1] - tgt_start[1]) > 0.001e-6):
                    pos = self.my_app.asc500.scanner.getPositionsXYRel()
                    with self.my_app.currPos_lock:
                        self.my_app.currPos=pos
                    time.sleep(0.005)
               
            
                tgt = [X_tgt, Y_tgt]
                
                #check if scan is within travel bounds of motors
                travel_lim_x = 0 <= tgt[0] < self.my_app.X_Travel_lim 
                travel_lim_y = 0 <= tgt[1] < self.my_app.Y_Travel_lim
        

                if(travel_lim_x == True and travel_lim_y == True):
                    t_start_line = time.time()
                    
                    if not self.scanning:
                        break
                    
                    pos = self.my_app.asc500.scanner.getPositionsXYRel()
                    
                    self.my_app.asc500.scanner.setPositionsXYRel(tgt, pos)
                    print('Movement set')
                    module.get_data(i)
                    
                    pos = self.my_app.asc500.scanner.getPositionsXYRel()
                     
                    ii = 0
                    while (abs(pos[0] - tgt[0]) > 0.001e-6 or abs(pos[1] - tgt[1]) > 0.001e-6):
                        'Run while current position is not target position'
                        if ii > 5:
                            break
                        print('Movement not finished after getting data')
                        if not self.scanning:
                            break
                        print(f"position: {pos} \n start of line: {tgt_start} \n target: {tgt} \n 'Xtarget limit = {self.my_app.X_Travel_lim }")
                        time.sleep(1)
                        ii+=1
                    

                    data_dict = module.data_dict  #Dictionary contains 'counts [kc/s]'
                    counts = data_dict.get('counts [kc/s]')
                    rowsmeasured = np.shape(counts)[0]
                    
                    if fast_axis == 'X':
                        self.heatmap_data_dict['counts [kc/s]'][i, :] = counts[i,:]
                        self.heatmap_data_dict['AFM height [um]'][i, :] = scipy.stats.binned_statistic(module.x_list[i], module.z_out_list[i], bins=module.fast_steps)[0]
                    elif fast_axis == 'Y':
                        self.heatmap_data_dict['counts [kc/s]'][:, i] = counts[i,:]
                        self.heatmap_data_dict['AFM height [um]'][:, i] = scipy.stats.binned_statistic(module.y_list[i], module.z_out_list[i], bins=module.fast_steps)[0]
                        
                    # Update the heatmap display
                    self.after(0, self.update_displayed_heatmap) 
                    self.canvas.draw_idle()
                    self.update_idletasks()       

                    print(f'line: {i+1}, number of lines measured: {rowsmeasured}')    

                    t_end_line = time.time()
                    # Update expected time left for the scan
                    avg_line_time = t_end_line - t_start_line
                    remaining_lines = module.slow_steps - (i + 1)
                    time_left_min = (avg_line_time * remaining_lines) / 60
                    self.time_left_label.config(text="{:.3f}".format(time_left_min))
                    self.after(0, self.update_idletasks)

                else:
                    print(f'Xtarget limit = {self.my_app.X_Travel_lim} , exceeded!')
            
            
            end_time = time.time()
            scantime = end_time - start_time_0
            
            self.headerlines = [f"#Scantype: Linescan \n#Date: {time.strftime('%Y-%m-%d %H:%M:%S')}", 
                                f"\n#Total scanning time: {scantime}", f"\n#Scan direction: {self.fast_axis.get()}", 
                               f"\n#X range: {self.x_array[0]} - {self.x_array[-1]} um", f"\n#Y range: {self.y_array[0]} - {self.y_array[-1]} um", 
                               f"\n#X pixels: {steps[0]}, pixelsize: {stepsize[0]} um", f"\n#Y pixels: {steps[1]}, pixelsize: {stepsize[1]} um",
                               f"\n#Integration time per pixel: {module.total_integration_time/1E6} ms", "\n#Columns:"]
            
            self.save_heatmap_data()
            
            self.my_app.asc500.scanner.setPositioningSpeed(1*1e-6)
            
            #flatten data to save inhomogeneous nested lists
            z_out_data = np.array([element for sublist in module.z_out_list for element in sublist])*1e6
            x_out_data = np.array([element for sublist in module.x_list for element in sublist])*1e6
            y_out_data = np.array([element for sublist in module.y_list for element in sublist])*1e6
            
            base_filename = self.file_name.get()
            self.save_directory = f"//WXPC724/Share/Data/{self.probe.get()}/{self.sample.get()}"  # Default save directory
            directory = self.save_directory + f"/{time.strftime('%Y%m%d')}"
            # Create the full path for saving the data, adding a .txt extension
            full_path_AFM = os.path.join(directory, f"{time.strftime('%Y%m%d-%H%M-%S')}_{base_filename}_AFM")  
            np.savez(full_path_AFM, x=x_out_data, z=z_out_data, y=y_out_data)
                
            print(f"AFM data saved at {full_path_AFM}")
            print("Done Measuring")
            module.disconnect()
            
            if self.scanning:
                self.my_app.move(x0, y0)
            
            
            self.scanning = False
            self.status_label.config(text="Idle")
        self.my_app.periodic_position_update()   
        self.line_scan_2D_thread = threading.Thread(target=line_scan_2D)
        self.line_scan_2D_thread.start()


    def start_tip_scan(self):
        "Start a new thread for tip scanning"
        
        tip_scanning_thread = threading.Thread(target=self.tip_scan)
        tip_scanning_thread.start()
        self.status_label.config(text="Scanning")
        
        
    def start_scan(self):
        
        "Start a new thread for scanning"
        
        scanning_thread = threading.Thread(target=self.scan_loop)
        scanning_thread.start()
        self.status_label.config(text="Scanning")


    def start_optimize(self):
        
        "Start a new thread for scanning"
        
        optimize_thread = threading.Thread(target=self.optimize)
        optimize_thread.start()
        self.status_label.config(text="Scanning")


    # Add this function to initialize the graph and colorbar
    
    
    def initialize_graph(self):
        "Initialise the main heatmap graph"
        
        self.ax.clear()
        self.im = self.ax.imshow(np.zeros((1, 1)), cmap='viridis', interpolation='nearest', aspect='auto', origin='lower')

    
        data_min = 0
        data_max = 1
        self.im.set_clim(data_min, data_max)
        self.ax.set_xlabel('X [um]')
        self.ax.set_ylabel('Y [um]')
    
        self.colorbar = self.fig.colorbar(self.im, ax=self.ax)

    def initialize_optimize_graph(self):
        "Initialise the optimisation heatmap graph"
        
        self.ax3.clear()
        self.im3 = self.ax3.imshow(np.zeros((1, 1)), cmap='viridis', interpolation='nearest', aspect='auto', origin='lower')
        
        # Get the color limits based on the data
        data_min = 0
        data_max = 1
        self.im3.set_clim(data_min, data_max)
        
        self.colorbar3 = self.fig3.colorbar(self.im3, ax=self.ax3)     
        
    def update_graph_thread(self, x_data, y_data1, y_data2):
        
        "Start a new thread for the ODMR fitting graph update"
        thread = threading.Thread(target=self.ODMR_Graph_Update, args=(x_data, y_data1, y_data2))
        thread.start()
        self.status_label.config(text="Scanning")



    def update_graph(self, data):
        """
        Updates the heatmap display and color scaling based on new data, 
        refreshing the canvas and displaying the latest APD signal value.
    
        Arguments:
        data: A 2D array where each row represents a measurement with x, z\y coordinates 
                and a data value (e.g., [x, z\y, value]), used to populate the heatmap.
        """
        data = np.array(data)
    
        # Get the unique x and z values and the number of steps
        x_values = np.unique(data[:, 0])
        z_values = np.unique(data[:, 1])
        x_steps = len(x_values)
        z_steps = len(z_values)
        

        
        # Create a 2D array for the heatmap data
        heatmap_data = np.zeros((z_steps, x_steps))
    
        # Replace the existing values with new values
        for d in data:
            x_idx = np.where(x_values == d[0])[0][0]
            z_idx = np.where(z_values == d[1])[0][0]
            heatmap_data[z_idx, x_idx] = d[2]
    
        # Update the heatmap data
        self.im.set_data(heatmap_data)
    
        # Get the minimum and maximum values of the heatmap data
        data_min = np.nanmin(heatmap_data)
        data_max = np.nanmax(heatmap_data)
    
        # Update the color limits of the color bar
        self.im.set_clim(data_min, data_max)
    
        # Update the color bar based on the data range
        self.update_colorbar(data_min, data_max)
       
        # Update the APD signal value
        apd_signal = data[-1, 2]
        self.apd_signal_label.config(text="{:.3f}".format(apd_signal))
    
        # Update the canvas
        self.canvas.draw_idle()
        self.update_idletasks()
    
    def update_colorbar(self, vmin, vmax):
        """
        Updates the color bar with a new range based on the specified minimum and maximum values.
        
        Arguments:
        vmin : The minimum value for the color scale.
        vmax : The maximum value for the color scale.
        """
        # Remove the existing color bar
        self.colorbar.remove()
    
        # Create new color bar with the updated range
        self.colorbar = self.fig.colorbar(self.im, ax=self.ax, boundaries=np.linspace(vmin, vmax, 256))
        self.colorbar.set_clim(vmin, vmax)
        
    def update_optimize_graph(self, data):
        """
        Updates the optimisation heatmap display and color scaling based on new data, 
        refreshing the canvas and displaying the latest APD signal value.
    
        Arguments:
        data: A 2D array where each row represents a measurement with x, z\y coordinates 
                and a data value (e.g., [x, z\y, value]), used to populate the heatmap.
        """
        data = np.array(data)
    
        # Get the unique x and z values and the number of steps
        x_values = np.unique(data[:, 0])
        z_values = np.unique(data[:, 1])
        x_steps = len(x_values)
        z_steps = len(z_values)
        
        # Create a 2D array for the heatmap data
        heatmap_data = np.zeros((z_steps, x_steps))
    
        # Replace the existing values with new values
        for d in data:
            x_idx = np.where(x_values == d[0])[0][0]
            z_idx = np.where(z_values == d[1])[0][0]
            heatmap_data[z_idx, x_idx] = d[2]
    
        # Update the heatmap data for the optimize graph
        self.im3.set_data(heatmap_data)
    
        # Get the minimum and maximum values of the heatmap data
        data_min = np.nanmin(heatmap_data)
        data_max = np.nanmax(heatmap_data)
    
        # Update the color limits of the color bar
        self.im3.set_clim(data_min, data_max)
        self.update_colorbar3(data_min, data_max)
    
        # Update the canvas
        self.canvas3.draw_idle()
        
        
    def update_colorbar3(self, vmin, vmax):  # New function to update colorbar for fig3
        """
        Updates the optimisation color bar with a new range based on the specified minimum and maximum values.
        
        Arguments:
        vmin : The minimum value for the color scale.
        vmax : The maximum value for the color scale.
        """
    
    
        self.colorbar3.remove()
        self.colorbar3 = self.fig3.colorbar(self.im3, ax=self.ax3, boundaries=np.linspace(vmin, vmax, 256))
        self.colorbar3.set_clim(vmin, vmax)



    def ODMR_Graph_Update(self, x_data, y_data1, fitted_y_data1 ):
        """
        Updates the ODMR plot by clearing any previous data, plotting new raw and fitted data,
        and adjusting the plot's labels, title, and autoscaling.
    
        Arguments:
        x_data : Array of frequency values in MHz.
        y_data1 : Array of photon counts corresponding to the x_data frequencies.
        fitted_y_data1 : Array of fitted photon count values for the fitted curve.
        """
        

     
        self.ax5.clear()  # Clear any previous plots
             
        # Plot the raw data
        self.line1, = self.ax5.plot(x_data, y_data1, label="photon counts")
     
        

        
        # Plot the fitted curve
        self.ax5.plot(x_data, fitted_y_data1, label="Fitted photon counts", linestyle='--')
       
        
        self.ax5.set_xlabel("MW frequency [MHz]")
        self.ax5.set_ylabel("Intensity [kcps]")
        self.ax5.set_title("ODMR")
        self.ax5.legend()
        self.ax5.relim()  # Recompute the limits
        self.ax5.autoscale_view()  # Autoscale the view
        self.canvas5.draw_idle()  # Update the canvas
        
    def update_plot(self, x_data, y_data1, fitted_y_data1):
        
        """
        Schedules an update to the ODMR graph by calling ODMR_Graph_Update with the provided data.
    
        Arguments:
        x_data : Array of frequency values in MHz.
        y_data1 : Array of photon counts corresponding to the x_data frequencies.
        fitted_y_data1 : Array of fitted photon count values for the fitted curve.
        """
        self.after(0, lambda: self.ODMR_Graph_Update(x_data, y_data1, fitted_y_data1))
        
        
    def rectselect(self, eclick, erelease):
        """
        Click function selecting a rectangular region in the optimize plot.
        The AFM tip will ramp to the center of the rectangle and the total x and y scan range will be adjusted.
        """
    
        # get the extent and center of the selected rectangular area
    
        extent = self.rect_selector.extents
        [x_min, x_max, y_min, y_max] = extent
        
        
        print("Extents:", extent)

        # round the values of x0 and y0 to ramp
        x0 = round(self.rect_selector.center[0], 1)
        y0 = round(self.rect_selector.center[1], 1)


        # move to the center of the rectangular region and print the values
        self.my_app.ANC.ramp(1, x0)
        self.my_app.ANC.ramp(2, y0)
    
        # display the center position
        while (float(self.my_app.ANC.get_output(1, Print=False)) != x0) and (float(self.my_app.ANC.get_output(2, Print=False)) != y0) :
            time.sleep(0.1) # if the voltage is not there yet, wait 
                
        else:
            self.my_app.ANC_dynamiclabels[0].set(f"{self.my_app.ANC.get_output(1, Print=False)} V")
            self.my_app.ANC_dynamiclabels[1].set(f"{self.my_app.ANC.get_output(2, Print=False)} V")    

        
        # adjust total x length and total y length of the measurement
        
        dY = round(y_max-y_min, 1)
        dX = round(x_max-x_min, 1)
        
        self.total_X_length.delete(0,tk.END)
        self.total_X_length.insert(0,dX)
        
        self.total_Y_length.delete(0,tk.END)
        self.total_Y_length.insert(0,dY)

        # Zoom the selected part
        # Set xlim range for plot as xmin to xmax
        # of rectangle selector box.
        # self.ax3.set_xlim(extent[0], extent[1])
    
        # Set ylim range for plot as ymin to ymax
        # of rectangle selector box.
        # self.ax3.set_ylim(extent[2], extent[3])
    
    
    
    
    def optimize(self):
        """
        Scans the tip in x and y direction and, finds the maximum of the measurement, 
        moves to that spot and then measures in z direction.
        """
        
        start_time_0 = time.time() # get the starting time of the measurement
        
        try:
            
            # Begin scanning process and update status

            self.scanning = True
            self.status_label.config(text="Scanning")
        
            # Update UI functions for refreshing the display
            def update_ui():
              self.canvas3.draw_idle()
              self.update_idletasks()
            def update_plot(canvas):
              self.after(0, canvas3.draw_idle)
              self.after(0, self.update_idletasks) # Updating plots in thread
              
            # Determine the selected module for scanning (PL or ODMR)
            selection = self.dropdown_var.get()
            
            if selection == 'PL':
                module = self.pl_module
              
            elif selection == 'ODMR':   
                self.heatmap_data_dict.update({ 
                    'freq_center': None,
                    'fwhm': None,
                    'contrast': None,
                    'sensitivity': None
                    })
    
                module = self.odmr_module
                self.odmr_params_confirmed = False
                self.odmr_popup = ODMRPopup(self)
                print("printed")
            
                # Wait for the user to confirm ODMR parameters
                while self.odmr_popup.params == {}:
                    time.sleep(0.1)
                print("here in ODMR after close ")
            
                self.odmr_module.set_odmr_params(self.odmr_popup.params)
                self.odmr_fit_data = []
                self.odmr_data = []
                self.freq_centers= []
                        
           
            module.z_control = self.my_app.asc500.zcontrol
            module.scannerpos = self.my_app.asc500.scanner 
           
            
           # Check if a measurement is already running       
            
            if module.state == 'job_started':
                module.stop_job()
               
            if module.state == 'get_data':
                module.finish_getting_data()
            
            if module.state != 'disconnected':
                module.disconnect()
                # Now it's safe to connect and start the job
          
            
            # update the scanning limits of the voltage of the tip 
            temp = float(self.temp.get())            
            self.my_app.ANC.update_T(temp)
            print("The voltage limit for the tip is {} V !".format(self.my_app.ANC.limits)) 
        
            # Get the x,y parameters from the control panel
            total_X_length = float(self.total_X_length.get())
            total_Y_length = float(self.total_Y_length.get())
                        
            # Get the step size from the caption of the window
            delta_X = float(self.delta_X.get())
            delta_Y = float(self.delta_Y.get())
            
            # Get the delay time from the control panel
            delay_fast = float(self.delay_fast.get())
            delay_slow = float(self.delay_slow.get())
           
            # Get the file name and integration time from the control panel
            file_name = self.file_name.get()
            module.total_integration_time = int(float(self.integration_time.get()) * u.ms)
    
            #corrected stepsizes to ensure an integer number of pixels in the scan
            steps = [int(round(total_X_length/delta_X)), int(round(total_Y_length/delta_Y))]
            stepsize = [float(total_X_length/steps[0]), float(total_Y_length/steps[1])]
            
            # Save the initial positions
            x0 = float(self.my_app.ANC.get_output(1)) 
            y0 = float(self.my_app.ANC.get_output(2))
            
            # get the starting x,y values
            x_start = x0 - total_X_length/2 + stepsize[0]/2
            x_end = x0 + total_X_length/2 
            y_start = y0 - total_Y_length/2 + stepsize[1]/2
            y_end = y0 + total_Y_length/2
            
            # print the arrays of x- and y-points that will be measured
            self.x_array = np.arange(x_start, x_end, stepsize[0])
            self.y_array = np.arange(y_start, y_end, stepsize[1])
            print(self.x_array)
            print(self.y_array)
            
            
            fast_axis = self.fast_axis.get() # 'X' or 'Y'
            
            if fast_axis == 'X':
                [module.fast_steps, module.slow_steps] = steps
                [delta_fast, delta_slow] = stepsize
                [fast0, slow0] = [x_start, y_start]
                
                
            elif fast_axis == 'Y':
                [module.fast_steps, module.slow_steps] = [steps[1], steps[0]]
                [delta_fast, delta_slow] = [stepsize[1], stepsize[0]]
                [fast0, slow0] = [y_start, x_start]
                
            
            # Initialize heatmap data
            module.connect()
            module.start_job()
            module.start_fetching()
            
            #Initialize heatmap data structure 
            for key in self.heatmap_data_dict.keys():
                self.heatmap_data_dict[key] = np.zeros([steps[1], steps[0]])
                self.heatmap_data_dict[key][:,:] = np.nan
                    
            #Reset persisting save path for new scan
            if hasattr(self, 'persistent_save_path'): 
                del self.persistent_save_path
            
            self.im3.set_extent([x0 - total_X_length/2 , x0 + total_X_length/2, y0 - total_Y_length/2, y0 + total_Y_length/2])
            
            line_times = []
    
            # Main scanning loop 
            for i in range(module.slow_steps):
                
                # start_time = int(time.strftime("%M")) * 60 + int(time.strftime("%S"))
                slow = float(slow0 + (i)*delta_slow)
                fast = float(fast0)
                move_to_start_time=time.time()
                
                #Set the positions of slow axis
                if(fast_axis == 'X'):
                    #print(slow)
                    self.my_app.ANC.ramp(2, slow)
                    time.sleep(0.05)
                    self.my_app.ANC_dynamiclabels[1].set(f"{self.my_app.ANC.get_output(2, Print=False)} V")

                elif(fast_axis == 'Y'):
                    #print(slow)
                    self.my_app.ANC.ramp(1, slow)
                    time.sleep(0.05)
                    self.my_app.ANC_dynamiclabels[0].set(f"{self.my_app.ANC.get_output(1, Print=False)} V")
                    
                   
                move_to_start_time_end=time.time()
                
                line_start_time=move_to_start_time_end-move_to_start_time
                print(f'line_start_time : {line_start_time}')
      
                # Inner loop for the fast axis scanning
                for j in range(module.fast_steps):
                    if not self.scanning:
                        break
                
                    fast = float(fast0 + (j)*delta_fast)
                    
                    if fast_axis == 'X':
                        [X, Y] = [fast, slow]
                        [idx1, idx2] = [i, j]
                        
                        #print(fast)
                        self.my_app.ANC.ramp(1, fast)
                        self.my_app.ANC_dynamiclabels[0].set(f"{self.my_app.ANC.get_output(1, Print=False)} V")

                    
                    elif fast_axis == 'Y': 
                        [X, Y] = [slow, fast]
                        [idx1, idx2] = [j, i]
                        
                        #print(fast)
                        self.my_app.ANC.ramp(2, fast)
                        self.my_app.ANC_dynamiclabels[1].set(f"{self.my_app.ANC.get_output(2, Print=False)} V")


                    
                    b = time.time()
                    time.sleep(0.01)
                    e = time.time()
                    #print(f'X_fast time passed= {e - b}')
                
                    time.sleep(delay_fast)
                    
                    #print(f'getdata_using_qua = { time.time()}')
                    f_idx = i * module.fast_steps + j
                    module.get_data(f_idx) # Get data from the module after moving
                    
                    # check if this is an ODMR module with fitting:
                    if hasattr(module, "start_fitting_thread"):
                        module.start_fitting_thread()
                        threading.Thread(
                            target=self.update_odmr_plot_2dscan,
                            args=(module,),
                            daemon=True
                        ).start()
                    else:
                        # PL module
                        # no fitting, no plotting
                        pass
                
                    # Access the data dictionary directly from the module object
                    
                    
                    data_dict = module.data_dict
                    #print(f'after_getting_data= { time.time()}')
                    
                    
                    # Update heatmap data
                    for key in self.heatmap_data_dict.keys():
                        self.heatmap_data_dict[key][idx1, idx2] = data_dict.get(key, 0)
                    
                    # Update the fitted plot if ODMR
                    if selection=='ODMR':
                        
                        self.update_plot(data_dict.get('x_data'), data_dict.get('y_data'), data_dict.get('fitted_y_data'))
                        self.odmr_frequencies = data_dict.get('x_data')
                        self.odmr_data.append([data_dict.get('y_data')])
                        self.odmr_fit_data.append([data_dict.get('fitted_y_data')])
                        self.freq_centers.append(data_dict.get('freq_center', np.nan))
                        
                        #odmr_spectrum.append('')
                    
                    # Update the heatmap display and UI
                    self.after(0, self.update_displayed_heatmap_opt)
                    self.after(0, update_ui)
                    self.update_idletasks()
                    # Time left estimation
                    line_end_time = time.time()
                    line_duration = line_end_time - move_to_start_time
                    line_times.append(line_duration)
                    average_line_time = np.mean(line_times)
                    lines_remaining = module.slow_steps - (i + 1)
                    minutes_left = (average_line_time * lines_remaining) / 60
                    self.time_left_label.config(text="{:.3f} ".format(minutes_left))
                    

                    if self.save_flag.get():  # If auto-save is ON
                        end_time = time.time()
                        scantime = end_time - start_time_0
                        self.headerlines = [f"#Scantype: Stepscan \n#Date: {time.strftime('%Y-%m-%d %H:%M:%S')}", 
                                            f"\n#Total scanning time: {scantime}", f"\n#Scan direction: {self.fast_axis.get()}", 
                                            f"\n#X range: {self.x_array[0]} - {self.x_array[-1]} um", f"\n#Y range: {self.y_array[0]} - {self.y_array[-1]} um", 
                                            f"\n#X pixels: {steps[0]}, pixelsize: {stepsize[0]} um", f"\n#Y pixels: {steps[1]}, pixelsize: {stepsize[1]} um",
                                            f"\n#Integration time per pixel: {module.total_integration_time/1E6} ms", "\n#Columns:"]
                       
                        self.save_heatmap_data(selection=selection)
              
                               
                if not self.scanning:
                    break
        
            end_time = time.time()
            scantime = end_time - start_time_0
            
            self.headerlines = [f"#Scantype: Stepscan \n#Date: {time.strftime('%Y-%m-%d %H:%M:%S')}", 
                                f"\n#Total scanning time: {scantime}", f"\n#Scan direction: {self.fast_axis.get()}", 
                                f"\n#X range: {self.x_array[0]} - {self.x_array[-1]} um", f"\n#Y range: {self.y_array[0]} - {self.y_array[-1]} um", 
                                f"\n#X pixels: {steps[0]}, pixelsize: {stepsize[0]} m", f"\n#Y pixels: {steps[1]}, pixelsize: {stepsize[1]} m",
                                f"\n#Integration time per pixel: {module.total_integration_time/1E6} ms", "\n#Columns:"]
            
            if selection == 'ODMR':
                ODMRheader = ["\n#ODMR Parameters",
                              f"\n#Frequency range: {np.min(self.odmr_frequencies)} - {np.max(self.odmr_frequencies)} GHz",
                              f"\n#Number of frequency points: {np.size(self.odmr_frequencies)}", 
                              f"\n#Number of averages: {module.N_average}"]
                print(ODMRheader)

                self.headerlines.extend(ODMRheader)
            
            # If auto-save is off update the heatmap data 
            if not self.save_flag.get():
                print("Auto-save is OFF. Saving heatmap data after scan completion...")
                self.save_heatmap_data(selection=selection)  
            
            if selection =='ODMR':
                frequencies = module.x_data
 
            
            # get the counts
            counts = self.heatmap_data_dict['counts [kc/s]']

            # Find the index of highest counts
            
            # print(np.argmax(counts))
            ind = np.unravel_index(np.argmax(counts, axis=None), counts.shape)
            #print(ind)          
            
            # find x and y values of highest counts
            x_maxC = self.x_array[(ind[1])]
            y_maxC = self.y_array[(ind[0])]
            
            print(x_maxC, y_maxC)
            
            self.my_app.ANC.ramp(1, x_maxC)
            self.my_app.ANC.ramp(2, y_maxC)
        
            # display the starting position
            while (abs(float(self.my_app.ANC.get_output(1, Print=False)) - x_maxC ) > stepsize[0]) and ( abs(float(self.my_app.ANC.get_output(2, Print=False)) - y_maxC ) > stepsize[1]) :
                time.sleep(0.1) # if the voltage is not there yet, wait 
                    
            else:
                time.sleep(0.5)
                self.my_app.ANC_dynamiclabels[0].set(f"{self.my_app.ANC.get_output(1, Print=False)} V")
                self.my_app.ANC_dynamiclabels[1].set(f"{self.my_app.ANC.get_output(2, Print=False)} V")
            
            
            ### Perform a z-scan
            
            # Define the scanning values
            total_Z_length  = 100    
            delta_Z         = 1
            z0              = 50
            z_start         = z0 - total_Z_length/2 
            z_end           = z0 + total_Z_length/2 + delta_Z/2
            self.z_array    = np.arange(z_start, z_end, delta_Z)
            
           #print(z0, z_start, delta_Z, self.z_array)
            
            counts_z = []
            
            self.my_app.ANC.ramp(3, z0)
            
            while (abs(float(self.my_app.ANC.get_output(3, Print=False)) - z0) > delta_Z):
                time.sleep(0.1) # if the voltage is not there yet, wait 
                    
            else:
                time.sleep(0.5)
                self.my_app.ANC_dynamiclabels[2].set(f"{self.my_app.ANC.get_output(3, Print=False)} V")           

            
            # main scanning loop 
            for j in range(len(self.z_array)):
                
                # move to z values and display
                self.my_app.ANC.ramp(3, self.z_array[j])
                time.sleep(0.05)
                self.my_app.ANC_dynamiclabels[2].set(f"{self.my_app.ANC.get_output(3, Print=False)} V")
                
                # measure the counts
                f_idx = module.fast_steps*module.slow_steps + j
                module.get_data(f_idx)
                
                
                counts_z = np.append(counts_z, module.data_dict['counts [kc/s]'])
                
                # # Update the fitted plot if ODMR
                # if selection=='ODMR':
                    
                #     self.update_plot(data_dict.get('x_data'), data_dict.get('y_data'), data_dict.get('fitted_y_data'))
                #     self.odmr_frequencies = data_dict.get('x_data')
                #     self.odmr_data.append([data_dict.get('y_data')])
                #     self.odmr_fit_data.append([data_dict.get('fitted_y_data')])
                #     self.freq_centers.append(data_dict.get('freq_center', np.nan))
                  
                self.ax4.clear()
                self.ax4.plot(self.z_array[:j+1], counts_z)
                self.canvas4.draw_idle()
                self.update_idletasks()
            
            # find z values of highest counts
            i_maxC = np.argmax(counts_z)
            z_maxC = self.z_array[i_maxC] 
            
            #print(i_maxC, z_maxC)
            
            # move to the z position of the highest counts
            self.my_app.ANC.ramp(3, z_maxC)
    
            while (abs(float(self.my_app.ANC.get_output(3, Print=False)) - z_maxC) > delta_Z):
                time.sleep(0.1) # if the voltage is not there yet, wait 
                    
            else:
                time.sleep(0.5)
                self.my_app.ANC_dynamiclabels[2].set(f"{self.my_app.ANC.get_output(3, Print=False)} V")    
        
            
            
            if module.state == 'job_started':
                module.stop_job()

            if module.state == 'get_data':
                  module.finish_getting_data()
                 
            if module.state != 'disconnected':
                module.disconnect()
            
            
            self.scanning = False
            self.status_label.config(text="Idle")        


        except Exception as e:
            print(f"Error during scan: {e}")
            self.status_label.config(text="Error")
            self.scanning = False 
            
            
  

    def scan_loop(self):
        """
       Executes a scanning loop for data acquisition, updating heatmap data, and managing 
       scan control logic, including axis selection, motor control, and data fetching from 
       the selected module (e.g., PL or ODMR). This function handles the entire scan sequence,
       periodic UI updates, heatmap updates, and optional auto-saving of data.
    
       Arguments:
       None (this function uses class attributes and UI elements directly for configuration).
       """
        
        start_time_0 = time.time()
        
        try:
            # Begin scanning process and update status

            self.scanning = True
            self.status_label.config(text="Scanning")
            
            # Update UI functions for refreshing the display
            def update_ui():
              self.canvas.draw_idle()
              self.update_idletasks()
            def update_plot(canvas):
              self.after(0, canvas.draw_idle)
              self.after(0, self.update_idletasks) # Updating plots in thread
              
            # Determine the selected module for scanning (PL or ODMR)
            selection = self.dropdown_var.get()
            
            if selection == 'PL':
                module = self.pl_module
              
            elif selection == 'ODMR':
                self.heatmap_data_dict.update({
                    'freq_center': None,
                    'fwhm': None,
                    'contrast': None,
                    'sensitivity': None
                    })
                
                module = self.odmr_module
                self.odmr_params_confirmed = False
                self.odmr_popup = ODMRPopup(self)
                #print(self.odmr_popup)
                print("printed")
                
                # Wait for the user to confirm ODMR parameters
                while self.odmr_popup.params == {}:
                    time.sleep(0.1)
                print("here in ODMR after close ")
                
                self.odmr_module.set_odmr_params(self.odmr_popup.params)
                self.odmr_fit_data = []
                self.odmr_data = []
                self.freq_centers=  []
                
                
            module.z_control = self.my_app.asc500.zcontrol
            module.scannerpos = self.my_app.asc500.scanner
            module.app = app
                
               
            if module.state == 'job_started':
                module.stop_job()
           
            if module.state == 'get_data':
                 module.finish_getting_data()
            if module.state != 'disconnected':
                module.disconnect()
            # Now it's safe to connect and start the job
      
    
            # Get the parameters from the control panel
            total_X_length = float(self.total_X_length.get())*1e-6
            total_Y_length = float(self.total_Y_length.get())*1e-6
            delta_X = float(self.delta_X.get())*1e-6
            delta_Y = float(self.delta_Y.get())*1e-6
            delay_fast = float(self.delay_fast.get())
            delay_slow = float(self.delay_slow.get())
            file_name = self.file_name.get()
            module.total_integration_time = int(float(self.integration_time.get()) * u.ms)
    
            #corrected stepsizes to ensure an integer number of pixels in the scan
            steps = [int(round(total_X_length/delta_X)), int(round(total_Y_length/delta_Y))]
            stepsize = [total_X_length/steps[0], total_Y_length/steps[1]]
                       
            # Save the initial positions
            x0, y0 = self.my_app.get_xy_position()
            x_start = x0 - total_X_length/2 + stepsize[0]/2
            x_end = x0 + total_X_length/2 
            y_start = y0 - total_Y_length/2 + stepsize[1]/2
            y_end = y0 + total_Y_length/2
            
            self.x_array = np.arange(x_start, x_end, stepsize[0])*1e6
            self.y_array = np.arange(y_start, y_end, stepsize[1])*1e6
            print(self.x_array)
            print(self.y_array)
            
                        
            fast_axis = self.fast_axis.get() # 'X' or 'Y'
            
            if fast_axis == 'X':
                [module.fast_steps, module.slow_steps] = steps
                [delta_fast, delta_slow] = stepsize
                [fast0, slow0] = [x_start, y_start]
                
                            
            elif fast_axis == 'Y':
                [module.fast_steps, module.slow_steps] = [steps[1], steps[0]]
                [delta_fast, delta_slow] = [stepsize[1], stepsize[0]]
                [fast0, slow0] = [y_start, x_start]
                           
            
            # Initialize heatmap data
            module.connect()
            module.start_job()
            module.start_fetching()
            
            #Initialize heatmap data structure 
            for key in self.heatmap_data_dict.keys():
                self.heatmap_data_dict[key] = np.zeros([steps[1], steps[0]])
                self.heatmap_data_dict[key][:,:] = np.nan
                
            #Reset persisting save path for new scan
            if hasattr(self, 'persistent_save_path'): 
                del self.persistent_save_path
    
            
            self.im.set_extent([x0 - total_X_length/2 , x0 + total_X_length/2, y0 - total_Y_length/2, y0 + total_Y_length/2])
            
            line_times = []
    
            # Main scanning loop 
            for i in range(module.slow_steps):
                
                # start_time = int(time.strftime("%M")) * 60 + int(time.strftime("%S"))
                slow = slow0 + (i) * delta_slow
                fast = fast0
                move_to_start_time=time.time()
                
                #Set the positions of slow axis
                if(fast_axis == 'X'):
                    self.my_app.move(fast, slow)
                    time.sleep(0.05)

                elif(fast_axis == 'Y'):
                    self.my_app.move(slow, fast)
                    time.sleep(0.05)
                    
                   
                move_to_start_time_end=time.time()
                
                line_start_time=move_to_start_time_end-move_to_start_time
                print(f'line_start_time : {line_start_time}')
      
                # Inner loop for the fast axis scanning
                for j in range(module.fast_steps):
                    if not self.scanning:
                        break
                
                    fast = fast0 + (j) * delta_fast
                    
                    if fast_axis == 'X':
                        [X, Y] = [fast, slow]
                        [idx1, idx2] = [i, j]
                        
                    elif fast_axis == 'Y':
                        [X, Y] = [slow, fast]
                        [idx1, idx2] = [j, i]
                    
                    b = time.time()
                    self.my_app.move(X, Y)
                    time.sleep(0.01)
                    e = time.time()
                    #print(f'X_fast time passed= {e - b}')
                
                    time.sleep(delay_fast)
                    
                    #print(f'getdata_using_qua = { time.time()}')
                    f_idx = i * module.fast_steps + j
                    module.get_data(f_idx) # Get data from the module after moving
                    
                    # check if this is an ODMR module with fitting:
                    if hasattr(module, "start_fitting_thread"):
                        module.start_fitting_thread()
                        threading.Thread(
                            target=self.update_odmr_plot_2dscan,
                            args=(module,),
                            daemon=True
                        ).start()
                    else:
                        # PL module
                        # no fitting, no plotting
                        pass
                
                    # Access the data dictionary directly from the module object
                    
                    data_dict = module.data_dict
                    #print(f'after_getting_data= { time.time()}')
                        
                    # Update heatmap data
                    for key in self.heatmap_data_dict.keys():
                        self.heatmap_data_dict[key][idx1, idx2] = data_dict.get(key, 0)
                    
                    # Update the fitted plot if ODMR
                    if selection=='ODMR':
                        
                        self.update_plot(data_dict.get('x_data'), data_dict.get('y_data'), data_dict.get('fitted_y_data'))
                        self.odmr_frequencies = data_dict.get('x_data')
                        self.odmr_data.append([data_dict.get('y_data')])
                        self.odmr_fit_data.append([data_dict.get('fitted_y_data')])
                        self.freq_centers.append(data_dict.get('freq_center', np.nan))
                        
                        #odmr_spectrum.append('')
                    
                    # Update the heatmap display and UI
                    self.after(0, self.update_displayed_heatmap)
                    self.after(0, update_ui)
                    self.update_idletasks()
                    # Time left estimation
                    line_end_time = time.time()
                    line_duration = line_end_time - move_to_start_time
                    line_times.append(line_duration)
                    average_line_time = np.mean(line_times)
                    lines_remaining = module.slow_steps - (i + 1)
                    minutes_left = (average_line_time * lines_remaining) / 60
                    self.time_left_label.config(text="{:.3f} ".format(minutes_left))
                    

                    if self.save_flag.get():  # If auto-save is ON
                        end_time = time.time()
                        scantime = end_time - start_time_0
                        self.headerlines = [f"#Scantype: Stepscan \n#Date: {time.strftime('%Y-%m-%d %H:%M:%S')}", 
                                            f"\n#Total scanning time: {scantime}", f"\n#Scan direction: {self.fast_axis.get()}", 
                                           f"\n#X range: {self.x_array[0]} - {self.x_array[-1]} um", f"\n#Y range: {self.y_array[0]} - {self.y_array[-1]} um", 
                                           f"\n#X pixels: {steps[0]}, pixelsize: {stepsize[0]} um", f"\n#Y pixels: {steps[1]}, pixelsize: {stepsize[1]} um",
                                           f"\n#Integration time per pixel: {module.total_integration_time/1E6} ms", "\n#Columns:"]
                       
                        self.save_heatmap_data(selection=selection)
                    
                    #print(f'after_plot = {time.time()}')
                    
              
                               
                if not self.scanning:
                    break
        
              
                          
                # Update expected time left for the scan
                # finish_time = int(time.strftime("%M")) * 60 + int(time.strftime("%S"))
                # time.sleep(delay_slow)
                # expected_time = ((finish_time - start_time) * (1 - i / module.slow_steps) *  module.slow_steps) / 60
                # self.time_left_label.config(text="{:.3f}".format(expected_time))
                # self.after(0, update_ui)
            
            end_time = time.time()
            scantime = end_time - start_time_0
            
            self.headerlines = [f"#Scantype: Stepscan \n#Date: {time.strftime('%Y-%m-%d %H:%M:%S')}", 
                                f"\n#Total scanning time: {scantime}", f"\n#Scan direction: {self.fast_axis.get()}", 
                               f"\n#X range: {self.x_array[0]} - {self.x_array[-1]} um", f"\n#Y range: {self.y_array[0]} - {self.y_array[-1]} um", 
                               f"\n#X pixels: {steps[0]}, pixelsize: {stepsize[0]} m", f"\n#Y pixels: {steps[1]}, pixelsize: {stepsize[1]} m",
                               f"\n#Integration time per pixel: {module.total_integration_time/1E6} ms", "\n#Columns:"]
            
            if selection == 'ODMR':
                ODMRheader = ["\n#ODMR Parameters",
                              f"\n#Frequency range: {np.min(self.odmr_frequencies)} - {np.max(self.odmr_frequencies)} GHz",
                              f"\n#Number of frequency points: {np.size(self.odmr_frequencies)}", 
                              f"\n#Number of averages: {module.N_average}"]
                print(ODMRheader)

                self.headerlines.extend(ODMRheader)
            
            # If auto-save is off update the heatmap data 
            if not self.save_flag.get():
                print("Auto-save is OFF. Saving heatmap data after scan completion...")
                self.save_heatmap_data(selection=selection)  
            
            if selection =='ODMR':
                frequencies = module.x_data
                
                
            if module.state == 'job_started':
                module.stop_job()

            if module.state == 'get_data':
                 module.finish_getting_data()
                 
            if module.state != 'disconnected':
                module.disconnect()
                

 
            self.my_app.move(x0, y0)
            self.scanning = False
            self.status_label.config(text="Idle")
        except Exception as e:
            print(f"Error during scan: {e}")
            self.status_label.config(text="Error")
            self.scanning = False

    def tip_scan(self):
        """
        Executes a scanning loop for the AFM tip, updating heatmap data, and managing 
        scan control logic, including axis selection, motor control, and data fetching from 
        the selected module (e.g., PL or ODMR). This function handles the entire scan sequence,
        periodic UI updates, heatmap updates, and optional auto-saving of data.
 
        Arguments:
            None (this function uses class attributes and UI elements directly for configuration).
        """
        
        start_time_0 = time.time() # get the starting time of the measurement
        
        try:
            
            # Begin scanning process and update status

            self.scanning = True
            self.status_label.config(text="Scanning")
        
            # Update UI functions for refreshing the display
            def update_ui():
              self.canvas.draw_idle()
              self.update_idletasks()
            def update_plot(canvas):
              self.after(0, canvas.draw_idle)
              self.after(0, self.update_idletasks) # Updating plots in thread
              
            # Determine the selected module for scanning (PL or ODMR)
            selection = self.dropdown_var.get()
            
            if selection == 'PL':
                module = self.pl_module
              
            elif selection == 'ODMR':   
                self.heatmap_data_dict.update({ 
                    'freq_center': None,
                    'fwhm': None,
                    'contrast': None,
                    'sensitivity': None
                    })
    
                module = self.odmr_module
                self.odmr_params_confirmed = False
                self.odmr_popup = ODMRPopup(self)
                print("printed")
            
                # Wait for the user to confirm ODMR parameters
                while self.odmr_popup.params == {}:
                    time.sleep(0.1)
                print("here in ODMR after close ")
            
                self.odmr_module.set_odmr_params(self.odmr_popup.params)
                self.odmr_fit_data = []
                self.odmr_data = []
                self.freq_centers= []
                        
           
            module.z_control = self.my_app.asc500.zcontrol
            module.scannerpos = self.my_app.asc500.scanner 
           

            
            # Check if a measurement is already running       
            
            if module.state == 'job_started':
                module.stop_job()
               
            if module.state == 'get_data':
                module.finish_getting_data()
            
            if module.state != 'disconnected':
                module.disconnect()
                # Now it's safe to connect and start the job
          
            # update the scanning limits of the voltage of the tip 
            temp = float(self.temp.get())            
            self.my_app.ANC.update_T(temp)
            print("The voltage limit for the tip is {} V !".format(self.my_app.ANC.limits)) 
        
            # Get the x,y parameters from the control panel
            total_X_length = float(self.total_X_length.get())
            total_Y_length = float(self.total_Y_length.get())
                        
            # Get the step size from the caption of the window
            delta_X = float(self.delta_X.get())
            delta_Y = float(self.delta_Y.get())
            
            # Get the delay time from the control panel
            delay_fast = float(self.delay_fast.get())
            delay_slow = float(self.delay_slow.get())
           
            # Get the file name and integration time from the control panel
            file_name = self.file_name.get()
            module.total_integration_time = int(float(self.integration_time.get()) * u.ms)
    
            #corrected stepsizes to ensure an integer number of pixels in the scan
            steps = [int(round(total_X_length/delta_X)), int(round(total_Y_length/delta_Y))]
            stepsize = [float(total_X_length/steps[0]), float(total_Y_length/steps[1])]
            
            # Save the initial positions
            x0 = float(self.my_app.ANC.get_output(1)) 
            y0 = float(self.my_app.ANC.get_output(2))
            
            # get the starting x,y values
            x_start = x0 - total_X_length/2 + stepsize[0]/2
            x_end = x0 + total_X_length/2 
            y_start = y0 - total_Y_length/2 + stepsize[1]/2
            y_end = y0 + total_Y_length/2
            
            # print the arrays of x- and y-points that will be measured
            self.x_array = np.arange(x_start, x_end, stepsize[0])
            self.y_array = np.arange(y_start, y_end, stepsize[1])
            print(self.x_array)
            print(self.y_array)
            
            
            fast_axis = self.fast_axis.get() # 'X' or 'Y'
            
            if fast_axis == 'X':
                [module.fast_steps, module.slow_steps] = steps
                [delta_fast, delta_slow] = stepsize
                [fast0, slow0] = [x_start, y_start]
                
                
            elif fast_axis == 'Y':
                [module.fast_steps, module.slow_steps] = [steps[1], steps[0]]
                [delta_fast, delta_slow] = [stepsize[1], stepsize[0]]
                [fast0, slow0] = [y_start, x_start]
                
            
            # Initialize heatmap data
            module.connect()
            module.start_job()
            module.start_fetching()
            
            #Initialize heatmap data structure 
            for key in self.heatmap_data_dict.keys():
                self.heatmap_data_dict[key] = np.zeros([steps[1], steps[0]])
                self.heatmap_data_dict[key][:,:] = np.nan
                    
            #Reset persisting save path for new scan
            if hasattr(self, 'persistent_save_path'): 
                del self.persistent_save_path
            
            self.im.set_extent([x0 - total_X_length/2 , x0 + total_X_length/2, y0 - total_Y_length/2, y0 + total_Y_length/2])
            
            line_times = []
    
            # Main scanning loop 
            for i in range(module.slow_steps):
                
                # start_time = int(time.strftime("%M")) * 60 + int(time.strftime("%S"))
                slow = float(slow0 + (i)*delta_slow)
                fast = float(fast0)
                move_to_start_time=time.time()
                
                #Set the positions of slow axis
                if(fast_axis == 'X'):
                    #print(slow)
                    self.my_app.ANC.ramp(2, slow)
                    time.sleep(0.05)
                    self.my_app.ANC_dynamiclabels[1].set(f"{self.my_app.ANC.get_output(2)} V")

                elif(fast_axis == 'Y'):
                    #print(slow)
                    self.my_app.ANC.ramp(1, slow)
                    time.sleep(0.05)
                    self.my_app.ANC_dynamiclabels[0].set(f"{self.my_app.ANC.get_output(1)} V")
                    
                   
                move_to_start_time_end=time.time()
                
                line_start_time=move_to_start_time_end-move_to_start_time
                print(f'line_start_time : {line_start_time}')
      
                # Inner loop for the fast axis scanning
                for j in range(module.fast_steps):
                    if not self.scanning:
                        break
                
                    fast = float(fast0 + (j)*delta_fast)
                    
                    if fast_axis == 'X':
                        [X, Y] = [fast, slow]
                        [idx1, idx2] = [i, j]
                        
                        #print(fast)
                        self.my_app.ANC.ramp(1, fast)
                        self.my_app.ANC_dynamiclabels[0].set(f"{self.my_app.ANC.get_output(1)} V")

                    
                    elif fast_axis == 'Y': 
                        [X, Y] = [slow, fast]
                        [idx1, idx2] = [j, i]
                        
                        #print(fast)
                        self.my_app.ANC.ramp(2, fast)
                        self.my_app.ANC_dynamiclabels[1].set(f"{self.my_app.ANC.get_output(2)} V")


                    
                    b = time.time()
                    time.sleep(0.01)
                    e = time.time()
                    #print(f'X_fast time passed= {e - b}')
                
                    time.sleep(delay_fast)
                    
                    #print(f'getdata_using_qua = { time.time()}')
                    f_idx = i * module.fast_steps + j
                    module.get_data(f_idx) # Get data from the module after moving
                    
                    # check if this is an ODMR module with fitting:
                    if hasattr(module, "start_fitting_thread"):
                        module.start_fitting_thread()
                        threading.Thread(
                            target=self.update_odmr_plot_2dscan,
                            args=(module,),
                            daemon=True
                        ).start()
                    else:
                        # PL module
                        # no fitting, no plotting
                        pass
                
                    # Access the data dictionary directly from the module object
                    
                    
                    data_dict = module.data_dict
                    #print(f'after_getting_data= { time.time()}')
                    
                    
                    # Update heatmap data
                    for key in self.heatmap_data_dict.keys():
                        self.heatmap_data_dict[key][idx1, idx2] = data_dict.get(key, 0)
                    
                    # Update the fitted plot if ODMR
                    if selection=='ODMR':
                        
                        self.update_plot(data_dict.get('x_data'), data_dict.get('y_data'), data_dict.get('fitted_y_data'))
                        self.odmr_frequencies = data_dict.get('x_data')
                        self.odmr_data.append([data_dict.get('y_data')])
                        self.odmr_fit_data.append([data_dict.get('fitted_y_data')])
                        self.freq_centers.append(data_dict.get('freq_center', np.nan))
                        
                        #odmr_spectrum.append('')
                    
                    # Update the heatmap display and UI
                    self.after(0, self.update_displayed_heatmap)
                    self.after(0, update_ui)
                    self.update_idletasks()
                    # Time left estimation
                    line_end_time = time.time()
                    line_duration = line_end_time - move_to_start_time
                    line_times.append(line_duration)
                    average_line_time = np.mean(line_times)
                    lines_remaining = module.slow_steps - (i + 1)
                    minutes_left = (average_line_time * lines_remaining) / 60
                    self.time_left_label.config(text="{:.3f} ".format(minutes_left))
                    

                    if self.save_flag.get():  # If auto-save is ON
                        end_time = time.time()
                        scantime = end_time - start_time_0
                        self.headerlines = [f"#Scantype: Stepscan \n#Date: {time.strftime('%Y-%m-%d %H:%M:%S')}", 
                                            f"\n#Total scanning time: {scantime}", f"\n#Scan direction: {self.fast_axis.get()}", 
                                            f"\n#X range: {self.x_array[0]} - {self.x_array[-1]} um", f"\n#Y range: {self.y_array[0]} - {self.y_array[-1]} um", 
                                            f"\n#X pixels: {steps[0]}, pixelsize: {stepsize[0]} um", f"\n#Y pixels: {steps[1]}, pixelsize: {stepsize[1]} um",
                                            f"\n#Integration time per pixel: {module.total_integration_time/1E6} ms", "\n#Columns:"]
                       
                        self.save_heatmap_data(selection=selection)
                    
                    #print(f'after_plot = {time.time()}')
                    
              
                               
                if not self.scanning:
                    break
        
              
                          
                # Update expected time left for the scan
                # finish_time = int(time.strftime("%M")) * 60 + int(time.strftime("%S"))
                # time.sleep(delay_slow)
                # expected_time = ((finish_time - start_time) * (1 - i / module.slow_steps) *  module.slow_steps) / 60
                # self.time_left_label.config(text="{:.3f}".format(expected_time))
                # self.after(0, update_ui)
            
            end_time = time.time()
            scantime = end_time - start_time_0
            
            self.headerlines = [f"#Scantype: Stepscan \n#Date: {time.strftime('%Y-%m-%d %H:%M:%S')}", 
                                f"\n#Total scanning time: {scantime}", f"\n#Scan direction: {self.fast_axis.get()}", 
                                f"\n#X range: {self.x_array[0]} - {self.x_array[-1]} um", f"\n#Y range: {self.y_array[0]} - {self.y_array[-1]} um", 
                                f"\n#X pixels: {steps[0]}, pixelsize: {stepsize[0]} m", f"\n#Y pixels: {steps[1]}, pixelsize: {stepsize[1]} m",
                                f"\n#Integration time per pixel: {module.total_integration_time/1E6} ms", "\n#Columns:"]
            
            if selection == 'ODMR':
                ODMRheader = ["\n#ODMR Parameters",
                              f"\n#Frequency range: {np.min(self.odmr_frequencies)} - {np.max(self.odmr_frequencies)} GHz",
                              f"\n#Number of frequency points: {np.size(self.odmr_frequencies)}", 
                              f"\n#Number of averages: {module.N_average}"]
                print(ODMRheader)

                self.headerlines.extend(ODMRheader)
            
            # If auto-save is off update the heatmap data 
            if not self.save_flag.get():
                print("Auto-save is OFF. Saving heatmap data after scan completion...")
                self.save_heatmap_data(selection=selection)  
            
            if selection =='ODMR':
                frequencies = module.x_data
                
                
            if module.state == 'job_started':
                module.stop_job()

            if module.state == 'get_data':
                  module.finish_getting_data()
                 
            if module.state != 'disconnected':
                module.disconnect()
                

            # go to the starting position 
            self.my_app.ANC.ramp(1, x0)
            self.my_app.ANC.ramp(2, y0)
            
            # display the starting position
            while (abs(float(self.my_app.ANC.get_output(1, Print=False)) - x0 ) > stepsize[0]) and ( abs(float(self.my_app.ANC.get_output(2, Print=False)) - y0 ) > stepsize[1]) :
                time.sleep(0.1) # if the voltage is not there yet, wait 
                    
            else:
                time.sleep(0.5)
                self.my_app.ANC_dynamiclabels[0].set(f"{self.my_app.ANC.get_output(1, Print=False)} V")
                self.my_app.ANC_dynamiclabels[1].set(f"{self.my_app.ANC.get_output(2, Print=False)} V")
                          
            
            self.scanning = False
            self.status_label.config(text="Idle")        


        except Exception as e:
            print(f"Error during scan: {e}")
            self.status_label.config(text="Error")
            self.scanning = False                    

        
    def abort_scan(self):
        """
        Aborts an ongoing scan by stopping scanning processes, updating the status label,
        and cleaning up resources for the PL and ODMR modules if they exist.
        """
        #self.my_app.closed = True
        self.scanning = False
        self.status_label.config(text="Idle")
        
        # find out which scan is being executed
        selected_scan = self.scan_type.get()

        if selected_scan == "2D Scan" or selected_scan == "2D F_Line Scan":
           self.my_app.asc500.scanner.pauseScanner()  # Stop the motors
        
        elif selected_scan == "2D Scan Tip":
            self.my_app.ANC_abort_move() # ANC Tip abort move
    
    
        # Cleanup PL Module
        if hasattr(self, 'pl_module'):
            self.pl_module.cleanup()
            
        # Cleanup PL Module for linescan
        if hasattr(self, 'pl_module_linescan'):
            self.pl_module_linescan.cleanup()
    
        # Cleanup ODMR Module
        if hasattr(self, 'odmr_module'):
            self.odmr_module.cleanup()
            
            
            
    def update_odmr_plot_2dscan(self, module):
        """
        Waits for the fitting to complete, then updates the ODMR plot
        with x_data, y_data, and fitted_y_data from the module.
        Arguments:
        module : The ODMR module instance running the measurement.
        """
        while module.data_dict.get("fit_status", "") != "ok":
            time.sleep(0.01)
        with data_lock:
            x_data = module.data_dict.get("x_data")
            y_data = module.data_dict.get("y_data")
            fitted_y_data = module.data_dict.get("fitted_y_data")
        self.update_plot(x_data, y_data, fitted_y_data)        
            


if __name__ == "__main__":
    app = ScannerApp()
    app.mainloop()
