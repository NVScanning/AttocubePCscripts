# -*- coding: utf-8 -*-
"""
Created on Sun May 10 13:04:04 2020

@author: schaecl
"""

import numpy as np
from matplotlib import pyplot as plt
import asc500_device as asc

# #binPath = "../../\01 ASC500 Installer and Data\ASC500CL-V2.7.13\ASC500CL-V2.7.13"
# binPath = "Users\attocube\Desktop\ASC500 package V3 16.03.2022\01 ASC500 Installer and Data\ASC500CL-V2.7.13\ASC500CL-V2.7.13"
# #dllPath = "../../\04 ASC500 64bit libraries\ASC500CL-LIB-WIN64-V2.7.13\daisybase\lib"
# dllPath = "Users\attocube\Desktop\ASC500 package V3 16.03.2022\01 ASC500 Installer and Data\ASC500CL-V2.7.13\ASC500CL-V2.7.13\daisybase\lib"
# # asc500 = asc.ASC500Base(binPath, dllPath)

binPath = "C:\Users\attocube\Desktop\ASC500 package V3 16.03.2022\01 ASC500 Installer and Data"
dllPath = "64bit_lib\\ASC500CL-LIB-WIN64-V2.7.13\\daisybase\\lib\\"

asc500 = asc.Device(binPath, dllPath)

asc500.base.startServer('FindSim')

asc500.base.sendProfile(binPath + 'AFM_SampleScan_Daisy-Profil.ngp')

asc500.base.setDataEnable(1)

sampTime = 1e-3
average = 0
chnNo = 0
bufSize = 256
expTime = 1e-6 # Counter exposure time in us

asc500.base.configureChannel(chnNo,
                        asc500.getConst('CHANCONN_PERMANENT'),
                        asc500.getConst('CHANADC_COUNTER'),
                        average,
                        sampTime)

print(asc500.base.getChannelConfig(chnNo))

asc500.base.configureDataBuffering(chnNo, bufSize)

asc500.base.setCounterExposureTime(expTime)
print("Exposure time ", asc500.base.getCounterExposureTime())

#%% Poll data

while True:
    # Wait until buffer is full
    if asc500.base.waitForFullBuffer(chnNo) != 0:
        break

out = \
asc500.base.getDataBuffer(chnNo,
                     0,
                     bufSize)

#%% Close ASC500

asc500.base.stopServer()

#%% Check data

print("Frame number: ", out[0])
print("Index       : ", out[1])
print("Data size   : ", out[2])
print("Meta data   : ", out[4])
counts = np.asarray(out[3][:])
print("Data        :\n", counts)

#%% Plot counts

plt.figure(0)

plt.scatter((np.arange(bufSize) + 1) * 2.5e-6 * expTime * 1e3,
            counts)
plt.xlabel('Time / ms')
plt.ylabel('Counts / 1')
