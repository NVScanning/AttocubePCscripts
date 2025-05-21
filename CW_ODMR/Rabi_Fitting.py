import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from pathlib import Path

def load_rabi_data(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    t_vec_idx = lines.index("# t_vec (Pulse Durations in clock cycles):\n") + 1
    counts_idx = lines.index("# Counts Data:\n") + 1
    counts_dark_idx = lines.index("# Dark Counts Data:\n") + 1

    t_vec = np.array(list(map(float, lines[t_vec_idx].split())))
    counts = np.array(list(map(float, lines[counts_idx].split())))
    counts_dark = np.array(list(map(float, lines[counts_dark_idx].split())))

    return t_vec, counts, counts_dark

def rabi_func(x, amp, freq, phase, decay, offset):
    return amp * np.sin(np.pi * freq * x + phase)**2 * np.exp(-x / decay) + offset

# # Load latest dataset
# script_name = "06_time_rabi"
# results_path = Path(r"\\wxpc724\share\attocubepcscripts\cw_odmr\results")
# latest_folder = max(results_path.glob(f"{script_name}_*"), key=lambda x: x.stat().st_mtime)
# filepath = latest_folder / f"{script_name}_time_rabi_data.txt"
# print(f"Loading data from: {filepath}")

results_path = Path(r"\\wxpc724\share\attocubepcscripts\cw_odmr\results")
script_name = "06_time_rabi"

# === Option 1: Specify manually (optional) ===
timestamp_folder = "2025-03-23_21-19-57"  # <--- Put None if you want latest
# timestamp_folder = False  # <--- Put None if you want latest


if timestamp_folder:
    # Manually use the folder
    # folder = min(results_path.glob( f"{script_name}_{timestamp_folder}"), key=lambda x: x.stat().st_mtime)
    folder = results_path / f"{script_name}_{timestamp_folder}"

else:
    # Automatically find latest
    folder = max(results_path.glob(f"{script_name}_*"), key=lambda x: x.stat().st_mtime)
    print(folder)

filepath = folder / f"{script_name}_time_rabi_data.txt"
print(f"Loading data from: {filepath}")

t_vec, counts, counts_dark = load_rabi_data(filepath)
t_vec_ns = t_vec * 4  # convert to ns

# Normalize counts
counts_normalized = counts / counts_dark

# --- Improve initial guess ---
# FFT to estimate frequency:
fft = np.fft.fft(counts_normalized - np.mean(counts_normalized))
freqs = np.fft.fftfreq(len(t_vec_ns), d=(t_vec_ns[1]-t_vec_ns[0]))  # in ns^-1
peak_idx = np.argmax(np.abs(fft[1:])) + 1
freq_guess = abs(freqs[peak_idx])  # ns^-1

# Initial guesses:
amp_guess = np.ptp(counts_normalized)
offset_guess = np.mean(counts_normalized)
decay_guess = max(t_vec_ns) / 2
phase_guess = 0

print(f"Initial guess freq: {freq_guess:.6f} ns^-1")

initial_guess = [amp_guess, freq_guess, phase_guess, decay_guess, offset_guess]

# --- Fit ---
params, cov = curve_fit(rabi_func, t_vec_ns, counts_normalized, p0=initial_guess)

amp_fit, freq_fit, phase_fit, decay_fit, offset_fit = params
pi_pulse_ns = 0.5 / freq_fit
print(f"Pi-pulse duration = {pi_pulse_ns:.2f} ns")

# --- Plot ---
plt.figure(figsize=(8, 5))
plt.plot(t_vec_ns, counts_normalized, 'o',  markersize=3, label='Normalized Data')
plt.plot(t_vec_ns, rabi_func(t_vec_ns, *params), '-', label='Fit')
plt.axvline(pi_pulse_ns, color='red', linestyle='--', label=f'π ≈ {pi_pulse_ns:.1f} ns')
plt.xlabel("Rabi pulse duration [ns]")
plt.ylabel("Normalized Counts")
plt.title("Rabi Oscillation Fit ")
plt.legend()
plt.grid(True)
plt.show()
