import numpy as np
import matplotlib.pyplot as plt
import AMC
import time

# IP of the Tip positioner
IP = "192.168.1.2"  # Tip positioner
#IP = "192.168.1.1"  # Sample positioner


# Setup connection to AMC
amc = AMC.Device(IP)
amc.connect()

# Axis configuration
axis = 1  # Axis 1

# Activate axis
amc.control.setControlOutput(axis, True)

# Movement parameters
frequency = 500 * 1e3  # mHz
amplitude = 50 * 1e3   # mV
move_distance = 10000   # nm
num_trials = 30       # Number of trials

# Configure AMC parameters
amc.control.setControlFrequency(axis, frequency)
amc.control.setControlAmplitude(axis, amplitude)

# Target range values
tgt_range = np.linspace(0.12, 0.04, 8)  # Reversed range

def move_tgt(axis, dist):
    """Performs a forward movement and returns the difference between targe♥t and final position."""
    # Get initial position
    position = amc.move.getPosition(axis)
    target_position = position + dist

    amc.move.setControlTargetPosition(axis, target_position)
    amc.control.setControlMove(axis, True)

    while not amc.status.getStatusTargetRange(axis):
    #while (abs(position - target_position) > 100):
       position = amc.move.getPosition(axis)
       #print(f'Target, currentPos:{target_position, position}')
       time.sleep(0.01)

    # Stop movement
    amc.control.setControlMove(axis, False)

    # Get final position
    final_position = amc.move.getPosition(axis)
    # print(f'Final Position: {final_position}, Target: {target_position}, Difference: {target_position - final_position}')
    return target_position - final_position



# Plot sub-histograms for error data
fig, axes = plt.subplots(2, 4, figsize=(20, 8), sharey=True)
axes = axes.flatten()

# Separate figure for time histograms
fig_time, axes_time = plt.subplots(2, 4, figsize=(20, 8), sharey=True)
axes_time = axes_time.flatten()
hist_range = (-200, 200)
time_hist_range = (0, 1.5)  # Range in minutes

