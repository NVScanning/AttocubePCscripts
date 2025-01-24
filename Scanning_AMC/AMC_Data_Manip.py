import re
import matplotlib.pyplot as plt
from collections import defaultdict

# Function to parse the data
def parse_data(file_path):
    data = defaultdict(lambda: {"forward_errors": [], "backward_errors": [], 
                                "forward_times": [], "backward_times": []})
    with open(file_path, 'r') as file:
        current_target = None
        for line in file:
            # Match target range
            target_match = re.match(r"Target Range:\s*([\d.]+)\s*nm", line)
            if target_match:
                current_target = float(target_match.group(1))
                continue
            
            # Match forward and backward data
            forward_match = re.match(r".*Forward: Error:\s*([\d.-]+)\s*nm,\s*Time:\s*([\d.]+)\s*sec", line)
            if forward_match and current_target is not None:
                error = float(forward_match.group(1))
                time = float(forward_match.group(2))
                data[current_target]["forward_errors"].append(error)
                data[current_target]["forward_times"].append(time)
            
            backward_match = re.match(r".*Backward: Error:\s*([\d.-]+)\s*nm,\s*Time:\s*([\d.]+)\s*sec", line)
            if backward_match and current_target is not None:
                error = float(backward_match.group(1))
                time = float(backward_match.group(2))
                data[current_target]["backward_errors"].append(error)
                data[current_target]["backward_times"].append(time)
    return data

# Function to select the 8 target ranges with the most data
def select_top_ranges(data, top_n=8):
    target_counts = {target: len(values["forward_errors"]) + len(values["backward_errors"]) for target, values in data.items()}
    sorted_targets = sorted(target_counts, key=target_counts.get, reverse=True)
    return sorted_targets[:top_n]

# Function to write the merged data to a file
def write_merged_data(selected_ranges, data, output_file):
    with open(output_file, 'w') as file:
        file.write("Merged Data for Selected Target Ranges\n")
        for target in selected_ranges:
            if target in data:
                file.write(f"\nTarget Range: {target:.2f} nm\n")
                forward_errors = data[target]["forward_errors"]
                backward_errors = data[target]["backward_errors"]
                forward_times = data[target]["forward_times"]
                backward_times = data[target]["backward_times"]

                for i in range(len(forward_errors)):
                    file.write(f"Trial {i + 1} - Forward: Error: {forward_errors[i]:.2f} nm, Time: {forward_times[i]:.2f} sec\n")
                    file.write(f"Trial {i + 1} - Backward: Error: {backward_errors[i]:.2f} nm, Time: {backward_times[i]:.2f} sec\n")
    print(f"Merged data written to {output_file}")

# Function to plot histograms for selected target ranges
def plot_selected_histograms(selected_ranges, data):
    num_targets = len(selected_ranges)
    fig, axes = plt.subplots(num_targets, 2, figsize=(12, 5 * num_targets))
    hist_range = (-250, 250)
    time_hist_range = (0, 2)  # Adjust range as per your time data

    for idx, target in enumerate(selected_ranges):
        if target not in data:
            print(f"Target range {target} not found in data, skipping...")
            continue

        values = data[target]
        forward_errors = values["forward_errors"]
        backward_errors = values["backward_errors"]
        forward_times = values["forward_times"]
        backward_times = values["backward_times"]
        # Erro data histograms
        num_data_points = len(forward_errors) + len(backward_errors)
        num_data_time =  len(forward_times) + len(backward_times)
        
        # Error histograms
        ax = axes[idx, 0]
        ax.hist(forward_errors, bins=20, range=hist_range, edgecolor='black', color='blue', alpha=0.8, label='Forward')
        ax.hist(backward_errors, bins=20, range=hist_range, edgecolor='black', color='orange', alpha=0.6, label='Backward', hatch='//')
        ax.set_title(f'Target Range: {target:.1f} nm\nData Points: {num_data_points}')
        ax.set_xlabel('Error Distance (nm)')
        ax.set_ylabel('Frequency')
        ax.legend()

        # Time histograms
        ax_time = axes[idx, 1]
        ax_time.hist(forward_times, bins=10, range=time_hist_range, edgecolor='black', color='green', alpha=0.8, label='Forward')
        ax_time.hist(backward_times, bins=10, range=time_hist_range, edgecolor='black', color='red', alpha=0.6, label='Backward', hatch='//')
        ax_time.set_title(f'Target Range: {target:.1f} nm\nData Points: {num_data_time}')
        ax_time.set_xlabel('Time (sec)')
        ax_time.set_ylabel('Frequency')
        ax_time.legend()

    plt.tight_layout()
    plt.show()

# Path to the file
file_path = 'scan_timings.txt'
output_file = 'merged_scan_data.txt'

# Parse data
data = parse_data(file_path)

# Select the 8 target ranges with the most data
# selected_ranges = select_top_ranges(data, top_n=5)
# print(selected_ranges)
selected_ranges=[108.57142857142857,74.28571428571429]
# Write the merged data to a file
write_merged_data(selected_ranges, data, output_file)

# Plot histograms for selected target ranges
plot_selected_histograms(selected_ranges, data)
