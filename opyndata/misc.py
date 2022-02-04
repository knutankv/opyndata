"""
##############################################
Miscellaneous tools
##############################################
Support tools.
"""

from datetime import datetime
from datetime import timedelta
import numpy as np


def datenum_to_datetime(datenum):
    """
    Convert datenumber to datetime
    """

    dt = datetime.fromordinal(int(datenum)) + timedelta(days=datenum%1) - timedelta(days = 366)
    return dt


def create_sensor_dict_from_groups(group_dict):
    """
    Establish sensor dictionary from sensor group dictionary
        
    Arguments
    ---------------------------
    group_dict : dict
        dictionary with keys equal the sensor group/type names and values
        equal the sensor names (inverse of sensor_dict)

    Returns
    ---------------------------
    sensor_dict : dict
        dictionary with keys equal the sensor names and 
        values equal the sensor type names (inverse of group_dict)

    """
    sensor_dict = {}
    for g in group_dict.keys():
        sensors = group_dict[g]
        new_dict = dict(zip(sensors, [g]*len(sensors)))
        sensor_dict.update(new_dict)
        
    return sensor_dict


def create_sensor_dict(hf_recording):
    """
    Establish sensor dictionary from recording established from h5py.
        
    Arguments
    ---------------------------
    hf_recording : obj
        object from h5py representing the recording 
        (if multiple recs in same file, hf['my_rec_name'])

    Returns
    ---------------------------
    sensor_dict : dict
        dictionary with keys equal the sensor names and 
        values equal the sensor type names (inverse of group_dict)

    """
    sensor_groups = list(hf_recording.keys())
    sensor_dict = {}
    
    for g in sensor_groups:
        sensors = list(hf_recording[g].keys())
        g_expanded = [g]*len(sensors)
        new_dict = dict(zip(sensors, g_expanded))

        sensor_dict.update(new_dict)
        
    return sensor_dict


def filter_sensor_dict(sensor_dict, sensors='all', groups='all'):
    """
    Filter sensor dictionary by including certain sensors and certain sensor groups.
        
    Arguments
    ---------------------------
    sensor_dict : dict
        dictionary with keys equal the sensor names and values equal the sensor type names
    sensors : str, optional
        list of strings with sensor names to include in new sensor_dict - standard is 'all'
    groups : str, optional
        list of strings with sensor type/group names to include in new sensor_dict - standard is 'all'
    
    Returns
    ---------------------------
    sensor_dict : dict
        filtered dict

    """
    if sensors != 'all':
        sensor_dict = {sensor:group for sensor, group in sensor_dict.items() if sensor in sensors}
    
    if groups != 'all':
        sensor_dict = {sensor:group for sensor, group in sensor_dict.items() if group in groups}
    
    return sensor_dict


def time_axis(hf_recording, sensor_name, component=None, sensor_dict=None, starttime=0.0):
    """
    Create time axis from h5py data, from specific sensor and component.
        
    Arguments
    ---------------------------
    hf_recording : obj
        object from h5py representing the recording (if multiple recs in same 
        file, hf['my_rec_name'])
    sensor_name : str
        name of sensor
    component : str, optional
        name of component - standard is the first component in the specified sensor
    sensor_dict : dictionary with keys equal the sensor names and values equal the 
        sensor type names (inverse of group_dict)
    starttime : 0.0, optional
        float number indicating first value in time axis

    Returns
    ---------------------------
    t : float
        numpy array of time instances corresponding to the data in the h5py file

    """
    if sensor_dict is None:
        sensor_dict = create_sensor_dict(hf_recording)
    if component is None:
        component = list(hf_recording[sensor_dict[sensor_name]][sensor_name].keys())[0]
        
    t =  np.linspace(0, hf_recording.attrs['duration'], len(hf_recording[sensor_dict[sensor_name]][sensor_name][component]))

    return t

