import fnmatch
from opyndata.misc import get_all_dataset_names
import h5py

def apply_to_all_data(hf, fun=lambda x: x, pattern='*', output_path='tmp.h5'):
    '''
    Apply function to all datasets in hf object. Note that the function modifies
    the input hf object - please ensure that you input data that is okay to mess around with.

    Parameters
    -----------
    hf : obj
        object from h5py representing a group or file
    fun : function
        function to apply to relevant datasets
    pattern : default='*'
        pattern to match with full paths, defining what datasets to filter;
        follows convention of `fnmatch` function in the `fnmatch` package, see
        example below
    create_copy : bool, default=False
        if True, a temporary file is created to store the data

    Returns
    --------------
    hf : obj
        modified version of input object; make sure to create copies before running function

    Example
    --------------
    To lowpass filter (`sos` from scipy) all datasets in acceleration group, the following code can be used:

    ```
    from scipy.signal import sosfiltfilt
    fun = lambda x: sosfiltfilt(x, sos, axis=0)
    pattern = '/acceleration/*'
    hf_filtered = apply_to_all_data(hf, fun=fun, pattern=pattern)
    ```

    '''
    print(output_path)
    with h5py.File(output_path, 'w') as hf_out:
        names = get_all_dataset_names(hf)
        names_to_filter = [s for s in names if fnmatch.fnmatch(s, pattern)]
        
        for obj in hf:
            hf.copy(obj, hf_out, expand_external=True)

        for key in hf.attrs:
            hf_out.attrs[key] = hf.attrs[key]

        for name in names_to_filter:
            hf_out[name][:] = fun(hf_out[name][:])
