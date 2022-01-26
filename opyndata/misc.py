from datetime import datetime
from datetime import timedelta
import numpy as np


def datenum_to_datetime(datenum):
    dt = datetime.fromordinal(int(datenum)) + timedelta(days=datenum%1) - timedelta(days = 366)
    return dt


def create_sensor_dict_from_groups(group_dict):
    sensor_dict = {}
    for g in group_dict.keys():
        sensors = group_dict[g]
        new_dict = dict(zip(sensors, [g]*len(sensors)))
        sensor_dict.update(new_dict)
        
    return sensor_dict

def create_sensor_dict(hf_recording):
    sensor_groups = list(hf_recording.keys())
    sensor_dict = {}
    
    for g in sensor_groups:
        sensors = list(hf_recording[g].keys())
        g_expanded = [g]*len(sensors)
        new_dict = dict(zip(sensors, g_expanded))

        sensor_dict.update(new_dict)
        
    return sensor_dict


def time_axis(hf_recording, sensor_name, component=None, sensor_dict=None, starttime=0):
    if sensor_dict is None:
        sensor_dict = create_sensor_dict(hf_recording)
    if component is None:
        component = list(hf_recording[sensor_dict[sensor_name]][sensor_name].keys())[0]
        
    return np.linspace(0, hf_recording.attrs['duration'], len(hf_recording[sensor_dict[sensor_name]][sensor_name][component]))

def make_path(paths):
    # Sort so deepest paths are first
    paths = sorted(paths, key = lambda s: len(s.lstrip('/').split('/')), reverse = True)

    tree_path = {}
    for path in paths:
        # Split into list and remove leading '/' if present
        levels = path.lstrip('/').split("/")
        
        file = levels.pop()
        acc = tree_path
        for i, p in enumerate(levels, start = 1):
            if i == len(levels):
                # Reached termination of a path
                # Use current terminal object is present, else use list
                acc[p] = acc[p] if p in acc else []
                if isinstance(acc[p], list):
                    # Only append if we are at a list
                    acc[p].append(file)
            else:
                # Exaand with dictionary by default
                acc.setdefault(p, {})
            acc = acc[p]

    return tree_path