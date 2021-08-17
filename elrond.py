import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

import plotly.express as px
import pandas as pd
#import numpy as np
import glob
import base64
import datetime
from lib.histogram_generator import hist_gen

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

offline_tab_content = html.Div([
                        html.Label(['Select Histogram ',
                            dcc.Dropdown(
                                id='hist_file_selection',
                                style={'width': '40vH', 'height': '40px'},
                                multi=False,
                            )
                        ])
                        ])
online_tab_content = html.Div()

app.title = 'HistPlot'

app.layout = html.Div([
    html.Div([
        html.H4(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
        html.H2('Test Hist - Project Elrond', style={
            'textAlign': 'center'})
    ]),
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
    html.Div([
        dcc.Store(id='tab-mode-selection'),
        html.Div(id='tabs-content-inline'),

        html.Label(['GRIF16 Channel Select ',
            dcc.Dropdown(
                id='grif16_chan_dropdown',
                options=[
                        {"label": chan, "value": str(chan)}
                        for chan in range(0, 16)
                        ],
                style={'width': '40vH', 'height': '40px'},
                multi=True
        )]),
        html.Label(['MDPP16 Channel Select ',
            dcc.Dropdown(
                id='mdpp16_chan_dropdown',
                options=[
                        {"label": chan, "value": str(chan)}
                        for chan in range(0, 16)
                        ],
                style={'width': '40vH', 'height': '40px'},
                multi=True)
        ])
    ], style=dict(display='flex')),
    html.Hr(),
    html.Div(id='call-static-grapher'),
    html.Div([dcc.Graph(id='static-hist'),
        dcc.Store(id='hist_filename'),
        dcc.Store(id='peak_fit_first_point'),
        html.Button('Fit Peak', id='fit-peak-button', n_clicks=0)]),
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


def create_static_histogram(mydata_df, channels_to_display, yaxis_type, xmin, xmax):
    # !! Need to check that all the channels exist as columns in the DF and remove those that don't
    for channel in channels_to_display:
        if channel not in mydata_df.columns:
            channels_to_display.remove(channel)

    fig_hist_static = px.line(mydata_df[channels_to_display][xmin:xmax],
                              line_shape='hv',
                              render_mode='webgl',
                              height=800,
                              log_y=True,
                              labels={'index': "Pulse Height", 'value': "Counts"})
#    fig_hist_static = px.histogram(mydata_df['100'])
    fig_hist_static.update_layout(
        showlegend=False,
        plot_bgcolor="lightgrey",
        xaxis_showgrid=False, yaxis_showgrid=False
    )
    fig_hist_static.update_layout(plot_bgcolor='rgba(0, 0, 0, 0)',
                                  paper_bgcolor='rgba(0, 0, 0, 0)',
                                  font_color='white')
    fig_hist_static.update_yaxes(type='linear' if yaxis_type == 'Linear' else 'log')

    #fig_hist_static.update_layout(hovermode='x unified')

    return fig_hist_static


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


@app.callback(
    Output('xmin', 'value'),
    Output('xmax', 'value'),
    Input('static-hist', 'relayoutData'))
def zoom_event(relayoutData):
    print(relayoutData)
    if relayoutData is None:
        raise dash.exceptions.PreventUpdate

    if 'xaxis.autorange' in relayoutData.keys():
        print("Do something, we're zoomed out..")
        return 0, 20000

    else:
        if 'xaxis.range[0]' in relayoutData.keys():
            print("We are zoomed in!!")
            return int(relayoutData['xaxis.range[0]']), int(relayoutData['xaxis.range[1]'])
    return 0, 20000

@app.callback(
    Output('hist_filename', 'data'),
    Output('call-static-grapher', 'children'),
    Input('hist_file_selection', 'value'),
    State('hist_filename', 'data'),
)
def set_static_hist_filename(hist_file_selection, stored_hist_filename):
    call_static_grapher = False
    print("Hist selection", hist_file_selection)
    print("Stored value", stored_hist_filename)
    stored_hist_filename = hist_file_selection
    if stored_hist_filename is not None:
        call_static_grapher = True

    return stored_hist_filename, call_static_grapher

@app.callback(
    Output('static-hist', 'figure'),
    Output('peak_fit_first_point', 'data'),
    #Output('hist_filename', 'data'),
    Input('call-static-grapher', 'children'),
    Input('yaxis-type', 'value'),
    Input("xmin", "value"),
    Input("xmax", "value"),
    Input("grif16_chan_dropdown", "value"),
    Input("mdpp16_chan_dropdown", "value"),
    Input('fit-peak-button', 'n_clicks'),
    Input('static-hist', 'clickData'),
    State('peak_fit_first_point', 'data'),
    State('hist_filename', 'data'),
    State('tab-mode-selection', 'data')

    )
def process_static_hist(call_static_grapher, yaxis_type, xmin, xmax, grif16_chan_dropdown, mdpp16_chan_dropdown, fit_peak_button, click_data, stored_data, stored_hist_filename, tab_mode_selection):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]  # determines what property changed, in this case which button was pushed
    print("Change id", changed_id)
    print("Tab mode:", tab_mode_selection)
    print("Stored hist filename:", stored_hist_filename)
    hist_file_selection = stored_hist_filename #"./hists/run770.hist"
    mdpp16_chan_dropdown = [0]
    channels_to_display = []
    if hist_file_selection is None:
        raise dash.exceptions.PreventUpdate

    if mdpp16_chan_dropdown is not None:  # Make sure we adjust for mdpp16 channel #'ing (100-115)
        for mychan_id in range(0, len(mdpp16_chan_dropdown)):
            mdpp16_chan_dropdown[mychan_id] = str(int(mdpp16_chan_dropdown[mychan_id]) + 100)

    if grif16_chan_dropdown is not None:
        channels_to_display = channels_to_display + grif16_chan_dropdown
    if mdpp16_chan_dropdown is not None:
        channels_to_display = channels_to_display + mdpp16_chan_dropdown
    if len(channels_to_display) > 0:
        mydata_df = pd.read_csv(hist_file_selection, sep='|', engine='c')
        print("Xmin:", xmin, "Xmax:", xmax)
        fig_hist_static = create_static_histogram(mydata_df, channels_to_display, yaxis_type, xmin, xmax)
    else:
        # PreventUpdate prevents ALL outputs updating.  Don't throw errors before channels and files selected
        raise dash.exceptions.PreventUpdate
    fig_hist_static.update_layout(clickmode="none")

    if click_data is not None:
        clicked_x_value = click_data['points'][0]['x']
        if (stored_data is not None) and ('fit_first_index' in stored_data.keys()):
            fig_hist_static.add_vline(x=stored_data['fit_first_index'], line_width=3, line_dash="dash", line_color="green")
            print("Point 1", stored_data['fit_first_index'], "Point 2", clicked_x_value)
            hist_gen_tools = hist_gen()
            print("Channel to display", channels_to_display[0])
            # We're just going to choose to use the first selected channel for now, change later if needed
            hist_gen_tools.peak_fitting(mydata_df[channels_to_display[0]], None, stored_data['fit_first_index'], clicked_x_value)
            stored_data.pop('fit_first_index', None)  # Remove 1st point dict key when done
        else:
            print("Got the else")
            stored_data = {'fit_first_index': clicked_x_value}
            fig_hist_static.update_layout(hovermode='x unified')
            fig_hist_static.update_layout(clickmode='event+select')

        fig_hist_static.add_vline(x=clicked_x_value, line_width=3, line_dash="dash", line_color="green")

    if changed_id == 'fit-peak-button.n_clicks':
        print("We need to start fitting some stuffs!!")
        fig_hist_static.update_layout(hovermode='x unified')
        fig_hist_static.update_layout(clickmode='event+select')

    return fig_hist_static, stored_data #, stored_hist_filename

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


@app.callback(
    Output("hist_file_selection", "options"),
    Input("hist_file_selection", "search_value")
)
def update_options(search_value):
    file_list_options = []
    for hist_filename in glob.glob('./hists/*.hist'):
        file_list_options.append({"label": hist_filename, "value": hist_filename})
    #if not search_value:
    #    print("Here we go..")
    #    raise dash.exceptions.PreventUpdate
    return file_list_options


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
