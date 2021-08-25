# *************************************************************************************
# * Written by : Jon Ringuette
# * Started : August 12 2021 - Still during the plague..
# * Purpose : Online and offline analysis of histogram data
#  * Requirements : Python 3, Dash  1.21+, pandas
# *************************************************************************************

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, ALL  # , MATCH

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from pathlib import Path
import glob
import base64
import datetime
from lib.histogram_generator import hist_gen
from lib.online_analyzer_requests import online_analyzer_requests
#from lib.radware_fit import radware_fit
#from pathlib import Path

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

nudat_form = html.Div([html.Form([
                                html.Label(['NuDat Lookup ',
                                    dcc.Input(name='nuc', type="text", style={'width':'60px'}, minLength=2, maxLength=5, placeholder="ex. sb129")]),
                                html.Button('Submit', type='submit', value='go')],
                                action='https://www.nndc.bnl.gov/nudat2/decaysearchdirect.jsp',
                                target="_blank", method='post')])

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

offline_tab_content = html.Div([html.Button('Plus', id='add-file-hist', n_clicks=0),
                                html.Button('Minus', id='remove-file-hist', n_clicks=0),
                                html.Div(id='hist-dropdown-list', children=[])])

online_tab_content = html.Div([
                        channel_selections_from_daqs])

app.title = 'HistPlot'

app.layout = html.Div([
    html.Div([
        html.H4(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
        html.H2('Project Elrond', style={
            'textAlign': 'center'})
    ]),
    nudat_form,
    html.Div([
        html.Label(['Y-Axis ',
            dcc.RadioItems(
                    id='yaxis-type',
                    options=[{'label': axis_type_select, 'value': axis_type_select} for axis_type_select in ['Linear', 'Log']],
                    value='Linear')
                #    labelStyle={'display': 'inline-block'})
        ]),
        html.Label(['xmin ',
            dcc.Input(
                id="xmin", type="number",
                debounce=True, value=0)
        ]),
        html.Label(['xmax ',
            dcc.Input(
                id="xmax", type="number",
                debounce=True, value=20000)
        ])
    ]),
    html.Hr(),
    html.Div([dcc.Tabs(id='mode-tabs', value='offline-analysis', children=[
        dcc.Tab(label='Offline Analysis', value='offline-analysis', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Online Analysis', value='online-analysis', style=tab_style, selected_style=tab_selected_style),
        ],
        style=tabs_styles)]), #,, html.Div(id='tabs-content-inline')]),
    dcc.Store(id='tab-mode-selection'),
    dcc.Store(id='hist_filename'),
    html.Div(id='tabs-content-inline'),

    #channel_selections_from_daqs,
    html.Hr(),

    html.Div(id='call-static-grapher'),
    html.Div([dcc.Graph(id='hist_graph_display')]),
    html.Div(dcc.Interval(id='interval-component', interval=999999999)),
    #html.Div(id='hist_graph_div', children=[dcc.Graph(id='hist_graph_display')]),

    html.Div([html.Button('Fit Peak', id='fit-peak-button', n_clicks=0),
              dcc.Store(id='peak_fit_first_point')]),
    html.Div([
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select Files')
            ]),
            style={
                'width': '20%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            },
            # Allow multiple files to be uploaded
            multiple=True
        ),
        html.Div(id='output-data-upload'),
    ])
])


@app.callback(Output('tabs-content-inline', 'children'),
              Output('tab-mode-selection', 'data'),
              Input('mode-tabs', 'value'),
              State('tab-mode-selection', 'data')
              )
def render_tab_content(tab_selection, tab_mode):
    print("Getting tab initially!!")
    tab_mode = tab_selection
    if tab_selection == 'offline-analysis':
        return offline_tab_content, tab_mode
    elif tab_selection == 'online-analysis':
        return online_tab_content, tab_mode


@app.callback(
    Output('xmin', 'value'),
    Output('xmax', 'value'),
    Input('hist_graph_display', 'relayoutData'))
