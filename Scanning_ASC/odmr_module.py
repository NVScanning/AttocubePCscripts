import numpy as np
from scipy.optimize import curve_fit
from transitions import Machine
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
import time
#from configuration_octave_scan import *
from configuration_with_octave_Last import *


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
        self.app = None
        self.counts_old = []

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
        self.counts_sum = np.zeros(np.shape(self.f_vec))
        self.fitted_y_data= np.zeros(np.shape(self.f_vec))
        self.y_data=np.zeros(np.shape(self.f_vec))
        self.x_data= np.zeros(np.shape(self.f_vec))
        self.x_data = (NV_LO_freq + self.f_vec) / u.GHz
        
        
            
        with program() as cw_odmr:
                            
            f = declare(int)
            n = declare(int)
            m  = declare(int)
            i = declare(int)  
            n_st = declare_stream()
            times = declare(int, size=100)
            counts = declare(int)
            counts_st = declare_stream()
            iteration = declare(int)
            m_avg = self.N_average
            counts_dark_st = declare_stream()  # stream for counts
            
            with for_(i, 0, i < flattened + 1, i + 1):
                
                pause()
                
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
                        play("laser_ON", "AOM1", duration=self.readout_len * u.ns)
                        play("cw" * amp(0.1), "NV", duration=self.readout_len * u.ns)
                        # ... and the laser pulse simultaneously (the laser pulse is delayed by 'laser_delay_1')
                        #play("laser_ON", "AOM1", duration=self.readout_len * u.ns)
                        wait(1_000 * u.ns, "SPCM1")  # so readout don't catch the first part of spin reinitialization
                        # Measure and detect the photons on SPCM1
                        measure("long_readout", "SPCM1", None, time_tagging.analog(times, self.readout_len, counts))

                        save(counts, counts_st)  # save counts on stream

                        # # #assign(counts1, counts+counts1)
                        # # Wait and align all elements before measuring the dark events
                        # wait(wait_between_runs * u.ns)
                        # align()  # align all elements
                        # # Play the mw pulse with zero amplitude...
                        # play("cw" * amp(0), "NV", duration=self.readout_len * u.ns)
                        # # ... and the laser pulse simultaneously (the laser pulse is delayed by 'laser_delay_1')
                        # play("laser_ON", "AOM1", duration=self.readout_len * u.ns)
                        # wait(1_000 * u.ns, "SPCM1")  # so readout don't catch the first part of spin reinitialization
                        # measure("long_readout", "SPCM1", None, time_tagging.analog(times, self.readout_len, counts))

                        # # save(counts, counts_dark_st)  # save counts on stream
                        save(m, n_st)  # save number of iteration inside for_loop

                        wait(wait_between_runs * u.ns)
                        
                    
            with stream_processing():
                counts_st.buffer(m_avg, len(self.f_vec)).map(FUNCTIONS.average(0)).save_all("counts")
                n_st.save("iteration")
         
        self.job = self.qm.execute(cw_odmr)  
        self.job_start_time = time.time()  # Record the start time
        print("Job started.")


    def on_start_fetching(self):
        print("Started fetching data.")
        # self.res_handles = self.job.result_handles
        # self.counts_handle = self.res_handles.get("counts")
        # self.iteration_handle = self.res_handles.get("iteration")
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
        
        #self.qm.octave.set_rf_output_mode("NV", RFOutputMode.off)
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
    
    @staticmethod
    def get_minima_from_single(x_data, y_data, fit_type, center_freq=2875):
        """
        Estimate indices of Lorentzian dip centers based on signal minima.
    
        Parameters:
        - x_data: array of frequency values.
        - y_data: array of corresponding measured counts.
        - fit_type: string, one of "Single Lorentzian", "Double Lorentzian", "Triple Lorentzian".
        - center_freq: expected central frequency of the ODMR feature (in MHz).
    
        Returns:
        - Sorted array of indices corresponding to estimated dip centers, used as fit initial guesses.
        """
        bg = np.max(y_data)
        min_idx = np.argmin(y_data)  # Find first minimum
        min_x = x_data[min_idx]
        min_indices = [min_idx]
    
        if fit_type in ["Double Lorentzian", "Triple Lorentzian"]:
            # Estimate second dip position symmetrically around center
            est_x2 = 2 * center_freq - min_x
            idx2 = np.argmin(np.abs(x_data - est_x2))
            min_indices.append(idx2)
            min_indices = sorted(min_indices, key=lambda i: x_data[i])
    
        if fit_type == "Triple Lorentzian":
            # Estimate third dip near center_freq
            est_x3 = center_freq
            idx3 = np.argmin(np.abs(x_data - est_x3))
            min_indices.append(idx3)
    
        return np.array(sorted(min_indices))
    
    
    @staticmethod
    def fit_lorentzian(x_data, y_data, fit_type, center_freq=2875):
        """
        Perform Lorentzian fitting (single, double, or triple) on ODMR data.
    
        Parameters:
        - x_data: frequency array (MHz).
        - y_data: corresponding PL counts (kc/s).
        - fit_type: fit model ("Single Lorentzian", "Double Lorentzian", "Triple Lorentzian").
        - center_freq: expected ODMR center (used for initial guess symmetry).
    
        Returns:
        - popt: optimized fit parameters.
        - fitted_y: fitted Lorentzian curve evaluated over x_data.
        """
        bg = np.max(y_data)
        min_idx = ODMRModule.get_minima_from_single(x_data, y_data, fit_type, center_freq)
    
        # Estimate amplitudes (dip depths)
        A1 = bg - y_data[min_idx[0]]
        A2 = bg - y_data[min_idx[1]] if fit_type != "Single Lorentzian" else 0
        A3 = bg - y_data[min_idx[2]] if fit_type == "Triple Lorentzian" else 0
    
        # Estimate initial FWHM
        gamma_guess = 5 if fit_type == "Single Lorentzian" else np.mean(np.diff(x_data[min_idx])) / 2
    
        if fit_type == "Single Lorentzian":
            p0 = [x_data[min_idx[0]], A1, gamma_guess, bg]
            popt, _ = curve_fit(ODMRModule.lorentzian, x_data, y_data, p0=p0, maxfev=10000)
            return popt, ODMRModule.lorentzian(x_data, *popt)
    
        elif fit_type == "Double Lorentzian":
            p0 = [x_data[min_idx[0]], A1, gamma_guess,
                  x_data[min_idx[1]], A2, gamma_guess,
                  bg]
            
            try:
                popt, _ = curve_fit(ODMRModule.double_lorentzian, x_data, y_data, p0=p0, maxfev=50000)
                
            except:
                popt = p0
                
            return popt, ODMRModule.double_lorentzian(x_data, *popt)
    
        elif fit_type == "Triple Lorentzian":
            p0 = [x_data[min_idx[0]], A1, gamma_guess,
                  x_data[min_idx[1]], A2, gamma_guess,
                  x_data[min_idx[2]], A3, gamma_guess,
                  bg]
            popt, _ = curve_fit(ODMRModule.triple_lorentzian, x_data, y_data, p0=p0, maxfev=50000)
            return popt, ODMRModule.triple_lorentzian(x_data, *popt)
    
        return None, None
    



    def get_data(self, f_idx):
        try:
            self.job.resume()
            # Wait until the program reaches the 'pause' statement again, indicating that the QUA program is done
            while not self.job.is_paused() and self.job.status == 'running':
                time.sleep(0.1)
        except Exception as e:
            print(f"[ERROR] Could not resume job: {e}")
            return
        if f_idx == 0:
            self.res_handles = self.job.result_handles
            self.counts_handle = self.res_handles.get("counts")
            self.iteration_handle = self.res_handles.get("iteration")
        # print("in get data")
        # self.iteration_handle.wait_for_values(1)
        # print(f'state:{self.state}')
        # self.iteration_sum=0
        # self.counts_sum = np.zeros(np.shape(self.f_vec))
        # self.fitted_y_data= np.zeros(np.shape(self.f_vec))
        # self.y_data=np.zeros(np.shape(self.f_vec))
        # print('wa')
        self.counts_handle.wait_for_values(1)
        self.iteration_handle.wait_for_values(1)
        # print('it')
        new_counts = self.counts_handle.fetch_all()  # add something to check size of fetched array
        while np.shape(new_counts)[0] != f_idx + 1 and type(self.job) != type(None):
            print('waiting for counts')
            time.sleep(0.1)
            new_counts = self.counts_handle.fetch_all()
        counts = new_counts["value"][-1]
        self.x_data = (NV_LO_freq + self.f_vec) / u.MHz  # x axis [frequencies]
        # self.x_data = (NV_LO_freq + self.f_vec*u.MHz) / u.GHz
        self.y_data = self.generate_fake_data(self.x_data, self.fit_type)
        # self.y_data = (counts / 1000 / (self.readout_len * 1e-9))  # counts( [frequencies])
        # print(f"y_data: {self.y_data}")
        # print(f"fitted_y: {self.fitted_y_data}")
        # Read AFM position and height
       
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
        

    def start_fitting_thread(self):
        threading.Thread(target=self.run_fitting, daemon=True).start() 
   
    def run_fitting(self):
        try:
            popt, fitted = self.fit_lorentzian(self.x_data, self.y_data, self.fit_type)
            fit_status = 'ok'
        except Exception as e:
            print(f"[WARNING] Fit failed: {e}")
            fitted = np.full_like(self.y_data, np.mean(self.y_data))
            popt = [-1, -1, -1, np.mean(self.y_data)]
            fit_status = 'failed'
        self.fitted_y_data = fitted
        h = 6.62607015e-34
        g = 2.00231930436256
        mu_B = 9.2740100783e-24
        try:
            center_freq = popt[0]
            fwhm = 2 * popt[2]
            contrast = (np.max(fitted) - np.min(fitted)) / np.max(fitted)
            I0 = np.max(self.y_data)
            sensitivity = (h * fwhm) / (g * mu_B * contrast * np.sqrt(I0))
        except:
            center_freq = fwhm = contrast = sensitivity = -1
        elapsed = time.time() - self.job_start_time
        count_mean = np.mean(self.y_data)
        self.data_dict.update({
            'fitted_y_data': self.fitted_y_data,
            'counts [kc/s]': count_mean,
            'freq_center': center_freq,
            'fwhm': fwhm,
            'contrast': contrast,
            'sensitivity': sensitivity,
            'time_elapsed': elapsed,
            'fit_status': fit_status
        })

    def generate_fake_data(self, x_data, fit_type, center_freq=2875, noise_level=0.01):
        """
        Generates realistic fake ODMR data in kcps, mimicking real experimental output.
        Parameters:
        - x_data: frequency axis [MHz]
        - fit_type: "Single Lorentzian", "Double Lorentzian", "Triple Lorentzian"
        - center_freq: main dip frequency in MHz
        - noise_level: relative noise level (as a fraction of signal)
        Returns:
        - y_data: simulated kcps signal
        """
        bg_kcps = 300  # Background level in kcps (typical real value)
        contrast = 0.5  # 5% contrast
        fwhm = 10  # FWHM in MHz (typical value)
        gamma = fwhm / 2  # Convert to gamma
        if fit_type == "Single Lorentzian":
            y_data = self.lorentzian(x_data, center_freq, bg_kcps * contrast, gamma, bg_kcps)
        elif fit_type == "Double Lorentzian":
            y_data = self.double_lorentzian(
                x_data,
                center_freq - 40, bg_kcps * contrast * 0.8, gamma,
                center_freq + 40, bg_kcps * contrast * 0.6, gamma,
                bg_kcps
            )
        elif fit_type == "Triple Lorentzian":
            y_data = self.triple_lorentzian(
                x_data,
                center_freq - 50, bg_kcps * contrast * 0.8, gamma,
                center_freq,       bg_kcps * contrast * 1.0, gamma,
                center_freq + 50, bg_kcps * contrast * 0.6, gamma,
                bg_kcps
            )
        else:
            raise ValueError(f"Unsupported fit type: {fit_type}")
        # Add small noise relative to signal
        noise = np.random.normal(0, noise_level * bg_kcps, len(x_data))
        y_data += noise
        return y_data
    
 

            

    @staticmethod
    def lorentzian(x, x0, a, gamma, bg):
        
        """
        Single Lorentzian function.
        Parameters:
        x  : array-like, The frequency values.
        x0 : float, The center frequency of the dip.
        a  : float, The amplitude (depth) of the dip.
        gamma : float, The full-width at half maximum (FWHM).
        bg : float, Background offset.
        Returns:
        y : array-like, The computed Lorentzian function values.
        """
        return -abs(a) * (gamma ** 2 / ((x - x0) ** 2 + gamma ** 2)) + bg

    @staticmethod
    def double_lorentzian(x, x0, a1, gamma1, x1, a2, gamma2, bg):
        """
        Double Lorentzian function (sum of two dips).
        Parameters:
        x  : array-like, The frequency values.
        x0 : float, The center frequency of the first dip.
        a1 : float, The amplitude (depth) of the first dip.
        gamma1 : float, The FWHM of the first dip.
        x1 : float, The center frequency of the second dip.
        a2 : float, The amplitude (depth) of the second dip.
        gamma2 : float, The FWHM of the second dip.
        bg : float, Background offset.
        Returns:
        y : array-like, The computed function values for two Lorentzians.
        """
        # bg = 10
        return (ODMRModule.lorentzian(x, x0, a1, gamma1, 0) + ODMRModule.lorentzian(x, x1, a2, gamma2, 0) + bg)

    @staticmethod
    def triple_lorentzian(x, x0, a1, gamma1, x1, a2, gamma2, x2, a3, gamma3, bg):
        """
        Triple Lorentzian function (sum of three dips).
        Parameters:
        x  : array-like, The frequency values.
        x0 : float, The center frequency of the first dip.
        a1 : float, The amplitude (depth) of the first dip.
        gamma1 : float, The FWHM of the first dip.
        x1 : float, The center frequency of the second dip.
        a2 : float, The amplitude (depth) of the second dip.
        gamma2 : float, The FWHM of the second dip.
        x2 : float, The center frequency of the third dip.
        a3 : float, The amplitude (depth) of the third dip.
        gamma3 : float, The FWHM of the third dip.
        bg : float, Background offset.
        Returns:
        y : array-like, The computed function values for three Lorentzians.
        """
        # bg = 10
        return (ODMRModule.lorentzian(x, x0, a1, gamma1, 0) +
                ODMRModule.lorentzian(x, x1, a2, gamma2, 0) +
                ODMRModule.lorentzian(x, x2, a3, gamma3, 0) + bg)




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