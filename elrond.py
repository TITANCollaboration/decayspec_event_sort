# *************************************************************************************
# * Written by : Jon Ringuette
# * Started : August 12 2021 - Still during the plague..
# * Purpose : Online and offline analysis of histogram data
#  * Requirements : Python 3, Dash  1.21+, pandas
# *************************************************************************************

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, ALL, MATCH
from random import randrange
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from math import log
import numpy as np
import json
from pathlib import Path
import glob
import base64
import datetime
from os.path import exists
from lib.histogram_generator import hist_gen
from lib.online_analyzer_requests import online_analyzer_requests
from lib.energy_calibration import energy_calibration

#from lib.radware_fit import radware_fit

app = dash.Dash(__name__)

app.config.suppress_callback_exceptions = True

tabs_styles = {
    'height': '30px'
}
tab_style = {
    'color': 'grey',
    'borderBottom': '2px solid #d6d6d6',
    'padding': '2px',
    'fontWeight': 'bold'
}

tab_selected_style = {
    'borderTop': '1px solid #4C4C4C',
    'borderBottom': '1px solid #4C4C4C',
    'backgroundColor': '#119DFF',
    'color': 'white',
    'padding': '2px'
}

upload_data = html.Div([
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select Files')
            ]),
            style={
                'width': '90%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '2px',
                'textAlign': 'center',
                'margin': '20px'
            },
            # Allow multiple files to be uploaded
            multiple=True
        ),
        html.Div(id='output-data-upload'),
    ], style={'float': 'right'})

nudat_form = html.Div([html.Form([
                                html.Label(['NuDat Lookup ',
                                dcc.Input(name='nuc', type="text", style={'width':'60px'}, minLength=2, maxLength=5, placeholder="ex. sb129")]),
                                html.Button('Submit', type='submit', value='go')],
                                action='https://www.nndc.bnl.gov/nudat2/decaysearchdirect.jsp',
                                target="_blank", method='post')])

graph_title_form = html.Div([
                            dcc.Input(id='graph_title', type="text", style={'width':'200px'}, placeholder="Graph Title")])


channel_selections_from_hist = html.Div()

channel_selections_from_daqs = html.Div([
                            dcc.Dropdown(
                                id={'type': 'selected_chan_dropdown', 'index': 'n_clicks'},
                                options=[
                                        {"label": chan, "value": 'grif16_' + str(chan)}
                                        for chan in range(0, 16)
                                        ],
                                style={'width': '40vH', 'height': '40px'},
                                multi=True,
                                placeholder="GRIF16 Channel Select"
                            ),
                            dcc.Dropdown(
                                id={'type': 'selected_chan_dropdown', 'index': 'n_clicks'},
                                options=[
                                        {"label": chan, "value": 'mdpp16_' + str(chan)}
                                        for chan in range(0, 16)
                                        ],
                                style={'width': '40vH', 'height': '40px'},
                                multi=True,
                                placeholder="MDPP16 Channel Select")

                        ], style=dict(display='flex'))

tabbed_modes = html.Div([dcc.Tabs(id='mode-tabs', value='offline-analysis', children=[
                         dcc.Tab(label='Offline', value='offline-analysis', style=tab_style, selected_style=tab_selected_style),
                         dcc.Tab(label='Online', value='online-analysis', style=tab_style, selected_style=tab_selected_style),
                         ], style=tabs_styles)])

offline_tab_content = html.Div([html.Div(className='clear'),
                                upload_data,
                                html.Button('Plus', id='add-file-hist', n_clicks=0),
                                html.Button('Minus', id='remove-file-hist', n_clicks=0),
                                html.Div(id='hist-dropdown-list', children=[]),
                                html.Div(className='clear'),
                                ])

online_tab_content = html.Div([
                        channel_selections_from_daqs,
                        html.Div(id={'type': 'temporal_graph', 'index': 'my_temporal_graph_index'})])

