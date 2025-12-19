# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 17:49:02 2024

@author: attocube
"""

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
import time


###################
# The QUA program #
###################

# Frequency vector
f_vec = np.arange(-70 * u.MHz, 70 * u.MHz, 0.5 * u.MHz)
n_avg = 100  # number of averages
m_avg=100
readout_len = long_meas_len_1  # Readout duration for this experiment

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
    m = declare(int)

    with for_(n, 0, n < n_avg, n + 1):
        
        with for_(m, 0, m < m_avg, m + 1):
            with for_(*from_array(f, f_vec)):
                # Update the frequency of the digital oscillator linked to the element "NV"
                update_frequency("NV", f)
                # align all elements before starting the sequence
                align()
                # Play the mw pulse...
                play("cw" * amp(1), "NV", duration=readout_len * u.ns)
                # ... and the laser pulse simultaneously (the laser pulse is delayed by 'laser_delay_1')
                play("laser_ON", "AOM1", duration=readout_len * u.ns)
                wait(1_000 * u.ns, "SPCM1")  # so readout don't catch the first part of spin reinitialization
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
                wait(1_000 * u.ns, "SPCM1")  # so readout don't catch the first part of spin reinitialization
                measure("long_readout", "SPCM1", None, time_tagging.analog(times, readout_len, counts))
    
                save(counts, counts_dark_st)  # save counts on stream
    
                wait(wait_between_runs * u.ns)
    
                save(n, n_st)  # save number of iteration inside for_loop
            save(counts1, counts_st1)  # save counts on stream
            assign(counts1, 0)
        pause()
    with stream_processing():
        # Cast the data into a 1D vector, average the 1D vectors together and store the results on the OPX processor
        counts_st.buffer(m_avg, len(f_vec)).map(FUNCTIONS.average(0)).save_all("counts")
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
        try:
            job.resume()
                # Wait until the program reaches the 'pause' statement again, indicating that the QUA program is done
            while not job.is_paused() and job.status == 'running':
                time.sleep(0.1)
        
        except:
            pass
        c = counts_handle.count_so_far()
        counts, counts_dark, iteration = results.fetch_all()
        print(f'c_len{len(counts)}')
        print(f'c: {c}')
        
        # Progress bar
        #progress_counter(iteration, n_avg, start_time=results.get_start_time())
        # Plot data
        ax1.cla()
        ax2.cla()
        ax1.plot((NV_LO_freq * 0 + f_vec) / u.MHz, counts[-1] / 1000 / (readout_len * 1e-9), label="photon counts")
        ax1.plot((NV_LO_freq * 0 + f_vec) / u.MHz, counts_dark / 1000 / (readout_len * 1e-9), label="dark counts")
        new_counts = counts_handle.fetch_all() 
        print("value")
        print(new_counts["value"] )
        counts2 = np.append(counts2,(new_counts["value"] / 1000 / (readout_len * 1e-9) ))
        time = np.append(time,new_counts["timestamp"] / u.s)  # Convert timestams to seconds
        ax1.set_xlabel("MW frequency [MHz]")
        ax1.set_ylabel("Intensity [kcps]")
        ax1.set_title("ODMR")
        ax1.legend()

        print(counts2)
        print(type(time))
        ax2.plot(time,counts2)
        ax2.set_xlabel("Times")
        ax2.set_ylabel("Counts (kcps)")
        plt.pause(0.1)
        print(f'Number of Iterations:{iteration}')
    qm.octave.set_rf_output_mode("NV", RFOutputMode.trig_normal)
