import dash
import dash_core_components as dcc
import dash_html_components as html

from opyndata.misc import create_sensor_dict

import os
import plotly.graph_objs as go
import numpy as np
from flask import send_from_directory
from scipy import signal

import h5py
import matplotlib.pyplot as plt


def plot_sensors(hf_rec, view_axis=None, sensor_type_symbols=None, 
                 sensor_type_colors=None, coordinate_field_name='position', 
                 fig=None, click_callback=None, camera=None, 
                 ):
    """
    Plot sensors in 3d space from coordinates specified in h5py object
        
    Arguments
    ---------------------------
    hf_rec : obj
        object from h5py representing the recording (if multiple recs in same file, hf['my_rec_name'])
    view_axis : int, optional
        scalar indicating axis to show plot from (2d projection)
    sensor_type_symbols : str, optional
        dictionary with keys equal the sensor types/groups and values equal to the string of the symbol to use
    sensor_type_colors : str, optional
        dictionary with keys equal the sensor types/groups and values equal to the color (type must be valid argument in plotly)
    coordinate_field_name : 'position', optional
        from what field should the coordinates be retrieved
    fig : plotly figure object, optional
        figure to plot the sensors in
    click_callback : function, optional
        callback function to run when clicking sensors
    camera : obj, optional
        plotly camera object (e.g. if a consistent view is wanted)

    Returns
    ---------------------------
    fig : obj
        plotly figure object

    """
    
    sensor_types = list(hf_rec.keys())
    
    if fig is None:
        fig = go.Figure(
            data=[],
            layout=go.Layout()
        )
        only_update_data = False
    else:
        only_update_data = True
        fig.update_layout(uirevision='constant')
    
    if sensor_type_symbols is None:
        standard_markers = ['circle', 'cross', 'diamond', 'square', 'x']
        sensor_type_symbols = dict(zip(sensor_types, standard_markers))
        
    if sensor_type_colors is None:
        standard_colors = ['r', 'b', 'g', 'm', 'gray', 'k']
        sensor_type_colors = dict(zip(sensor_types, standard_colors))
                    
    traces = []
    for s_type in sensor_types:
        coors = []
        sensors = list(hf_rec[s_type].keys())
        for s in sensors:
            coors.append(hf_rec[s_type][s].attrs[coordinate_field_name][0])
            
        coors = np.vstack(coors)
        
        ht = '<b>%{text}</b> <br> Position: (%{x}, %{y}, %{z})'
        
        traces.append(
            go.Scatter3d(x=coors[:,0], y=coors[:,1], z=coors[:,2], mode='markers', 
                         name=s_type, text=sensors, hovertemplate=ht))
        
        if click_callback is not None:
            traces[-1].on_click(click_callback(s_type, s))
        
    fig.add_traces(traces)    
    
    if ~only_update_data:
        if camera is None:
            if view_axis is not None:
                vals_eye = [0,0,0]
                vals_up = [0,1,0]   #needs adjustment
                vals_eye[view_axis] = 2.5
                camera = dict(eye=dict(zip(['x', 'y', 'z'], vals_eye)),
                              up=dict(zip(['x', 'y', 'z'], vals_up)), 
                              projection=dict(type='orthographic'))
            else:
                camera = dict(projection=dict(type='orthographic'))
                
        fig.update_layout(scene_aspectmode='data', scene_aspectratio=dict(x=1.5, y=1.5, z=1.5),
                          scene_camera=camera)
    
    for i,d in enumerate(fig.data):
        fig.data[i].marker.symbol = sensor_type_symbols[fig.data[i].name]
            
    return fig