def zoom_event(relayoutData):
    print(relayoutData)
    if relayoutData is None:
        raise dash.exceptions.PreventUpdate

    if 'xaxis.autorange' in relayoutData.keys():
        print("Do something, we're zoomed out..")
        return 0, 20000

    else:
        if 'xaxis.range[0]' in relayoutData.keys():
            return int(relayoutData['xaxis.range[0]']), int(relayoutData['xaxis.range[1]'])
    return 0, 20000


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
    print("Chan index! :", chan_index)
    print("Hist selection", hist_file_selection)
    print("hist_available_channel_dropdown", hist_available_channel_dropdown)
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
    print("hist_available_channel_dropdown AFTER", hist_available_channel_dropdown)
    return stored_hist_filename, hist_available_channel_dropdown

@app.callback(
    Output('hist_graph_display', 'figure'),
    Output('peak_fit_first_point', 'data'),
    Output('interval-component', 'interval'),
    Output('fit-peak-button', 'n_clicks'),
    Output('hist_graph_display', 'clickData'),
    Input('interval-component', 'n_intervals'),
    Input('yaxis-type', 'value'),
    Input("xmin", "value"),
    Input("xmax", "value"),
    Input({'type': 'selected_chan_dropdown', 'index': ALL}, 'value'),
    Input('fit-peak-button', 'n_clicks'),
    Input('hist_graph_display', 'clickData'),
    State('peak_fit_first_point', 'data'),
    State('hist_filename', 'data'),
    State('tab-mode-selection', 'data'),
    )
def process_static_hist(n_intervals, yaxis_type, xmin, xmax, hist_available_channel_list, fit_peak_button, click_data, stored_data, stored_hist_filename, tab_mode_selection):
    triggered = [t["prop_id"] for t in dash.callback_context.triggered]
    print("Fit peak button:", fit_peak_button)
    print("Triggerd:", triggered)
    print("Tab mode:", tab_mode_selection)
    print("Channels we should be looking at:", hist_available_channel_list, "Filename", stored_hist_filename)
    update_interval = 9999999999  # Set this to a long period of time assuming we're in offline mode, change it only when we are definitly in online mode with channels selected.

    channels_to_display = []
    for channels in hist_available_channel_list:
        if channels is not None:
            channels_to_display.extend(channels)

    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]  # determines what property changed, in this case which button was pushed
    print("Change id", changed_id)
    hist_file_selection = stored_hist_filename

    if len(channels_to_display) > 0:
        if tab_mode_selection == "offline-analysis":
            if hist_file_selection is None:
                raise dash.exceptions.PreventUpdate
            print("Offline Graphing mode...")
            mydata_df = pd.DataFrame()
            for hist_file_enum in enumerate(stored_hist_filename):
                if hist_file_enum[1] is not None:
                    tmp_df = pd.read_csv(hist_file_enum[1], sep='|', engine='c')
                    for my_column_name in tmp_df.columns:
                        new_column_name = new_chanel_name(hist_file_enum[1], my_column_name)
                        tmp_df.rename(columns={my_column_name: new_column_name}, inplace=True)
                    mydata_df = pd.concat([mydata_df, tmp_df], axis=1).fillna(0)
            print(mydata_df)
            print("hist available list:", hist_available_channel_list)
        else:
            mydata_df, channels_to_display, status = remote_online_df(channels_to_display, "Pulse_Height")
            update_interval = 5*1000
        fig_hist = create_histogram(mydata_df, channels_to_display, yaxis_type, xmin, xmax)

        fig_hist.update_layout(clickmode="none")  #  Disable line based selection on graph unless driven by event
        fig_hist.update_layout(hovermode='x')  # This gives a little box with info when hovering over data
    else:
        fig_hist = {}

    if fit_peak_button == 1:
        #  !!Currently I'm only caring about one channel, need to have that be selectable!
        stored_data, fig_hist, update_interval, fit_peak_button, click_data = fit_peak_button_mode(click_data, stored_data, fig_hist, mydata_df, channels_to_display[0])

    return fig_hist, stored_data, update_interval, fit_peak_button, click_data


@app.callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def save_uploaded_hist(list_of_contents, list_of_names, list_of_dates):
    # Write contents of uploaded histogram to disk after properly decoding from base64
    if list_of_contents is not None:
        print(list_of_names)
        for hist_filename, contents in zip(list_of_names, list_of_contents):
            content_type, content_string = contents.split(',')

            decoded = base64.b64decode(content_string)
            output_filename = './hists/' + hist_filename
            output_file = open(output_filename, 'w', encoding="utf-8")
            output_file.write(decoded.decode("utf-8"))
            output_file.close()
    return


