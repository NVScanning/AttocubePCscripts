"""
        RABI CHEVRON (MW DURATION VS FREQUENCY)
        
This sequence involves applying microwave (MW) pulses to the NV center with varying durations and intermediate frequencies,
while measuring the photoluminescence (PL) signal using the SPCM detector.
By sweeping both the MW pulse duration and the MW frequency, we obtain a 2D map (chevron pattern) showing how the NV spin
responds to the applied MW field.

Analyzing the chevron pattern allows us to:
    - Accurately determine the NV resonance frequency.
    - Estimate the optimal π-pulse duration for the selected MW amplitude.

Prerequisites:
    - Measurement of the NV ODMR spectrum to find the approximate resonance frequency (ODMR spectroscopy).
    - Calibration of the IQ mixer or MW source connected to the NV MW line.
    - Selection of the desired π-pulse amplitude (labeled as "mw_amp_NV") in the configuration.
    - Setting the NV intermediate frequency (

"""



##################
#   Parameters   #
##################
# Parameters Definition
from qm import QuantumMachinesManager
from qm.qua import *
import matplotlib.pyplot as plt
from configuration_with_octave_Last import *
from qualang_tools.results import fetching_tool, progress_counter
from qualang_tools.plot import interrupt_on_close
import numpy as np

##################
#   Parameters   #
##################
n_avg =5_000  # Number of averages
# Frequency sweep parameters
span = 3 * u.MHz  # You can adjust wider/narrower
df = 0.1 * u.MHz
dfs = np.arange(-span, span + df, df)

# Pulse duration sweep
t_min = 4
t_max = 800
dt = 4
durations = np.arange(t_min, t_max, dt)

###################
# The QUA program #
###################
with program() as rabi_chevron:
    n = declare(int)
    f = declare(int)  # Frequency sweep variable
    t = declare(int)  # Pulse duration sweep variable
    counts = declare(int)
    counts_st = declare_stream()
    n_st = declare_stream()
    times = declare(int, size=100)

    # Initialization (spin polarization)
    play("laser_ON", "AOM1")
    wait(wait_for_initialization * u.ns, "AOM1")

    with for_(n, 0, n < n_avg, n + 1):
        with for_(*from_array(t, durations)):
            with for_(*from_array(f, dfs)):
                # Update MW frequency
                update_frequency("NV", NV_IF_freq + f)
                # MW pulse with varying duration
                play("x180" * amp(0.25), "NV", duration=t)
                align()
                play("laser_ON", "AOM1")
                # Photon detection
                measure("readout", "SPCM1", None, time_tagging.analog(times, meas_len_1, counts))
                save(counts, counts_st)
                wait(wait_after_measure)
        save(n, n_st)

    with stream_processing():
        counts_st.buffer(len(dfs)).buffer(len(durations)).average().save("counts")
        n_st.save("iteration")

#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name, octave=octave_config)

#######################
# Run the QUA program  #
#######################
simulate = False

if simulate:
    simulation_config = SimulationConfig(duration=10_000)  # Clock cycles
    job = qmm.simulate(config, rabi_chevron, simulation_config)
    job.get_simulated_samples().con1.plot()
else:
    qm = qmm.open_qm(config)
    job = qm.execute(rabi_chevron)
    results = fetching_tool(job, data_list=["counts", "iteration"], mode="live")
    fig = plt.figure()
    interrupt_on_close(fig, job)

    #######################
    # Live Plotting
    #######################
    while results.is_processing():
        counts_data, iteration = results.fetch_all()
        progress_counter(iteration, n_avg, start_time=results.get_start_time())

        plt.clf()
        plt.title("NV Rabi Chevron")
        plt.pcolor(dfs / u.MHz, durations * 4, counts_data / 1000)  # kcps
        plt.xlabel("Frequency Detuning [MHz]")
        plt.ylabel("MW Pulse Duration [ns]")
        plt.colorbar(label="Photon Counts [kcps]")
        plt.tight_layout()
        plt.pause(0.1)

