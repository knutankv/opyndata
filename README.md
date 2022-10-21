![opyndata logo](https://raw.githubusercontent.com/knutankv/opyndata/master/opyndata-logo.svg)
=======================

What is opyndata?
=======================
OpyNDATA is a package supporting the open data from measurement projects at the Structural Dynamics group at Department of Structural Engineering, NTNU.

Installation 
========================
Either download the repository to your computer and install, e.g. by **pip**

```
pip install .
```

or install directly from github:

```
pip install git+https://www.github.com/knutankv/opyndata.git@master
```

Quick start
=======================
Import the relevant package modules, exemplified for the `data_import` module, as follows:
    
```python
from opyndata import data_import
```

This code snippet imports h5 file into data object:

```python
import h5py

file_name = 'data_2Hz.h5'
rec_name = 'NTNU142M-2016-12-26_22-33-33'
hf = h5py.File(fname, 'r')[rec_name]
```

To establish graphical visualization of data set, the following code can be run:

```python
from opyndata import visualization

data_path = 'C:/Users/knutankv/BergsoysundData/data_10Hz.h5'
app_setup = visualization.AppSetup(data_path=data_path)
app = app_setup.create_app()

server = app.server

if __name__ == '__main__':
    app.run_server(debug=False)
```  

For full code reference visit [knutankv.github.io/opyndata](https://knutankv.github.io/opyndata/).

Examples
=======================
Examples are provided as Jupyter Notebooks in the [examples folder](https://github.com/knutankv/opyndata/tree/master/examples).

Open data
=======================
For open data from us, visit https://www.ntnu.edu/kt/open-data.

Citation
=======================
Cite as:
Knut Andreas Kvåle. (2022). knutankv/opyndata: Initial release, available on Zenodo (v0.0.2). Zenodo. https://doi.org/10.5281/zenodo.5978358

![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5978357.svg)](https://doi.org/10.5281/zenodo.5978357

Support
=======================
Please [open an issue](https://github.com/knutankv/opyndata/issues/new) for support.

