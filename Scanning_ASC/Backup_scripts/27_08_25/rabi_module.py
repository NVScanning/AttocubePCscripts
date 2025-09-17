import numpy as np
from scipy.optimize import curve_fit
from transitions import Machine
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
import time
from configuration_with_octave_Last import *

import threading
from threading import Lock
data_lock = Lock()

class RabiModule:
    states = ['disconnected', 'connected', 'job_started', 'fetching']

    def __init__(self):
        self.qmm = None
        self.qm = None
        self.job = None
        self.rabi_params = None
        self.readout_len = long_meas_len_1
        self.res_handles = None
        self.counts_handle = None
        self.flattened = None
        self.counts_sum = []
        self.fitted_y_data = []
        self.y_data = []
        self.x_data = []
        self.data_dict = {}
        self.stop_fetching_flag = threading.Event()
        self.lock = threading.Lock()
        self.job_start_time = None

        self.slow_steps = None
        self.fast_steps = None
        self.z_control = None
        self.scannerpos = None
        self.app = None

        self.machine = Machine(model=self, states=RabiModule.states, initial='disconnected')
        self.machine.add_transition(trigger='connect', source='disconnected', dest='connected', after='on_connect')
        self.machine.add_transition(trigger='start_job', source='connected', dest='job_started', after='on_start_job')
        self.machine.add_transition(trigger='start_fetching', source='job_started', dest='fetching', after='on_start_fetching')
        self.machine.add_transition(trigger='stop_fetching', source='fetching', dest='connected', after='on_stop_fetching')
        self.machine.add_transition(trigger='stop_job', source='job_started', dest='connected', after='on_stop_job')
        self.machine.add_transition(trigger='disconnect', source=['connected', 'job_started', 'fetching'], dest='disconnected', after='on_disconnect')

    def on_connect(self):
        self.qmm = QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name, octave=octave_config)
        self.qm = self.qmm.open_qm(config)

    def on_start_job(self):
        if not self.rabi_params:
            raise ValueError("Rabi parameters not set.")

        Typ_gain = 42
        rf_freq = self.rabi_params["rf_freq"] * u.MHz
        f_IF = (rf_freq - NV_LO_freq) / u.MHz
        print(f'IF is : {f_IF}')
        rf_power_dbm = self.rabi_params["rf_power"] - Typ_gain
        rf_power_watt = 10 ** ((rf_power_dbm - 30) / 10)
        R = 50
        Vrms = (rf_power_watt * R) ** 0.5 / 2
        amp_val = Vrms * 2 ** 0.5
        print(f'amp_value: {amp_val}')

        t_min = 0
        t_step = int(self.rabi_params["pulse_spacing"])  # e.g. 4 ns
        n_points = int(self.rabi_params["n_pulses"])     # e.g. 150
        t_max =  t_step * n_points
        self.N_average = self.rabi_params["N_average"]
        flattened = self.slow_steps*self.fast_steps

        t_step = int(self.rabi_params["pulse_spacing"])
        self.t_vec = np.arange(self.rabi_params["n_pulses"], dtype=int) * t_step


        self.x_data = self.t_vec
        self.y_data = np.zeros_like(self.x_data)
        self.fitted_y_data = np.zeros_like(self.x_data)

        with program() as rabi:
            t = declare(int)
            i = declare(int)  
            m = declare(int)
            times = declare(int, size=100)  # QUA vector for storing the time-tags
            m_avg = self.N_average
            counts = declare(int)
            counts_dark = declare(int)
            counts_st = declare_stream()
            counts_dark_st = declare_stream()
            
            update_frequency("NV", f_IF * u.MHz)
            
            with for_(i, 0, i < flattened + 1, i + 1):
                
                pause()
                
    
                with for_(m, 0, m < m_avg, m + 1):
                    with for_(*from_array(t, self.t_vec)):
                        # Real Rabi pulse
                        
                        play("x180" * amp(0.1), "NV", duration=t)
                        align()
                        play("laser_ON", "AOM1")
                        measure("readout", "SPCM1", None, time_tagging.analog(times, self.readout_len, counts))
                        save(counts, counts_st)
        
                        wait(wait_after_measure)
                        align()
        
                        # # Dark count (no MW pulse)
                        # play("x180" * amp(0), "NV", duration=t )
                        # align()
                        # play("laser_ON", "AOM1")
                        # measure("readout", "SPCM1", None, time_tagging.analog(times, self.readout_len, counts_dark))
                        # save(counts_dark, counts_dark_st)
        
            with stream_processing():
                counts_st.buffer(m_avg, len(self.t_vec)).map(FUNCTIONS.average(0)).save_all("counts")
                # counts_st.buffer(n_points).average().save("counts")
                # counts_dark_st.buffer(n_points).average().save("counts_dark")
    
        self.job = self.qm.execute(rabi)
        self.job_start_time = time.time()
        print("Job started.")
        
    def on_start_fetching(self):
        print("Started fetching data.")
        if not self.job:
            return

    def on_stop_fetching(self):
        self.stop_fetching_flag.set()

    def on_stop_job(self):
        if self.job:
            self.job.halt()

    def on_disconnect(self):
        self.qmm.close_all_quantum_machines()
        self.qmm = None
        self.qm = None
        self.job = None

    def set_rabi_params(self, params):
        self.rabi_params = params

    def get_data(self, f_idx):
        try:
            self.job.resume()
            while not self.job.is_paused() and self.job.status == 'running':
                time.sleep(0.1)
        except:
            pass

        if f_idx == 0:
            self.res_handles = self.job.result_handles
            self.counts_handle = self.res_handles.get("counts")
            self.last_idx = 0
            self.new_counts = []
            self.counts_handle.wait_for_values(1)

        while self.counts_handle.count_so_far() < f_idx + 1:
            time.sleep(0.1)

        first_idx = self.last_idx
        self.last_idx = self.counts_handle.count_so_far()
        self.new_counts.append(self.counts_handle.fetch(slice(first_idx, self.last_idx)))

        counts = self.new_counts[-1]["value"][-1]
        self.y_data = self.generate_fake_data(self.x_data)

        pos_out = self.scannerpos.getPositionsXYRel()
        z_out = self.z_control.getPositionZ()

        self.data_dict = {
            'x [um]': pos_out[0] * 1e6,
            'y [um]': pos_out[1] * 1e6,
            'AFM height [um]': z_out * 1e6,
            'x_data': self.x_data,
            'y_data': self.y_data,
            'fit_status': 'pending'
        }

    def run_fitting(self):
        try:
            popt, fitted = self.fit_decaying_cosine(self.x_data, self.y_data)
            fit_status = 'ok'
        except Exception as e:
            fitted = np.full_like(self.y_data, np.mean(self.y_data))
            popt = [0, 0, 0, np.mean(self.y_data)]
            fit_status = 'failed'

        self.fitted_y_data = fitted
        freq = popt[1]
        decay = popt[2]
        contrast = abs(popt[0])
        elapsed = time.time() - self.job_start_time

        self.data_dict.update({
            'fitted_y_data': self.fitted_y_data,
            'rabi_freq': freq,
            'rabi_decay': decay,
            'rabi_contrast': contrast,
            'counts [kc/s]': np.mean(self.y_data),
            'time_elapsed': elapsed,
            'fit_status': fit_status
        })

    @staticmethod
    def fit_decaying_cosine(t, y):
        def model(t, A, f, tau, offset):
            return A * np.cos(2 * np.pi * f * t * 1e-3) * np.exp(-t / tau) + offset

        p0 = [np.max(y) - np.min(y), 1, np.max(t)/2, np.mean(y)]
        popt, _ = curve_fit(model, t, y, p0=p0)
        return popt, model(t, *popt)

    def generate_fake_data(self, t, f=1.5, A=50, tau=500, offset=200, noise_level=5):
        y = A * np.cos(2 * np.pi * f * t * 1e-3) * np.exp(-t / tau) + offset
        noise = np.random.normal(0, noise_level, size=len(t))
        return y + noise

    def cleanup(self):
        try:
            if self.state == 'fetching':
                self.stop_fetching()
            if self.state == 'job_started':
                self.stop_job()
            if self.state == 'connected':
                self.disconnect()
        except Exception as e:
            print(f"Error during cleanup: {e}")
