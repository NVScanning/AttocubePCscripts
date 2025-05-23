import os
import numpy as np
from set_octave import OctaveUnit, octave_declaration
from qualang_tools.units import unit
from qualang_tools.plot import interrupt_on_close
from qualang_tools.results import progress_counter, fetching_tool
from qualang_tools.loops import from_array
from qm.octave import *

#######################
# AUXILIARY FUNCTIONS #
#######################
u = unit(coerce_to_integer=True)


#############
# VARIABLES #
#############
qop_ip = "192.168.88.10"  # Write the OPX IP address
cluster_name = "my_cluster"  # Write your cluster_name if version >= QOP220
qop_port = None  # Write the QOP port if version < QOP220
octave_ip = "192.168.88.249"  # Write the Octave IP address
octave_port = 80  # 11xxx, where xxx are the last three digits of the Octave IP address


###########################
# Set octave configuration #
############################
# The Octave port is 11xxx, where xxx are the last three digits of the Octave internal IP that can be accessed from
# the OPX admin panel if you QOP version is >= QOP220. Otherwise, it is 50 for Octave1, then 51, 52 and so on.
octave_1 = OctaveUnit("octave1", octave_ip, port=octave_port, con="con1")
# octave_2 = OctaveUnit("octave2", qop_ip, port=11051, con="con1")

# If the control PC or local network is connected to the internal network of the QM router (port 2 onwards)
# or directly to the Octave (without QM the router), use the local octave IP and port 80.
# octave_ip = "192.168.88.X"
# octave_1 = OctaveUnit("octave1", octave_ip, port=80, con="con1")

# Add the octaves
octaves = [octave_1]
# Configure the Octaves
octave_config = octave_declaration(octaves)


#############
# VARIABLES #
#############
# Frequencies
NV_IF_freq = 70 * u.MHz
NV_LO_freq = 2.80 * u.GHz

# Pulses lengths
initialization_len_1 = 3_000 * u.ns
meas_len_1 = 500 * u.ns
long_meas_len_1 = 5_000 * u.ns

initialization_len_2 = 3000 * u.ns
meas_len_2 = 500 * u.ns
long_meas_len_2 = 5_000 * u.ns

# Relaxation time from the metastable state to the ground state after during initialization
relaxation_time = 300 * u.ns
wait_for_initialization = 5 * relaxation_time

# MW parameters
# WARNNING! The maximum voltage threshold to the RF amplifier is 0.5 V
mw_amp_NV = 0.1 # in units of volts, 
mw_len_NV = 500 * u.ns

x180_amp_NV = 0.1  # in units of volts
x180_len_NV = 168  # in units of ns

x90_amp_NV = x180_amp_NV / 2  # in units of volts
x90_len_NV = x180_len_NV  # in units of ns

# RF parameters
rf_frequency = 10 * u.MHz
rf_amp = 0.1
rf_length = 1000

# Readout parameters
signal_threshold_1 = -5_00  # ADC untis, to convert to volts divide by 4096 (12 bit ADC)
signal_threshold_2 = -2_000  # ADC untis, to convert to volts divide by 4096 (12 bit ADC)

# Delays
detection_delay_1 = 424 * u.ns
detection_delay_2 = 80 * u.ns
laser_delay_1 = 0 * u.ns
laser_delay_2 = 0 * u.ns
mw_delay = 100 * u.ns
rf_delay = 0 * u.ns

trigger_delay = mw_delay+57 #Sync with mw_delay  # 57ns with QOP222 and above otherwise 87ns
trigger_buffer = 18  # 18ns with QOP222 and above otherwise 15ns

wait_after_measure = 1 * u.us  # Wait time after each measurement
wait_between_runs = 100