header = html.Header([html.Span('GammaGraph', style={'float': 'left'}),
                      html.Span(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"), style={'float': 'right'}),
                      html.Div(className='clear')], className='header')

 #html.Div(className="container__right", children=[
graph_controls = html.Div(children=[html.Label(['Y-Axis :',
                    dcc.RadioItems(
                            id='yaxis-type',
                            options=[{'label': axis_type_select, 'value': axis_type_select} for axis_type_select in ['Linear', 'Log']],
                            value='Linear',
                            )
                ], style=dict(display='flex')),
                html.Hr(),
                html.Label(['xmin ',
                    dcc.Input(
                        id="xmin", type="number",
                        debounce=True, value=0, style={'width':'65px'})
                ]),
                html.Br(),
                html.Label(['xmax ',
                    dcc.Input(
                        id="xmax", type="number",
                        debounce=True, style={'width':'65px'})
                ]),
                html.Hr(),
#                html.Br(),
                html.Label(['ymin ',
                    dcc.Input(
                        id="ymin", type="number", min=0,
                        debounce=True, value=0, style={'width':'65px'})
                ]),
                html.Br(),
                html.Label(['ymax ',
                    dcc.Input(
                        id="ymax", type="number",
                        debounce=True, style={'width':'65px'})
                ]),
                html.Br(),
                html.Hr(),
                html.Button('Unzoom', id='unzoom-graph', n_clicks=0),
                ])
app.title = 'GammaGraph'

plotly_graph_settings = {'displaylogo': False,
                         'toImageButtonOptions': {
                                'format': 'png', # one of png, svg, jpeg, webp
                                'filename': 'custom_image',
                                'height': 1080,
                                'width': 1440,
                                'scale': 2.5 # Multiply title/legend/axis/canvas sizes by this factor
                                },
                        }

app.layout = html.Div([
    header,
    nudat_form,
    #graph_controls,
    html.Hr(),
    #tabbed_modes,
    dcc.Store(id='tab-mode-selection'),
    dcc.Store(id='hist_filename'),
    dcc.Store(id='graphing_online_ph_vs_time'),
    html.Div(id='tabs-content-inline'),
    html.Hr(),
    html.Main(className="container__main",
              children=[
                        html.Div(dcc.Graph(id='hist_graph_display', config=plotly_graph_settings), className="container__middle"),
                        html.Div(className="container__right",
                                 children=[
                                           tabbed_modes,
                                           html.Hr(),
                                           graph_controls,
                                           html.Hr(),
                                           graph_title_form])]),
    html.Div(dcc.Interval(id='temporal-hist-interval-component', interval=999999999)),
    html.Div(dcc.Interval(id='interval-component', interval=999999999)),
    html.Div([html.Button('Fit Peak', id='fit-peak-button', value=None, n_clicks=0),
              dcc.Store(id='peak_fit_first_point')]),
    html.Div(id='channel_list_with_info', children=[]),
])


@app.callback(Output('tabs-content-inline', 'children'),
              Output('tab-mode-selection', 'data'),
              Input('mode-tabs', 'value'),
              State('tab-mode-selection', 'data')
              )
def render_tab_content(tab_selection, tab_mode):
    tab_mode = tab_selection
    if tab_selection == 'offline-analysis':
        return offline_tab_content, tab_mode
    elif tab_selection == 'online-analysis':
        return online_tab_content, tab_mode


@app.callback(Output({'type': 'temporal_graph', 'index': ALL}, 'children'),
              Output('temporal-hist-interval-component', 'interval'),
              Output('graphing_online_ph_vs_time', 'data'),
              Output({'type': 'pulse_height_vs_time', 'index': ALL}, 'n_clicks'),
              [Output({'type': 'online_ph_v_time_hist_graph', 'index': ALL}, 'figure')],
              Input('temporal-hist-interval-component', 'n_intervals'),
              Input('temporal-hist-interval-component', 'interval'),
              Input({'type': 'pulse_height_vs_time', 'index': ALL}, 'n_clicks'),
              Input({'type': 'selected_chan_dropdown', 'index': ALL}, 'value'),
              Input({'type': 'temporal_graph', 'index': ALL}, 'children'),
              State('graphing_online_ph_vs_time', 'data'),
              State({'type': 'online_ph_v_time_hist_graph', 'index': ALL}, 'figure'),
              )
def online_temporal_histogram(temporal_hist_interval_component, temporal_hist_interval_time, pulse_height_vs_time_nclicks, selected_chan_dropdown_value, temporal_graph_children, graphing_online_ph_vs_time_data, mine):
    return_figure_data = True  # if we should return figure data or just []
    online_ph_v_time_hist_graph = []
    pulse_height_vs_time_n_clicks_output = []
    #  Check if mdpp16_0 is in the list, there are some problems here but oh well, also make sure we aren't
    #  already performing a temporal histogram plot

    triggered = [t["prop_id"] for t in dash.callback_context.triggered]
    if triggered[0] == '.':  # This should be the initial run
        graphing_online_ph_vs_time_data = False

    if ('mdpp16_0' in str(selected_chan_dropdown_value)) and (graphing_online_ph_vs_time_data is False):
        temporal_graph_children[0] = [html.Button('PH v. Time', id={'type': 'pulse_height_vs_time', 'index': 'pulse_height_vs_time'}, n_clicks=0)]

    if pulse_height_vs_time_nclicks:  # Check if it exists or if this is just the init run
        if (pulse_height_vs_time_nclicks[0] == 1):  # Check if the button was pushed
            if graphing_online_ph_vs_time_data is True:  # Flip value every button press
                graphing_online_ph_vs_time_data = False
            else:
                graphing_online_ph_vs_time_data = True
            pulse_height_vs_time_n_clicks_output = pulse_height_vs_time_nclicks
            pulse_height_vs_time_n_clicks_output[0] = pulse_height_vs_time_n_clicks_output[0] - 1

            if graphing_online_ph_vs_time_data is False:  # if it's even shut off the graph and interval timer
                temporal_hist_interval_time = 999999999
                temporal_graph_children[0] = [html.Button('PH v. Time', id={'type': 'pulse_height_vs_time', 'index': 'pulse_height_vs_time'}, n_clicks=0)]
                return_figure_data = False
                online_ph_v_time_hist_graph = [create_temporal_hist()] # Need to append a graph one more time before the dcc.graph element goes away
            else:  # We should be graphing here..
                online_ph_v_time_hist_graph = create_temporal_hist()  # Get initial graphing data
                temporal_graph_children[0].append(dcc.Graph(id={'type': 'online_ph_v_time_hist_graph', 'index': 'online_ph_v_time_hist_graph_index'}, figure=online_ph_v_time_hist_graph))
                temporal_hist_interval_time = 5*1000
                return_figure_data = False
        else:
            pulse_height_vs_time_n_clicks_output = pulse_height_vs_time_nclicks

    if graphing_online_ph_vs_time_data is True:  # Check if we've set stuff and need to handle this differently
        if return_figure_data is True:
            online_ph_v_time_hist_graph = [create_temporal_hist()]
        else:
            online_ph_v_time_hist_graph = []

        pulse_height_vs_time_n_clicks_output = pulse_height_vs_time_nclicks
    return temporal_graph_children, temporal_hist_interval_time, graphing_online_ph_vs_time_data, pulse_height_vs_time_n_clicks_output, online_ph_v_time_hist_graph

@app.callback(
    Output('xmin', 'value'),
    Output('xmax', 'value'),
    Output('ymin', 'value'),
    Output('ymax', 'value'),
    #Output('hist_relay_data', 'relayoutData'),
    Input('hist_graph_display', 'relayoutData'))
def zoom_event(relayoutData):
    print("relayoutData", relayoutData)
    if relayoutData is None or ('dragmode' in relayoutData.keys()):
        print("We're getting to the exception!!")
        raise dash.exceptions.PreventUpdate

    if 'xaxis.autorange' in relayoutData.keys():
        print("Do something, we're zoomed out..")
        return 0, 0, 0, 0 # , []

    else:
        if 'xaxis.range[0]' in relayoutData.keys() and (relayoutData['yaxis.range[0]'] < 0):
            relayoutData['yaxis.range[0]'] = 0
        if 'xaxis.range[0]' in relayoutData.keys():
            return int(relayoutData['xaxis.range[0]']), int(relayoutData['xaxis.range[1]']), int(relayoutData['yaxis.range[0]']), int(relayoutData['yaxis.range[1]']) # , []
    return 0, 0, 0, 0 # , []


@app.callback(
            Output('hist-dropdown-list', 'children'),
            Input('add-file-hist', 'n_clicks'),
            Input('remove-file-hist', 'n_clicks'),
            State('hist-dropdown-list', 'children')
              )
def create_hist_file_dropdown(add_nclicks, remove_nclicks, hist_dropdown):
    # Create list of available files to select and imbed an element for channnel selection
    # once file is selected, also add and remove file elements
    triggered = [t["prop_id"] for t in dash.callback_context.triggered]
    if triggered[0] != 'remove-file-hist.n_clicks':
        my_id = 'hist_file_selection_' + str(add_nclicks)
        chan_dropdown_id = 'chan_selection_' + str(add_nclicks)
        hist_dropdown.append(html.Div([
                dcc.Dropdown(
                    id={'type': 'hist_filename_dropdown', 'index': my_id},
                    style={'width': '40vH', 'height': '40px'},
                    options=get_hist_files_avail(),
                    multi=False,
                    placeholder="Select Histogram"
                )
             , html.Div(id={'type': 'chan_dropdown', 'index':chan_dropdown_id}, children=[])], style=dict(display='flex')))
    elif triggered[0] == 'remove-file-hist.n_clicks':
        if len(hist_dropdown) > 1:
            hist_dropdown = hist_dropdown[:-1]
    return hist_dropdown


@app.callback(
    Output('hist_filename', 'data'),
    Output({'type': 'chan_dropdown', 'index': ALL},  'children'),
    Input({'type': 'hist_filename_dropdown', 'index': ALL}, 'value'),
    State({'type': 'chan_dropdown', 'index': ALL}, 'children'),
    State({'type': 'chan_dropdown', 'index': ALL}, 'index'),
#    State('hist_available_channel_dropdown', 'children'),
    State('hist_filename', 'data'),
)
def set_static_hist_filename_w_chan_selection(hist_file_selection, hist_available_channel_dropdown, chan_index, stored_hist_filename):
    #print("Chan index! :", chan_index)
    #print("Hist selection", hist_file_selection)
    #print("hist_available_channel_dropdown", hist_available_channel_dropdown)
    stored_hist_filename = hist_file_selection
    #hist_file_selection = hist_file_selection[0]
    print("Stored value", stored_hist_filename)
    for my_file_index in enumerate(hist_file_selection):
        current_file = my_file_index[1]
        if current_file is not None:
            mydata_df = pd.read_csv(current_file, sep='|', nrows=0, engine='c')
            print("Current File:", current_file, "Channels available:", mydata_df.columns)
            channel_names = []
            for available_chan in mydata_df.columns:
                # Create channel values that are prefixed with the filename to keep track
                # of which channel goes with which file
                channel_names.append(new_chanel_name(current_file, available_chan))

            hist_available_channel_dropdown[my_file_index[0]] = html.Div([
                                                dcc.Dropdown(
                                                            id={'type': 'selected_chan_dropdown', 'index': my_file_index[1]},
                                                            options=[{'label': i, 'value': j} for i, j in zip(mydata_df.columns, channel_names)],
                                                            style={'width': '40vH', 'height': '40px'},
                                                            multi=True,
                                                            placeholder="Select Channel")
                                                            ])
    return stored_hist_filename, hist_available_channel_dropdown

@app.callback(
    Output('hist_graph_display', 'figure'),
    Output('peak_fit_first_point', 'data'),
    Output('interval-component', 'interval'),
    Output('fit-peak-button', 'n_clicks'),
    Output('hist_graph_display', 'clickData'),
    Output('channel_list_with_info', 'children'),
    Output('fit-peak-button', 'value'),
    Input('interval-component', 'n_intervals'),
    Input('yaxis-type', 'value'),
    Input("xmin", "value"),
    Input("xmax", "value"),
    Input("ymin", "value"),
    Input("ymax", "value"),
    Input("unzoom-graph", 'n_clicks'),
    Input({'type': 'selected_chan_dropdown', 'index': ALL}, 'value'),
    Input('fit-peak-button', 'n_clicks'),
    Input('fit-peak-button', 'value'),
    Input({'type': 'fit_chan_radio', 'index': ALL}, 'value'),
    Input('hist_graph_display', 'clickData'),
    Input('channel_list_with_info', 'children'),
    Input('graph_title', 'value'),
#    Input('hist_relay_data', 'relayoutData'),
    State('peak_fit_first_point', 'data'),
    State('hist_filename', 'data'),
    State('tab-mode-selection', 'data'),

    )
def process_static_hist(n_intervals, yaxis_type, xmin, xmax, ymin, ymax, unzoom, hist_available_channel_list, fit_peak_button, fit_peak_button_value, fit_chan_radio_value, hist_graph_click_data, channel_list_with_info, graph_title, stored_data, stored_hist_filename, tab_mode_selection, ):
    print("hist_graph_display:", hist_graph_click_data)
    print("dash.callback_context:", dash.callback_context)
    #print("hist_relay_data:", hist_relay_data)
    if fit_chan_radio_value:
        fit_peak_button_value = fit_chan_radio_value[0]
    else:
        fit_peak_button_value = None
    triggered = [t["prop_id"] for t in dash.callback_context.triggered]
    print("Graph Title!!:", graph_title)
    print("Triggerd:", triggered)
    update_interval = 9999999999  # Set this to a long period of time assuming we're in offline mode, change it only when we are definitly in online mode with channels selected.

    channels_to_display = []
    for channels in hist_available_channel_list:
        if channels is not None:
            channels_to_display.extend(channels)

    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]  # determines what property changed, in this case which button was pushed
    #print("Change id", changed_id)
    hist_file_selection = stored_hist_filename

    if len(channels_to_display) > 0:
        if tab_mode_selection == "offline-analysis":
            if hist_file_selection is None:
                raise dash.exceptions.PreventUpdate
            mydata_df = pd.DataFrame()
            for hist_file_enum in enumerate(stored_hist_filename):
                if hist_file_enum[1] is not None:
                    tmp_df = pd.read_csv(hist_file_enum[1], sep='|', engine='c')
                    for my_column_name in tmp_df.columns:
                        new_column_name = new_chanel_name(hist_file_enum[1], my_column_name)
                        tmp_df.rename(columns={my_column_name: new_column_name}, inplace=True)
                    mydata_df = pd.concat([mydata_df, tmp_df], axis=1).fillna(0)
        else:
            mydata_df, channels_to_display, status = remote_online_df(channels_to_display, "Pulse_Height")
            update_interval = 5*1000
        if changed_id == "unzoom-graph.n_clicks":
            xmin = 0
            xmax = len(mydata_df.index)
            ymin = 0
            ymax = mydata_df[channels_to_display[0]].max() + mydata_df[channels_to_display[0]].max() * .05
        fig_hist, energy_axis = create_histogram(mydata_df, channels_to_display, yaxis_type, xmin, xmax, ymin, ymax, stored_hist_filename, tab_mode_selection, graph_title)
        channel_list_with_info = generate_channel_list_with_info(mydata_df, tab_mode_selection, channels_to_display, fit_peak_button_value)
        fig_hist.update_layout(clickmode="none")  #  Disable line based selection on graph unless driven by event
        fig_hist.update_layout(hovermode='x')  # This gives a little box with info when hovering over data
    else:
        fig_hist = {}

    if fit_peak_button == 1:
        #  !!Currently I'm only caring about one channel, need to have that be selectable!
        stored_data, fig_hist, update_interval, fit_peak_button, hist_graph_click_data = fit_peak_button_mode(hist_graph_click_data, stored_data, fig_hist, mydata_df, fit_peak_button_value, energy_axis, stored_hist_filename)

    return fig_hist, stored_data, update_interval, fit_peak_button, hist_graph_click_data, channel_list_with_info, fit_peak_button_value


