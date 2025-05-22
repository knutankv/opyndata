"""
##############################################
Data import module
##############################################
All functions related to data import
"""

import numpy as np
import scipy.io as sio
from collections import namedtuple
import pandas as pd
from .misc import create_sensor_dict
import h5py

# ------------------------ HDF export functions ----------------------------
def get_all_comp(obj):
    """
    Get all components (datasets) from h5py object.
        
    Arguments
    ---------------------------
    obj : obj
        object from h5 file with datasets placed in groups

    Returns
    ---------------------------
    keys : str
        tuple of strings indicating the names of all datasets (components)

    """

    keys = ()
    if isinstance(obj, h5py.Group):
        for key, value in obj.items():
            if isinstance(value, h5py.Group):
                keys = keys + get_all_comp(value)
            else:
                keys = keys + (value.name,)
    return keys

def export_from_multirec_hdf(hf, rec_names, **kwargs):
    """
    Export all specified recordings from h5 file with recordings as groups.
        
    Arguments
    ---------------------------
    hf : obj
        object from h5py representing the h5-file with multiple recordings
    rec_names : str
        list of strings with requested recordings
    component_dict : dict
        dictionary with keys equal the names of either sensor groups or sensors, 
        and items equal the corresponding requested components
    lookup_sensor_groups : True, optional
        specifying if sensor _groups_ are used in component_dict - if False sensor names are used
    decimation_factor : 1, optional
        integer defining the decimation wanted for data retrieval (every n-th sample)
    level_separator : '/', optional
        separator used for dataframes when combining sensor name and component name to a single string

    
    Returns
    ---------------------------
    df_full : obj
        pandas dataframe with all requested data
    """

    if rec_names == 'all':
        rec_names = list(hf.keys())
        
    df_full = pd.DataFrame()
    
    for rec_name in rec_names:
        df = export_from_hdf(hf[rec_name], return_as='dataframe', **kwargs)

        if 't' in df:
            df['t'] = pd.to_datetime(hf[rec_name].attrs['starttime']) + pd.to_timedelta(df['t'], unit='s')
            
        df_full = df_full.append(df)

    if 't' in df:
        df_full = df_full.set_index('t')
        
    return df_full
        
def export_from_hdf(hf_recording, component_dict=None, 
                    lookup_sensor_groups=True,
                    return_as='dataframe', decimation_factor=1,
                    level_separator='/', return_t=True, name_from=None):
    """
    Export data from recording established from h5py.
        
    Arguments
    ---------------------------
    hf_recording : obj
        object from h5py representing the recording (if multiple recs in same file, hf['my_rec_name'])
    component_dict : dict
        dictionary with keys equal the names of either sensor groups or sensors, 
        and items equal the corresponding requested components
    lookup_sensor_groups : True, optional
        specifying if sensor _groups_ are used in component_dict - if False sensor names are used
    return_as : 'dataframe', optional
        how to return data - valid options are 'dataframe', 'array', 'dict'
    decimation_factor : 1, optional
        integer defining the decimation wanted for data retrieval (every n-th sample)
    level_separator : '/', optional
        separator used for dataframes when combining sensor name and component name to a single string
    return_t : True
        whether or not to return time axis
    name_from : str, default=None
        name of sensor from given attribute of sensor group (if None, the original name is used)


    Returns
    ---------------------------
    output
        pandas dataframe, dictionary or array depending on input of return_as
    """
    
    ds = decimation_factor
    
    def get_valid_components():
        if lookup_sensor_groups:
            check_val = sensor_group + ''
        else:
            check_val = sensor + ''
      
        if type(component_dict) is dict:
            if check_val in component_dict:
                return list(component_dict[check_val])
            else:
                return []
        elif component_dict is None:
            return components
        else:
            raise ValueError('Wrong format. Use None or dict as input for sensors_and_components.')
    
    sensor_data = dict()
    sensor_groups = list(hf_recording.keys())
    for sensor_group in sensor_groups:
        sensors_in_group = list(hf_recording[sensor_group].keys())

        for sensor in sensors_in_group:
            components = list(hf_recording[sensor_group][sensor].keys())

            for c in get_valid_components():
                if name_from is not None:
                    sensor_name = hf_recording[sensor_group][sensor].attrs[name_from]
                else:
                    sensor_name = sensor+''

                sc = f'{sensor_name}{level_separator}{c}'
                sensor_data[sc] = hf_recording[sensor_group][sensor][c][::ds]
    
    if 'samplerate' in hf_recording.attrs and 'duration' in hf_recording.attrs and return_t: #global sample rate
        sensor1 = list(sensor_data.keys())[0]  
        sensor_data['t'] = np.linspace(0, hf_recording.attrs['duration'], len(sensor_data[sensor1]))
    
    if return_as == 'array':
        return np.vstack(list(sensor_data.values())).T, list(sensor_data.keys())
    elif return_as == 'dataframe':
        return pd.DataFrame.from_dict(sensor_data)
    elif return_as == 'dict':
        return sensor_data
    else:
        raise ValueError('Use "array", "dataframe" or "dict" as value for return_as')


