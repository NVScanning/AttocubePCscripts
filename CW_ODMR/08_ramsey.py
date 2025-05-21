"""
       RAMSEY MEASUREMENT (T2*)
The program consists in playing two Ramsey sequence successively (first ending with x90 and then with -x90)
and measure the photon counts received by the SPCM across varying idle times.
The sequence is repeated without playing the mw pulses to measure the dark counts on the SPCM.

The data is then post-processed to determine the dephasing time T2*.

Prerequisites:
    - Ensure calibration of the different delays in the system (calibrate_delays).
    - Having updated the different delays in the configuration.
    - Having updated the NV frequency, labeled as "NV_IF_freq", in the configuration.
    - Having set the pi pulse amplitude and duration in the configuration

Next steps before going to the next node:
    -
"""

from qm import QuantumMachinesManager
from qm.qua import *
from qm import SimulationConfig
import matplotlib.pyplot as plt
from configuration_with_octave_Last import *
from qualang_tools.loops import from_array
#from qualang_tools.results.data_handler import DataHandler

##################
#   Parameters   #
##################
# Parameters Definition
t_vec = np.arange(4, 250, 10)  # The time vector for varying the idle time in clock cycles (4ns)
n_avg = 1_000_000  # The number of averaging iterations

# Detuning in rad/sec (example: 2 MHz detuning)
detuning = 2e6   

# Tau sweep range (clock cycles, 4ns steps)
taus = np.arange(4, 500, 1)  # Change as needed

# Data to save
save_data_dict = {
    "n_avg": n_avg,
    "t_vec": t_vec,
    "config": config,
}

# ###################
# # The QUA program #
# ###################
with program() as ramsey:
    counts1 = declare(int)
    counts2 = declare(int)
    counts_dark = declare(int)
    times1 = declare(int, size=100)
    times2 = declare(int, size=100)
    times_dark = declare(int, size=100)
    counts_1_st = declare_stream()
    counts_2_st = declare_stream()
    counts_dark_st = declare_stream()
    tau = declare(int)
    phase = declare(fixed)
    n = declare(int)
    n_st = declare_stream()

    # Static Spin Initialization
    play("laser_ON", "AOM1")
    wait(wait_for_initialization * u.ns, "AOM1")
    
    with for_(n, 0, n < n_avg, n + 1):
        with for_(*from_array(tau, taus)):
            # --- Phase Calculation for Virtual Z-Rotation ---
            assign(phase, Cast.mul_fixed_by_int(detuning * 1e-9, 4 * tau))

            # === First Ramsey: x90 → idle → x90 ===
            with strict_timing_():
                play("x90" * amp(0.2), "NV")
                wait(tau, "NV")
                frame_rotation_2pi(phase, "NV")
                play("x90" * amp(0.2), "NV")
            align()
            play("laser_ON", "AOM1")
            measure("readout", "SPCM1", None, time_tagging.analog(times1, meas_len_1, counts1))
            save(counts1, counts_1_st)
            reset_frame("NV")  # === Reset Frame ===
            wait(wait_between_runs * u.ns, "AOM1")

            # === Second Ramsey: x90 → idle → -x90 ===
            align()
            with strict_timing_():
                play("x90" * amp(0.2), "NV")
                wait(tau, "NV")
                frame_rotation_2pi(phase, "NV")
                play("-x90" * amp(0.2), "NV")
            align()
            play("laser_ON", "AOM1")
            measure("readout", "SPCM1", None, time_tagging.analog(times2, meas_len_1, counts2))
            save(counts2, counts_2_st)
            reset_frame("NV")  # === Reset Frame ===
            wait(wait_between_runs * u.ns, "AOM1")

            # === Dark Counts ===
            align()
            play("x90" * amp(0), "NV")
            wait(tau, "NV")
            frame_rotation_2pi(phase, "NV")
            play("-x90" * amp(0), "NV")
            align()
            play("laser_ON", "AOM1")
            measure("readout", "SPCM1", None, time_tagging.analog(times_dark, meas_len_1, counts_dark))
            save(counts_dark, counts_dark_st)
            reset_frame("NV")  # === Reset Frame ===
            wait(wait_between_runs * u.ns, "AOM1")

           

        save(n, n_st)

    # === Stream Processing ===
    with stream_processing():
        counts_1_st.buffer(len(taus)).average().save("counts1")
        counts_2_st.buffer(len(taus)).average().save("counts2")
        counts_dark_st.buffer(len(taus)).average().save("counts_dark")
        n_st.save("iteration")


    
    

#     # Ramsey sequence
#     with for_(n, 0, n < n_avg, n + 1):
#         with for_(*from_array(t, t_vec)):
#             # First Ramsey sequence with x90 - idle time - x90
#             play("x90" * amp(0.4), "NV")  # Pi/2 pulse to qubit
#             wait(t, "NV")  # Variable idle time
#             play("x90" * amp(0.4), "NV")  # Pi/2 pulse to qubit
#             align()  # Play the laser pulse after the Ramsey sequence
#             # Measure and detect the photons on SPCM1
#             play("laser_ON", "AOM1")
#             measure("readout", "SPCM1", None, time_tagging.analog(times1, meas_len_1, counts1))
#             save(counts1, counts_1_st)  # save counts
#             wait(wait_between_runs * u.ns, "AOM1")