@app.callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def save_uploaded_hist(list_of_contents, list_of_names, list_of_dates):
    # Write contents of uploaded histogram to disk after properly decoding from base64
    if list_of_contents is not None:
        for hist_filename, contents in zip(list_of_names, list_of_contents):
            content_type, content_string = contents.split(',')

            decoded = base64.b64decode(content_string)
            output_filename = './hists/' + hist_filename
            output_file = open(output_filename, 'w', encoding="utf-8")
            output_file.write(decoded.decode("utf-8"))
            output_file.close()
    return


def generate_channel_list_with_info(mydata_df, tab_mode_selection, channels_to_display, fit_peak_button_value):
    channel_info_list_children = []
    chan_radio_options = []
    hit_count = []
    print("Fit Peak Button Value:", fit_peak_button_value)
    if fit_peak_button_value is None:  # Put in a default value of the first available channel if nothing has been selected
        fit_peak_button_value = channels_to_display[0]
    for channel in channels_to_display:
        chan_radio_options.append({"label": channel, "value": (channel)})
        hit_count.append(mydata_df[channel].sum())
    channel_info_list_children.append(
                                html.Div([html.H4("Fit", className='row'),
                                    dcc.RadioItems({'type': 'fit_chan_radio', 'index': 'value'},
                                            options=chan_radio_options,
                                            labelClassName='row',
                                            value=fit_peak_button_value,
                                            labelStyle={'display': 'block'}),
                                          ], className='column'))
    hit_count_children = []
    hit_count_children.append(html.H4("Hit Count", className='row'))
    for channel_sum in hit_count:
        hit_count_children.append(html.Div(html.Div(channel_sum, className='row')))

    channel_info_list_children.append(html.Div(className='column', children=hit_count_children))

    return channel_info_list_children


