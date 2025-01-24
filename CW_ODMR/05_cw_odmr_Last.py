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
from qm.octave import *
from qm.octave.octave_manager import ClockMode
from qm.qua import *
from qm import SimulationConfig
#from qm import LoopbackInterface
import matplotlib.pyplot as plt
from configuration_with_octave_Last import *


###################
# The QUA program #
###################

# Frequency vector
f_vec = np.arange(-70 * u.MHz, 70 * u.MHz, 0.5 * u.MHz)
print(len(f_vec))
n_avg = 100_000_000 # number of averages
readout_len = long_meas_len_1  # Readout duration for this experiment

with program() as cw_odmr:
    times = declare(int, size=100)  # QUA vector for storing the time-tags
    counts = declare(int)  # variable for number of counts
    counts_dark = declare(int)
    iteration = declare(int)
    counts_st = declare_stream()  # stream for counts
    counts_dark_st = declare_stream()  # stream for counts
    f = declare(int)  # frequencies
    n = declare(int)  # number of iterations
    n_st = declare_stream()  # stream for number of iterations

    with infinite_loop_():
        
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
   
    with stream_processing():
        # Cast the data into a 1D vector, average the 1D vectors together and store the results on the OPX processor
        
        
        counts_st.buffer(len(f_vec)).save("counts")

        counts_dark_st.buffer(len(f_vec)).save("counts_dark")
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
    simulation_config = SimulationConfig(duration=1_000)  # In clock cycles = 4ns
    job = qmm.simulate(config, cw_odmr, simulation_config)
    Time = []
    counts = []
    #job.get_simulated_samples().con1.plot()
    samples = job.get_simulated_samples()
    # plot all ports:
    #samples.con1.plot()
    print('before')
    results = job.result_handles
    counts_handle = results.get("counts")
    #counts_handle.wait_for_values(1)
    print('after')

    while results.is_processing():
        
        # Fetch results
        new_counts = counts_handle.fetch_all() 
        
        counts.append(new_counts["value"] )
        Time.append(new_counts["timestamp"])  # Convert timestams to seconds
        plt.cla()
        samples = job.get_simulated_samples()
        # plot all ports:
        samples.con1.plot()
        print(counts)
        

        
else:
    # Open the quantum machine
    qm = qmm.open_qm(config)
    # Send the QUA program to the OPX, which compiles and executes it
    job = qm.execute(cw_odmr)
    Time=[]
    # Get results from QUA program
    #results = fetching_tool(job, data_list=["counts", "counts_dark", "iteration"], mode="live")
    res_handles = job.result_handles
    counts_handle = res_handles.get("counts")
    dark_counts_handle= res_handles.get("counts_dark")
    it_handle=res_handles.get("iteration")
    
    counts_handle.wait_for_values(1)
    dark_counts_handle.wait_for_values(1)
    #counts_list= []
    #dark_counts_list =[]
    counts_sum = np.zeros(len(f_vec))  # Initialize to store the cumulative sum
    dark_counts_sum = np.zeros(len(f_vec))
    iteration_sum = 0
    # Live plotting
    fig = plt.figure()
    interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
    
    while res_handles.is_processing():
     
        # Fetch results
        #counts, counts_dark, iteration = results.fetch_all()
        counts = counts_handle.fetch("counts")

        counts_dark= dark_counts_handle.fetch('counts_dark')
        iteration=it_handle.fetch('iteration')
        #print(iteration)
        if counts_sum is None:
            counts_sum =  counts
            dark_counts_sum = counts_dark 
            
        else:
            iteration_sum += 1 
            #print(iteration_sum)
            counts_sum = counts_sum + counts
            #print(f"Iteration {iteration_sum}: {counts_sum}")
            dark_counts_sum = (dark_counts_sum + counts_dark ) 
            #print(f"Iteration {iteration_sum}: {dark_counts_sum}")
            
            
        # counts_list.append( counts / 1000 / (readout_len * 1e-9))
        
        # iteration = it_handle.fetch("iteration")
        # iteration_list.append(iteration)
        # #print(summed_counts_array.shape)
        # #print(counts_dark)
        # # Sum all arrays element-wise
        # summed_counts_array = np.sum(counts_list, axis=0)/len(iteration_list)+1
        
        # print(f"Iteration {len(iteration_list) + 1}: {summed_counts_array}")
        
        # counts_dark = dark_counts_handle.fetch("counts_dark")
        # dark_counts_list.append(counts_dark / 1000 / (readout_len * 1e-9))
        # summed_dark_counts_array = np.sum(dark_counts_list, axis=0)/len(iteration_list)+1
        # print(f"Iteration {len(iteration_list) + 1}: {summed_dark_counts_array}")
        


    
    
        # Progress bar
        #progress_counter(iteration, n_avg, start_time=res_handles.get_start_time())
        # # # Plot data
        plt.cla()
        plt.plot((NV_LO_freq * 0 + f_vec) / u.MHz, (counts_sum / 1000 / (readout_len * 1e-9)) /iteration_sum, label="photon counts")
        plt.plot((NV_LO_freq * 0 + f_vec) / u.MHz, (dark_counts_sum / 1000 / (readout_len * 1e-9)) /iteration_sum , label="dark counts")
        plt.xlabel("MW frequency [MHz]")
        plt.ylabel("Intensity [kcps]")
        plt.title("ODMR")
        plt.legend()
        plt.pause(0.1)
    qm.octave.set_rf_output_mode("NV", RFOutputMode.trig_normal)
                