#############################################
#                  Config                   #
#############################################
config = {
    "version": 1,
    "controllers": {
        "con1": {
            "analog_outputs": {
                1: {"offset": 0.0, "delay": mw_delay},  # NV I
                2: {"offset": 0.0, "delay": mw_delay},  # NV Q
                3: {"offset": 0.0, "delay": rf_delay},  # RF
            },
            "digital_outputs": {
                1: {},  # Octave switch
                2: {},  # AOM/Laser 1
                3: {},  # SPCM1 - indicator
                4: {},  # AOM/Laser 2
                5: {},  # SPCM2 - indicator
            },
            "analog_inputs": {
                1: {"offset": 0},  # SPCM1
                2: {"offset": 0},  # SPCM2
            },
        }
    },
    "elements": {
        "NV": {
            "RF_inputs": {"port": ("octave1", 1)},
            "intermediate_frequency": NV_IF_freq,
            "operations": {
                "cw": "const_pulse",
                "x180": "x180_pulse",
                "x90": "x90_pulse",
                "-x90": "-x90_pulse",
                "-y90": "-y90_pulse",
                "y90": "y90_pulse",
                "y180": "y180_pulse",
            },
            "digitalInputs": {
                "marker": {
                    "port": ("con1", 1),
                    "delay": trigger_delay,
                    "buffer": trigger_buffer,
                },
            },
        },
        "RF": {
            "singleInput": {"port": ("con1", 3)},
            "intermediate_frequency": rf_frequency,
            "operations": {
                "const": "const_pulse_single",
            },
        },
        "AOM1": {
            "digitalInputs": {
                "marker": {
                    "port": ("con1", 2),
                    "delay": laser_delay_1,
                    "buffer": 0,
                },
            },
            "operations": {
                "laser_ON": "laser_ON_1",
            },
        },
        "AOM2": {
            "digitalInputs": {
                "marker": {
                    "port": ("con1", 4),
                    "delay": laser_delay_2,
                    "buffer": 0,
                },
            },
            "operations": {
                "laser_ON": "laser_ON_2",
            },
        },
        "SPCM1": {
            "singleInput": {"port": ("con1", 1)},  # not used
            "digitalInputs": {  # for visualization in simulation
                "marker": {
                    "port": ("con1", 3),
                    "delay": detection_delay_1,
                    "buffer": 0,
                },
            },
            "operations": {
                "readout": "readout_pulse_1",
                "long_readout": "long_readout_pulse_1",
            },
            "outputs": {"out1": ("con1", 1)},
            "outputPulseParameters": {
                "signalThreshold": signal_threshold_1,  # ADC units
                "signalPolarity": "Below",
                "derivativeThreshold": -1_023,
                "derivativePolarity": "Above",
            },
            "time_of_flight": detection_delay_1,
            "smearing": 0,
        },
        "SPCM2": {
            "singleInput": {"port": ("con1", 1)},  # not used
            "digitalInputs": {  # for visualization in simulation
                "marker": {
                    "port": ("con1", 5),
                    "delay": detection_delay_2,
                    "buffer": 0,
                },
            },
            "operations": {
                "readout": "readout_pulse_2",
                "long_readout": "long_readout_pulse_2",
            },
            "outputs": {"out1": ("con1", 2)},
            "outputPulseParameters": {
                "signalThreshold": signal_threshold_2,  # ADC units
                "signalPolarity": "Below",
                "derivativeThreshold": -2_000,
                "derivativePolarity": "Above",
            },
            "time_of_flight": detection_delay_2,
            "smearing": 0,
        },
    },
    "octaves": {
        "octave1": {
            "RF_outputs": {
                1: {
                    "LO_frequency": NV_LO_freq,
                    "LO_source": "internal",  # can be external or internal. internal is the default
                    "output_mode": "triggered",  # can be: "always_on" / "always_off"/ "triggered" / "triggered_reversed". "always_off" is the default
                    "gain": -10,  # can be in the range [-20 : 0.5 : 20]dB
                },
            },
            "connectivity": "con1",
        }
    },
    "pulses": {
        "const_pulse": {
            "operation": "control",
            "length": mw_len_NV,
            "waveforms": {"I": "cw_wf", "Q": "zero_wf"},
            "digital_marker": "ON"
        },
        "x180_pulse": {
            "operation": "control",
            "length": x180_len_NV,
            "waveforms": {"I": "x180_wf", "Q": "zero_wf"},
            "digital_marker": "ON"
        },
        "x90_pulse": {
            "operation": "control",
            "length": x90_len_NV,
            "waveforms": {"I": "x90_wf", "Q": "zero_wf"},
            "digital_marker": "ON"
        },
        "-x90_pulse": {
            "operation": "control",
            "length": x90_len_NV,
            "waveforms": {"I": "minus_x90_wf", "Q": "zero_wf"},
            "digital_marker": "ON"
        },
        "-y90_pulse": {
            "operation": "control",
            "length": x90_len_NV,
            "waveforms": {"I": "zero_wf", "Q": "minus_x90_wf"},
            "digital_marker": "ON"
        },
        "y90_pulse": {
            "operation": "control",
            "length": x90_len_NV,
            "waveforms": {"I": "zero_wf", "Q": "x90_wf"},
            "digital_marker": "ON"
        },
        "y180_pulse": {
            "operation": "control",
            "length": x180_len_NV,
            "waveforms": {"I": "zero_wf", "Q": "x180_wf"},
            "digital_marker": "ON"
        },
        "const_pulse_single": {
            "operation": "control",
            "length": rf_length,  # in ns
            "waveforms": {"single": "rf_const_wf"},
            "digital_marker": "ON"
        },
        "laser_ON_1": {
            "operation": "control",
            "length": initialization_len_1,
            "digital_marker": "ON",
        },
        "laser_ON_2": {
            "operation": "control",
            "length": initialization_len_2,
            "digital_marker": "ON",
        },
        "readout_pulse_1": {
            "operation": "measurement",
            "length": meas_len_1,
            "digital_marker": "ON",
            "waveforms": {"single": "zero_wf"},
        },
        "long_readout_pulse_1": {
            "operation": "measurement",
            "length": long_meas_len_1,
            "digital_marker": "ON",
            "waveforms": {"single": "zero_wf"},
        },
        "readout_pulse_2": {
            "operation": "measurement",
            "length": meas_len_2,
            "digital_marker": "ON",
            "waveforms": {"single": "zero_wf"},
        },
        "long_readout_pulse_2": {
            "operation": "measurement",
            "length": long_meas_len_2,
            "digital_marker": "ON",
            "waveforms": {"single": "zero_wf"},
        },
    },
    "waveforms": {
        "cw_wf": {"type": "constant", "sample": mw_amp_NV},
        "rf_const_wf": {"type": "constant", "sample": rf_amp},
        "x180_wf": {"type": "constant", "sample": x180_amp_NV},
        "x90_wf": {"type": "constant", "sample": x90_amp_NV},
        "minus_x90_wf": {"type": "constant", "sample": -x90_amp_NV},
        "zero_wf": {"type": "constant", "sample": 0.0},
    },
    "digital_waveforms": {
        "ON": {"samples": [(1, 0)]},  # [(on/off, ns)]
        "OFF": {"samples": [(0, 0)]},  # [(on/off, ns)]
    },
}
