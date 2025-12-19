"""
        CW Optically Detected Magnetic Resonance (ODMR)
The program consists in playing a mw pulse and the readout laser pulse simultaneously to extract
the photon counts received by the SPCM across varying intermediate frequencies.
The sequence is repeated without playing the mw pulses to measure the dark counts on the SPCM.

The data is then post-processed to determine the spin resonance frequency.
This frequency can be used to update the NV intermediate frequency in the configuration under "NV_IF_freq".

Prerequisites:
    - Ensure calibration of the different delays in the system (calibrate_delays).
    - Update the different delays in the configuration

Next steps before going to the next node:
    - Update the NV frequency, labeled as "NV_IF_freq", in the configuration.
"""

from qm import QuantumMachinesManager
from qm.qua import *
from qm import SimulationConfig
import matplotlib.pyplot as plt
from configuration_with_octave_Last import *
import numpy as np
import os
import time as time_module
from scipy.optimize import curve_fit


@staticmethod
def lorentzian(x, x0, a, gamma, bg):
    
    """
    Single Lorentzian function.
    Parameters:
    x  : array-like, The frequency values.
    x0 : float, The center frequency of the dip.
    a  : float, The amplitude (depth) of the dip.
    gamma : float, The full-width at half maximum (FWHM).
    bg : float, Background offset.
    Returns:
    y : array-like, The computed Lorentzian function values.
    """
    return -abs(a) * (gamma ** 2 / ((x - x0) ** 2 + gamma ** 2)) + bg

def fit_lorentzian(x_data, y_data):
    """
    Perform Lorentzian fitting (single, double, or triple) on ODMR data.

    Parameters:
    - x_data: frequency array (MHz).
    - y_data: corresponding PL counts (kc/s).
    - fit_type: fit model ("Single Lorentzian", "Double Lorentzian", "Triple Lorentzian").
    - center_freq: expected ODMR center (used for initial guess symmetry).

    Returns:
    - popt: optimized fit parameters.
    - fitted_y: fitted Lorentzian curve evaluated over x_data.
    """
    p0 = [x_data[np.where(y_data==np.min(y_data))][0],np.max(y_data)-np.min(y_data),5,np.max(y_data)]
    print(p0)

    popt, _ = curve_fit(lorentzian, x_data, y_data, p0=p0, maxfev=10000)
    return popt, lorentzian(x_data, *popt)

###################
# The QUA program #
###################

# Frequency vector
f_vec = np.arange(75 * u.MHz, 125 * u.MHz, 0.5 * u.MHz)
#f_vec = np.arange(70 * u.MHz,  120* u.MHz, 0.5 * u.MHz)
#f_abs = np.arange(2.35*u.GHz, 2.4*u.GHz, 0.25*u.MHz)
#f_vec = f_abs - NV_LO_freq
#f_vec = np.array([0*u.MHz])
n_avg = 1000000  # number of averages
readout_len = long_meas_len_1  # Readout duration for this experiment
mw_amp = 1.5
wait_between_runs = 15*u.us
phi = '58' #in plane
theta = '-45' #z angle
B = 15 #absolute value of B in mT

#f_vec = [100 * u.MHz]

with program() as cw_odmr:
    times = declare(int, size=100)  # QUA vector for storing the time-tags
    counts = declare(int)  # variable for number of counts
    counts1 = declare(int)  # variable for number of counts
    counts_st = declare_stream()  # stream for counts
    counts_st1 = declare_stream()  # stream for counts
    counts_dark_st = declare_stream()  # stream for counts
    f = declare(int)  # frequencies
    n = declare(int)  # number of iterations
    n_st = declare_stream()  # stream for number of iterations

    with for_(n, 0, n < n_avg, n + 1):
        #wait(50*u.us)
        with for_(*from_array(f, f_vec)):
            # Update the frequency of the digital oscillator linked to the element "NV"
            update_frequency("NV", f)
            # align all elements before starting the sequence
            align()
            # Play the mw pulse...
            play("cw" * amp(mw_amp), "NV", duration=readout_len * u.ns)
            # ... and the laser pulse simultaneously (the laser pulse is delayed by 'laser_delay_1')
            play("laser_ON", "AOM1", duration=readout_len * u.ns)
            wait(500 * u.ns, "SPCM1")  # so readout don't catch the first part of spin reinitialization
            # Measure and detect the photons on SPCM1
            measure("long_readout", "SPCM1", None, time_tagging.analog(times, readout_len, counts))

            save(counts, counts_st)  # save counts on stream

            assign(counts1, counts+counts1)
            # Wait and align all elements before measuring the dark events
            wait(wait_between_runs * u.ns)
            align()  # align all elements
            # Play the mw pulse with zero amplitude...
            play("cw" * amp(0), "NV", duration=readout_len * u.ns)
            # ... and the laser pulse simultaneously (the laser pulse is delayed by 'laser_delay_1')
            play("laser_ON", "AOM1", duration=readout_len * u.ns)
            wait(500 * u.ns, "SPCM1")  # so readout don't catch the first part of spin reinitialization
            measure("long_readout", "SPCM1", None, time_tagging.analog(times, readout_len, counts))

            save(counts, counts_dark_st)  # save counts on stream

            wait(wait_between_runs * u.ns)
            
            save(n, n_st)  # save number of iteration inside for_loop
        save(counts1, counts_st1)  # save counts on stream
        assign(counts1, 0)
    with stream_processing():
        # Cast the data into a 1D vector, average the 1D vectors together and store the results on the OPX processor
        counts_st.buffer(len(f_vec)).average().save("counts")
        counts_dark_st.buffer(len(f_vec)).average().save("counts_dark")
        counts_st1.with_timestamps().save("counts1")
        n_st.save("iteration")

