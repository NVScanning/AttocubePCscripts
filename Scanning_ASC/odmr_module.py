import numpy as np
from scipy.optimize import curve_fit
from transitions import Machine
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
import time
from configuration_octave_scan import *


import threading
from threading import Lock
data_lock = Lock()

class ODMRModule:
    states = ['disconnected', 'connected', 'job_started', 'fetching']

    def __init__(self):
        self.qmm = None
        self.qm = None
        self.job = None
        self.odmr_params = None
        self.readout_len = long_meas_len_1  # Readout duration for this experiment
        self.res_handles = None
        self.counts_handle = None
        self.n_handle = None
        self.flattened= None
        self.counts_sum = np.zeros(1)
        self.fitted_y_data = np.zeros(1)
        self.iteration_sum = 0
        self.y_data = np.zeros(1)
        self.x_data=np.zeros(1)
        self.data_dict = {}
        self.stop_fetching_flag = threading.Event()
        self.lock = threading.Lock()
        self.job_start_time = None  # Add this line to initialize job_start_time
        
        self.slow_steps=None
        self.fast_steps=None
        
        self.z_control = None
        self.scannerpos = None

        # Initialize the state machine
        self.machine = Machine(model=self, states=ODMRModule.states, initial='disconnected')

        # Add transitions
        self.machine.add_transition(trigger='connect', source='disconnected', dest='connected', after='on_connect')
        self.machine.add_transition(trigger='start_job', source='connected', dest='job_started', after='on_start_job')
        self.machine.add_transition(trigger='start_fetching', source='job_started', dest='fetching', after='on_start_fetching')
        # self.machine.add_transition(trigger='start_getting_data', source='fetching', dest='get_data', after='on_get_data')
        # self.machine.add_transition(trigger='finish_getting_data', source='get_data', dest='connected')
        self.machine.add_transition(trigger='stop_fetching', source='fetching', dest='connected', after='on_stop_fetching')
        self.machine.add_transition(trigger='stop_job', source='job_started', dest='connected', after='on_stop_job')
        self.machine.add_transition(trigger='disconnect', source=['connected', 'job_started', 'fetching'], dest='disconnected', after='on_disconnect')

    def on_connect(self):
        self.qmm = QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name, octave=octave_config)
        self.qm = self.qmm.open_qm(config)
        print("Connected to Quantum Machine Manager.")

    def on_start_job(self):
        self.iteration_sum = 0
        if not self.odmr_params:
            raise ValueError("ODMR parameters not set.")
        Typ_gain = 42  # db
        fmin = self.odmr_params["fmin"] 
        print(f'fmin{fmin}')
        fmin = (fmin*u.GHz-NV_LO_freq)
        print(f'fmin{type(fmin)}')       
        fmax = self.odmr_params["fmax"]
        fmax = (fmax*u.GHz-NV_LO_freq)
        print(f'fmax{fmax}')        
        
        N_points = self.odmr_params["N_points"]
        rf_power_dbm = self.odmr_params["rf_power"] - Typ_gain
        self.N_average = self.odmr_params["N_average"]
        self.fit_type = self.odmr_params["fit_type"]
        
        # Convert RF Power from dBm to Watts
        rf_power_watt = 10 ** ((rf_power_dbm - 30) / 10)
        # Calculate Vrms
        R = 50  # Ohms
        Vrms = (rf_power_watt * R) ** 0.5 / 2  # Include factor of 1/2 for peak-to-peak conversion
        print(f"RF Power (W): {rf_power_watt}, Vrms: {Vrms}")
        
        flattened = self.slow_steps*self.fast_steps
        m_avg = 1e2  # number of averages

        
        # Frequency vector
        self.f_vec = np.arange(fmin, fmax, (fmax  - fmin ) / N_points)
        
        print(f'f_vec:{self.f_vec}')
        self.counts_sum = np.zeros(np.shape(self.f_vec))
        self.fitted_y_data= np.zeros(np.shape(self.f_vec))
        self.y_data=np.zeros(np.shape(self.f_vec))
        #self.x_data= np.zeros(np.shape(self.f_vec))
        self.x_data = (NV_LO_freq + self.f_vec*u.MHz) / u.GHz
        
        #counts_st = []
        print(f'readout_1: {int(self.readout_len//4)} ')
        print(f'readout_2: {int(self.readout_len * u.ns)} ')
        
        # f_min_external = 3e9 - fmin
        # f_max_external = 4e9 - fmax
        # df_external = fmax - fmin
        # freqs_external = np.arange(f_min_external, f_max_external + 0.1, df_external)
        # frequency = np.array(np.concatenate([self.f_vec + freqs_external[i] for i in range(len(freqs_external))]))
            
        with program() as cw_odmr:
                            
            f = declare(int)
            n = declare(int)
            m  = declare(int)
            i = declare(int)  
            times = declare(int, size=100)
            counts = declare(int)
            counts_st = declare_stream()
            # iteration = declare(int)
            m_avg = self.N_average
            counts_dark_st = declare_stream()  # stream for counts

          
            
            with for_(i, 0, i < flattened + 1, i + 1):
                
                with for_(m, 0, m < m_avg, m + 1):
               
                    with for_(*from_array(f, self.f_vec)):
                        
                      #   update_frequency("NV", f)  # update frequency
                      #   align()  # align all elements
                      # #  play("cw" * amp(Vrms * 2 ** 0.5), "NV", duration=self.readout_len * u.ns)
                      #   play("cw" * amp(0.5), "NV", duration=self.readout_len * u.ns)
                      #   play("laser_ON", "AOM1", duration=self.readout_len * u.ns)
                      #   wait(1_000 * u.ns, "SPCM1")
                      #   measure("long_readout", "SPCM1", None, time_tagging.analog(times, self.readout_len, counts))
                        
                      #   save(counts, counts_st)  # save counts on stream
                        
                      #   wait(self.readout_len*u.ns)
                        
                        # Update the frequency of the digital oscillator linked to the element "NV"
                        update_frequency("NV", f)
                        # align all elements before starting the sequence
                        align()
                        # Play the mw pulse...
                        play("cw" * amp(0.5), "NV", duration=self.readout_len * u.ns)
                        # ... and the laser pulse simultaneously (the laser pulse is delayed by 'laser_delay_1')
                        play("laser_ON", "AOM1", duration=self.readout_len * u.ns)
                        wait(1_000 * u.ns, "SPCM1")  # so readout don't catch the first part of spin reinitialization
                        # Measure and detect the photons on SPCM1
                        measure("long_readout", "SPCM1", None, time_tagging.analog(times, self.readout_len, counts))

                        save(counts, counts_st)  # save counts on stream

                        #assign(counts1, counts+counts1)
                        # Wait and align all elements before measuring the dark events
                        wait(wait_between_runs * u.ns)
                        align()  # align all elements
                        # Play the mw pulse with zero amplitude...
                        play("cw" * amp(0), "NV", duration=self.readout_len * u.ns)
                        # ... and the laser pulse simultaneously (the laser pulse is delayed by 'laser_delay_1')
                        play("laser_ON", "AOM1", duration=self.readout_len * u.ns)
                        wait(1_000 * u.ns, "SPCM1")  # so readout don't catch the first part of spin reinitialization
                        measure("long_readout", "SPCM1", None, time_tagging.analog(times, self.readout_len, counts))

                        save(counts, counts_dark_st)  # save counts on stream

                        wait(wait_between_runs * u.ns)
            pause()

            with stream_processing():
                counts_st.buffer(m_avg, len(self.f_vec)).map(FUNCTIONS.average(0)).save_all("counts")
         
        self.job = self.qm.execute(cw_odmr)  
        self.job_start_time = time.time()  # Record the start time
        print("Job started.")


    def on_start_fetching(self):
        print("Started fetching data.")
        self.res_handles = self.job.result_handles
        self.counts_handle = self.res_handles.get("counts")
        self.n_handle = self.res_handles.get("iteration")
        if not self.job:
            print("No job to fetch data from.")
            return
        
        print("Data fetched.")
    #     self.start_getting_data()  # Trigger the state transition to `get_data`
    # def on_get_data(self):
    #     print("Fetching data...")
        #threading.Thread(target=self.get_data, daemon=True).start()
      
         

    def on_stop_fetching(self):
        self.stop_fetching_flag.set()
        print("Stopped fetching data.")
        
    def on_stop_job(self):
        if self.job:
            self.job.halt()
        
        self.qm.octave.set_rf_output_mode("NV", RFOutputMode.off)
        print("Job stopped.")
        

    def on_disconnect(self):
        self.qmm.close_all_quantum_machines()
        self.qmm = None
        self.qm = None
        self.job = None
        print("Disconnected from Quantum Machine Manager.")

    def set_odmr_params(self, params):
        self.odmr_params = params
        
        print(f'setodmr: {self.odmr_params}')
        
    def wait_until_job_is_paused(self, current_job):
        """
        Waits until the OPX FPGA reaches the pause statement.
        Used when the OPX sequence needs to be synchronized with an external parameter sweep.
    
        :param current_job: the job object.
        """
        while not current_job.is_paused():
            time.sleep(0.1)
            pass
        return True
    



    def get_data(self,f_idx):
        print("in get data")
      
        
        #self.iteration_handle.wait_for_values(1)
        print(f'state:{self.state}')
        
        self.iteration_sum=0
        self.counts_sum = np.zeros(np.shape(self.f_vec))
        self.fitted_y_data= np.zeros(np.shape(self.f_vec))
        self.y_data=np.zeros(np.shape(self.f_vec))
        

        try:
            self.job.resume()
                # Wait until the program reaches the 'pause' statement again, indicating that the QUA program is done
            while not job.is_paused() and job.status == 'running':
                time.sleep(0.1)
        
        except:
            pass
                      
        print('wa')
        self.counts_handle.wait_for_values(1)
        #self.n_handle.wait_for_values(1)
        print('it')

    
        #print(f'state before data: {self.state}')
       
        #print('here')
        c = self.counts_handle.count_so_far()
        
        while c <= f_idx+2:
            time.sleep(0.1)
            print(f'waiting for results, c:{c}, pixel:{f_idx+2}')
            c = self.counts_handle.count_so_far()
        
        counts = self.counts_handle.fetch_all()

        #print(f'conts {counts}')
        #print(f'c: {c}')
        #iteration = self.n_handle.fetch_all()
    
        #print(f'odmr x:{self.x_data}')
        
        self.x_data = (NV_LO_freq + self.f_vec) / u.MHz # x axis [frequencies]
        #self.x_data = (NV_LO_freq + self.f_vec*u.MHz) / u.GHz
        #self.y_data = self.generate_fake_data( self.x_data, self.fit_type) 
        self.y_data = (counts[-1][0] / 1000 / (self.readout_len * 1e-9)) # counts( [frequencies])
        #print(f"y_data: {self.y_data}")
        # print(f"fitted_y: {self.fitted_y_data}")
        
        
        fit_functions = {
            "Single Lorentzian": (self.lorentzian, [self.x_data[np.argmin(self.y_data)], np.max(self.y_data), 10, np.max(self.y_data)]),
            "Double Lorentzian": (self.double_lorentzian, [self.x_data[np.argmax(self.y_data)] , np.max(self.y_data), 10,
                                                            self.x_data[np.argmax(self.y_data)] + 0.01, np.max(self.y_data) / 2, 10]),
            "Triple Lorentzian": (self.triple_lorentzian, [self.x_data[np.argmax(self.y_data)], np.max(self.y_data), 10,
                                                            self.x_data[np.argmax(self.y_data)]  + 0.01, np.max(self.y_data) / 2, 10,
                                                            self.x_data[np.argmax(self.y_data)] - 0.01, np.max(self.y_data) / 3, 10])
        }

        # Define fitting functions and initial parameters
        fit_function, p0 = fit_functions[self.fit_type]
        # try:
        popt, _ = curve_fit(fit_function, self.x_data, self.y_data, p0=p0, maxfev=10000)
        # except RuntimeError as e:
        #     print(f"Fitting error: {e}")
        #     continue

        self.fitted_y_data = fit_function(self.x_data, *popt)
        #print(f'fitdatashape{np.shape(self.fitted_y_data)}')

        center_freq = popt[0]
        fwhm = 2 * popt[2]
        contrast = (np.max(self.fitted_y_data) - np.min(self.fitted_y_data)) / np.max(self.fitted_y_data)
        I0 = np.max(self.y_data)
        h = 6.62607015e-34  # Planck's constant
        g = 2.00231930436256  # g-factor for electron
        mu_B = 9.2740100783e-24  # Bohr magneton

        sensitivity = (h * fwhm) / (g * mu_B * contrast * np.sqrt(I0))
        elapsed_time = time.time() - self.job_start_time
        
        z_out = self.z_control.getPositionZ()
        pos_out = self.scannerpos.getPositionsXYRel()

        self.data_dict.update({
            'x [um]': pos_out[0]*1E6,
            'y [um]': pos_out[1]*1E6,
            'AFM height [um]': z_out*1E6,
            'counts [kc/s]': np.mean(self.y_data),
            'freq_center': center_freq,
            'fwhm': fwhm,
            'contrast': contrast,
            'sensitivity': sensitivity,
            'time_elapsed': elapsed_time,
            'x_data': self.x_data,
            'y_data': self.y_data,
            'fitted_y_data': self.fitted_y_data
        })
        #print(f'data dict: {self.data_dict}')

        # if self.iteration_sum >= self.N_average:
        #     self.finish_getting_data()  # Trigger state transition when the iteration limit is reached

       
        print("done!")
     
   


    @staticmethod
    def generate_fake_data(x_data, fit_type, noise_level=0.05, gamma_broad=1000, bg=10):
        if fit_type == "Single Lorentzian":
            y_data = ODMRModule.lorentzian(x_data, x_data[len(x_data) // 2], 10, gamma_broad, bg)
        elif fit_type == "Double Lorentzian":
            y_data = ODMRModule.double_lorentzian(x_data, x_data[len(x_data) // 3], 1, gamma_broad,
                                                  x_data[2 * len(x_data) // 3], 0.5, gamma_broad)
        elif fit_type == "Triple Lorentzian":
            y_data = ODMRModule.triple_lorentzian(x_data, x_data[len(x_data) // 4], 1, gamma_broad,
                                                  x_data[2 * len(x_data) // 4], 0.5, gamma_broad,
                                                  x_data[3 * len(x_data) // 4], 0.3, gamma_broad)
        else:
            raise ValueError(f"Unsupported fit type: {fit_type}")
    
        noise = np.random.normal(0, noise_level, len(x_data))
        y_data += noise
        return y_data



            

    @staticmethod
    def lorentzian(x, x0, a, gamma, bg):
        return -abs(a) * (gamma ** 2 / ((x - x0) ** 2 + gamma ** 2)) + bg

    @staticmethod
    def double_lorentzian(x, x0, a1, gamma1, x1, a2, gamma2):
        bg = 10
        return ODMRModule.lorentzian(x, x0, a1, gamma1, bg) + ODMRModule.lorentzian(x, x1, a2, gamma2, bg)

    @staticmethod
    def triple_lorentzian(x, x0, a1, gamma1, x1, a2, gamma2, x2, a3, gamma3):
        bg = 10
        return (ODMRModule.lorentzian(x, x0, a1, gamma1, bg) +
                ODMRModule.lorentzian(x, x1, a2, gamma2, bg) +
                ODMRModule.lorentzian(x, x2, a3, gamma3, bg))

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