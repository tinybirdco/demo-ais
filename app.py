import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import requests
import json
from datetime import date
import time

TB_BASE_URL = 'https://api.tinybird.co/v0/pipes/'

# Read in token from the .tinyb JSON file
with open('.tinyb') as f:
    tinyb_data = json.load(f)
    TB_TOKEN = tinyb_data['token']

# Utility function to format bytes
def format_bytes(size):
    """Convert bytes to a more readable format."""
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while size >= 1024 and i < len(suffixes)-1:
        size /= 1024.
        i += 1
    return f"{size:.2f} {suffixes[i]}"

def fetch_mmsi_list():
    """Fetches a list of unique MMSIs from Tinybird."""
    response = requests.get(f"{TB_BASE_URL}mmsi_unique.json?token={TB_TOKEN}")
    mmsis = response.json()['data']
    return [{'label': str(mmsi['mmsi']), 'value': mmsi['mmsi']} for mmsi in mmsis]

# Initialize the Dash app
app = dash.Dash(__name__)

mmsi_options = fetch_mmsi_list()

app.layout = html.Div([
    dcc.Store(id='cached-data'),  # Store for caching fetched data
    # Flex container
    html.Div([
        # Left column for input elements
        html.Div([
            html.H2("AIS Data Visualization", style={'padding': '10px'}),
        html.H4('Select MMSI:', style={'padding': '5px'}),
        dcc.Dropdown(
            id='mmsi-dropdown',
            options=mmsi_options,
            value=mmsi_options[0]['value'] if mmsi_options else None,
            style={'width': '100%', 'padding': '5px'},
            searchable=True,
            placeholder='Select MMSI'
        ),
        html.H4('Start Date:', style={'padding': '5px'}),
        dcc.DatePickerSingle(
            id='start-date-input',
            min_date_allowed=date(2020, 1, 1),
            max_date_allowed=date(2020, 5, 31),
            initial_visible_month=date(2020, 1, 1),
            date=date(2020, 1, 1),
            style={'width': '100%', 'padding': '5px'}
        ),
        html.H4('End Date:', style={'padding': '5px'}),
        dcc.DatePickerSingle(
            id='end-date-input',
            min_date_allowed=date(2020, 1, 1),
            max_date_allowed=date(2020, 5, 31),
            initial_visible_month=date(2020, 5, 31),
            date=date(2020, 1, 31),
            style={'width': '100%', 'padding': '5px'}
        ),
        html.Button('Submit', id='submit-val', n_clicks=0, style={'margin': '20px'}),
        html.Div(id="performance-info", style={'padding': '5px'})
        ], style={'width': '20%', 'display': 'inline-block', 'vertical-align': 'top', 'padding': '20px'}),
        # Right column for the map
        html.Div([
            dcc.Graph(id='map-display', style={"height": "90vh"})
        ], style={'width': '70%', 'display': 'inline-block', 'padding': '20px'})
    ], style={'display': 'flex', 'flex-direction': 'row', 'justify-content': 'space-between', 'align-items': 'start'}),
], style={'font-family': 'Arial, sans-serif'})

@app.callback(
    Output('cached-data', 'data'),
    [Input('submit-val', 'n_clicks')],
    [State('mmsi-dropdown', 'value'), 
     State('start-date-input', 'date'), 
     State('end-date-input', 'date')],
    prevent_initial_call=True
)
def fetch_data(n_clicks, mmsi, start_date, end_date):
    if n_clicks > 0:
        start_request_time = time.time()
        url = f'{TB_BASE_URL}h3_by_date_by_mmsi.json?mmsis={mmsi}&startdate={start_date}&enddate={end_date}&latlon_only=t&token={TB_TOKEN}'
        response = requests.get(url)
        end_request_time = time.time()

        # Calculate request roundtrip time
        request_roundtrip_time = end_request_time - start_request_time

        data = response.json()
        # Add request roundtrip time to the data for later display
        data['request_roundtrip_time'] = request_roundtrip_time

        return data
    return {}

@app.callback(
    [Output('map-display', 'figure'), 
     Output("performance-info", "children")],
    [Input('cached-data', 'data')]
)
def update_map(cached_data):
    if cached_data and 'data' in cached_data:
        start_local_processing_time = time.time()
        
        df = pd.DataFrame(cached_data['data'])
        fig = generate_map_figure(df)
        
        tb_elapsed = cached_data.get('statistics', {}).get('elapsed', 'N/A')
        tb_bytes_read = cached_data.get('statistics', {}).get('bytes_read', 'N/A')
        request_roundtrip_time = cached_data.get('request_roundtrip_time', 'N/A')

        end_local_processing_time = time.time()
        local_processing_time = end_local_processing_time - start_local_processing_time

        performance_info = [
            html.Div(f"Request roundtrip time: {request_roundtrip_time:.3f} s"),
            html.Div(f"Tinybird processing time: {tb_elapsed:.3f} ms"),
            html.Div(f"Local processing time: {local_processing_time:.3f} s"),
            html.Div(f"Tinybird Bytes read: {format_bytes(tb_bytes_read)}"),
            html.Div(f"Data points: {len(df)}")
        ]
        return fig, performance_info
    else:
        # If no data is available, show an empty map and initial message or placeholder
        return go.Figure(), "Select options and click submit to see data."

def generate_map_figure(df):
    """Generates the map figure from the DataFrame."""
    fig = go.Figure()
    fig.add_trace(go.Scattergeo(
        lon=df['lon'],
        lat=df['lat'],
        mode='markers+lines',
        marker=dict(size=7, color='red', symbol='circle'),
        text=df['basedatetime'],
        name='Path'
    ))
    lon_center = (df['lon'].min() + df['lon'].max()) / 2
    lat_center = (df['lat'].min() + df['lat'].max()) / 2
    lon_padding = (df['lon'].max() - df['lon'].min()) * 0.1
    lat_padding = (df['lat'].max() - df['lat'].min()) * 0.1
    fig.update_geos(
        visible=False,
        showcountries=True, countrycolor="RebeccaPurple",
        lonaxis_range=[df['lon'].min() - lon_padding, df['lon'].max() + lon_padding],
        lataxis_range=[df['lat'].min() - lat_padding, df['lat'].max() + lat_padding],
        center=dict(lon=lon_center, lat=lat_center)
    )
    fig.update_layout(
        margin={"r":0, "t":0, "l":0, "b":0},
        geo=dict(
            scope='world',
            showland=True,
            landcolor="LightGreen",
            showocean=True,
            oceancolor="LightBlue"
        )
    )
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