#@app.callback(
#    Output("hist_file_selection", "options"),
#    Input("hist_file_selection", "search_value")
#)
def new_chanel_name(filename, channel):
    file_path = Path(filename)  # Setup to extract filename prefix (stem)
    new_column_name = file_path.stem + "_chan_" + str(channel)
    return new_column_name


def get_hist_files_avail():
    print("got here!")
    file_list_options = []
    for hist_filename in glob.glob('./hists/*.hist'):
        file_list_options.append({"label": hist_filename, "value": hist_filename})
    #if not search_value:
    #    print("Here we go..")
    #    raise dash.exceptions.PreventUpdate
    return file_list_options


def create_histogram(mydata_df, channels_to_display, yaxis_type, xmin, xmax):
    # !! Need to check that all the channels exist as columns in the DF and remove those that don't
    print("Do we get to static hist creation?")
    for channel in channels_to_display:
        if channel not in mydata_df.columns:
            print("We're removing it!!")
            channels_to_display.remove(channel)
    print("in hist creation:", channels_to_display)

    fig_hist = px.line(mydata_df[channels_to_display][xmin:xmax],
                              line_shape='hv',
                              render_mode='webgl',
                              height=800,
                              log_y=True,
                              labels={'index': "Pulse Height", 'value': "Counts"})
    fig_hist.update_layout(
        showlegend=True,
        legend_title_text='Channels',
        plot_bgcolor="lightgrey",
        xaxis_showgrid=False, yaxis_showgrid=False
    )
    fig_hist.update_layout(plot_bgcolor='rgba(0, 0, 0, 0)',
                           paper_bgcolor='rgba(0, 0, 0, 0)',
                           font_color='white')
    fig_hist.update_yaxes(type='linear' if yaxis_type == 'Linear' else 'log')
    return fig_hist


def fit_peak_button_mode(click_data, stored_data, fig_hist, mydata_df, channel):
    print("We need to start fitting some stuffs!!")
    fig_hist.update_layout(hovermode='x unified')
    fig_hist.update_layout(clickmode='event+select')
    fit_peak_button = 1
    update_interval = 9999999999

    if click_data is not None:
        clicked_x_value = click_data['points'][0]['x']
        if (stored_data is not None) and (stored_data['fit_first_index'] is not None):#('fit_first_index' in stored_data.keys()):
            fit_min_x = stored_data['fit_first_index']
            fit_max_x = clicked_x_value
            fig_hist.add_vline(x=fit_min_x, line_width=3, line_dash="dash", line_color="green")
            print("Point 1", fit_min_x, "Point 2", fit_max_x)
            hist_gen_tools = hist_gen()
            #print("Channel to display", channels_to_display[0])
            # We're just going to choose to use the first selected channel for now, change later if needed
            true_peak_center, best_fit, result = hist_gen_tools.peak_fitting(mydata_df[channel], None, fit_min_x, fit_max_x, prominence=100)
            fit_axis = np.linspace(fit_min_x, fit_max_x, fit_max_x-fit_min_x, dtype=int)
            fig_hist.add_trace(go.Scatter(x=fit_axis,
                                          y=best_fit,
                                          showlegend=False,
                                          line=dict(width=8))
                                )
            #fig_hist.update_traces(name="Best Fit")
            stored_data.pop('fit_first_index', None)  # Remove 1st point dict key when done
            print("Resetting layout..")
            fig_hist.update_layout(clickmode="none")
            fig_hist.update_layout(hovermode='x')
            stored_data['fit_first_index'] = None
            fit_peak_button = 0
            click_data = None
        else:
            stored_data = {'fit_first_index': clicked_x_value}
            fig_hist.update_layout(hovermode='x unified')
            #fig_hist.update_layout(clickmode='event+select')

        fig_hist.add_vline(x=clicked_x_value, line_width=3, line_dash="dash", line_color="green")
    return stored_data, fig_hist, update_interval, fit_peak_button, click_data


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
