from qm import QuantumMachinesManager
from qm.qua import *
import matplotlib.pyplot as plt
import numpy as np
from configuration_with_octave_Last import *
import os
import time as time_module

##################
# Parameters
##################

f_vec = np.arange(65 * u.MHz, 75 * u.MHz, 0.25 * u.MHz)  # Sweep narrower range
mw_amp = 0.1 # Start lower, adjust

# Parameters Definition
init_laser_len = 5000*u.ns  # laser duration length [ns]
mw_len =164 # ns, short MW pulse x4 clock cycles 
readout_laser_len = 600 * u.ns  # Short readout for best contrast

wait_between_runs = 50_000  # [ns]
n_avg = 50_000

###################
# The QUA program #
###################

with program() as pulsed_odmr:
    times = declare(int, size=100)
    counts = declare(int)
    counts_dark = declare(int)
    counts_st = declare_stream()
    counts_dark_st = declare_stream()
    f = declare(int)
    n = declare(int)
    n_st = declare_stream()

    with for_(n, 0, n < n_avg, n + 1):
        with for_(*from_array(f, f_vec)):

            update_frequency("NV", f)

            # Spin Initialization Laser Pulse
            play("laser_ON", "AOM1", duration=init_laser_len)
            wait(wait_for_initialization, "AOM1")

            # MW pulse - short
            play("x180" * amp(mw_amp), "NV", duration=mw_len)

            align()

            # Laser Readout Pulse
            play("laser_ON", "AOM1", duration=init_laser_len)
            measure("readout", "SPCM1", None, time_tagging.analog(times, readout_laser_len, counts))
            save(counts, counts_st)

            wait(wait_between_runs * u.ns)

            # --- Dark Counts
            align()
            play("laser_ON", "AOM1")
            wait(wait_for_initialization, "AOM1")
            play("x180" * amp(0), "NV", duration=mw_len)
            align()
            play("laser_ON", "AOM1")
            measure("readout", "SPCM1", None, time_tagging.analog(times, readout_laser_len, counts_dark))
            save(counts_dark, counts_dark_st)

            wait(wait_between_runs * u.ns)

        save(n, n_st)

    with stream_processing():
        counts_st.buffer(len(f_vec)).average().save("counts")
        counts_dark_st.buffer(len(f_vec)).average().save("counts_dark")
        n_st.save("iteration")

##################################
# Communication with OPX
##################################

qmm = QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name, octave=octave_config)

######################
# Execute
######################

qm = qmm.open_qm(config)
job = qm.execute(pulsed_odmr)
results = fetching_tool(job, data_list=["counts", "counts_dark", "iteration"], mode="live")

fig, ax = plt.subplots()
interrupt_on_close(fig, job)

while results.is_processing():
    counts, counts_dark, iteration = results.fetch_all()

    ax.cla()
    ax.plot((NV_LO_freq * 0 + f_vec) / u.MHz, counts / 1000 / (readout_laser_len / u.s), 'o', label="Photon counts")
    ax.plot((NV_LO_freq * 0 + f_vec) / u.MHz, counts_dark / 1000 / (readout_laser_len / u.s), label="Dark counts")
    ax.set_xlabel("MW Frequency [MHz]")
    ax.set_ylabel("Intensity [kcps]")
    ax.set_title(f"Pulsed ODMR - Iteration {iteration}")
    ax.legend()
    plt.pause(0.1)

########################
# Afterward:
########################

# Find frequency dip
# Update NV_IF_freq
# Use same mw_amp and mw_len in Rabi!