def new_chanel_name(filename, channel):
    file_path = Path(filename)  # Setup to extract filename prefix (stem)
    new_column_name = file_path.stem + "_chan_" + str(channel)
    return new_column_name


def get_hist_files_avail():
    file_list_options = []
    for hist_filename in glob.glob('./hists/*.hist'):
        file_list_options.append({"label": hist_filename, "value": hist_filename})
    return file_list_options


def create_temporal_hist():
    myrequests = online_analyzer_requests()
    mydata_df, status = myrequests.fetch_remote_2d_hist()
#    print(len(mydata_df['hist']))
    numpy_2d_array = np.vstack(mydata_df['hist'])
    print("!!Got to Create Temporal Histogram!!")
    img_rgb = np.array([[[randrange(0, 255), 0, 0], [0, randrange(0, 255), 0], [0, 0, 255]],
                    [[0, 255, 0], [0, 0, 255], [randrange(0, 255), 0, 0]]
                   ], dtype=np.uint8)
    fig_time_hist = px.imshow(numpy_2d_array)
    #fig_time_hist = px.imshow(mydata_df)
    return fig_time_hist


def generate_energy_axis(mydata_df, channel, hist_filename):
    calibration_found = False
    cal_file = './hists/' + str(Path(hist_filename).stem) + '.cal'
    print("Cal file:", cal_file)
    bin_num = mydata_df[channel].count()
    if exists(cal_file):  # Check if cal file exists for first filename used, ignore the rest.
        bin_num = mydata_df[channel].count()
        my_energy_calibration = energy_calibration(cal_file)
        my_energy_calibration.read_in_calibration_file()
        first_channel = int(channel.split('_')[-1])
        max_x_value = (bin_num * my_energy_calibration.cal_dict[first_channel][0]) + my_energy_calibration.cal_dict[first_channel][1]
        energy_axis = np.linspace(0, max_x_value, bin_num)
        calibration_found = True
    else:
        max_x_value = bin_num
        energy_axis = np.linspace(0, bin_num, bin_num)
    return energy_axis, max_x_value, calibration_found


