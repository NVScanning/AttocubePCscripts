# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 13:35:33 2025

@author: attocube
"""

from qm import QuantumMachinesManager
from qm.qua import *
from qm import SimulationConfig
import matplotlib.pyplot as plt
from configuration_with_octave_Last import *
import numpy as np
import time


###################
# The QUA program #
###################

readout_len = long_meas_len_1  # Readout duration for this experiment

with program() as cw_odmr:
    update_frequency("NV", 50*u.MHz)
    
    with infinite_loop_():
        play('cw'*amp(1), 'NV',duration=readout_len * u.ns)


#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name, octave=octave_config)

#######################
# Simulate or execute #
#######################

# Open the quantum machine
qm = qmm.open_qm(config)
# Send the QUA program to the OPX, which compiles and executes it
job = qm.execute(cw_odmr)

time.sleep(5)  # The program will run for 30 seconds
job.halt()

qm.octave.set_rf_output_mode("NV", RFOutputMode.off)