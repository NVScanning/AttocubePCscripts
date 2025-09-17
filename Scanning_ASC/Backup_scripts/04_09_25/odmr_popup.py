# -*- coding: utf-8 -*-
"""
Created on Thu Jun 27 12:52:14 2024

@author: nvcryo
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

class ODMRPopup(tk.Toplevel):
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        # Remove the redundant super() call
        self.parent = parent
        self.title("ODMR Parameters")
        # self.confirm_callback = confirm_callback
        # self.cancel_callback = cancel_callback
        self.protocol("WM_DELETE_WINDOW", self.on_close)  # Handle window close event
        self.create_widgets()
        self.transient(parent) #set to be on top of the main window
        self.grab_set() #hijack all commands from the master (clicks on the main window are ignored)
        self.params ={}
        parent.wait_window(self) #pause anything on the main window until this one closes (optional)        

    def create_widgets(self):
        # fmin
        ttk.Label(self, text="fmin(GHz)").grid(row=0, column=0, padx=10, pady=5)
        self.fmin_entry = ttk.Entry(self)
        self.fmin_entry.grid(row=0, column=1, padx=10, pady=5)
        self.fmin_entry.insert(0, "2.8")  # Set initial value for fmin

        # fmax
        ttk.Label(self, text="fmax(GHz)").grid(row=1, column=0, padx=10, pady=5)
        self.fmax_entry = ttk.Entry(self)
        self.fmax_entry.grid(row=1, column=1, padx=10, pady=5)
        self.fmax_entry.insert(0, "3.0")  # Set initial value for fmax

        # N_points
        ttk.Label(self, text="N_points").grid(row=2, column=0, padx=10, pady=5)
        self.N_points_entry = ttk.Entry(self)
        self.N_points_entry.grid(row=2, column=1, padx=10, pady=5)
        self.N_points_entry.insert(0, "100")  # Set initial value for N_points

        # rf_power
        ttk.Label(self, text="rf_power(dBm)").grid(row=3, column=0, padx=10, pady=5)
        self.rf_power_entry = ttk.Entry(self)
        self.rf_power_entry.grid(row=3, column=1, padx=10, pady=5)
        self.rf_power_entry.insert(0, "10")  # Set initial value for rf_power

        # N_average
        ttk.Label(self, text="N_average").grid(row=4, column=0, padx=10, pady=5)
        self.N_average_entry = ttk.Entry(self)
        self.N_average_entry.grid(row=4, column=1, padx=10, pady=5)
        self.N_average_entry.insert(0, "10")  # Set initial value for N_average
        
        ttk.Label(self, text="Fit Type").grid(row=5, column=0, pady=5)
        self.fit_type_combobox = ttk.Combobox(self, values=["Single Lorentzian", "Double Lorentzian","Triple Lorentzian"])
        self.fit_type_combobox.current(0)  # Set default selection to the first option    
        self.fit_type_combobox.grid(row=5, column=1, padx=10, pady=5)

        # Button frame
        button_frame = ttk.Frame(self)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)

        self.confirm_button = ttk.Button(button_frame, text="Confirm", command=self.on_confirm)
        self.confirm_button.grid(row=0, column=0, padx=5)

        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        self.cancel_button.grid(row=0, column=1, padx=5)

    def on_confirm(self):
        rf_power = float(self.rf_power_entry.get())
        Typ_gain=42 #db
        if rf_power > -21+Typ_gain:
            print("You exceeded the required value for rf_power.")
            return
        self.params = {
            "fmin": float(self.fmin_entry.get()),
            "fmax": float(self.fmax_entry.get()),
            "N_points": int(self.N_points_entry.get()),
            "rf_power": rf_power,
            "N_average": int(self.N_average_entry.get()),
            "fit_type": self.fit_type_combobox.get(),
        }
        #self.confirm_callback(self.params)
        print(self.params)
        self.destroy()

    def on_cancel(self): 
        self.destroy()

    def on_close(self):
        self.on_cancel()