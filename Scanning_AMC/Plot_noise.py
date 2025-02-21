import numpy as np
import matplotlib.pyplot as plt

def read_and_plot_data(file_path):
    """
    Reads movement data from the file and plots Y vs. X positions for each line with real data points.
    """
    x_positions = []
    y_positions = []
    line_numbers = []  # Store the line numbers
    metadata = {}  # Dictionary to store selected metadata
    
    # Read the file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Extract selected metadata from headers
    for line in lines:
        if line.startswith("#"):
            if "Fast axis" in line:
                metadata["Fast axis"] = line.strip().split(": ", 1)[1]
            elif "X range" in line:
                metadata["X range"] = line.strip().split(": ", 1)[1]
            elif "Y range" in line:
                metadata["Y range"] = line.strip().split(": ", 1)[1]
            elif "Step size" in line:
                metadata["Step size"] = line.strip().split(": ", 1)[1]
            elif "Slow steps" in line:
                metadata["Slow steps"] = line.strip().split(": ", 1)[1]
            continue
        
        # Read the position and the line number
        try:
            x, y, z, line_number = line.strip().split('\t')
            x_positions.append(float(x))
            y_positions.append(float(y))
            line_numbers.append(line_number)  # Store the line number
        except ValueError:
            continue  # Skip any malformed lines
    
    # Define a set of known colors
    known_colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan', 'lime', 'black']
    
    # Group data by line number
    unique_lines = sorted(set(line_numbers))  # Get all unique line numbers
    
    # Create a single plot for Y vs. X positions
    plt.figure(figsize=(10, 8))
    for idx, current_line in enumerate(unique_lines):
        color = known_colors[idx % len(known_colors)]  # Use a color from the known_colors list
        
        # Filter the X and Y positions for the current line
        x_scanning = [x_positions[i] for i in range(len(line_numbers)) if line_numbers[i] == current_line]
        y_scanning = [y_positions[i] for i in range(len(line_numbers)) if line_numbers[i] == current_line]
        
        # Plot the line connecting the points
        plt.plot(x_scanning, y_scanning, color=color, label=f'Line {current_line}', linewidth=1.5)
        
        # Add the actual data points as a scatter plot
        plt.scatter(x_scanning, y_scanning, color=color, edgecolor='black', s=30, zorder=3, label=f'Points {current_line}')
    
    plt.xlabel("X Position (nm)")
    plt.ylabel("Y Position (nm)")
    plt.title("Scanning Movements")
    plt.legend()
    plt.grid(True)
    
    # Add the selected metadata as text in the plot
    metadata_text = "\n".join([f"{key}: {value}" for key, value in metadata.items()])
    plt.figtext(0.99, 0.01, metadata_text, ha="right", va="bottom", fontsize=10, bbox=dict(facecolor='white', alpha=0.5))
    
    # Adjust layout to make space for the titles and labels
    plt.tight_layout()
    plt.show()

# Specify the path to the output file
file_path = "movement_data_with_noise.txt"  # Replace with your actual file path

# Call the function to read and plot data
read_and_plot_data(file_path)
