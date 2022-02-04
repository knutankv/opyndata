from opyndata.data_import import export_from_hdf           
from opyndata.visualization import plot_sensors
import h5py
import plotly.io as pio

pio.renderers.default='browser'

# Define file and recordings
fname = 'C:/Users/knutankv/BergsoysundData/data_2Hz.h5'
rec_name = 'NTNU142M-2017-03-14_22-27-06'

# Plot sensors'
with h5py.File(fname, 'r') as hf:
    hf_rec = hf[rec_name]
    fig = plot_sensors(hf_rec, view_axis=2)
    fig.show()
    
# Choose components to import
comp_dict = {'wave': ['h'], 
                  'acceleration': ['x', 'y', 'z'],
                  'wind': ['U']}

# Import recording from h5 file as Pandas dataframe
with h5py.File(fname, 'r') as hf:
    data_df = export_from_hdf(hf[rec_name], component_dict=comp_dict)
    data_df = data_df.set_index('t')    # set time as index