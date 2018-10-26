#######################
### IMPORT PACKAGES ###
#######################

# import normal Python packages
import pyvisa
import time
import numpy as np
import csv
import logging

# suppress weird h5py warnings
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import h5py
warnings.resetwarnings()

# import my device drivers
import sys
sys.path.append('..')
from drivers import Hornet 
from drivers import LakeShore218
from drivers import LakeShore330

########################
### DEFINE FUNCTIONS ###
########################

def create_database(fname, length):
    """Create a new HDF5 file, defining the data structure."""

    f = h5py.File(fname, 'w-')

    # groups
    root     = f.create_group("beam_source")
    pressure = root.create_group("pressure")
    thermal  = root.create_group("thermal")
    gas      = root.create_group("gas")
    lasers   = root.create_group("lasers")
    events   = root.create_group("events")

    # datasets
    length = length
    ig_dset = pressure.create_dataset("IG", (length,2), dtype='f', maxshape=(None,2))
    ig_dset.set_fill_value = np.nan
    t_dset = thermal.create_dataset("cryo", (length,13), dtype='f', maxshape=(None,13))
    t_dset.set_fill_value = np.nan

def timestamp():
    return time.time() - 1540324934

def run_recording(temp_dir, N, dt):
    """Record N datapoints every dt seconds to CSV files in temp_dir."""

    # open files and devices
    rm = pyvisa.ResourceManager()
    with open(temp_dir+"/beam_source/pressure/IG.csv",'a',1) as ig_f,\
         open(temp_dir+"/beam_source/thermal/cryo.csv",'a',1) as cryo_f,\
         Hornet(rm, 'COM4')            as ig,\
         LakeShore218(rm, 'COM1')      as therm1,\
         LakeShore330(rm, 'GPIB0::16') as therm2:

        # create csv writers
        ig_dset = csv.writer(ig_f)
        cryo_dset = csv.writer(cryo_f)

        # main recording loop
        for i in range(N):
            ig_dset.writerow( [timestamp(), ig.ReadSystemPressure()] )
            cryo_dset.writerow( [timestamp()] + therm1.QueryKelvinReading() +
                [therm2.ControlSensorDataQuery(), therm2.SampleSensorDataQuery()] )
            time.sleep(dt)

#######################
### RUN THE PROGRAM ###
#######################

temp_dir = "C:/Users/CENTREX/Documents/data/temp_run_dir"
logging.basicConfig(filename=temp_dir+'ParameterMonitor.log')
run_recording(temp_dir, 12*3600, 1)
