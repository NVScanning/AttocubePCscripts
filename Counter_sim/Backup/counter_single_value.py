from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
from qm import SimulationConfig
import matplotlib.pyplot as plt
from configuration import *
from qm import LoopbackInterface

###################
# The QUA program #
###################

total_integration_time = int(100 * u.ms)  # 100ms
single_integration_time_ns = int(500 * u.us)  # 500us
single_integration_time_cycles = single_integration_time_ns // 4
n_count = int(total_integration_time / single_integration_time_ns)


with program() as counter:
    times = declare(int, size=100)
    counts = declare(int)
    total_counts = declare(int)
    n = declare(int)
    m = declare(int)
    counts_st = declare_stream()
    with infinite_loop_():
        with for_(m, 0, m < 10, m + 1):
            play("gauss", "photon_source", condition= Random().rand_fixed() > 0.95)  # plays single_photon operation on qubit
            wait(100, "photon_source")  # qubit waits 4 clock cycles (16 ns)

    with infinite_loop_():
        with for_(n, 0, n < n_count, n + 1):
            measure("readout", "SPCM", None, time_tagging.analog(times, single_integration_time_ns, counts))
            assign(total_counts, total_counts + counts)
        save(total_counts, counts_st)
        assign(total_counts, 0)

    with stream_processing():
        counts_st.with_timestamps().save("counts")

#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host='192.168.88.10', port='80')



qm = qmm.open_qm(config)

job = qm.execute(counter)
# Get results from QUA program
res_handles = job.result_handles
counts_handle = res_handles.get("counts")
counts_handle.wait_for_values(1)
time = []
counts = []

new_counts = counts_handle.fetch("counts")
print(new_counts)