def convert_stats(stats_dict, sensor_dict=None, fields=['mean', 'std']):
    """
    Convert dictionary with stats to dataframe.
        
    Arguments
    ---------------------------
    stats_dict : dict
        dictionary with nested dictionary with statistics (result from get_stats)
    sensor_dict : dict, optional
        dictionary with keys equal the sensor names and  values equal the sensor type names
    fields : ['mean', 'std'], optional
        statistical fields to convert
   
    Returns
    ---------------------------
    stats_df : dict
        dictionary with requested fields as keys and pandas dataframes 
        with statistics in a flattened format as items
    """
        
    stats_df = {field: pd.DataFrame(stats_dict['recording'], 
                                    columns=['recording']) for field in fields}

    for sensor_name in stats_dict['sensor']:
        sensor_data = stats_dict['sensor'][sensor_name]
        
        if sensor_dict:
            sensor_group = f'{sensor_dict[sensor_name]}/'
        else:
            sensor_group = ''
            
        for comp_ix, comp_name in enumerate(sensor_data['component_names']):
            col_name = f'{sensor_group}{sensor_name}/{comp_name}'
            
            for field in fields:   
                stats_df[field][col_name] = sensor_data[field][:,comp_ix]
              
    for field in fields:
        stats_df[field] = stats_df[field].set_index('recording')
    
    return stats_df


def get_stats(hf_recording, fields=['std', 'mean']):
    """
    Export statistics from recording established from h5py.
        
    Arguments
    ---------------------------
    hf_recording : obj
        object from h5py representing the recording (if multiple recs in same file, hf['my_rec_name'])
    fields : ['mean', 'std'], optional
        statistical fields to import

    Returns
    ---------------------------
    stats : dict
        nested dictionary with these levels: sensor (lowest) / component / field (highest)
    """  
    sensor_dict = create_sensor_dict(hf_recording)
    stats = dict()
    
    sensor_groups = list(hf_recording.keys())
    
    for s in sensor_dict.keys():
        sensor = hf_recording[sensor_dict[s]][s]
        stats[s] = dict()
        components = list(sensor.keys())

        for c in components:
            component = sensor[c]
            stats[s][c] = dict()
            for field in fields:
                stats[s][c][field] = component.attrs[field]
    
    return stats


def get_stats_multi(hf, fields=['mean', 'std'], rec_names=None, avoid=['.global_stats']):
    """
    Export statistics from recording established from h5py.
        
    Arguments
    ---------------------------
    hf : obj
        object from h5py representing the h5-file with multiple recordings
    fields : ['mean', 'std'], optional
        statistical fields to import
    rec_names : str, optional
        list of strings with requested recordings - standard value imports all recordings
    avoid : ['.global_stats'], optional
        list of groups on root (recordings, statistics, etc.) to avoid, s

    Returns
    ---------------------------
    stats_df : dict
        dictionary with requested fields as keys and pandas dataframes 
        with statistics in a flattened format as items
    """  
    
    if rec_names is None:
        rec_names = list(hf.keys())
        
    for el in list(avoid):
        rec_names.remove(el)

    stats_df = dict()
    for field in fields:
        stats_df[field] = pd.DataFrame(rec_names, columns=['recording'])
        
    for ix, rec_name in enumerate(rec_names):        
        for sensor_group in hf[rec_name]:      
            for sensor in hf[f'{rec_name}/{sensor_group}'].keys():
                for comp in hf[f'{rec_name}/{sensor_group}/{sensor}'].keys():
                    col_name = f'{sensor_group}/{sensor}/{comp}'
                    for field in fields:             
                        stats_df[field].at[ix, col_name] = hf[f'{rec_name}/{sensor_group}/{sensor}/{comp}'].attrs[field]
               
    for field in fields:
        stats_df[field] = stats_df[field].set_index('recording')
        
    return stats_df

