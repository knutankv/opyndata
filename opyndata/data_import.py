import numpy as np
import scipy.io as sio
from collections import namedtuple
import pandas as pd
import datetime
from .misc import create_sensor_dict
import h5py


def get_all_comp(obj):
    keys = ()
    if isinstance(obj, h5py.Group):
        for key, value in obj.items():
            if isinstance(value, h5py.Group):
                keys = keys + get_all_comp(value)
            else:
                keys = keys + (value.name,)
    return keys


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


def loadrec(path, output_format='dataframe', name='recording'):
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


def export_from_multirec_hdf(hf, rec_names, **kwargs):

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
        
def export_from_hdf(hf, component_dict=None, 
                    lookup_sensor_groups=True,
                    return_as='dataframe', decimation_factor=1):
    
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
    sensor_groups = list(hf.keys())
    for sensor_group in sensor_groups:
        sensors_in_group = list(hf[sensor_group].keys())

        for sensor in sensors_in_group:
            components = list(hf[sensor_group][sensor].keys())

            for c in get_valid_components():
                sc = f'{sensor}_{c}'
                sensor_data[sc] = hf[sensor_group][sensor][c][::ds]
    
    if 'samplerate' in hf.attrs: #global sample rate
        sensor1 = list(sensor_data.keys())[0]  
        sensor_data['t'] = np.linspace(0, hf.attrs['duration'], len(sensor_data[sensor1]))
    
    if return_as == 'array':
        return np.vstack(list(sensor_data.values())).T, list(sensor_data.keys())
    elif return_as == 'dataframe':
        return pd.DataFrame.from_dict(sensor_data)
    elif return_as == 'dict':
        return sensor_data
    else:
        raise ValueError('Use "array", "dataframe" or "dict" as value for return_as')


def convert_stats(stats_dict, sensor_dict=None, fields=['mean', 'std']):
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