# pl_module.py
import numpy as np
from transitions import Machine
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
import time
from configuration_octave_scan import *

import threading
from threading import Lock
data_lock = Lock()

class PLModuleLinescan:
    
    states = ['disconnected', 'connected', 'job_started', 'fetching','get_data']

    def __init__(self):
        self.data_dict = {}
        self.single_integration_time_ns = long_meas_len_1  # 1 ms in ns
        print(self.single_integration_time_ns)
        self.qmm = None
        self.qm = None
        self.job = None
        self.counts_handle = None
        self.data_lock = Lock()  # Initialize a lock for data_dict
        # Initialize the state machine
        self.machine = Machine(model=self, states=PLModuleLinescan.states, initial='disconnected')
        
        self.slow_steps=None
        self.fast_steps=None
        self.total_integration_time = None
        self.n_data_points_per_pixel = None 
        self.job_done = False
        self.z_control = None
        self.scannerpos = None
        self.z_out_list = []
        self.pos_list = []


        # Add transitions
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
        
        with program() as counter:
            times = declare(int, size=16000)
            counts = declare(int)
            k = declare(int)
            l = declare(int)
            counts_st = declare_stream()

            with for_(l, 0, l < self.slow_steps, l + 1):
                    
                pause()
                
                with for_(k, 0, k < self.n_data_points_per_pixel*self.fast_steps, k + 1):
                    measure("long_readout", "SPCM1", None, time_tagging.analog(times, self.single_integration_time_ns, counts))
                    save(counts, counts_st)

            with stream_processing():
                counts_st.buffer(self.n_data_points_per_pixel).map(FUNCTIONS.average()).buffer(self.fast_steps).save_all("counts")

        self.job = self.qm.execute(counter)
        print("Job started.")

    def on_start_fetching(self):
        print("Started fetching data.")
        # res_handles = self.job.result_handles
        # self.counts_handle = res_handles.get("counts")
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


        

    def get_data(self, line_index):
        
        try:
            self.job.resume()
                # Wait until the program reaches the 'pause' statement again, indicating that the QUA program is done
                
            sleep_time = 0.0005

            while not self.job.is_paused() and self.job.status == 'running':
                #print('job running (get_data)')
                z_out = self.z_control.getPositionZ()
                self.z_out_list.append(z_out)
                pos_out = self.scannerpos.getPositionsXYRel()
                self.pos_list.append(pos_out)
                self.job_done = False
                time.sleep(sleep_time)
                
            print(f'job paused: {self.job.is_paused()}, job status: {self.job.status}')
            self.job_done = True
            print('job finished running')
            print(z_out_list)
            print(pos_list)
            
        
        except:
            pass
        
        if line_index == 0:
            res_handles = self.job.result_handles
            self.counts_handle = res_handles.get("counts")
            
            
        self.counts_handle.wait_for_values(1)
        
        new_counts = self.counts_handle.fetch_all() #add something to check size of fetched array
        
        while np.shape(new_counts)[0] != line_index + 1:
            print('waiting for counts')
            time.sleep(0.1)
            new_counts = self.counts_handle.fetch_all()
        
        counts = (new_counts["value"] / (self.single_integration_time_ns / 1e9)) / 1000
    
        timestamp = 0 #new_counts["timestamp"]/1E9  # Convert timestamps to seconds
      

        self.data_dict.update({
            'counts [kc/s]': counts,
            'timestamp': timestamp,
            'AFM height [um]': None,
            'freq_center': None,
            'fwhm': None,
            'contrast': None,
            'sensitivity': None
        })
  
    


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