# File to store timing and error information
with open("scan_timings.txt", "a") as file:  # Open in append mode
    for idx, t in enumerate(tgt_range):
        error_fwd = []
        error_bwd = []
        T_fwd = []
        T_bwd = []

        amc.control.setControlTargetRange(axis, t * 1e3)  # Set target range in nm
        print(f"\nTarget Range: {t * 1e3} nm")
        file.write(f"\nTarget Range: {t * 1e3} nm\n")

        for i in range(num_trials):
            # Forward movement
            t0 = time.time()
            error_f = move_tgt(axis, move_distance)
            t1 = time.time()

            error_fwd.append(error_f)
            T_fwd.append(t1 - t0)
            print(f"Forward Trial {i + 1}, Error: {error_f:.2f} nm, Time: {t1 - t0:.2f} sec")

            # Backward movement
            t2 = time.time()
            error_b = move_tgt(axis, -move_distance)
            t3 = time.time()

            error_bwd.append(error_b)
            T_bwd.append(t3 - t2)
            print(f"Backward Trial {i + 1}, Error: {error_b:.2f} nm, Time: {t3 - t2:.2f} sec")

            # Write trial details to the file
            file.write(f"Trial {i + 1} - Forward: Error: {error_f:.2f} nm, Time: {t1 - t0:.2f} sec\n")
            file.write(f"Trial {i + 1} - Backward: Error: {error_b:.2f} nm, Time: {t3 - t2:.2f} sec\n")
          
        # Calculate average error and time
        avg_error_fwd = sum(abs(e) for e in error_fwd) / len(error_fwd)
        avg_time_fwd = sum(T_fwd) / len(T_fwd)
        avg_error_bwd = sum(abs(e) for e in error_bwd) / len(error_bwd)
        avg_time_bwd = sum(T_bwd) / len(T_bwd)
        
        # # Calculate global x-axis ranges for errors and times
        # error_min = min(min(error_fwd), min(error_bwd))
        # error_max = max(max(error_fwd), max(error_bwd))
        # time_min = min(min(T_fwd), min(T_bwd))
        # time_max = max(max(T_fwd), max(T_bwd))


        # Write average details for this target range to the file
        file.write(f"Average Forward Error: {avg_error_fwd:.2f} nm, Average Time: {avg_time_fwd:.2f} sec\n")
        file.write(f"Average Backward Error: {avg_error_bwd:.2f} nm, Average Time: {avg_time_bwd:.2f} sec\n")

        # # Plot error histogram for the current target range
        # ax = axes[idx]
        # ax.hist(error_fwd, bins=20, edgecolor='black', color='blue', label='Forward')
        # ax.hist(error_bwd, bins=20, edgecolor='black', color='orange', label='Backward', alpha=0.7, hatch='//')
        # ax.set_title(f'Tgt_Range: {t * 1e3:.1f} nm\n'
        #               f'F_avg_Err: {avg_error_fwd:.2f}nm, B_avg_Err: {avg_error_bwd:.2f}nm')
        # ax.set_xlabel('Error Distance (nm)')
        # ax.set_ylabel('Frequency')
        # ax.legend()
        # ax.grid(axis='y', linestyle='--', alpha=0.7)

        # # Plot time histogram for the current target range
        # ax_time = axes_time[idx]
        # ax_time.hist(T_fwd, bins=10, edgecolor='black', color='green', label='Forward')
        # ax_time.hist(T_bwd, bins=10, edgecolor='black', color='red', label='Backward', alpha=0.7, hatch='//')
        # ax_time.set_title(f'Tgt_Range: {t * 1e3:.1f} nm\n'
        #                   f'F_avg_t: {avg_time_fwd:.2f}sec, B_avg_t: {avg_time_bwd:.2f}sec')
        # ax_time.set_xlabel('Time (sec)')
        # ax_time.set_ylabel('Frequency')
        # ax_time.legend()
        # ax_time.grid(axis='y', linestyle='--', alpha=0.7)
        
        
        
        # Plot error histogram for the current target range
        ax = axes[idx]
        ax.hist(error_fwd, bins=20, range=hist_range, edgecolor='black', color='blue', label='Forward', alpha=0.8)
        ax.hist(error_bwd, bins=20, range=hist_range, edgecolor='black', color='orange', label='Backward', alpha=0.6, hatch='//')
        ax.set_title(f'Tgt_Range: {t * 1e3:.1f} nm\n'
                     f'F_avg: {avg_error_fwd:.2f}nm, B_avg: {avg_error_bwd:.2f}nm')
        
        # Set consistent x-axis range for error histograms
        ax.set_xlim(-250, 250)
        #ax.set_xticks(np.arange(-200, 201, 5))  # Set step size for x-axis ticks
        
        # Only show x-labels on the bottom row
        if idx >= len(axes) - 4:  # Assuming a 2x4 grid
            ax.set_xlabel('Error Distance (nm)')
        else:
            ax.set_xlabel('')  # Hide x-labels for non-bottom axes
        
        ax.set_ylabel('Frequency')
        ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Plot time histogram for the current target range
        ax_time = axes_time[idx]
        ax_time.hist(T_fwd, bins=10, range=time_hist_range, edgecolor='black', color='green', label='Forward', alpha=0.8)
        ax_time.hist(T_bwd, bins=10, range=time_hist_range, edgecolor='black', color='red', label='Backward', alpha=0.6, hatch='//')
        ax_time.set_title(f'Tgt_Range: {t * 1e3:.1f} nm\n'
                          f'F_avg_t: {avg_time_fwd:.2f}sec, B_avg_t: {avg_time_bwd:.2f}sec')
        
        # Set consistent x-axis range for time histograms
        ax_time.set_xlim(0, 1.50)
        
        # Only show x-labels on the bottom row
        if idx >= len(axes_time) - 4:  # Assuming a 2x4 grid
            ax_time.set_xlabel('Time (sec)')
        else:
            ax_time.set_xlabel('')  # Hide x-labels for non-bottom axes
        
        ax_time.set_ylabel('Frequency')
        ax_time.legend()
        ax_time.grid(axis='y', linestyle='--', alpha=0.7)
        

# Deactivate axis
amc.control.setControlOutput(axis, False)

# Close connection
amc.close()

# Adjust layouts and show plots
plt.tight_layout()
plt.show()
fig_time.tight_layout()
plt.show()
