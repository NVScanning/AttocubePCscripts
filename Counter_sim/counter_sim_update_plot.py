import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
from qm import SimulationConfig
from configuration import *
from qm import LoopbackInterface

###################
# The QUA program #
###################

total_integration_time = int(100 * u.ms)  # 100ms
single_integration_time_ns = int(50 * u.us)  # 50us
single_integration_time_cycles = single_integration_time_ns // 4
n_count = int(total_integration_time / single_integration_time_ns)

simulate = False

if simulate:
    n_count = 20
    single_integration_time_ns = 5000

with program() as counter:
    times = declare(int, size=10000)
    counts = declare(int)
    total_counts = declare(int)
    n = declare(int)
    m = declare(int)
    counts_st = declare_stream()
    with infinite_loop_():
        play('ON', 'digital1')
    with infinite_loop_():
        with for_(m, 0, m < 10, m + 1):
            play("gauss", "photon_source", condition=Random().rand_fixed() > 0.95)
            wait(100, "photon_source")

    with infinite_loop_():
        with for_(n, 0, n < n_count, n + 1):
            measure("readout", "SPCM", None, time_tagging.analog(times, single_integration_time_ns, counts))
            assign(total_counts, total_counts + counts)
        save(total_counts, counts_st)
        assign(total_counts, 0)

    with stream_processing():
        if simulate:
            counts_st.save_all("counts")
        else:
            counts_st.with_timestamps().save("counts")

#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host='192.168.88.10', port='80', log_level='DEBUG')

if simulate:
    simulate_config = SimulationConfig(
        duration=int(20000),
        simulation_interface=LoopbackInterface(
            ([("con1", 1, "con1", 1)])
        ),
    )
    job_sim = qmm.simulate(config, counter, simulate_config)
    job_sim.get_simulated_samples().con1.plot()
    res_handle = job_sim.result_handles
    res_handle.wait_for_all_values()
    counts = res_handle.get("counts").fetch_all().tolist()
    plt.figure()
    plt.plot(counts)

else:
    qm = qmm.open_qm(config)

    job = qm.execute(counter)
    res_handles = job.result_handles
    counts_handle = res_handles.get("counts")
    counts_handle.wait_for_values(1)

    # Tkinter root window
    root = tk.Tk()
    root.title("Real-time Counter Plot")

    fig, ax = plt.subplots()
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    time = []
    counts = []

    def update_plot():
        global time, counts
        if res_handles.is_processing():
            new_counts = counts_handle.fetch_all()
            counts.append((new_counts["value"] / (total_integration_time / 1000000000)) / 1000)
            time.append(new_counts["timestamp"] / u.s)
            ax.cla()
            if len(time) > 300:
                ax.plot(time[-300:], counts[-300:])
            else:
                ax.plot(time, counts)
            ax.set_xlabel("time [s]")
            ax.set_ylabel("counts [kcps]")
            ax.set_title("Counter")
            canvas.draw()
        root.after(100, update_plot)  # Update the plot every 100 ms

    root.after(100, update_plot)  # Start updating the plot
    root.mainloop()
