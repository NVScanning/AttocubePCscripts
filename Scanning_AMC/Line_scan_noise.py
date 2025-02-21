import numpy as np
import time
import AMC

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
amc.control.setControlTargetRange(x_axis, tgt_range*1e3)
amc.control.setControlTargetRange(y_axis, tgt_range*1e3)

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

        # Collect position data (50 samples from each of the two loops)
        x_positions_first_loop = []
        y_positions_first_loop = []
        # x_positions_second_loop = []
        # y_positions_second_loop = []

        # First loop (collect 50 samples)
        for _ in range(250):
            pos = amc.move.getPosition(x_axis), amc.move.getPosition(y_axis)
            x_positions_first_loop.append(pos[0])
            y_positions_first_loop.append(pos[1])
            file.write(f"{pos[0]:.3f}\t{pos[1]:.3f}\t0.0\t Idle\n")
            time.sleep(0.01)  # Collect samples every 10ms (adjust as needed)

        # Calculate noise for first loop (standard deviation)
        x_noise = np.std(x_positions_first_loop)
        y_noise = np.std(y_positions_first_loop)
        print(f"Noise during first loop (X): {x_noise:.3f} nm")
        print(f"Noise during first loop (Y): {y_noise:.3f} nm")

        # # Second loop (collect another 50 samples)
        # for _ in range(50):
        #     pos = amc.move.getPosition(x_axis), amc.move.getPosition(y_axis)
        #     x_positions_second_loop.append(pos[0])
        #     y_positions_second_loop.append(pos[1])
        #     file.write(f"{pos[0]:.3f}\t{pos[1]:.3f}\t0.0\t Idle\n")
        #     time.sleep(0.01)  # Collect samples every 10ms (adjust as needed)

        # # Calculate noise for second loop (standard deviation)
        # x_noise_2 = np.std(x_positions_second_loop)
        # y_noise_2 = np.std(y_positions_second_loop)
        # print(f"Noise during second loop (X): {x_noise_2:.3f} nm")
        # print(f"Noise during second loop (Y): {y_noise_2:.3f} nm")

        # Combine noise results (optional)
        # total_x_noise = (x_noise + x_noise_2) / 2
        # total_y_noise = (y_noise + y_noise_2) / 2
        # print(f"Total noise (X): {total_x_noise:.3f} nm")
        # print(f"Total noise (Y): {total_y_noise:.3f} nm")

        # Optionally, you can write the noise values to the file as well:
        file.write(f"# Noise (X): {x_noise:.3f} nm\n")
        file.write(f"# Noise (Y): {y_noise:.3f} nm\n")
        # file.write(f"# Total noise (X): {total_x_noise:.3f} nm\n")
        # file.write(f"# Total noise (Y): {total_y_noise:.3f} nm\n")

        print("Done Measuring")


# Parameters for 2D scan
fast_axis = 'X'  # Fast axis ('X' or 'Y')
slow_steps = 1 # Number of slow steps
total_X_length = 10000  # Total length along X-axis in nm
total_Y_length = 10000   # Total length along Y-axis in micrometers
stepsize = (500, 500)    # Step size in nm (X, Y)

# Specify output file
output_file = "movement_data_with_noise4.txt"

line_scan_2D(fast_axis, slow_steps, total_X_length, total_Y_length, stepsize, output_file)

# Deactivate axis
amc.control.setControlOutput(x_axis, False)
amc.control.setControlOutput(y_axis, False)

# Close connection
amc.close()