#             align()
#             # Second Ramsey sequence with x90 - idle time - -x90
#             play("x90" * amp(0.4), "NV")  # Pi/2 pulse to qubit
#             wait(t, "NV")  # variable delay in spin Echo
#             play("-x90" * amp(0.4), "NV")  # Pi/2 pulse to qubit
#             align()  # Play the laser pulse after the Ramsey sequence
#             # Measure and detect the photons on SPCM1
#             play("laser_ON", "AOM1")
#             measure("readout", "SPCM1", None, time_tagging.analog(times2, meas_len_1, counts2))
#             save(counts2, counts_2_st)  # save counts
#             wait(wait_between_runs * u.ns, "AOM1")

#             align()
#             # Third Ramsey sequence for measuring the dark counts
#             play("x90" * amp(0), "NV")  # Pi/2 pulse to qubit
#             wait(t, "NV")  # variable delay in spin Echo
#             play("-x90" * amp(0), "NV")  # Pi/2 pulse to qubit
#             align()  # Play the laser pulse after the Ramsey sequence
#             # Measure and detect the dark counts on SPCM1
#             play("laser_ON", "AOM1")
#             measure("readout", "SPCM1", None, time_tagging.analog(times_dark, meas_len_1, counts_dark))
#             save(counts_dark, counts_dark_st)  # save counts
#             wait(wait_between_runs * u.ns, "AOM1")

#         save(n, n_st)  # save number of iteration inside for_loop

#     with stream_processing():
#         # Cast the data into a 1D vector, average the 1D vectors together and store the results on the OPX processor
#         counts_1_st.buffer(len(t_vec)).average().save("counts1")
#         counts_2_st.buffer(len(t_vec)).average().save("counts2")
#         counts_dark_st.buffer(len(t_vec)).average().save("counts_dark")
#         n_st.save("iteration")





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
    # Simulate blocks python until the simulation is done
    job = qmm.simulate(config, ramsey, simulation_config)
    # Get the simulated samples
    samples = job.get_simulated_samples()
    # Plot the simulated samples
    samples.con1.plot()
    # Get the waveform report object
    waveform_report = job.get_simulated_waveform_report()
    # Cast the waveform report to a python dictionary
    waveform_dict = waveform_report.to_dict()
    # Visualize and save the waveform report
    waveform_report.create_plot(samples, plot=True, save_path=str(Path(__file__).resolve()))
else:
    # Open the quantum machine
    qm = qmm.open_qm(config)
    # Send the QUA program to the OPX, which compiles and executes it
    job = qm.execute(ramsey)
    # Get results from QUA program
    results = fetching_tool(job, data_list=["counts1", "counts2", "counts_dark", "iteration"], mode="live")
    # Live plotting
    fig = plt.figure()
    interrupt_on_close(fig, job)  # Interrupts the job when closing the figure

    while results.is_processing():
        # Fetch results
        counts1, counts2, counts_dark, iteration = results.fetch_all()
        # Progress bar
        progress_counter(iteration, n_avg, start_time=results.get_start_time())
        # Plot data
        plt.cla()
        # # plt.plot(4 * t_vec, counts1 / 1000 / (meas_len_1 / u.s), label="x90_idle_x90")
        # plt.plot(4 * taus, counts1 / 1000 / (meas_len_1 / u.s), label="x90_idle_x90")

        # # plt.plot(4 * t_vec, counts2 / 1000 / (meas_len_1 / u.s), label="x90_idle_-x90")
        # plt.plot(4 * taus, counts2 / 1000 / (meas_len_1 / u.s), label="x90_idle_-x90")
        
        plt.plot(4 * taus, (counts1 - counts2) / 1000 / (meas_len_1 / u.s), label="Difference: x90_x90 - x90_-x90")


        # plt.plot(4 * t_vec, counts_dark / 1000 / (meas_len_1 / u.s), label="dark counts")
        plt.plot(4 * taus, counts_dark / 1000 / (meas_len_1 / u.s), label="dark counts")

        plt.xlabel("Ramsey idle time [ns]")
        plt.ylabel("Intensity [kcps]")
        plt.title("Ramsey")
        plt.legend()
        plt.pause(0.1)
    # Save results
    # script_name = Path(__file__).name
    # data_handler = DataHandler(root_data_folder=save_dir)
    # save_data_dict.update({"counts1_data": counts1})
    # save_data_dict.update({"counts2_data": counts2})
    # save_data_dict.update({"counts_dark_data": counts_dark})
    # save_data_dict.update({"fig_live": fig})
    # data_handler.additional_files = {script_name: script_name, **default_additional_files}
    # data_handler.save_data(data=save_data_dict, name="_".join(script_name.split("_")[1:]).split(".")[0])
