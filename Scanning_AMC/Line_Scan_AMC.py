import numpy as np
import matplotlib.pyplot as plt
import AMC
import time

# IP of the Tip positioner
IP = "192.168.1.2"  # Tip positioner

# Setup connection to AMC
amc = AMC.Device(IP)
amc.connect()

# Axis configuration
x_axis = 0  # Axis 1
y_axis = 1

# Activate axis
amc.control.setControlOutput(x_axis, True)
amc.control.setControlOutput(y_axis, True)

# Movement parameters
frequency = 500 * 1e3  # mHz
amplitude = 50 * 1e3   # mV
move_distance = 10000   # nm
num_trials = 30         # Number of trials

# Configure AMC parameters
amc.control.setControlFrequency(x_axis, frequency)
amc.control.setControlAmplitude(x_axis, amplitude)
amc.control.setControlFrequency(y_axis, frequency)
amc.control.setControlAmplitude(y_axis, amplitude)

# Target range 
tgt_range = 0.1   

def line_scan_2D(fast_axis, slow_steps, total_X_length, total_Y_length, stepsize):
    """
    2D Fast-Line scan function averages the n_data_points_per_pixel for every pixel
    and updates the heat-map. Also contains the logic to operate whether X or Y as a fast_axis.
    """
    
    # Initializing the time and counts lists
    Time = []
    Time_b = []
    counts = []
    
    # Initialize plot
    #plt.ion()  # Turn on interactive mode for real-time plotting
    fig, ax = plt.subplots()
    ax.set_xlabel('X Position (µm)')
    ax.set_ylabel('Y Position (µm)')
    ax.set_title('Real-time 2D Scan Movement')
    ax.set_xlim(-total_X_length/2, total_X_length/2)
    ax.set_ylim(-total_Y_length/2, total_Y_length/2)
    ax.grid(True)
    
    # Initial position (for plotting)
    x0, y0 = amc.move.getPosition(x_axis), amc.move.getPosition(y_axis)
    print(f'Initial pos: x: {x0}, y: {y0}')
    
    # Bottom left of center scan
    X_start = x0 - total_X_length/2
    Y_start = y0 - total_Y_length/2
    
    x_start = x0 - total_X_length/2 + stepsize[0]/2
    x_end = x0 + total_X_length/2
    y_start = y0 - total_Y_length/2 + stepsize[1]/2
    y_end = y0 + total_Y_length/2
    
    x_array = np.arange(x_start, x_end, stepsize[0])
    y_array = np.arange(y_start, y_end, stepsize[1])

    # Loop over slow steps to simulate the 2D scan
    for i in range(slow_steps): 
        print('Move to new line')
        
        if fast_axis == 'X':
            X = X_start  # Start of line
            X_tgt = X + total_X_length  # End of line
            Y = y_start + i * stepsize[1]  # Constant Y for line
            Y_tgt = Y
        elif fast_axis == 'Y':
            X = x_start + i * stepsize[0]  # Constant X for line
            X_tgt = X
            Y = Y_start  # Start of line
            Y_tgt = Y + total_Y_length  # End of line
        else:
            print("Invalid Axis Entered")
        
        # Move to the beginning of the next line
        tgt_start = [X, Y]
        
        amc.move.setControlTargetPosition(x_axis, tgt_start[0])
        amc.control.setControlMove(x_axis, True)
        amc.move.setControlTargetPosition(y_axis, tgt_start[1])
        amc.control.setControlMove(y_axis, True)
        time.sleep(0.0005)
        
        while not amc.status.getStatusTargetRange(x_axis) and not amc.status.getStatusTargetRange(x_axis):
            pos = amc.move.getPosition(x_axis), amc.move.getPosition(y_axis)
            time.sleep(0.01)
        
        # Stop movement
        amc.control.setControlMove(x_axis, False)
        amc.control.setControlMove(y_axis, False)
        
        # Update plot with the final position of the first movement
        pos = amc.move.getPosition(x_axis), amc.move.getPosition(y_axis)
        ax.scatter(pos[0], pos[1], color='blue', s=10, label='Start Position' if i == 0 else "")
        plt.draw()  # Update the plot
        plt.pause(0.1)  # Pause for a short time to allow plot update
        
        # Move to the target position
        tgt = [X_tgt, Y_tgt]
        amc.move.setControlTargetPosition(x_axis, tgt[0])
        amc.control.setControlMove(x_axis, True)
        amc.move.setControlTargetPosition(y_axis, tgt[1])
        amc.control.setControlMove(y_axis, True)
        
        while not amc.status.getStatusTargetRange(x_axis) and not amc.status.getStatusTargetRange(x_axis):
            pos = amc.move.getPosition(x_axis), amc.move.getPosition(y_axis)
            time.sleep(0.01)
            # Update plot with the final position of the main movement
        pos = amc.move.getPosition(x_axis), amc.move.getPosition(y_axis)
        ax.scatter(pos[0], pos[1], color='red', s=10, label='Scan Position' if i == 0 else "")
        plt.draw()  # Update the plot
        plt.pause(0.1)  # Pause for a short time to allow plot update
        
        # Stop movement again
        amc.control.setControlMove(x_axis, False)
        amc.control.setControlMove(y_axis, False)
        
        print("Done Measuring")

    
    #plt.ioff()  # Turn off interactive mode
    plt.show()  # Finalize the plot display


# Parameters for 2D scan
fast_axis = 'X'  # Fast axis ('X' or 'Y')
slow_steps = 5  # Number of slow steps
total_X_length = 5000  # Total length along X-axis in nm
total_Y_length = 5000   # Total length along Y-axis in micrometers
stepsize = (50, 50)    # Step size in nm (X, Y)

line_scan_2D(fast_axis, slow_steps, total_X_length, total_Y_length, stepsize)
# Deactivate axis
amc.control.setControlOutput(x_axis, False)
# Deactivate axis
amc.control.setControlOutput(y_axis, False)

# Close connection
amc.close()


