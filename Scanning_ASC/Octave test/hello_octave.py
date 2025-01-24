"""
hello_octave.py: template for basic usage of octave
"""

from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
from set_octave import *
from configuration import *
from qm import SimulationConfig
import time

qop_ip = "192.168.88.10"
cluster_name = "my_cluster"
opx_port = None
octave_ip = "192.168.88.50"

octave_port = 80  # Must be 11xxx, where xxx are the last three digits of the Octave IP address
con = "con1"
octave = "octave1"

# Create the octave config object
octave_config = QmOctaveConfig()
# Specify where to store the outcome of the calibration (correction matrix, offsets...)
octave_config.set_calibration_db(os.getcwd())
# Add an Octave called 'octave1' with the specified IP and port
octave_config.add_device_info(octave, octave_ip, octave_port)

qmm = QuantumMachinesManager(host=qop_ip, port=opx_port, cluster_name=cluster_name, octave=octave_config)

###################
# The QUA program #
###################
with program() as hello_octave:
    with infinite_loop_():
        play('cw', 'qe1')

simulate = False
if simulate:
    simulation_config = SimulationConfig(duration=400)  # in clock cycles
    job_sim = qmm.simulate(config, hello_octave, simulation_config)
    # Simulate blocks python until the simulation is done
    job_sim.get_simulated_samples().con1.plot()
else:
    qm = qmm.open_qm(config)
    job = qm.execute(hello_octave)
    # Execute does not block python! As this is an infinite loop, the job would run forever. In this case, we've put a 10
    # seconds sleep and then halted the job.
    time.sleep(10)
    job.halt()

