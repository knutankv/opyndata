from opyndata.data_import import (
    export_from_hdf, 
    export_from_multirec_hdf, 
    get_stats_multi
    )
                                 
from opyndata.visualization import plot_sensors
import h5py

#%% Definitions
fname = 'C:/Users/knutankv/BergsoysundData/data_2Hz.h5'

#%% Get all statistics
with h5py.File(fname, 'r') as hf:
    all_stats = get_stats_multi(hf)    
    
#%% Plot sensors
import plotly.io as pio
pio.renderers.default = 'browser'

with h5py.File(fname, 'r') as hf:
    rec_names = list(hf.keys())
    hf_rec = hf[rec_names[-1]]
    fig = plot_sensors(hf_rec, view_axis=2)
    fig.show()

#%% Full h5 datastructure from chosen file
rec_name = 'NTNU142M-2016-12-26_22-33-33'
hf = h5py.File(fname, 'r')[rec_name]

# E.g. you could grab transformation matrix from GNSS sensor (North, East compared to X, Y)
tmat = hf['displacement']['GNSS'].attrs['transformation_matrix']

#%% Some components only
component_dict = {'wave': ['h'], 
                  'acceleration': ['x', 'y', 'z'],
                  'wind': ['U']}

with h5py.File(fname, 'r') as hf:
    rec_names = list(hf.keys())
    hf_rec = hf[rec_names[-1]]

    # Select last 10 recs
    data_multiple = export_from_multirec_hdf(hf, rec_names[-10:], component_dict=component_dict, decimation_factor=100)

data_multiple.plot()