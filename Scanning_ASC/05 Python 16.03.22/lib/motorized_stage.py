import tkinter as tk
import thorlabs_apt as apt
#import asc500_device as asc

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
        
        
        self.motor_x = apt.Motor(90335875)
        self.motor_y = apt.Motor(90335876)
        self.motor_z = apt.Motor(90335877)

        #self.motor_x.set_velocity_parameters(0, 0.3, 0.01) #(0,1,0.5)
        #self.motor_y.set_velocity_parameters(0, 0.3, 0.01)
        #self.motor_z.set_velocity_parameters(0, 0.3, 0.01)

        self.x_pos = self.motor_x.position
        self.y_pos = self.motor_y.position
        self.z_pos = self.motor_z.position

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

        return self.motor_y.position, self.motor_z.position
    
    def get_xz_position(self):
        """
        Get the current X and Z positions of the motorized stage.

        Returns:
            tuple: A tuple containing the current X and Z positions (x, z).
        """

        return self.motor_x.position, self.motor_z.position
    
    def move_x_to(self):
        try:
            x_target = round(float(self.entry_x_to.get()), 5)
            self.motor_x.move_to(x_target)
        except ValueError:
            pass

    def move_y_to(self):
        try:
            y_target = round(float(self.entry_y_to.get()), 5)
            self.motor_y.move_to(y_target)
        except ValueError:
            pass

    def move_z_to(self):
        try:
            z_target = round(float(self.entry_z_to.get()), 5)
            self.motor_z.move_to(z_target)
        except ValueError:
            pass

    # X-button actions
    def move_x_up(self):
        self.motor_x.backlash_distance = 0
        x_movement = round(abs(float(self.entry_x.get())),5)
        self.motor_x.move_by(x_movement)
        self.motor_x.backlash_distance = 0.01   
        
        
    def move_x_down(self):
        self.motor_x.backlash_distance = 0
        x_movement = round(-abs(float(self.entry_x.get())),5)
        self.motor_x.move_by(x_movement)
        self.motor_x.backlash_distance = 0.01        
        
    # Y-button actions
    def move_y_up(self):
        self.motor_y.backlash_distance = 0
        y_movement = round(abs(float(self.entry_y.get())),5)
        self.motor_y.move_by(y_movement)
        self.motor_y.backlash_distance = 0.01
        
    def move_y_down(self):
        self.motor_y.backlash_distance = 0
        y_movement = round(-abs(float(self.entry_y.get())),5)
        self.motor_y.move_by(y_movement)
        self.motor_y.backlash_distance = 0.01
        
    # Z-button actions

    def move_z_up(self):
        self.motor_z.backlash_distance = 0
        z_movement = round(abs(float(self.entry_z.get())),5)
        self.motor_z.move_by(z_movement)
        self.motor_z.backlash_distance = 0.01
        
    def move_z_down(self):
        self.motor_z.backlash_distance = 0
        z_movement = round(-abs(float(self.entry_z.get())),5)
        self.motor_z.move_by(z_movement)
        self.motor_z.backlash_distance = 0.01


    def move_x(self):
        self.motor_x.backlash_distance = 0
        try:
            x_movement = round(float(self.entry_x.get()),5)
            self.motor_x.move_by(x_movement)
        except ValueError:
            pass
        self.motor_x.backlash_distance = 0.01
    def move_y(self):
        self.motor_y.backlash_distance = 0
        try:
            y_movement = round(float(self.entry_y.get()),5)
            self.motor_y.move_by(y_movement)
        except ValueError:
            pass
        self.motor_y.backlash_distance = 0.01
    def move_z(self):
        self.motor_z.backlash_distance = 0
        try:
            z_movement = round(float(self.entry_z.get()),5)
            self.motor_z.move_by(z_movement)
        except ValueError:
            pass
        self.motor_z.backlash_distance = 0.01
    def home_x(self):
        threading.Thread(target=self.home_x_thread).start()

    def home_x_thread(self):
        self.motor_x.move_home(True)
        self.x_pos = self.motor_x.position

    def home_y(self):
        threading.Thread(target=self.home_y_thread).start()

    def home_y_thread(self):
        self.motor_y.move_home(True)
        self.y_pos = self.motor_y.position
        
    def home_z(self):
        threading.Thread(target=self.home_z_thread).start()

    def home_z_thread(self):
        self.motor_z.move_home(True)
        self.z_pos = self.motor_z.position
        
        
    def on_close(self):
        self.closed = True
        self.destroy()

    def periodic_position_update(self):
        if not self.closed:
            self.x_pos = round(self.motor_x.position,5)
            self.y_pos = round(self.motor_y.position,5)
            self.z_pos = round(self.motor_z.position,5)
            self.label_x.config(text=f"X: {self.x_pos:0.5f}")
            self.label_y.config(text=f"Y: {self.y_pos:0.5f}")
            self.label_z.config(text=f"Z: {self.z_pos:0.5f}")
            self.after(100, self.periodic_position_update)

if __name__ == "__main__":
    root = tk.Tk()
    app = MotorizedStageApp(root)
    app.grid()
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
