import tkinter as tk
from tkinter import ttk
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from motorized_stage import MotorizedStageApp
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

sourceFile = open('debug.py', 'w')
print(generate_qua_script(counter, config), file=sourceFile)
sourceFile.close()


# new_counts = counts_handle.fetch("counts")["value"] # counts exports
# print(new_counts)

class ScannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("2D Photoluminescence Scanner")
        self.my_app = MotorizedStageApp()
    
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
    
        self.motorized_stage_app = MotorizedStageApp(self.motorized_stage_frame)
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
        
        
    def on_close(self):
        # Your closing logic here
        self.destroy()

    def create_control_panel(self):
        control_frame = self.control_frame

        style = ttk.Style()
        style.configure('Large.TButton', font=("Helvetica", 12, "bold"), padding=(20, 10))

        # Create a new frame for the control panel elements
        scanning_control_frame = ttk.Frame(control_frame)
        scanning_control_frame.grid(row=1, column=1, sticky="nsew")

        ttk.Label(scanning_control_frame, text="Total Fast Length (mm)").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.total_fast_length = ttk.Entry(scanning_control_frame, width=10)
        self.total_fast_length.insert(0, "0.01")
        self.total_fast_length.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(scanning_control_frame, text="Total Slow Length (mm)").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.total_slow_length = ttk.Entry(scanning_control_frame, width=10)
        self.total_slow_length.insert(0, "0.01")
        self.total_slow_length.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(scanning_control_frame, text="Step Fast Length (mm)").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.delta_fast = ttk.Entry(scanning_control_frame, width=10)
        self.delta_fast.insert(0, "0.0001")
        self.delta_fast.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(scanning_control_frame, text="Step Slow Length (mm)").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.delta_slow = ttk.Entry(scanning_control_frame, width=10)
        self.delta_slow.insert(0, "0.0001")
        self.delta_slow.grid(row=2, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(scanning_control_frame, text="Fast Delay (sec)").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.delay_fast = ttk.Entry(scanning_control_frame, width=10)
        self.delay_fast.insert(0, "0.1")
        self.delay_fast.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(scanning_control_frame, text="Slow Delay (sec)").grid(row=3, column=2, padx=5, pady=5, sticky="w")
        self.delay_slow = ttk.Entry(scanning_control_frame, width=10)
        self.delay_slow.insert(0, "0.1")
        self.delay_slow.grid(row=3, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(scanning_control_frame, text="File Name").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.file_name = ttk.Entry(scanning_control_frame, width=20)
        self.file_name.insert(0, "test.txt")
        self.file_name.grid(row=5, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(scanning_control_frame, text="Integration Time (sec)").grid(row=4, column=2, padx=5, pady=5, sticky="w")
        self.integration_time = ttk.Entry(scanning_control_frame, width=10)
        self.integration_time.insert(0, "0.1")
        self.integration_time.grid(row=4, column=3, padx=5, pady=5, sticky="w")
        
        self.start_button = ttk.Button(scanning_control_frame, text="2D Scan", command=self.start_scan, style='Large.TButton')
        self.start_button.grid(row=6, column=0, columnspan=1, padx=10, pady=10, sticky="ew")
        
        self.start_button = ttk.Button(scanning_control_frame, text="Fast Axis Line Scan", command=self.start_line_scan, style='Large.TButton')
        self.start_button.grid(row=6, column=1, columnspan=1, padx=10, pady=10, sticky="ew")
        
        self.start_button = ttk.Button(scanning_control_frame, text="Start Time Trace", command=self.start_time_trace, style='Large.TButton')
        self.start_button.grid(row=6, column=2, columnspan=1, padx=10, pady=10, sticky="ew")
        
        
        self.abort_button = ttk.Button(scanning_control_frame, text="Abort", command=self.abort_scan, style='Large.TButton')
        self.abort_button.grid(row=6, column=3, columnspan=1, padx=10, pady=10, sticky="ew")

        ttk.Label(scanning_control_frame, text="Slow Axis").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.slow_axis = ttk.Entry(scanning_control_frame, width=10)
        self.slow_axis.insert(0, "X")
        self.slow_axis.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(scanning_control_frame, text="Fast Axis").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.fast_axis = ttk.Entry(scanning_control_frame, width=10)
        self.fast_axis.insert(0, "Z")
        self.fast_axis.grid(row=0, column=1, padx=5, pady=5, sticky="w")        
        # Add a label for the APD signal value
        
        status_frame = ttk.Frame(control_frame)
        status_frame.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        ttk.Label(status_frame, text="APD Signal", font=("Helvetica", 20)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.apd_signal_label = ttk.Label(status_frame, text="N/A", font=("Helvetica", 24), foreground="#0077FF", background="black", width=12)
        self.apd_signal_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        ttk.Label(status_frame, text="Status", font=("Helvetica", 20)).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.status_label = ttk.Label(status_frame, text="Idle", font=("Helvetica", 24), foreground="#0077FF", background="black", width=12)
        self.status_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(status_frame, text="Time Left(m)", font=("Helvetica", 20)).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.time_left_label = ttk.Label(status_frame, text="Idle", font=("Helvetica", 24), foreground="#0077FF", background="black", width=12)
        self.time_left_label.grid(row=1, column=2, padx=5, pady=5, sticky="w")

        self.Line_scan_velocity = ttk.Entry(scanning_control_frame)
        self.Line_scan_velocity.grid(row=4,column =1, padx=5, pady = 5, sticky = "ew")
        ttk.Label(scanning_control_frame, text="Velocity").grid(row=4,column=0, padx=5, pady = 5, sticky = "ew")

        self.initialize_graph()
        # Add other text boxes and labels as needed
    
    
    
    def start_time_trace(self):
        self.scanning = True
        self.status_label.config(text="Scanning")
        self.fig2 = plt.figure()

        def run_time_trace(): 
            # Get results 
            res_handles = job.result_handles
            counts_handle = res_handles.get("counts")
            counts_handle.wait_for_values(1)
            Time = []
            counts = []
            plt.xlabel("time [s]")
            plt.ylabel("counts [kcps]")
            plt.title("Counter")
            while(self.scanning == True):
                counts_handle.wait_for_values(1)
                new_counts = counts_handle.fetch_all() 
                counts.append((new_counts["value"] / (single_integration_time_ns / 1000000000)) /1000 )
                #counts.append(new_counts["value"])
                Time.append(new_counts["timestamp"])  # Convert timestams to seconds
                #print(Time)
                #print(counts)
                
                self.ax2.cla()
                plt.xlabel("time [s]")
                plt.ylabel("counts [kcps]")
                plt.title("Counter")

                if len(Time) > 300:
                    self.ax2.plot(Time[-300:], counts[-300:])
                else:
                    self.ax2.plot(Time, counts)
                
                self.canvas2.draw_idle()
                self.update_idletasks() 
            
            self.canvas2.draw_idle()
            self.update_idletasks() 
    
    
        # Create and start a separate thread for the time trace
        self.time_trace_thread = threading.Thread(target=run_time_trace)
        self.time_trace_thread.start()    
        self.status_label.config(text="Idle")
    
    
    def start_line_scan(self):
        self.scanning = True
        self.status_label.config(text="Scanning")
        self.fig2 = plt.figure()
        velocity = round(float(self.Line_scan_velocity.get()),4)

        self.my_app.motor_x.set_velocity_parameters(0, velocity, 0.01) #(0,1,0.5)
        self.my_app.motor_y.set_velocity_parameters(0, velocity, 0.01)
        self.my_app.motor_z.set_velocity_parameters(0, velocity, 0.01)
        def line_scan(): 
            # Get results
            res_handles = job.result_handles
            counts_handle = res_handles.get("counts")
            counts_handle.wait_for_values(1)
            Time = []
            counts = []
            plt.xlabel("time [s]")
            plt.ylabel("counts [kcps]")
            plt.title("Counter")                
            
            # Create and start a separate thread for the time trace

            x0, z0 = self.my_app.get_xz_position()
            y0, z0 = self.my_app.get_yz_position()
            
            line_length = float(self.total_fast_length.get())
            if(self.fast_axis.get() == 'X'):
                self.my_app.motor_x.move_to(x0 + line_length)
                x_active = True
                while(x_active == True and self.status_label != "Idle"):
                    x_active = self.my_app.motor_x.is_in_motion
                    new_counts = counts_handle.fetch_all() 
                    
                    counts.append((new_counts["value"] / (single_integration_time_ns / 1000000000)) /1000 )
                    Time.append(new_counts["timestamp"])  # Convert timestams to seconds
                    self.ax2.cla()
                    
                    time.sleep(0.1)
                    if len(Time) > 300:
                        self.ax2.plot(Time[-300:], counts[-300:])
                    else:
                        self.ax2.plot(Time, counts)
                            
                    self.canvas2.draw_idle()
                    self.update_idletasks() 
                    print(self.scanning)
                self.canvas2.draw_idle()
                self.update_idletasks() 
                self.my_app.motor_x.set_velocity_parameters(0, 0.3, 0.01) #(0,1,0.5)
                self.my_app.motor_y.set_velocity_parameters(0, 0.3, 0.01)
                self.my_app.motor_z.set_velocity_parameters(0, 0.3, 0.01)
                
                self.scanning = False
                print("Done Measuring")
                
            elif(self.fast_axis.get() == 'Y'):
                self.my_app.motor_y.move_to(y0 + line_length)
                y_active = True
                while( y_active == True and self.status_label != "Idle"):
                    y_active = self.my_app.motor_y.is_in_motion
                    new_counts = counts_handle.fetch_all() 
                    counts.append((new_counts["value"] / (single_integration_time_ns / 1000000000)) /1000 )
                    Time.append(new_counts["timestamp"])  # Convert timestams to seconds
                    self.ax2.cla()

                    time.sleep(0.1)
                    if len(Time) > 300:
                        self.ax2.plot(Time[-300:], counts[-300:])
                    else:
                        self.ax2.plot(Time, counts)
                
                    self.canvas2.draw_idle()
                    self.update_idletasks() 
                self.canvas2.draw_idle()
                self.update_idletasks()
                self.scanning = False
                self.my_app.motor_x.set_velocity_parameters(0, 0.3, 0.01) #(0,1,0.5)
                self.my_app.motor_y.set_velocity_parameters(0, 0.3, 0.01)
                self.my_app.motor_z.set_velocity_parameters(0, 0.3, 0.01)
                
                print("Done Measuring")

            elif(self.fast_axis.get() == 'Z'):
                self.my_app.motor_z.move_to(z0 + line_length)

                z_active = True
                while( z_active == True and self.status_label != "Idle"):
                    z_active = self.my_app.motor_z.is_in_motion
                    new_counts = counts_handle.fetch_all() 
                    counts.append((new_counts["value"] / (single_integration_time_ns / 1000000000)) /1000 )
                    Time.append(new_counts["timestamp"])  # Convert timestams to seconds
                    self.ax2.cla()
                    
                    time.sleep(0.1)
                    if len(Time) > 300:
                        self.ax2.plot(Time[-300:], counts[-300:])
                    else:
                        self.ax2.plot(Time, counts)
                
                    self.canvas2.draw_idle()
                    self.update_idletasks() 
                self.canvas2.draw_idle()
                self.update_idletasks() 
                print("Done Measuring")
                self.my_app.motor_x.set_velocity_parameters(0, 0.3, 0.01) #(0,1,0.5)
                self.my_app.motor_y.set_velocity_parameters(0, 0.3, 0.01)
                self.my_app.motor_z.set_velocity_parameters(0, 0.3, 0.01)
                
                self.scanning = False
            else:
                print("Invalid Axis Entered")
        
        
        self.time_trace_thread = threading.Thread(target=line_scan)
        self.time_trace_thread.start()  
        self.status_label.config(text="Idle")
        
        
    def start_scan(self):
        
        # Start a new thread for scanning
        scanning_thread = threading.Thread(target=self.scan_loop)
        scanning_thread.start()
        self.status_label.config(text="Scanning")


    # Add this function to initialize the graph and colorbar
    
    def initialize_graph(self):
        self.ax.clear()
        self.im = self.ax.imshow(np.zeros((1, 1)), cmap='viridis', interpolation='nearest', aspect='auto', origin='lower')
        
        # Get the color limits based on the data
        data_min = 0
        data_max = 1
        self.im.set_clim(data_min, data_max)
        
        self.colorbar = self.fig.colorbar(self.im, ax=self.ax)




    def update_graph(self, data):
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
        # Remove the existing color bar
        self.colorbar.remove()
    
        # Create new color bar with the updated range
        self.colorbar = self.fig.colorbar(self.im, ax=self.ax, boundaries=np.linspace(vmin, vmax, 256))
        self.colorbar.set_clim(vmin, vmax)
    



    def scan_loop(self):
        
        res_handles = job.result_handles
        counts_handle = res_handles.get("counts")
        counts_handle.wait_for_values(1)
        
        # Get the parameters from the control panel
        total_fast_length = float(self.total_fast_length.get())
        total_slow_length = float(self.total_slow_length.get())
        delta_fast = float(self.delta_fast.get())
        delta_slow = float(self.delta_slow.get())
        delay_fast = float(self.delay_fast.get())
        delay_slow = float(self.delay_slow.get())
        file_name = self.file_name.get()
        integration_time = float(self.integration_time.get())
        
        # Initialize the scanning process
        self.scanning = True
    
        #Save the initial positions
        x0, z0 = self.my_app.get_xz_position()
        y0, z0 = self.my_app.get_yz_position()

        #Determine which initial position is the fast and the slow position, then moves to get ready to start the scan.     
        if(self.fast_axis.get() == 'X'):
            fast0 = x0
            fast_overshoot = x0 - total_fast_length
            self.my_app.motor_x.move_to(fast_overshoot)
            x_active = True
            while x_active == True:
                x_active = self.my_app.motor_x.is_in_motion
                time.sleep(0.01)
            fast_correct = x0 - total_fast_length / 2
            self.my_app.motor_x.move_to(fast_correct)
            x_active = True
            while x_active == True:
                x_active = self.my_app.motor_x.is_in_motion
                time.sleep(0.01)
        elif(self.fast_axis.get() == 'Y'):
            fast0=y0
            fast_overshoot = fast0 - total_fast_length
            self.my_app.motor_y.move_to(fast_overshoot)
            x_active = True
            while x_active == True:
                x_active = self.my_app.motor_y.is_in_motion
                time.sleep(0.01)
            fast_correct = fast0 - total_fast_length / 2
            self.my_app.motor_y.move_to(fast_correct)
            y_active = True
            while y_active == True:
                y_active = self.my_app.motor_y.is_in_motion
                time.sleep(0.01)
        elif(self.fast_axis.get() == 'Z'):
            fast0=z0
            fast_overshoot = fast0 - total_fast_length
            self.my_app.motor_z.move_to(fast_overshoot)
            z_active = True
            while z_active == True:
                z_active = self.my_app.motor_z.is_in_motion
                time.sleep(0.01)
            fast_correct = fast0 - total_fast_length / 2
            self.my_app.motor_z.move_to(fast_correct)
            z_active = True
            while z_active == True:
                z_active = self.my_app.motor_z.is_in_motion
                time.sleep(0.01)
        else:
            print("Invalid Axis Entered")
            
        
        if(self.slow_axis.get() == 'X'):
            slow0 = x0    
            slow_overshoot = slow0 - total_slow_length
            self.my_app.motor_x.move_to(slow_overshoot)
            x_active = True
            while x_active == True:
                x_active = self.my_app.motor_x.is_in_motion
                time.sleep(0.01)
            slow_correct = slow0 - total_slow_length / 2
            self.my_app.motor_x.move_to(slow_correct)
            x_active = True
            while x_active == True:
                x_active = self.my_app.motor_x.is_in_motion
                time.sleep(0.01)
        elif(self.slow_axis.get() == 'Y'):
            slow0=y0
            slow_overshoot = slow0 - total_slow_length
            self.my_app.motor_y.move_to(slow_overshoot)
            y_active = True
            while y_active == True:
                y_active = self.my_app.motor_y.is_in_motion
                time.sleep(0.01)
            slow_correct = slow0 - total_slow_length / 2
            self.my_app.motor_y.move_to(slow_correct)
            y_active = True
            while y_active == True:
                y_active = self.my_app.motor_y.is_in_motion
                time.sleep(0.01)
        elif(self.slow_axis.get() == 'Z'):
            slow0=z0
            slow_overshoot = slow0 - total_slow_length
            self.my_app.motor_z.move_to(slow_overshoot)
            z_active = True
            while z_active == True:
                z_active = self.my_app.motor_z.is_in_motion
                time.sleep(0.01)
            slow_correct = slow0 - total_slow_length / 2
            self.my_app.motor_z.move_to(slow_correct)
            z_active = True
            while z_active == True:
                z_active = self.my_app.motor_z.is_in_motion
                time.sleep(0.01)
        else:
            print("Invalid Axis Entered")

        
        
        # Calculate the number of steps
        fast_steps = int(total_fast_length / delta_fast)
        slow_steps = int(total_slow_length / delta_slow)
    
        # Initialize the heatmap data array
        heatmap_data = np.zeros((slow_steps, fast_steps)) 
    
        # Scan loop
        for i in range(slow_steps):
            start_time = int(time.strftime("%M"))*60 + int(time.strftime("%S"))
            for j in range(fast_steps):

                # Check if scanning process is aborted
                if not self.scanning:
                    break
    
                # Move the stage
                fast = fast0 + j * delta_fast
                if(self.fast_axis.get() == 'X'):
                    self.my_app.motor_x.move_to(fast)
                    x_active = True
                    while x_active == True:
                        x_active = self.my_app.motor_x.is_in_motion
                        time.sleep(0.01)
                elif(self.fast_axis.get() == 'Y'):
                    self.my_app.motor_y.move_to(fast)
                    y_active = True
                    while y_active == True:
                        y_active = self.my_app.motor_y.is_in_motion
                        time.sleep(0.01)   
                elif(self.fast_axis.get() == 'Z'):
                    self.my_app.motor_z.move_to(fast)
                    z_active = True
                    while z_active == True:
                        z_active = self.my_app.motor_y.is_in_motion
                        time.sleep(0.01)   
                else:
                    print("Invalid Axis Entered")

                time.sleep(delay_fast)
    
                # APD signal
                apd_signal = counts_handle.fetch("counts")["value"] / (single_integration_time_ns/ 1000000000) / 1000 
                
                # Update the heatmap data
                x_idx = j
                z_idx = i
                heatmap_data[z_idx, x_idx] = apd_signal
    
                # Update the graph
                self.im.set_data(heatmap_data)
    
                # Update the color limits of the color bar
                data_min = np.min(heatmap_data)
                data_max = np.max(heatmap_data)
                self.im.set_clim(data_min, data_max)
    
                # Update the APD signal value
                self.apd_signal_label.config(text="{:.3f}".format(apd_signal))
                

                # Update the canvas
                self.canvas.draw_idle()
                self.update_idletasks()
    
            # Check if scanning process is aborted
            if not self.scanning:
                break
            
            slow = slow0 + i * delta_slow
            if(self.slow_axis.get() == 'X'):
                self.my_app.motor_x.move_to(slow)
                x_active = True
                while x_active == True:
                    x_active = self.my_app.motor_x.is_in_motion
                    time.sleep(0.01)
            elif(self.slow_axis.get() == 'Y'):
                self.my_app.motor_y.move_to(slow)
                y_active = True
                while y_active == True:
                    y_active = self.my_app.motor_y.is_in_motion
                    time.sleep(0.01)   
            elif(self.slow_axis.get() == 'Z'):
                self.my_app.motor_z.move_to(slow)
                z_active = True
                while z_active == True:
                    z_active = self.my_app.motor_y.is_in_motion
                    time.sleep(0.01)   
            else:
                print("Invalid Axis Entered")
            finish_time = int(time.strftime("%M"))*60 + int(time.strftime("%S"))
            time.sleep(delay_slow)
            expected_time = ((finish_time - start_time)*(1-i/slow_steps)*slow_steps)/60
            self.time_left_label.config(text=str(expected_time))          
        # Save the data to a file
        np.savetxt(file_name, heatmap_data)
        self.time_left_label.config("Idle")
        # Move the stage back to the initial position
        self.my_app.motor_x.move_to(x0)
        self.my_app.motor_y.move_to(y0)
        self.my_app.motor_z.move_to(z0)
        
        # Set scanning to False
        self.scanning = False
        self.status_label.config(text="Idle")

    
           


    def abort_scan(self):
        self.scanning = False
        self.status_label.config(text="Idle")
        self.my_app.motor_x.stop_profiled()
        self.my_app.motor_y.stop_profiled()
        self.my_app.motor_z.stop_profiled()
        

    def display_current_position(self):
        x, z = self.my_app.get_xz_position()
        current_position_label = ttk.Label(self.control_frame, text="Current Position: X = {:.2f}, Z = {:.2f}".format(y, z))
        current_position_label.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        return current_position_label

if __name__ == "__main__":
    app = ScannerApp()
    app.mainloop()


