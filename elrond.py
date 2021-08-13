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
app.title = 'HistPlot'

app.layout = html.Div([
    #html.Title("HistPlot"),
    html.Div([
    #    html.Title("HistPlot"),
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
    html.Div([
        html.Div([
            html.Label(['Select Histogram ',
                dcc.Dropdown(
                    id='hist_file_selection',
                    style={'width': '40vH', 'height': '40px'},
                    multi=False)
            ])
        ]),
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
    html.Div([dcc.Graph(id='static-hist'),
        dcc.Store(id='testme'),
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
    #mydata_df = pd.read_csv(hist_filename, sep='|', engine='c')
    # MOVE THIS LINE ELSEWHERE.  Want to just pass a histogram here so that this function and part of the one below can be reused for realtime/online portion


    # !! Need to check that all the channels exist as columns in the DF and remove those that don't
    for channel in channels_to_display:
        if channel not in mydata_df.columns:
            channels_to_display.remove(channel)

    fig_hist_static = px.line(mydata_df[channels_to_display][xmin:xmax],
                            #  x='Mine',
                #              y="101",
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

@app.callback(
#    Output('testme', 'data'),
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
    Output('static-hist', 'figure'),
    Output('peak_fit_first_point', 'data'),
    Input('hist_file_selection', 'value'),
    Input('yaxis-type', 'value'),
    Input("xmin", "value"),
    Input("xmax", "value"),
    Input("grif16_chan_dropdown", "value"),
    Input("mdpp16_chan_dropdown", "value"),
    Input('fit-peak-button', 'n_clicks'),
    Input('static-hist', 'clickData'),
    State('peak_fit_first_point', 'data')
    )
def process_static_hist(hist_file_selection, yaxis_type, xmin, xmax, grif16_chan_dropdown, mdpp16_chan_dropdown, fit_peak_button, click_data, stored_data):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]  # determines what property changed, in this case which button was pushed
    hist_file_selection="./hists/run770.hist"
    mdpp16_chan_dropdown = [0]
    #print("Relayout", relayoutData)
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

        print("Got some data!", click_data['points'][0]['x'])
        fig_hist_static.add_vline(x=clicked_x_value, line_width=3, line_dash="dash", line_color="green")

    if changed_id == 'fit-peak-button.n_clicks':
        print("We need to start fitting some stuffs!!")
        fig_hist_static.update_layout(hovermode='x unified')
        fig_hist_static.update_layout(clickmode='event+select')

    return fig_hist_static, stored_data

@app.callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def save_uploaded_hist(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        print(list_of_names)
        for hist_filename, contents in zip(list_of_names, list_of_contents):
            content_type, content_string = contents.split(',')

            decoded = base64.b64decode(content_string)
            output_filename = './hists/' + hist_filename
            output_file = open(output_filename, 'w', encoding="utf-8")
            output_file.write(decoded.decode("utf-8"))
            output_file.close()
        #    print(decoded)
#            print(io.StringIO(decoded.decode('utf-8')))
    return

options = [
    {"label": "New York City", "value": "NYC"},
    {"label": "Montreal", "value": "MTL"},
    {"label": "San Francisco", "value": "SF"},
]

@app.callback(
    Output("hist_file_selection", "options"),
    [Input("hist_file_selection", "search_value")],
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