def plot_sensors_2d(hf_rec, axes=[0,1], sensor_type_symbols=None, 
                    sensor_type_colors=None, coordinate_field_name='position', 
                    ax=None):
    """
    Plot sensors in 2d space from coordinates specified in h5py object
        
    Arguments
    ---------------------------
    hf_rec : obj
        object from h5py representing the recording (if multiple recs in same file, hf['my_rec_name'])
    axes : [0,1], optional
        list of two axis indices describing what components to plot (x,y are standard)
    sensor_type_symbols : str, optional
        dictionary with keys equal the sensor types/groups and values equal to the string of the symbol to use
    sensor_type_colors : str, optional
        dictionary with keys equal the sensor types/groups and values equal to the color (type must be valid argument in matplotlib)
    coordinate_field_name : 'position', optional
        from what field should the coordinates be retrieved
    ax : obj, optional
        matplotlib axis object to plot inside


    Returns
    ---------------------------
    fig : obj
        matplotlib figure object

    """

    sensor_types = list(hf_rec.keys())
    
    if sensor_type_symbols is None:
        standard_markers = ['o', '+', '^', 'd', 'v', 'x']
        sensor_type_symbols = dict(zip(sensor_types, standard_markers))
        
    if sensor_type_colors is None:
        standard_colors = ['r', 'b', 'g', 'm', 'gray', 'k']
        sensor_type_colors = dict(zip(sensor_types, standard_colors))
    
    if ax is None:
        fig, ax = plt.subplots(nrows=1, ncols=1)

    for s_type in sensor_types:
        for s in hf_rec[s_type]:
            coors = hf_rec[s_type][s].attrs[coordinate_field_name][0]
            ax.plot(coors[axes[0]], coors[axes[1]], linestyle=None, 
                    color=sensor_type_colors[s_type], marker=sensor_type_symbols[s_type], 
                    label=f'{s_type}: {s}')
    ax.axis('equal')
    ax.legend()
    
    return ax

