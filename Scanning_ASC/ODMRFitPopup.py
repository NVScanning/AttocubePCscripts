import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from scipy.optimize import curve_fit
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from odmr_module import ODMRModule  # Import the ODMRModule
import time
import numpy as np
import threading
from Motorized_asc import AscStageApp

data_lock = threading.Lock()

class ODMRFitPopup(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("ODMR Fit Parameters")
        self.odmr_module = ODMRModule()
        self.create_widgets()
        self.initialize_graph()
        self.protocol("WM_DELETE_WINDOW", self.on_close)  # Handle the window close event
        #self.update_flag = False
        self.transient(parent) #set to be on top of the main window
        self.grab_set() #hijack all commands from the master (clicks on the main window are ignored)
        self.my_app = AscStageApp()
        self.motorized_stage_app = self.my_app
        self.odmr_module.z_control = self.my_app.asc500.zcontrol
        self.odmr_module.scannerpos = self.my_app.asc500.scanner
        
        parent.wait_window(self) #pause anything on the main window until this one closes (optional)    


    def create_widgets(self):
        self.inputs_frame = ttk.LabelFrame(self, text="Inputs", padding="10")
        self.inputs_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.outputs_frame = ttk.LabelFrame(self, text="Outputs", padding="10")
        self.outputs_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.graph_frame = ttk.Frame(self, padding="10")
        self.graph_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self.inputs_frame, text="fmin(GHz)").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.fmin_entry = ttk.Entry(self.inputs_frame)
        self.fmin_entry.grid(row=0, column=1, padx=5, pady=5)
        self.fmin_entry.insert(0, "2.8")

        ttk.Label(self.inputs_frame, text="fmax(GHz)").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.fmax_entry = ttk.Entry(self.inputs_frame)
        self.fmax_entry.grid(row=0, column=3, padx=5, pady=5)
        self.fmax_entry.insert(0, "3.0")

        ttk.Label(self.inputs_frame, text="N_points").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.npoints_entry = ttk.Entry(self.inputs_frame)
        self.npoints_entry.grid(row=0, column=5, padx=5, pady=5)
        self.npoints_entry.insert(0, "100")

        ttk.Label(self.inputs_frame, text="Power(dBm)").grid(row=0, column=6, padx=5, pady=5, sticky="w")
        self.power_entry = ttk.Entry(self.inputs_frame)
        self.power_entry.grid(row=0, column=7, padx=5, pady=5)
        self.power_entry.insert(0, "10")

        ttk.Label(self.inputs_frame, text="Fit Type").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.fit_type_combobox = ttk.Combobox(self.inputs_frame, values=["Single Lorentzian", "Double Lorentzian", "Triple Lorentzian"])
        self.fit_type_combobox.current(0)
        self.fit_type_combobox.grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(self.inputs_frame, text="N_avg").grid(row=1, column=4, padx=5, pady=5, sticky="w")
        self.n_avg_entry = ttk.Entry(self.inputs_frame)
        self.n_avg_entry.grid(row=1, column=5, padx=5, pady=5)
        self.n_avg_entry.insert(0, "100")

        self.start_button = ttk.Button(self.inputs_frame, text="Start", width=10, command=self.start_odmr)
        self.start_button.grid(row=2, column=2, padx=5, pady=10, columnspan=2)
    
        self.stop_button = ttk.Button(self.inputs_frame, text="Stop", width=10, command=self.stop_odmr)
        self.stop_button.grid(row=2, column=4, padx=5, pady=10, columnspan=2)

        self.display_frame = tk.Frame(self.outputs_frame, bg="white")
        self.display_frame.grid(row=0, column=0, columnspan=2, pady=10, sticky="ew")
        
        ttk.Label(self.display_frame, text="Center Frequency: ", font=("Helvetica", 12), background="white", foreground="black").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.center_freq_value = tk.Label(self.display_frame, text="", font=("Helvetica", 12), bg="PaleGreen4", fg="white", width=15)
        self.center_freq_value.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(self.display_frame, text="FWHM: ", font=("Helvetica", 12), background="white", foreground="black").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.fwhm_value = tk.Label(self.display_frame, text="", font=("Helvetica", 12), bg="PaleGreen4", fg="white", width=15)
        self.fwhm_value.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(self.display_frame, text="Contrast: ", font=("Helvetica", 12), background="white", foreground="black").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.contrast_value = tk.Label(self.display_frame, text="", font=("Helvetica", 12), bg="PaleGreen4", fg="white", width=15)
        self.contrast_value.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(self.display_frame, text="Sensitivity: ", font=("Helvetica", 12), background="white", foreground="black").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.sensitivity_value = tk.Label(self.display_frame, text="", font=("Helvetica", 12), bg="PaleGreen4", fg="white", width=15)
        self.sensitivity_value.grid(row=3, column=1, padx=10, pady=5)
        
        ttk.Label(self.display_frame, text="Time Elapsed: ", font=("Helvetica", 12), background="white", foreground="black").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.time_elapsed_value = tk.Label(self.display_frame, text="", font=("Helvetica", 12), bg="PaleGreen4", fg="white", width=15)
        self.time_elapsed_value.grid(row=4, column=1, padx=10, pady=5)

    def initialize_graph(self):
        self.fig = Figure(figsize=(5, 4))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Frequency (GHz)")
        self.ax.set_ylabel("Counts/s")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw_idle()  # Ensure initial draw

    def start_odmr(self):
        a = time.time()
        params = {
            "fmin": float(self.fmin_entry.get()),
            "fmax": float(self.fmax_entry.get()),
            "N_points": int(self.npoints_entry.get()),
            "rf_power": float(self.power_entry.get()),
            "fit_type": self.fit_type_combobox.get(),
            "N_average": int(self.n_avg_entry.get())
        }
        self.odmr_module.set_odmr_params(params)
        #self.odmr_module.set_update_plot_callback(self.update_plot)
        self.odmr_module.fast_steps =0
        self.odmr_module.slow_steps = 0
        
        self.odmr_module.connect()
        
        self.odmr_module.start_job()
        #self.odmr_module.fetch_data()
        self.odmr_module.start_fetching()
        # Reset fit_status to make update_plot wait
        self.odmr_module.data_dict["fit_status"] = "pending"
        
        # Start new acquisition and fit
        
        threading.Thread(target=self.run_odmr_acq, daemon=True).start()
        

        b = time.time()
        print(f's_odmr_time: {b-a}')
        
        #self.odmr_module.get_data_thread()  # Moved this line up
        #self.update_plot()  # Initialize the plot immediately
    
        #counts = self.odmr_module.counts_sum
        self.fitted_y = self.odmr_module.fitted_y_data
        #readout = self.odmr_module.readout_len
        #f = self.odmr_module.f_vec
       
        
        self.y_data = self.odmr_module.y_data
        self.x_data = self.odmr_module.x_data
        
        print(f'popup x:{self.x_data}')
        
        self.ax.clear()
        #y_data = self.odmr_module.fitted_y_data
        self.graph, = self.ax.plot([] ,  [], label="Data", marker='o')
        self.fit_graph, = self.ax.plot([] ,  [], label="Fit", color='red')
        self.ax.set_xlabel("Frequency (MHz)")
        self.ax.set_ylabel("Counts/s")
        # if len(self.x_data) > 1:
        #     self.ax.set_xlim(min(self.x_data), max(self.x_data))
        # if len(self.y_data ) > 1:
        #     self.ax.set_ylim(min(self.y_data ) * 0.9, max(self.y_data ) * 1.1)
        # self.ax.set_xlim(min(self.x_data), max(self.x_data))  # Set x-axis limits
        # self.ax.set_ylim(min(self.y_data )*0.9, max(self.y_data )* 1.1)  # Update y-axis limits based on new data
        self.ax.legend()
        self.fig.canvas.draw_idle()  # Initial draw to update the plot
        # Schedule regular plot updates
        threading.Thread(target=self.update_plot, daemon=True).start()
        #self.schedule_update()
        print("after thread")
       
        
       
    def run_odmr_acq(self):
        start = time.time()
        self.odmr_module.get_data(0)  # Only fetches raw x_data, y_data
        self.odmr_module.start_fitting_thread()  # Triggers fit in background
        end = time.time()
        print(f"ODMR acquisition + fit  time is {end - start:.3f} s")

        

    def stop_odmr(self):

        self.odmr_module.cleanup()
        
    def schedule_update(self):
        
        self.update_plot()
        self.after(100, self.schedule_update)     

    def update_plot(self):
        print('Waiting for fit completion...')
        while self.odmr_module.data_dict.get("fit_status", "") != "ok":
            time.sleep(0.01)
    
        with data_lock:
            self.y_data = self.odmr_module.y_data
            self.x_data = self.odmr_module.x_data
            self.fitted_y = self.odmr_module.fitted_y_data
            data = self.odmr_module.data_dict.copy()
    
        # Update the graph
        self.graph.set_data(self.x_data, self.y_data)
        self.fit_graph.set_data(self.x_data, self.fitted_y)
    
        if len(self.y_data) > 1:
            self.ax.set_xlim(min(self.x_data), max(self.x_data))
            self.ax.set_ylim(min(self.y_data) * 0.9, max(self.y_data) * 1.1)
        else:
            print("Warning: y_data is too short to update limits")
    
        self.fig.canvas.draw_idle()
        self.update_idletasks()
    
        # Safely update the GUI labels with new fit results
        try:
            self.center_freq_value.config(text=f"{data['freq_center']:.2f} MHz")
            self.fwhm_value.config(text=f"{data['fwhm']:.2f} MHz")
            self.contrast_value.config(text=f"{data['contrast']:.2f} ")
            self.sensitivity_value.config(text=f"{data['sensitivity']:.2f}")
            self.time_elapsed_value.config(text=f"{data['time_elapsed']:.2f} s")
        except KeyError as e:
            print(f"[ODMR Popup] Missing key in data_dict: {e}")




    def on_close(self):
        self.stop_odmr()
        self.destroy()
