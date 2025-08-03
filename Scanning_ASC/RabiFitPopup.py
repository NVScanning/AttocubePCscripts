import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from rabi_module import RabiModule
import time
import numpy as np
import threading
import os
from Motorized_asc import AscStageApp

data_lock = threading.Lock()

class RabiFitPopup(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Rabi Fit Window")
        self.rabi_module = RabiModule()
        self.rf_freq = self.load_last_odmr_frequency()
        self.create_widgets()
        self.initialize_graph()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.transient(parent)
        self.grab_set()
        self.my_app = AscStageApp()
        self.rabi_module.z_control = self.my_app.asc500.zcontrol
        self.rabi_module.scannerpos = self.my_app.asc500.scanner
        parent.wait_window(self)

    def load_last_odmr_frequency(self):
        pointer_file = os.path.join("//WXPC724/Share/Data", "last_odmr_path.txt")
        try:
            with open(pointer_file, 'r') as f:
                last_odmr_path = f.read().strip()
            if os.path.exists(last_odmr_path):
                data = np.load(last_odmr_path)
                f_center_array = data.get('f_center')
                if f_center_array is not None and len(f_center_array) > 0:
                    return f_center_array[-1]
        except Exception as e:
            print("Failed to load last ODMR frequency:", e)
        print("Using default 2.87 GHz for RF frequency.")
        return 2.87

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

        ttk.Label(self.inputs_frame, text="RF Frequency (GHz)").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.rf_freq_entry = ttk.Entry(self.inputs_frame)
        self.rf_freq_entry.grid(row=0, column=1, padx=5, pady=5)
        self.rf_freq_entry.insert(0, f"{self.rf_freq:.3f}")
        self.rf_freq_entry.config(state="disabled")

        ttk.Label(self.inputs_frame, text="Init Time (µs)").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.init_time_entry = ttk.Entry(self.inputs_frame)
        self.init_time_entry.grid(row=0, column=3, padx=5, pady=5)
        self.init_time_entry.insert(0, "5.0")

        ttk.Label(self.inputs_frame, text="Pulse Spacing (ns)").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.pulse_spacing_entry = ttk.Entry(self.inputs_frame)
        self.pulse_spacing_entry.grid(row=0, column=5, padx=5, pady=5)
        self.pulse_spacing_entry.insert(0, "4")

        ttk.Label(self.inputs_frame, text="N Pulses").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.n_pulses_entry = ttk.Entry(self.inputs_frame)
        self.n_pulses_entry.grid(row=1, column=1, padx=5, pady=5)
        self.n_pulses_entry.insert(0, "596")

        ttk.Label(self.inputs_frame, text="N Avg").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.n_avg_entry = ttk.Entry(self.inputs_frame)
        self.n_avg_entry.grid(row=1, column=3, padx=5, pady=5)
        self.n_avg_entry.insert(0, "1000")

        ttk.Label(self.inputs_frame, text="RF Power (dBm)").grid(row=1, column=4, padx=5, pady=5, sticky="w")
        self.rf_power_entry = ttk.Entry(self.inputs_frame)
        self.rf_power_entry.grid(row=1, column=5, padx=5, pady=5)
        self.rf_power_entry.insert(0, "10")

        self.start_button = ttk.Button(self.inputs_frame, text="Start", width=10, command=self.start_rabi)
        self.start_button.grid(row=2, column=2, padx=5, pady=10)

        self.stop_button = ttk.Button(self.inputs_frame, text="Stop", width=10, command=self.stop_rabi)
        self.stop_button.grid(row=2, column=3, padx=5, pady=10)

        self.display_frame = tk.Frame(self.outputs_frame, bg="white")
        self.display_frame.grid(row=0, column=0, pady=10, sticky="ew")

        ttk.Label(self.display_frame, text="Rabi Frequency (MHz):", font=("Helvetica", 12), background="white", foreground="black").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.rabi_freq_value = tk.Label(self.display_frame, text="", font=("Helvetica", 12), bg="DarkOrange4", fg="white", width=15)
        self.rabi_freq_value.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(self.display_frame, text="Decay (ns):", font=("Helvetica", 12), background="white", foreground="black").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.decay_value = tk.Label(self.display_frame, text="", font=("Helvetica", 12), bg="DarkOrange4", fg="white", width=15)
        self.decay_value.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(self.display_frame, text="Contrast:", font=("Helvetica", 12), background="white", foreground="black").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.contrast_value = tk.Label(self.display_frame, text="", font=("Helvetica", 12), bg="DarkOrange4", fg="white", width=15)
        self.contrast_value.grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(self.display_frame, text="Time Elapsed (s):", font=("Helvetica", 12), background="white", foreground="black").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.time_elapsed_value = tk.Label(self.display_frame, text="", font=("Helvetica", 12), bg="DarkOrange4", fg="white", width=15)
        self.time_elapsed_value.grid(row=3, column=1, padx=10, pady=5)

    def initialize_graph(self):
        self.fig = Figure(figsize=(5, 4))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Rabi pulse duration (ns)")
        self.ax.set_ylabel("Instensity (kcps)")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw_idle()

    def start_rabi(self):
        params = {
            "rf_freq": self.rf_freq,
            "init_time": float(self.init_time_entry.get()),
            "pulse_spacing": float(self.pulse_spacing_entry.get()),
            "n_pulses": int(self.n_pulses_entry.get()),
            "N_average": int(self.n_avg_entry.get()),
            "rf_power": float(self.rf_power_entry.get())
        }
        self.rabi_module.set_rabi_params(params)
        self.rabi_module.fast_steps =0
        self.rabi_module.slow_steps = 0
        
        self.rabi_module.connect()
        self.rabi_module.start_job()
        self.rabi_module.start_fetching()
        
        # Reset fit_status to make update_plot wait
        self.rabi_module.data_dict["fit_status"] = "pending"

        threading.Thread(target=self.run_rabi_acq, daemon=True).start()
        threading.Thread(target=self.update_plot, daemon=True).start()

    def run_rabi_acq(self):
        self.rabi_module.get_data(0)
        self.rabi_module.run_fitting()

    def update_plot(self):
        while self.rabi_module.data_dict.get("fit_status") != "ok":
            time.sleep(0.05)
        with data_lock:
            x = self.rabi_module.x_data
            y = self.rabi_module.y_data
            fit = self.rabi_module.fitted_y_data
        self.ax.clear()
        self.ax.plot(x, y, label="Data", marker='o')
        self.ax.plot(x, fit, label="Fit", color='red')
        self.ax.set_xlim(min(x), max(x))
        self.ax.set_ylim(min(y) * 0.9, max(y) * 1.1)
        self.ax.set_xlabel("Time (ns)")
        self.ax.set_ylabel("Counts")
        self.ax.legend()
        self.canvas.draw_idle()

        data = self.rabi_module.data_dict
        self.rabi_freq_value.config(text=f"{data.get('rabi_freq', 0):.2f}")
        self.decay_value.config(text=f"{data.get('rabi_decay', 0):.2f}")
        self.contrast_value.config(text=f"{data.get('rabi_contrast', 0):.2f}")
        self.time_elapsed_value.config(text=f"{data.get('time_elapsed', 0):.2f}")

    def stop_rabi(self):
        self.rabi_module.cleanup()

    def on_close(self):
        self.stop_rabi()
        self.destroy()
