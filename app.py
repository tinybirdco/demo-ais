import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import requests
import json
from datetime import date
import time
import h3

TB_BASE_URL = 'https://api.tinybird.co/v0/pipes/'

# Read in token from the .tinyb JSON file
with open('.tinyb') as f:
    tinyb_data = json.load(f)
    TB_TOKEN = tinyb_data['token']

# Utility functions
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

def prepare_hexagon_data(df, h3_boundary_column_name):
    """
    Prepare hexagon boundary data for plotting from a DataFrame. Adjusts for closing polygons
    and ensures coordinates are in the expected order.
    
    :param df: The DataFrame with H3 boundary arrays.
    :param h3_boundary_column_name: The name of the column containing H3 boundaries.
    :return: A list of dictionaries with 'lon' and 'lat' keys for each hexagon.
    """
    hexagon_data = []
    for boundary in df[h3_boundary_column_name]:
        # Ensure the polygon is closed by appending the first vertex to the end
        boundary.append(boundary[0])
        
        # Unpack the array of [lat, lon] pairs into separate lists,
        # reversing the order to [lon, lat] if necessary for your mapping tool
        lons, lats = zip(*[(lon, lat) for lat, lon in boundary])
        
        hexagon_data.append({'lon': lons, 'lat': lats})
    return hexagon_data

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
        html.H4('Select Display Mode:', style={'padding': '5px'}),
        dcc.RadioItems(
            id='display-mode',
            options=[
                {'label': 'Show LatLong Points', 'value': 'data_points'},
                {'label': 'Show H3 Hexagons', 'value': 'h3_hexagons'},
            ],
            value='h3_hexagons',  # Default value
            labelStyle={'display': 'block'}  # Display options in block mode
        ),
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

def prepare_performance_info(cached_data):
    request_roundtrip_time = cached_data.get('request_roundtrip_time', 'N/A')
    tb_elapsed = cached_data.get('statistics', {}).get('elapsed', 'N/A')
    tb_bytes_read = cached_data.get('statistics', {}).get('bytes_read', 'N/A')
    data_points = len(cached_data.get('data', []))

    return [
        html.Div(f"Request roundtrip time: {request_roundtrip_time:.3f} s"),
        html.Div(f"Tinybird processing time: {tb_elapsed} ms"),
        html.Div(f"Tinybird Bytes read: {format_bytes(tb_bytes_read)}"),
        html.Div(f"Data points: {data_points}")
    ]

@app.callback(
    Output('cached-data', 'data'),
    [Input('submit-val', 'n_clicks'), Input('display-mode', 'value')],
    [State('mmsi-dropdown', 'value'), State('start-date-input', 'date'), State('end-date-input', 'date')]
)
def fetch_data(n_clicks, display_mode, mmsi, start_date, end_date):
    if n_clicks > 0:
        start_request_time = time.time()
        
        if display_mode == 'data_points':
            url = f'{TB_BASE_URL}latlon_by_date_by_mmsi.json?mmsis={mmsi}&startdate={start_date}&enddate={end_date}&token={TB_TOKEN}'
        elif display_mode == 'h3_hexagons':
            url = f'{TB_BASE_URL}h3_r6_by_date_by_mmsi.json?mmsis={mmsi}&startdate={start_date}&enddate={end_date}&token={TB_TOKEN}'
        
        response = requests.get(url)
        end_request_time = time.time()

        # Calculate request roundtrip time and package the data
        data = {
            'mode': display_mode,
            'data': response.json()['data'],  # Assuming the API response has a 'data' key
            'request_roundtrip_time': end_request_time - start_request_time,
            'statistics': response.json().get('statistics', {})  # Include additional response metadata if available
        }

        return data
    return {}

def update_geos_viewport(fig, lats, lons):
    """
    Update the map's viewport based on latitude and longitude bounds.
    """
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    fig.update_geos(
        projection_type="equirectangular",
        visible=False, 
        showcountries=True, 
        lonaxis=dict(range=[min_lon - 0.1, max_lon + 0.1]),  # Adding a small margin
        lataxis=dict(range=[min_lat - 0.1, max_lat + 0.1])
    )

    fig.update_layout(geo=dict(fitbounds="locations"))

@app.callback(
    [Output('map-display', 'figure'), Output("performance-info", "children")],
    [Input('cached-data', 'data'), Input('display-mode', 'value')]
)
def update_map(cached_data, display_mode):
    if not cached_data or 'data' not in cached_data:
        return go.Figure(), "Select options and click submit to see data."

    df = pd.DataFrame(cached_data['data'])
    fig = go.Figure()

    lats, lons = [], []

    if display_mode == 'h3_hexagons':
        # Preparing hexagon data
        hexagon_data = prepare_hexagon_data(df, 'h3_boundary')
        for hex_data in hexagon_data:
            fig.add_trace(go.Scattergeo(
                lon=hex_data['lon'], 
                lat=hex_data['lat'], 
                mode='lines',
                line=dict(width=1, color='orange'),  # Hexagon line color
                fill='toself',
                fillcolor='rgba(255, 165, 0, 0.5)'  # Hexagon fill color with some transparency
            ))
            lats.extend(hex_data['lat'])
            lons.extend(hex_data['lon'])

    elif display_mode == 'data_points':
        # Plotting lat-long points with specific marker settings
        fig.add_trace(go.Scattergeo(
            lon=df['lon'], 
            lat=df['lat'], 
            mode='markers+lines',
            marker=dict(size=7, color='red'),  # Data point color
            line=dict(width=2, color='red'),  # Line color connecting the points
            text=df['basedatetime'],  # Assuming 'basedatetime' contains timestamp or similar info
            name='Path'
        ))
        lats = df['lat'].tolist()
        lons = df['lon'].tolist()

    # Adjusting the map's viewport based on the newly loaded data
    update_geos_viewport(fig, lats, lons)

    # Updating layout to include custom styling
    fig.update_layout(
        margin={"r":0, "t":0, "l":0, "b":0},
        geo=dict(
            scope='world',
            showland=True,
            landcolor="LightGreen",
            showocean=True,
            oceancolor="LightBlue",
            showcountries=True,
            countrycolor="DarkGrey",
            fitbounds="locations"  # Automatically adjusting viewport to fit the data
        ),
        title=dict(text="AIS Data Visualization", x=0.5)  # Center title
    )

    performance_info = prepare_performance_info(cached_data)
    
    return fig, performance_info


if __name__ == '__main__':
    app.run_server(debug=True)
