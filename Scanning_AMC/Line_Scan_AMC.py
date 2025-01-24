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

def line_scan_2D(fast_axis, slow_steps, total_X_length, total_Y_length, stepsize, output_file):
    """
    2D Fast-Line scan function that moves the stage and writes position data to a file.
    """
    # Open the output file
    with open(output_file, 'w') as file:
        # Write header with scan parameters
        file.write(f"# Scantype: Linescan\n")
        file.write(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"# Fast axis: {fast_axis}\n")
        file.write(f"# X range: {-total_X_length / 2} - {total_X_length / 2} nm\n")
        file.write(f"# Y range: {-total_Y_length / 2} - {total_Y_length / 2} nm\n")
        file.write(f"# Step size: {stepsize} nm\n")
        file.write(f"# Slow steps: {slow_steps}\n")
        file.write("# Columns: X Position (nm), Y Position (nm), Z Position (nm), Movement Type\n")

        # Initial position
        x0, y0 = amc.move.getPosition(x_axis), amc.move.getPosition(y_axis)
        print(f'Initial pos: x: {x0}, y: {y0}')
        
        # Bottom left of center scan
        X_start = x0 - total_X_length / 2
        Y_start = y0 - total_Y_length / 2
        
        x_start = X_start + stepsize[0] / 2
        x_end = X_start + total_X_length
        y_start = Y_start + stepsize[1] / 2
        y_end = Y_start + total_Y_length
        
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
                return
            
            # Centering movement
            tgt_start = [X, Y]
            amc.move.setControlTargetPosition(x_axis, tgt_start[0])
            amc.control.setControlMove(x_axis, True)
            amc.move.setControlTargetPosition(y_axis, tgt_start[1])
            amc.control.setControlMove(y_axis, True)
            time.sleep(0.0005)
            
            while not amc.status.getStatusTargetRange(x_axis) or not amc.status.getStatusTargetRange(y_axis):
                pos = amc.move.getPosition(x_axis), amc.move.getPosition(y_axis)
                file.write(f"{pos[0]:.3f}\t{pos[1]:.3f}\t0.0\t Line {i}\n")
                time.sleep(0.01)
            
            # Stop movement
            amc.control.setControlMove(x_axis, False)
            amc.control.setControlMove(y_axis, False)
            
            # Scanning movement
            tgt = [X_tgt, Y_tgt]
            amc.move.setControlTargetPosition(x_axis, tgt[0])
            amc.control.setControlMove(x_axis, True)
            amc.move.setControlTargetPosition(y_axis, tgt[1])
            amc.control.setControlMove(y_axis, True)
            
            while not amc.status.getStatusTargetRange(x_axis) or not amc.status.getStatusTargetRange(x_axis):
                pos = amc.move.getPosition(x_axis), amc.move.getPosition(y_axis)
                file.write(f"{pos[0]:.3f}\t{pos[1]:.3f}\t0.0\t Line {i}\n")
                time.sleep(0.01)
            
            # Stop movement again
            amc.control.setControlMove(x_axis, False)
            amc.control.setControlMove(y_axis, False)
            
            print("Done Measuring")


# Parameters for 2D scan
fast_axis = 'X'  # Fast axis ('X' or 'Y')
slow_steps = 5  # Number of slow steps
total_X_length = 10000  # Total length along X-axis in nm
total_Y_length = 10000   # Total length along Y-axis in micrometers
stepsize = (500, 500)    # Step size in nm (X, Y)

# Specify output file
output_file = "movement_data.txt"

line_scan_2D(fast_axis, slow_steps, total_X_length, total_Y_length, stepsize, output_file)

# Deactivate axis
amc.control.setControlOutput(x_axis, False)
amc.control.setControlOutput(y_axis, False)

# Close connection
amc.close()




