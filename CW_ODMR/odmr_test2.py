
from qm import QuantumMachinesManager
from qm.qua import *
from qm import SimulationConfig
import matplotlib.pyplot as plt
from configuration_with_octave_Last import *
import numpy as np


print('here')

# counts_st=[]
# n_st=[]
# counts_strings=[]
# n_strings=[]
flattened=1
m_avg = 2*1e2
# counts_handle=np.zeros(flattened)
# print(counts_handle)
# n_handle= np.zeros(flattened)

readout_len = long_meas_len_1  # Readout duration for this experiment
fmin = 2.8

fmin = (fmin*1e3 - NV_LO_freq/u.GHz) 
      
fmax = 3.0
fmax = (fmax*1e3 - NV_LO_freq/u.GHz) 
N_points = 100
f_vec = np.arange(fmin*u.MHz, fmax*u.MHz , (fmax*u.MHz  - fmin*u.MHz ) / N_points)

N_average = 1e8

f_min_external = 3e9 - fmin
f_max_external = 4e9 - fmax
df_external = fmax - fmin
freqs_external = np.arange(f_min_external, f_max_external + 0.1, df_external)
frequency = np.array(np.concatenate([f_vec + freqs_external[i] for i in range(len(freqs_external))]))

with program() as cw_odmr:
    times = declare(int, size=100)
    counts = declare(int)
    counts_st=declare_stream()
    n_st=declare_stream()
    f = declare(int)
    n = declare(int)
    i = declare(int)  
    m  = declare(int)
    with for_(n, 0, n < N_average, n + 1):     
        with for_(i, 0, i < flattened + 1, i + 1):
            pause()  # This waits until it is resumed from python
            with for_(m, 0, m < m_avg, m + 1):
                with for_(*from_array(f, f_vec)):
                    update_frequency("NV", f)  # update frequency
                    align()  # align all elements
                    # play("cw" * amp(Vrms * 2 ** 0.5), "NV", duration=self.readout_len * u.ns)
                    play("cw" * amp(1), "NV", duration=readout_len * u.ns)
                    play("laser_ON", "AOM1", duration=readout_len * u.ns)
                    wait(1_000 * u.ns, "SPCM1")
                    measure("long_readout", "SPCM1", None, time_tagging.analog(times, readout_len, counts))
                    save(counts, counts_st)
                    save(n, n_st)

    with stream_processing():
        counts_st.buffer(m_avg, len(f_vec)).map(FUNCTIONS.average(0)).save("counts")
        n_st.save("iteration")
           
#####################################
#  Open Communication with the QOP  #
#####################################
print('here71')
qmm =  QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name, octave=octave_config)


simulate = False

def wait_until_job_is_paused(current_job):
    """
    Waits until the OPX FPGA reaches the pause statement.
    Used when the OPX sequence needs to be synchronized with an external parameter sweep.

    :param current_job: the job object.
    """
    while not current_job.is_paused():
        time.sleep(0.1)
        pass
    return True

if simulate:
    simulation_config = SimulationConfig(duration=28000)
    job = qmm.simulate(config, cw_odmr, simulation_config)
    job.get_simulated_samples().con1.plot()
else:
    qm = qmm.open_qm(config)

    job = qm.execute(cw_odmr)  # execute QUA program

    # Get results from QUA program
    res_handles = job.result_handles
    counts_handle = res_handles.get('counts')
    n_handle= res_handles.get('iteration')

 

    # Live plotting
    fig = plt.figure()
    interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
    
    time = np.array([])
    counts2 = np.array([])

    while res_handles.is_processing():
 
        try:
            print('here')
            job.resume()
        #     # Wait until the program reaches the 'pause' statement again, indicating that the QUA program is done
            #print('here')
            wait_until_job_is_paused(job)
            print('here1')
        except:
             pass

      
        # plt.pause(0.1)
        counts_handle.wait_for_values(1)
        n_handle.wait_for_values(1)
        
        # Fetch results
        counts = counts_handle.fetch('counts')
        iteration =  n_handle.fetch('iteration')
        # Progress bar
        #progress_counter(iteration, n_avg)
        # Plot data
        plt.cla()
        plt.plot(f_vec / u.MHz, counts / 1000 / (readout_len * 1e-9))
        plt.xlabel("Frequency [MHz]")
        plt.ylabel("Intensity [kcps]")
        plt.title("ODMR")
        
        plt.pause(0.1)
   