#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name, octave=octave_config)

#######################
# Simulate or execute #
#######################
simulate = False

if simulate:
    # Simulates the QUA program for the specified duration
    simulation_config = SimulationConfig(duration=10_000)  # In clock cycles = 4ns
    job = qmm.simulate(config, cw_odmr, simulation_config)
    job.get_simulated_samples().con1.plot()
else:
    # Open the quantum machine
    qm = qmm.open_qm(config)
    # Send the QUA program to the OPX, which compiles and executes it
    job = qm.execute(cw_odmr)
    
    res_handles = job.result_handles
    counts_handle = res_handles.get("counts1")
    counts_handle.wait_for_values(1)
    # Get results from QUA program
    results = fetching_tool(job, data_list=["counts", "counts_dark", "iteration"], mode="live")
    # Live plotting
    
    fig, (ax1, ax2) = plt.subplots(2,1)
    interrupt_on_close(fig, job)  # Interrupts the job when closing the figure

    time = np.array([])
    counts2 = np.array([])
    while results.is_processing():
        # Fetch results
        counts, counts_dark, iteration = results.fetch_all()
        # Progress bar
        #progress_counter(iteration, n_avg, start_time=results.get_start_time())
        # Plot data
        ax1.cla()
        ax2.cla()
        ax1.plot((NV_LO_freq * 1 + f_vec) / u.MHz, (counts) / 1000 / (readout_len * 1e-9), 'o', label="photon counts")
        #ax1.plot((NV_LO_freq * 1 + f_vec) / u.MHz, counts_dark / 1000 / (readout_len * 1e-9), label="dark counts")
        try:
            p, fit = fit_lorentzian((NV_LO_freq * 1 + f_vec) / u.MHz, (counts) / 1000 / (readout_len * 1e-9))
        except:
            pass
            
        ax1.plot((NV_LO_freq * 1 + f_vec) / u.MHz, fit, 'r', label=f'frequency: {round(p[0])}')
        #ax1.text(1,1,f'frequency: {p[0]}',transform=ax1.transAxes)
        new_counts = counts_handle.fetch_all() 
        #print("value")
        #print(new_counts["value"] )
        counts2 = np.append(counts2,(new_counts["value"] / 1000 / (readout_len * 1e-9) ))
        time = np.append(time,new_counts["timestamp"] / u.s)  # Convert timestams to seconds
        ax1.set_xlabel("MW frequency [MHz]")
        ax1.set_ylabel("Intensity [kcps]")
        ax1.set_title("ODMR")
        ax1.legend()

        print(counts2)
        print(type(time))
        ax2.plot(time,counts2)
        ax2.set_xlabel("Time (s)")
        ax2.set_ylabel("Counts (kcps)")
        plt.pause(0.1)
        print(f'Number of Iterations:{iteration}')
        
    
    qm.octave.set_rf_output_mode("NV", RFOutputMode.off)

    directory = f"//WXPC724/Share/Data/A-T09-23-Int/Bfield"
    # Create the full path for saving the data, adding a .txt extension
    full_path = os.path.join(directory, f"{time_module.strftime('%Y%m%d-%H%M-%S')}_ODMR_{phi}_{theta}_deg_{B}mT")  
    #Ensure the directory exists
    os.makedirs(directory, exist_ok=True)
    
    frequencies = (NV_LO_freq * 0 + f_vec) / u.MHz
    counts = counts / 1000 / (readout_len * 1e-9)
    counts_dark = counts_dark / 1000 / (readout_len * 1e-9)
    
    
    #np.savez(full_path, frequencies=(NV_LO_freq * 1 + f_vec) / u.MHz, counts=counts, counts_dark=counts_dark, counts2=counts2, time=time, mw_amp=mw_amp, theta=theta, phi=phi, fitparams=p)