class AppSetup:
    """
    Class defining Dash application for h5 browsing.
    
    Arguments
    ---------------------------
    data_path : str
        path to h5-file
    logo_path : str, optional
        path to logo to show in dashboard - no logo is standard
    stylesheet_path : 'github', optional
        path to css for stylesheet definitions - standard value uses css from GitHub repository
    requested_stat : ['std', 'mean'], optional
        fields to retrieve in .global_stats


    """

    def __init__(self, data_path,
                logo_path=None,
                stylesheet_path='github', requested_stat=['std', 'mean']):
        
        self.data_path = data_path
        self.logo_path = logo_path
        self.stylesheet_path = stylesheet_path 
        self.hf = h5py.File(data_path, 'r')
        self.requested_stat = requested_stat
        
        
        if self.stylesheet_path == 'github':
            self.stylesheet_path = 'https://knutankv.github.io/open-bridge-data/static/style.css'
        
    def create_app(self):
        # ------------ INITIALIZE LAYOUT ------------
        app = dash.Dash(__name__)
        rec_names = list(self.hf.keys())
        rec_names = [name for name in rec_names if name[0]!='.']
        
        if '.global_stats' in self.hf:
            global_stats = self.hf['.global_stats']
            
            field0 = list(global_stats.keys())[0]
            sensor_types = list(global_stats[field0].keys())
            sensor_gr0 = list(global_stats[field0].keys())[0]
            sensor0 = list(global_stats[field0][sensor_gr0].keys())[0]
            comp0 = list(global_stats[field0][sensor_gr0][sensor0].keys())[0]
        else:
            
            
            
            global_stats = {'Statistics not available':                       # rec name
                                {'N/A':                  # sensor group
                                    {'N/A':              # sensor
                                        {'N/A': np.array([np.nan]*len(rec_names))}}}} # component
            field0 = 'Statistics not available'
            sensor_types = ['N/A']
            sensor_gr0 = 'N/A'
            sensor0 = 'N/A'
            comp0 = 'N/A'
        
        rec0 = self.hf[rec_names[0]]
        opts0 = dict(
            grp = list(rec0.keys()),
            sens = list(rec0[list(rec0.keys())[0]].keys()),
            comp = list(rec0[list(rec0.keys())[0]][list(rec0[list(rec0.keys())[0]].keys())[0]].keys())
            )            
        
        all_fields = list(global_stats.keys())    #all fields in global stats
        valid_fields = [field for field in self.requested_stat if field in all_fields]
        
        # ------------ LAYOUT ------------
        logo_html = html.Img(src=self.logo_path, style={'width': '250px', 'margin':'1em'}) if self.logo_path else []

        app.layout = html.Div(className='main', children=
            [   html.Div(id='buffered_file', style={'display': 'none'}, title=''),        
                html.Link(
                    href=self.stylesheet_path,
                    rel='stylesheet'
                ),

                html.Link(href='https://fonts.googleapis.com/css?family=Source+Sans+Pro',
                rel='stylesheet'),

                logo_html,

                # Statistics and time series selection
                html.H2('Select time series'),
                html.Div(children=[
                        html.Div(
                                dcc.Graph(
                                    id = 'stat-plot',
                                    figure = go.Figure(
                                        data=[
                                            go.Scatter(x=np.arange(len(rec_names)), 
                                                       y=global_stats[field0][sensor_gr0][sensor0][comp0][()], 
                                                       hovertext=rec_names)
                                            ],
                                        layout = go.Layout(xaxis={'title': 'Recording number'}, 
                                                        yaxis={'tickformat': '.1e'}, 
                                                        height=300,  
                                                        margin=dict(l=0,r=0,t=5,b=0))

                                    )
                                ),
                            className='plot'
                        ),

                        html.Div(children=[
                                dcc.Dropdown(
                                    id='file-dropdown',
                                    options = [{'label':name, 'value':name} for name in rec_names],
                                    value = rec_names[0]
                                ),
                                
                                html.Div(style={'margin-top': '0.5em', 'margin-bottom': '1em'}),    
                                
                                dcc.Dropdown(
                                    id='sensor_group-dropdown-stat',
                                    options = [{'label':name, 'value':name} for name in sensor_types],
                                    value = sensor_types[0],
                                ),
                                
                                
                                dcc.Dropdown(
                                    id='sensor-dropdown-stat',
                                    options = [{'label':name, 'value':name} for name in global_stats[field0][sensor_gr0].keys()],
                                    value = list(global_stats[field0][sensor_gr0].keys())[0],
                                ),
                                
        
                                dcc.Dropdown(
                                    id='component-dropdown-stat',
                                    options=[{'label':name, 'value':name} for name in global_stats[field0][sensor_gr0][sensor0].keys()],
                                    value=list(global_stats[field0][sensor_gr0][sensor0].keys())[0]
                                ),

                                html.H4('Plot type'),
                                
                                dcc.Dropdown(
                                    id='stat-field-dropdown',
                                    options=[{'label':name, 'value':name} for name in valid_fields],
                                    value=valid_fields[0]),  
                            ], className='sac'
                        )
                ], className ='plot_wrapper'
                ),

                # Time series study
                html.H2(children=['Study time series'], className='h2'),
                html.Div(children=[
                        html.Div(
                                dcc.Graph(
                                    id = 'sensor-data-plot',
                                    figure = go.Figure(
                                        data=[
                                            go.Scatter(x=[], y=[])
                                            ],
                                        layout = go.Layout(xaxis={'title': 'Time [s]'}, height=300, margin=dict(l=0,r=0,t=20,b=0))
                                    )
                                ),
                            className='plot'
                        ),

          
                        html.Div(children=[
                                dcc.Dropdown(
                                    id='sensor_group-dropdown',
                                    options = [{'label':name, 'value':name} for name in opts0['grp']],
                                    value = opts0['grp'][0],
                                ),
                            
                                dcc.Dropdown(
                                    id='sensor-dropdown',
                                    options = [{'label':name, 'value':name} for name in opts0['sens']],
                                    value =  opts0['sens'][0],
                                ),
                                

                                dcc.Dropdown(
                                    id='component-dropdown',
                                    options = [{'label':name, 'value':name} for name in opts0['comp']],
                                    value = opts0['comp'][0],
                                ),  

                                html.H3('Options and visualization'),

                                dcc.RadioItems(
                                    id='psd-radio',
                                    options=[
                                        {'label': 'Time history', 'value': 'time'},
                                        {'label': 'Power spectral density', 'value': 'freq'},
                                    ],
                                    value='time'
                                ),

                                html.Div(children=[
                                    dcc.Checklist(
                                        id='detrend-checkbox',
                                        options= [{'label': 'Detrend (time history)', 'value': 1}],
                                        value=[1]
                                    ) ]
                                ),  

                                html.H4('Welch estimation'),
                                html.Div(children=[

                                    html.Div(children=[
                                        dcc.Slider(
                                            id='nfft-slider',
                                            min=0,
                                            max=11-6,
                                            step=None,
                                            marks={(n-6):str(int(2**n)) for n in [6,7,8,9,10,11]},
                                            value=3
                                        )
                                        ], style={'width':'100%'}),
                                    html.Div(children=[
                                        dcc.Slider(
                                            id='zp-slider',
                                            min=1,
                                            max=8,
                                            step=1,
                                            marks={n:str(n) for n in range(1,8+1)},
                                            value=2
                                    )
                                    ], style={'width':'100%'})],         
                                ),                     
                                    
                                
                            ], className='sac'
                        )
                ], className ='plot_wrapper'
                ),
                
                # Sensor plot
                html.H2(children=['Sensor layout'], className='h2'),
                
                html.Div(children=[
                    
                    # html.Div(children=[
                        
                        dcc.Graph(
                            id = 'sensor-plot',
                            figure = plot_sensors(self.hf[rec_names[0]], view_axis=2)
                            )
                        
                        # ], className ='plot')
                    
                    ], className='plot_wrapper')
                
                ]
            )


        #%% ------------ CALLBACKS -------------- #
        ###########################################
        
        
        #%% Figure updating
        # Stat plot click callback
        @app.callback(
            dash.dependencies.Output('file-dropdown', 'value'),
            [dash.dependencies.Input('stat-plot', 'clickData')])
        def select_file_by_click(clickData):
            if clickData:
                ix = clickData['points'][0]['pointIndex']
                load_file = rec_names[ix]
            else:
                load_file = rec_names[0]
            return load_file
        
        # Sensor plot click
        @app.callback(
            [dash.dependencies.Output('sensor_group-dropdown', 'value'),
             dash.dependencies.Output('sensor-dropdown', 'value')],     # output from next function
            
            [dash.dependencies.Input('sensor-plot', 'clickData')],
            [dash.dependencies.State('file-dropdown', 'value'),
             dash.dependencies.State('sensor_group-dropdown', 'value'),
             dash.dependencies.State('sensor-dropdown', 'value')
             ]
        )
        def sensor_click_fun(clickData, selected_file, sgroup, s):
            sensor_dict = create_sensor_dict(self.hf[selected_file])
            if clickData is not None:
                sensor = clickData['points'][0]['text']
                return [sensor_dict[sensor], sensor]
            else:
                return [sgroup, s]
            
        # Stat plot
        @app.callback(
            dash.dependencies.Output('stat-plot', 'figure'),
            [dash.dependencies.Input('sensor_group-dropdown-stat', 'value'),
             dash.dependencies.Input('sensor-dropdown-stat', 'value'),
            dash.dependencies.Input('component-dropdown-stat', 'value'),
            dash.dependencies.Input('stat-field-dropdown', 'value')
            ]
        )
        def update_figure_stat(selected_group, selected_sensor, selected_component, stat_quantity):
            gr = selected_group
            s = selected_sensor
            c = selected_component
            f = stat_quantity
              
            if f is None or f not in global_stats:
                missing = 'field'
            elif gr is None or gr not in global_stats[f]:
                missing = 'sensor group'  
            elif s is None or s not in global_stats[f][gr]:
                missing = 'sensor'
            elif c is None or c not in global_stats[f][gr][s]:
                missing = 'component'
            else:
                missing = None
            
            
            if missing is None:
                y = global_stats[f][gr][s][c][()]
                
                figout = go.Figure(
                                        data=[
                                            go.Scatter(x=np.arange(len(rec_names)), y=y, hovertext=rec_names)
                                            ],
                                        layout = go.Layout(xaxis={'title': 'Recording number'},  yaxis={'tickformat': '.1e'})
                                    )
                figout.update_layout(height=300, margin=dict(l=0,r=0,t=20,b=0))
            else:
                figout = go.Figure(data=[go.Scatter(x=None, y=None)])
                figout.add_annotation(x=0.5, y=0.5,
                      text=f'Please select {missing}...',
                      showarrow=False)
            return figout


        # Sensor plot        
        @app.callback(
            dash.dependencies.Output('sensor-plot', 'figure'),        # output from next function
            dash.dependencies.Input('file-dropdown', 'value'),
            dash.dependencies.State('sensor-plot', 'figure'))      # specified input given to next function

        def update_sensor_figure(selected_file, fig):
            
            if fig is not None:        
                fig['data'] = []
                fig = go.Figure(**fig)
                fig = plot_sensors(self.hf[selected_file], fig=fig)
                
            return fig
           
                        
        # Time series plot
        @app.callback(
            dash.dependencies.Output('sensor-data-plot', 'figure'),        # output from next function
            [dash.dependencies.Input('sensor_group-dropdown', 'value'),
             dash.dependencies.Input('sensor-dropdown', 'value'),
            dash.dependencies.Input('component-dropdown', 'value'),
            dash.dependencies.Input('file-dropdown', 'value'), 
            dash.dependencies.Input('detrend-checkbox', 'value'),
            dash.dependencies.Input('psd-radio', 'value'),
            dash.dependencies.Input('nfft-slider', 'value'),
            dash.dependencies.Input('zp-slider', 'value')])      # specified input given to next function

        def update_figure(selected_group, selected_sensor, selected_component, 
                          selected_file, detrend_state, domain, nfft, zp):
            gr = selected_group
            s = selected_sensor
            c = selected_component

            selected_hf = self.hf[selected_file]
            
            if gr is None or gr not in selected_hf:
                missing = 'sensor group'
            elif s is None or s not in selected_hf[gr]:
                missing = 'sensor'
            elif c is None or c not in selected_hf[gr][s]:
                missing = 'component'
            else:
                missing = None
            
            
            if missing is None:
                y = selected_hf[gr][s][c][()]
        
                if np.any(np.isnan(y)) and (detrend_state or domain=='freq'):
                    figout = go.Figure(data=[go.Scatter(x=None, y=None)])
                    figout.add_annotation(x=0.5, y=0.5,
                        text='NaNs detected - reduce post-processing',
                        showarrow=False)   
                else:     
                    t_max = selected_hf.attrs['duration']
                    n = len(y)
                    x = np.linspace(0, t_max, n)
        
                    if detrend_state:
                        y = signal.detrend(y)
        
                    if domain == 'freq':
                        fs = 1/(x[1]-x[0])
                        x, y = signal.welch(signal.detrend(y), fs, nperseg=2**(nfft+6), nfft=zp*2**(nfft+6))
                        layout = go.Layout(xaxis={'title': 'Frequency [Hz]'}, yaxis={'tickformat': '.1e'})
                    else:
                        layout = go.Layout(xaxis={'title': 'Time [s]'}, yaxis={'tickformat': '.1e'})
        
                    figout = go.Figure(
                                data=[
                                    go.Scatter(x=x, y=y
                                    )
                                ],
                                layout = layout
                                )
                    figout.update_layout(height=300, margin=dict(l=0,r=0,t=20,b=0))
                   
            else:
                
                figout = go.Figure(data=[go.Scatter(x=None, y=None)])
                figout.add_annotation(x=0.5, y=0.5,
                    text=f'Please select {missing}...',
                    showarrow=False)

            return figout
        
        
        
        #%% STATISTICS DROPDOWN
        # Sensor group --> sensors
        @app.callback(
            dash.dependencies.Output('sensor-dropdown-stat', 'value'),       # output from next function
            [dash.dependencies.Input('sensor_group-dropdown-stat', 'value')])      # specified input given to next function
        def update_sensor_dropdown_value_stat(selected_group):
            updated_sensor_value = list(list(global_stats.values())[0][selected_group].keys())[0]
            return updated_sensor_value

        @app.callback(
            dash.dependencies.Output('sensor-dropdown-stat', 'options'),       # output from next function
            [dash.dependencies.Input('sensor_group-dropdown-stat', 'value')])      # specified input given to next function
        def update_sensor_dropdown_stat(selected_group):
            valid_opts = list(list(global_stats.values())[0][selected_group].keys())
            updated_sensor_options = [{'label':name, 'value':name} for name in valid_opts]            
            return updated_sensor_options
        
        # Sensor --> component
        @app.callback(
            dash.dependencies.Output('component-dropdown-stat', 'options'),       # output from next function
            [dash.dependencies.Input('sensor_group-dropdown-stat', 'value'),
             dash.dependencies.Input('sensor-dropdown-stat', 'value')])      # specified input given to next function
        def update_component_dropdown_stat(selected_group, selected_sensor):
            valid_opts = list(list(global_stats.values())[0][selected_group][selected_sensor].keys())
            updated_component_options = [{'label':name, 'value':name} for name in valid_opts]            
            return updated_component_options

        #%% TIME SERIES DROPDOWN
        # File --> sensor groups
        @app.callback(
             dash.dependencies.Output('sensor_group-dropdown', 'options'),
             dash.dependencies.Input('file-dropdown', 'value')
            )
             
        def update_group_dropdown(selected_file):
            selected_hf = self.hf[selected_file]
            opts = [{'label':name, 'value':name} for name in list(selected_hf.keys())]    
            return opts
        
        # Sensor group + file --> sensors
        @app.callback(
            dash.dependencies.Output('sensor-dropdown', 'options'),       # output from next function
            dash.dependencies.Input('file-dropdown', 'value'),
            dash.dependencies.Input('sensor_group-dropdown', 'value')
            )      # specified input given to next function
        def update_sensor_dropdown(selected_file, selected_group):
            selected_hf = self.hf[selected_file]
            
            if selected_group not in selected_hf:
                valid_opts = ['']
            else:
                valid_opts = list(selected_hf[selected_group].keys())
                
            updated_sensor_options = [{'label':name, 'value':name} for name in valid_opts]            
            return updated_sensor_options

        # Sensor group + file + sensor --> component
        @app.callback(
            dash.dependencies.Output('component-dropdown', 'options'), # output from next function
            dash.dependencies.Input('file-dropdown', 'value'), 
            dash.dependencies.Input('sensor_group-dropdown', 'value'),
            dash.dependencies.Input('sensor-dropdown', 'value'))      # specified input given to next function
        
        def update_component_dropdown(selected_file, selected_group, selected_sensor):
            selected_hf = self.hf[selected_file]
                        
            if selected_group not in selected_hf:
                valid_opts = ['']
            
            elif selected_sensor not in selected_hf[selected_group]:
                valid_opts = ['']
            
            else:
                valid_opts = list(selected_hf[selected_group][selected_sensor].keys())
            
            updated_component_options = [{'label':name, 'value':name} for name in valid_opts]   
  
            return updated_component_options
        
        

        @app.server.route('/static/<recpath>')
        def static_file(recpath):
            static_folder = os.path.join(os.getcwd(), 'static')
            return send_from_directory(static_folder, recpath)


        return app