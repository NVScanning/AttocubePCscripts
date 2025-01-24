"""calling function libraries"""
import math

from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
from qm import SimulationConfig
from Configuration import *
import matplotlib.pyplot as plt

"""The QUA program"""
with program() as prog:
    with infinite_loop_():
        play('const','AOM') #play(waveform, element, duration), 'const' indicates 1 V.

    """defining a quantum machine"""
QMm = QuantumMachinesManager(host='192.168.88.10', port='80')


simulate = False
if simulate:

    simulate_config = SimulationConfig(
        duration=int(2000))  # simulation properties
    job = QMm.simulate(config, prog, simulate_config)  # do simulation
    """getting the simulated samples of the OPX output and plotting them"""
    samples = job.get_simulated_samples()
    samples.con1.plot()

else:
    QM1 = QMm.open_qm(config)  # calling the configuration file
    job = QM1.execute(prog)
