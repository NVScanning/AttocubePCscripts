# pl_module.py
import numpy as np
from transitions import Machine
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
import time
#from configuration_octave_scan import *
from configuration_with_octave_Last import *

import threading
from threading import Lock
data_lock = Lock()

class PLModule:
    
    states = ['disconnected', 'connected', 'job_started', 'fetching','get_data']

    def __init__(self):
        self.data_dict = {}
        self.single_integration_time_ns = meas_len_1  # 1 ms in ns
        print(self.single_integration_time_ns)
        self.qmm = None
        self.qm = None
        self.job = None
        self.counts_handle = None
        self.data_lock = Lock()  # Initialize a lock for data_dict
        # Initialize the state machine
        self.machine = Machine(model=self, states=PLModule.states, initial='disconnected')
        
        self.slow_steps=None
        self.fast_steps=None
        self.total_integration_time = None
        
        self.z_control = None
        self.scannerpos = None

        # Add transitions
        self.machine.add_transition(trigger='connect', source='disconnected', dest='connected', after='on_connect')
        self.machine.add_transition(trigger='start_job', source='connected', dest='job_started', after='on_start_job')
        self.machine.add_transition(trigger='start_fetching', source='job_started', dest='fetching', after='on_start_fetching')
        self.machine.add_transition(trigger='start_getting_data', source='fetching', dest='get_data', after='on_get_data')
        self.machine.add_transition(trigger='finish_getting_data', source='get_data', dest='connected')
        self.machine.add_transition(trigger='stop_fetching', source='fetching', dest='connected', after='on_stop_fetching')
        self.machine.add_transition(trigger='stop_job', source='job_started', dest='connected', after='on_stop_job')
        self.machine.add_transition(trigger='disconnect', source=['connected', 'job_started', 'fetching','get_data'], dest='disconnected', after='on_disconnect')
    def on_connect(self):
        self.qmm = QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name, octave=octave_config)
        self.qm = self.qmm.open_qm(config)
        print("Connected to Quantum Machine Manager.")

    def on_start_job(self):
        #number of iterations for total measurement time
        n_iterations = int(self.total_integration_time / self.single_integration_time_ns)
        
        with program() as counter:
            times = declare(int, size=16000)
            counts = declare(int)
            total_counts = declare(int)
            counts_st = declare_stream()
            n = declare(int)

            with infinite_loop_():
                
                with for_(n, 0, n < n_iterations, n + 1):
                    
                    play("laser_ON", "AOM1", duration=self.single_integration_time_ns)
                    
                    measure("readout", "SPCM1", None, time_tagging.analog(times, self.single_integration_time_ns, counts))
                    # Add the counts
                    assign(total_counts, total_counts + counts)
                    
                # Save the counts and set to zero
                save(total_counts, counts_st)
                assign(total_counts, 0)

            with stream_processing():
                counts_st.with_timestamps().save("counts")

        self.job = self.qm.execute(counter)
        print("Job started.")

    def on_start_fetching(self):
        print("Started fetching data.")
        res_handles = self.job.result_handles
        self.counts_handle = res_handles.get("counts")
        #self.counts_handle.wait_for_values(1)
        #self.start_getting_data()  # Trigger the state transition to `get_data`
        
    def on_get_data(self):
        print("Fetching data...")
        threading.Thread(target=self.get_data, daemon=True).start()

    def on_stop_fetching(self):
        # self.stop_fetching_flag.set()
        print("Stopped fetching data.")

    def on_stop_job(self):
        if self.job:
            
            self.job.halt()  # Assuming this is the method to stop the job

        print("Job stopped.")

    def on_disconnect(self):
        if self.qmm:
            self.qmm.close_all_quantum_machines()
        self.qmm = None
        self.qm = None
        self.job = None
        self.counts_handle = None
        print("Disconnected from Quantum Machine Manager.")


        

    def get_data(self, f_idx):
        #print(f'f_idx: {f_idx}')

        self.counts_handle.wait_for_values(1)
        new_counts = self.counts_handle.fetch_all()
        
        counts = (new_counts["value"] / (self.total_integration_time / 1E9)) / 1000
    
        timestamp = new_counts["timestamp"]/1E9  # Convert timestamps to seconds
        z_out = self.z_control.getPositionZ()
        pos_out = self.scannerpos.getPositionsXYRel()

        self.data_dict.update({
            'x [um]': pos_out[0]*1E6,
            'y [um]': pos_out[1]*1E6,
            'AFM height [um]': z_out*1E6,
            'counts [kc/s]': counts,
            'timestamp': timestamp,
        })
        #print('end get_data')
    


    def cleanup(self):
        try:
            if self.state == 'fetching':
                self.stop_fetching()
            if self.state == 'get_data':
                self.finish_getting_data()
            if self.state == 'job_started':
                self.stop_job()
            if self.state == 'connected':
                self.disconnect()
            elif self.state == 'disconnected':
                print("Already disconnected.")
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            print("Cleaned up ODMRModule state.")

    @staticmethod
    def twoD_Gaussian(coords, mu_x, mu_y, sigma_x, sigma_y, rho):
        x, y = coords
        norm_factor = 1 / (2 * np.pi * sigma_x * sigma_y * np.sqrt(1 - rho**2))
        exponent = - (1 / (2 * (1 - rho**2))) * (
            ((x - mu_x)**2 / sigma_x**2) +
            ((y - mu_y)**2 / sigma_y**2) -
            (2 * rho * (x - mu_x) * (y - mu_y) / (sigma_x * sigma_y))
        )
        return norm_factor * np.exp(exponent).ravel()