def load_matlab_rec(path, output_format='dataframe', name='recording'):
    """
    Import legacy Matlab open data files to python,.
        
    Arguments
    ---------------------------
    path : str
        path to mat-file
    output_format : 'dataframe', optional
        how to return data - valid options are 'dataframe', 'array', 'dict
    name : 'recording', optional
        name of variable in Matlab with recording


    Returns
    ---------------------------
    output
        pandas dataframe, dictionary or array depending on input of return_as
    """

    
    def avoid_ugly(arr):
        if arr.size is 1:
            arr = arr.flatten()[0]

        elif arr.dtype.name == 'object':
            value = []
            
            for val in arr[0]:
                if val.size !=0:
                    value.append(val[0])
                else: 
                    value.append('N/A')
            arr = value
                    
        return arr


    tmp = sio.loadmat(path, squeeze_me=False, struct_as_record=True)
    tmp_rec = tmp[name][0][0] 
    
    # ------------ Sensor fields --------------- 
    sensor_names = [sname[0] for sname in tmp_rec['sensor'][0]['sensor_name']]
    sensors = dict()
    
    for sensor_ix, sensor_name in enumerate(sensor_names):
        sensor = tmp_rec['sensor'][0][sensor_ix]
        keys = [key for key in sensor.dtype.names]

        sensordict = dict()
        for key in keys:
            sensordict[key] = avoid_ugly(sensor[key])             # modify to avoid ugly nested numpy arrays
        
        if output_format.lower() == 'dict' or output_format.lower() == 'dictionary': 
            sensors[sensor_name] = sensordict
        else:
            sensors[sensor_name] = namedtuple('Struct', sensordict.keys())(*sensordict.values())           
        
    # ------------ General fields ---------------
    recording = dict()
    keys = [key for key in tmp_rec.dtype.names]
    keys.remove('sensor')

    for key in keys:
        recording[key] = avoid_ugly(tmp_rec[key])
        
    recording['sensor'] = sensors
    
    if output_format.lower() == 'dict' or output_format.lower() == 'dictionary':    
        1 #do nothing    
    elif output_format.lower() == 'dataframe' or output_format.lower() == 'df':
        recording = namedtuple('Struct', recording.keys())(*recording.values())
        data_array = np.hstack([recording.sensor[s].data for s in recording.sensor_names])

        labels = []
        for sensor in recording.sensor_names:
            labels.append([sensor+'_'+component for component in recording.sensor[sensor].component_names])
            
        labels = [item for sublist in labels for item in sublist]
        
        t = recording.t
        recording = pd.DataFrame(data=data_array, columns=labels)
        recording.insert(0, 't', t)    
    elif output_format.lower() == 'struct':  
        recording = namedtuple('Struct', recording.keys())(*recording.values())
    else:
        raise ValueError('No valid output_format is given. Valid options are "dict", "df", and "struct"')

    return recording


def combine_h5s(input_paths, output_path):
    '''
    Create master h5 file linking to several single-recording files.

    Parameters
    ---------------
    input_paths : str
        list of strings of file paths
    output_path : str
        string to save resulting master h5-file
    '''
    with h5py.File(output_path, 'w') as hf:
        for file in input_paths:
            with h5py.File(file, 'r') as hf_file:
                fname = file.split('.h5')[0]
                hf[fname] = h5py.ExternalLink(file, "/")

