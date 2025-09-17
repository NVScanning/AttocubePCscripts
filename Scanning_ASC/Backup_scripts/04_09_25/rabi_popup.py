# -*- coding: utf-8 -*-
"""
Created on Thu Jul 31 15:45:27 2025

@author: attocube
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import numpy as np
class RabiPopup(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Rabi Parameters")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.params = {}
        self.rf_freq = self.load_last_odmr_frequency()
        self.create_widgets()
        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)
    def load_last_odmr_frequency(self):
        # Pointer file containing last saved ODMR .npz file path
        pointer_file = os.path.join("//WXPC724/Share/Data", "last_odmr_path.txt")
        try:
            with open(pointer_file, 'r') as f:
                last_odmr_path = f.read().strip()
            if os.path.exists(last_odmr_path):
                data = np.load(last_odmr_path)
                f_center_array = data.get('f_center')
                if f_center_array is not None and len(f_center_array) > 0:
                    return f_center_array[-1]  #Last value of f_center
        except Exception as e:
            print("Failed to load last ODMR frequency:", e)
        print("Using default 2.87 GHz for RF frequency.")
        return 2.87  # fallback
    def create_widgets(self):
        # RF frequency (from file, disabled)
        ttk.Label(self, text="RF Frequency (GHz)").grid(row=0, column=0, padx=10, pady=5)
        self.rf_freq_entry = ttk.Entry(self)
        self.rf_freq_entry.grid(row=0, column=1, padx=10, pady=5)
        self.rf_freq_entry.insert(0, f"{self.rf_freq:.6f}")
        self.rf_freq_entry.config(state="disabled")
        # Initialization time
        ttk.Label(self, text="Init Time (µs)").grid(row=1, column=0, padx=10, pady=5)
        self.init_time_entry = ttk.Entry(self)
        self.init_time_entry.grid(row=1, column=1, padx=10, pady=5)
        self.init_time_entry.insert(0, "5.0")
        # Time between pulses
        ttk.Label(self, text="Time Between Pulses (ns)").grid(row=2, column=0, padx=10, pady=5)
        self.pulse_spacing_entry = ttk.Entry(self)
        self.pulse_spacing_entry.grid(row=2, column=1, padx=10, pady=5)
        self.pulse_spacing_entry.insert(0, "4")
        # Number of pulses
        ttk.Label(self, text="N_pulses").grid(row=3, column=0, padx=10, pady=5)
        self.n_pulses_entry = ttk.Entry(self)
        self.n_pulses_entry.grid(row=3, column=1, padx=10, pady=5)
        self.n_pulses_entry.insert(0, "150")
        # Averages
        ttk.Label(self, text="N_average").grid(row=4, column=0, padx=10, pady=5)
        self.n_avg_entry = ttk.Entry(self)
        self.n_avg_entry.grid(row=4, column=1, padx=10, pady=5)
        self.n_avg_entry.insert(0, "1000")
        # RF power
        ttk.Label(self, text="RF Power (dBm)").grid(row=5, column=0, padx=10, pady=5)
        self.rf_power_entry = ttk.Entry(self)
        self.rf_power_entry.grid(row=5, column=1, padx=10, pady=5)
        self.rf_power_entry.insert(0, "10")
        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)
        self.confirm_button = ttk.Button(button_frame, text="Confirm", command=self.on_confirm)
        self.confirm_button.grid(row=0, column=0, padx=5)
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        self.cancel_button.grid(row=0, column=1, padx=5)
    def on_confirm(self):
        try:
            rf_power = float(self.rf_power_entry.get())
            Typ_gain = 42  # dB
            if rf_power > -21 + Typ_gain:
                messagebox.showwarning("RF Power Limit", "You exceeded the allowed RF power.")
                return
            self.params = {
                "rf_freq": self.rf_freq,  # already loaded
                "init_time": float(self.init_time_entry.get()),
                "pulse_spacing": float(self.pulse_spacing_entry.get()),
                "n_pulses": int(self.n_pulses_entry.get()),
                "N_average": int(self.n_avg_entry.get()),
                "rf_power": rf_power,
            }
            print(self.params)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")
    def on_cancel(self):
        self.destroy()
    def on_close(self):
        self.on_cancel()