def draw_fit_annotations_from_file(fig_hist, hist_filename, channel, yaxis_type):
    # Draw annotations for the fit of peaks
    fit_file_name = './hists/' + str(Path(hist_filename).stem) + '.fit'
    if exists(fit_file_name):
        with open(fit_file_name) as fit_file_pointer:
            for json_line in fit_file_pointer:
                fit_data = json.loads(json_line)
                if yaxis_type == 'Log':
                    amplitude = log(fit_data['amplitude']) / log(10)
                else:
                    amplitude = fit_data['amplitude']
                annotation_text = "Center: " + str(round(fit_data['center'], 2)) + " FWHM: " + str(round(fit_data['fwhm'], 2))
                try:
                    fig_hist.add_annotation(x=(fit_data['center']),
                                            y=amplitude,
                                            text=annotation_text,
                                            showarrow=True,
                                            arrowcolor='red',
                                            arrowhead=1,
                                            arrowwidth=2,
                                            font=dict(size=18))
                except:
                    print("Nope")
    return fig_hist


def create_histogram(mydata_df, channels_to_display, yaxis_type, xmin, xmax, ymin, ymax, hist_filenames, tab_mode_selection, graph_title):
    # !! Need to check that all the channels exist as columns in the DF and remove those that don't
    calibration_found = False
    my_graph_title = ""
    if graph_title is not None:
        my_graph_title = graph_title
    for channel in channels_to_display:
        if channel not in mydata_df.columns:
            channels_to_display.remove(channel)
    if tab_mode_selection == 'offline-analysis':
        energy_axis, max_x_value, calibration_found = generate_energy_axis(mydata_df, channels_to_display[0], hist_filenames[0])
    else:
        bin_num = mydata_df[channels_to_display[0]].count()
        energy_axis = np.linspace(0, bin_num, bin_num)
        max_x_value = bin_num
    x_axis_label = "Pulse Height"
    if calibration_found is True:
        x_axis_label = "Energy (keV)"
        
    tmp_hists_to_display = []
    for my_channel in channels_to_display:  # Need to put all the y axis stuff into one list to pass to px.line
        tmp_hists_to_display.append(mydata_df[my_channel])
    fig_hist = px.line(x=energy_axis, y=tmp_hists_to_display,
                       title=my_graph_title,
                       line_shape='hv',
                       render_mode='webgl',
                       height=900,
                       log_y=True,
                       labels={'x': x_axis_label, 'y': "Counts"},
                      )
    for my_channel in enumerate(channels_to_display):  # this is to rename the Channels labels properly
        fig_hist.data[my_channel[0]].name = str(my_channel[1])

    if xmax > max_x_value:  # Ensure we don't draw a crazy axis initially
        xmax = max_x_value
    print("MY YMax Value:", ymax)
    if xmax == 0:
        xmax = max_x_value
    fig_hist.update_xaxes(range=[xmin, xmax])
    if ymax > 0:
        fig_hist.update_yaxes(range=[ymin, ymax])

    fig_hist.update_layout(
        title={
            #'text': "Ba133 - Calibrated - LEGe",
            'y':1,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'})
    fig_hist.update_layout(
                            showlegend=True,
                            legend_title_text='Channels',
                            plot_bgcolor="lightgrey",
                            xaxis_showgrid=False, yaxis_showgrid=False,
                            font=dict(size=18)
                            )
    fig_hist.update_layout(plot_bgcolor='rgba(0, 0, 0, 0)',
                           paper_bgcolor='rgba(0, 0, 0, 0)',
                           font_color='white')
    fig_hist.update_yaxes(type='linear' if yaxis_type == 'Linear' else 'log')
    if tab_mode_selection == 'offline-analysis':
        fig_hist = draw_fit_annotations_from_file(fig_hist, hist_filenames[0], channels_to_display[0], yaxis_type)

    return fig_hist, energy_axis


def fit_peak_button_mode(hist_graph_click_data, stored_data, fig_hist, mydata_df, channel, energy_axis, hist_filenames):
    fit_file_name = './hists/' + str(Path(hist_filenames[0]).stem) + '.fit'  # Set filename to save peak fittings to
    fig_hist.update_layout(hovermode='x unified',
                           legend=dict(title=None),
                           hoverlabel=dict(bgcolor='rgba(255,255,255,0.75)',
                           font=dict(color='black')))
    fig_hist.update_layout(clickmode='event+select')
    # fig_hist.update_layout(hoverlabel=dict(bgcolor="black", font_size=12,))

    fit_peak_button = 1
    update_interval = 9999999999

    if hist_graph_click_data is not None:
        clicked_x_value = hist_graph_click_data['points'][0]['x']
        if (stored_data is not None) and (stored_data['fit_first_index'] is not None):#('fit_first_index' in stored_data.keys()):
            fit_min_x = stored_data['fit_first_index']
            fit_max_x = clicked_x_value
            fig_hist.add_vline(x=fit_min_x, line_width=3, line_dash="dash", line_color="green")
            fig_hist.add_vline(x=fit_max_x, line_width=3, line_dash="dash", line_color="green")
            print("Point 1", fit_min_x, "Point 2", fit_max_x)
            hist_gen_tools = hist_gen()
            # We're just going to choose to use the first selected channel for now, change later if needed
            true_peak_center, best_fit, result, amplitude, fit_energy_axis = hist_gen_tools.peak_fitting(mydata_df[channel], energy_axis, None, fit_min_x, fit_max_x, prominence=100)
            fit_dict = {'center': result.params['center'].value, 'fwhm': result.params['fwhm'].value, 'amplitude': amplitude}
            with open(fit_file_name, 'a') as json_file:
                json_str = json.dumps(fit_dict) + "\n"  # Write each entry as a new json line
                json_file.writelines(json_str)

            fig_hist.add_trace(go.Scatter(x=fit_energy_axis,
                                          y=best_fit,
                                          showlegend=False,
                                          line=dict(width=8))
                                )
            annotation_text = "Center: " + str(round(result.params['center'].value, 2)) + " FWHM: " + str(round(result.params['fwhm'].value, 2))
            fig_hist.add_annotation(x=(result.params['center'].value),
                                    y=amplitude,
                                    text=annotation_text,
                                    showarrow=True,
                                    arrowhead=1,
                                    arrowwidth=2,
                                    font=dict(size=18))

            stored_data.pop('fit_first_index', None)  # Remove 1st point dict key when done

            print("Resetting layout..")

            fig_hist.update_layout(clickmode="none")
            fig_hist.update_layout(hovermode='x')
            stored_data['fit_first_index'] = None
            fit_peak_button = 0
            hist_graph_click_data = None
        else:
            stored_data = {'fit_first_index': clicked_x_value}
        #if fit_peak_button = 0:
            fig_hist.add_vline(x=clicked_x_value, line_width=3, line_dash="dash", line_color="green")

    return stored_data, fig_hist, update_interval, fit_peak_button, hist_graph_click_data


def remote_online_df(channels_to_display, type):
    #  We're in online mode!! Let's see if we can grab remote data and display it
    print("Online Graphing mode...")
    for index, my_channel in enumerate(channels_to_display):
        channels_to_display[index] = my_channel + "_" + type
    myrequests = online_analyzer_requests()
    mydata_df, status = myrequests.fetch_remote_hist(channels_to_display)
    return mydata_df, channels_to_display, status


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8051)
