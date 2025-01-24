# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 15:00:59 2025

@author: attocube
"""

import numpy as np
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
import time
from configuration_octave_scan import *


steps = 50
delta_fast = 0.08e-6
velocity = 0.615e-6

data_dict = {}
single_integration_time_ns = long_meas_len_1
# Calculate how many data points per pixel
time_per_pixel = delta_fast / velocity  # in seconds
n_data_points_per_pixel = int(time_per_pixel / 5.225e-6) 
   
print(f"single_int_time {single_integration_time_ns / 1e9}")
print(f'Number of data points per pixel: {n_data_points_per_pixel}')
print(f'Number of pixels: {steps}')

qmm = QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name, octave=octave_config)

with program() as counter:
    times = declare(int, size=16000)
    counts = declare(int)
    k = declare(int)
    l = declare(int)
    counts_st = declare_stream()

    with for_(l, 0, l < steps, l + 1):
            
        pause()
        with for_(k, 0, k < n_data_points_per_pixel*steps, k + 1):
            measure("long_readout", "SPCM1", None, time_tagging.analog(times, single_integration_time_ns, counts))
            save(counts, counts_st)

    with stream_processing():
        counts_st.buffer(n_data_points_per_pixel).map(FUNCTIONS.average()).buffer(steps).save_all("counts")

qm = qmm.open_qm(config)
job = qm.execute(counter)


def get_data(line_index):
    try:
        job.resume()
            # Wait until the program reaches the 'pause' statement again, indicating that the QUA program is done
        while not job.is_paused() and job.status == 'running':
            #print('job running (get_data)')
            job_done = False
            time.sleep(0.1)
        
        print(f'job paused: {job.is_paused()}, job status: {job.status}')
        job_done = True
        print('job finished running')
    
    except:
        pass
    
    res_handles = job.result_handles
    counts_handle = res_handles.get("counts")
        
        
    counts_handle.wait_for_values(1)
    
    new_counts = counts_handle.fetch_all() #add something to check size of fetched array
    
    while np.shape(new_counts)[0] != line_index + 1:
        print('waiting for counts')
        time.sleep(0.1)
        new_counts = counts_handle.fetch_all()
    
    counts = (new_counts["value"] / (single_integration_time_ns / 1e9)) / 1000

    timestamp = 0 #new_counts["timestamp"]/1E9  # Convert timestamps to seconds
  

    data_dict.update({
        'counts': counts,
        'timestamp': timestamp,
        'freq_center': 0,
        'fwhm': 0,
        'contrast': 0,
        'sensitivity': 0
    })
    return data_dict

counts_arr = []
for i in range(steps): 
    print(f'Before line {i}')
    data_dict = get_data(i)  #Dictionary contains 'counts [kc/s]'
    counts = data_dict.get('counts')
    rowsmeasured = np.shape(counts)[0]
    
    counts_arr.append(counts[i,:])
    print(f'After line {i}')

