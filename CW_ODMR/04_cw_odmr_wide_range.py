"""
cw_odmr.py: Counts photons while sweeping the frequency of the applied MW.
"""
from qm import QuantumMachinesManager
from qm.qua import *
from qm import SimulationConfig
import matplotlib.pyplot as plt
from configuration import *

###################
# The QUA program #
###################

f_min = 50 * u.MHz  # start of freq sweep
f_max = 250 * u.MHz  # end of freq sweep
df = 2 * u.MHz  # freq step
frequencies = np.arange(f_min, f_max + 0.1, df)  # f_max + 0.1 so that f_max is included
n_avg = 1e6  # number of averages
m_avg = 1e2  # number of averages

f_min_external = 3e9 - f_min
f_max_external = 4e9 - f_max
df_external = f_max - f_min
freqs_external = np.arange(f_min_external, f_max_external + 0.1, df_external)
frequency = np.array(np.concatenate([frequencies + freqs_external[i] for i in range(len(freqs_external))]))

with program() as cw_odmr:
    times = declare(int, size=100)
    counts = declare(int)  # variable for number of counts
    counts_st = declare_stream()  # stream for counts
    for n in range(flattened):
        counts_st.append(declare_stream())
    f = declare(int)  # frequencies
    m = declare(int)  # number of iterations
    n = declare(int)  # number of iterations
    i = declare(int)  # number of iterations
    n_st = declare_stream()  # stream for number of iterations

    with for_(n, 0, n < n_avg, n + 1):
        with for_(i, 0, i < len(freqs_external) + 1, i + 1):
            pause()  # This waits until it is resumed from python
            with for_(m, 0, m < m_avg, m + 1):
                with for_(f, f_min, f <= f_max, f + df):  # Notice it's <= to include f_max (This is only for integers!)
                    update_frequency("NV", f)  # update frequency
                    align()  # align all elements
                    play("cw", "NV", duration=int(long_meas_len // 4))  # play microwave pulse
                    play("laser_ON", "AOM", duration=int(long_meas_len // 4))
                    measure("long_readout", "SPCM", None, time_tagging.analog(times, long_meas_len, counts))
                    # assign(counts, m)

                    save(counts, counts_st[i])
                                   
                    save(n, n_st)  # save number of iteration inside for_loop
                    
    with stream_processing():
        for j in range(flattened):
            counts_st[j].buffer(len(freqs_external), m_avg, len(frequencies)).map(FUNCTIONS.average(1)).average().save("counts")
        n_st.save("iteration")

#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(qop_ip, cluster_name=cluster_name)  # remove octave flag if not using it


def wait_until_job_is_paused(current_job):
    """
    Waits until the OPX FPGA reaches the pause statement.
    Used when the OPX sequence needs to be synchronized with an external parameter sweep.

    :param current_job: the job object.
    """
    while not current_job.is_paused():
        sleep(0.1)
        pass
    return True


simulate = False

if simulate:
    simulation_config = SimulationConfig(duration=28000)
    job = qmm.simulate(config, cw_odmr, simulation_config)
    job.get_simulated_samples().con1.plot()
else:
    qm = qmm.open_qm(config)

    job = qm.execute(cw_odmr)  # execute QUA program

    # Get results from QUA program
    res_handles = job.result_handles
    counts_handle = res_handles.get("counts")
    n_handle = res_handles.get("iteration")

    # Live plotting
    fig = plt.figure()
    interrupt_on_close(fig, job)  # Interrupts the job when closing the figure

    while res_handles.is_processing():
        for i in range(len(freqs_external)):  # Loop over the LO frequencies

            # Set the frequency of the LO source (if using an Octave)
            # qm.octave.set_lo_frequency('NV', freqs_external[i])  # change to the corresponding command relevant to LO used
            # qm.octave.set_element_parameters_from_calibration_db('NV', job)  # updates the calibration correction

            # to update the calibration matrix directly on the OPX use these lines:
            # insert suitable update_LO_frequency() function here
            # qm.set_output_dc_offset_by_element('NV', ('I', 'Q'), (-0.001, 0.003))
            # qm.set_mixer_correction('mixer_NV', int(NV_IF_freq), int(NV_LO_freq), IQ_imbalance(0.015, 0.01))

            # Resume the QUA program (escape the 'pause' statement). try to avoid crushing the console when closing the figure in the middle of a measurement
            try:
                job.resume()
                # Wait until the program reaches the 'pause' statement again, indicating that the QUA program is done
                wait_until_job_is_paused(job)
            except:
                break

        counts_handle.wait_for_values(1)
        n_handle.wait_for_values(1)

        # Fetch results
        counts = np.concatenate(counts_handle.fetch_all())
        iteration = n_handle.fetch_all()
        # Progress bar
        progress_counter(iteration, n_avg)
        # Plot data
        plt.cla()
        plt.plot(frequency / u.MHz, counts / 1000 / (long_meas_len * 1e-9))
        plt.xlabel("Frequency [MHz]")
        plt.ylabel("Intensity [kcps]")
        plt.title("ODMR")

        plt.pause(0.1)

