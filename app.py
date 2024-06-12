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
        # Reverse the order of vertices so they render correctly in plotly.
        boundary_reversed = boundary[::-1]
        # Unpack the array of [lat, lon] pairs into separate lists
        # reversing the order to [lon, lat] for plotly
        lons, lats = zip(*[(lon, lat) for lat, lon in boundary_reversed])

        hexagon_data.append({'lon': lons, 'lat': lats})
    return hexagon_data

# Initialize the Dash app
app = dash.Dash(__name__)

mmsi_options = fetch_mmsi_list()

app.layout = html.Div([
    dcc.Store(id='cached-data'),  # Store for caching fetched data
    html.Header([
        html.Img(src=app.get_asset_url('tinybird-logo.svg')),
        html.H2([html.Span("AIS", className='border-brand'), html.Span(" Data Visualization")], className='title'),
    ]),
    # Flex container
    html.Div([
        # Left column for input elements
            html.Div([
                html.P('Select options and click submit to see data.', className='subtitle'),
                html.Label('Display Mode', htmlFor='display-mode'),
                dcc.RadioItems(
                    id='display-mode',
                    options=[
                        {'label': 'H3 r4', 'value': 'h3_r4'},
                        {'label': 'H3 r6', 'value': 'h3_r6'},
                        {'label': 'H3 r8', 'value': 'h3_r8'},
                        {'label': 'LatLong', 'value': 'data_points'}
                    ],
                    value='h3_r4',  # Default value
                    className='input',
                    labelClassName="label-radio"
                ),
                html.Label('MMSI', htmlFor='mmsi-dropdown'),
                dcc.Dropdown(
                    id='mmsi-dropdown',
                    options=mmsi_options,
                    value=mmsi_options[0]['value'] if mmsi_options else None,
                    searchable=True,
                    placeholder='Select MMSI',
                    className='input'
                ),
                html.Label('Start Date', htmlFor='start-date-input'),
                dcc.DatePickerSingle(
                    id='start-date-input',
                    min_date_allowed=date(2020, 1, 1),
                    max_date_allowed=date(2020, 5, 31),
                    initial_visible_month=date(2020, 1, 1),
                    date=date(2020, 1, 1),
                    className='input'
                ),
                html.Label('End Date', htmlFor='end-date-input'),
                dcc.DatePickerSingle(
                    id='end-date-input',
                    min_date_allowed=date(2020, 1, 1),
                    max_date_allowed=date(2020, 5, 31),
                    initial_visible_month=date(2020, 5, 31),
                    date=date(2020, 1, 31),
                    className='input'
                ),
                html.Button('Submit', id='submit-val', n_clicks=0, className='submit'),
                html.Div(id="performance-info"),
            ], className='form'),
        # Right column for the map
        html.Div([
            dcc.Graph(id='map-display', className='map')
        ], className='graph')
    ], className='row'),
])

def prepare_performance_info(cached_data):
    request_roundtrip_time = cached_data.get('request_roundtrip_time', 'N/A')
    tb_elapsed = cached_data.get('statistics', {}).get('elapsed', 'N/A')
    tb_bytes_read = cached_data.get('statistics', {}).get('bytes_read', 'N/A')
    data_points = len(cached_data.get('data', []))

    return [
        html.Div(f"Request roundtrip time: {request_roundtrip_time:.3f} s"),
        html.Div(f"Tinybird processing time: {tb_elapsed:.3f} s"),
        html.Div(f"Tinybird Bytes read: {format_bytes(tb_bytes_read)}"),
        html.Div(f"Data points: {data_points}")
    ]

@app.callback(
    Output('cached-data', 'data'),
    [Input('submit-val', 'n_clicks')],
    [State('mmsi-dropdown', 'value'),
     State('start-date-input', 'date'),
     State('end-date-input', 'date'),
     State('display-mode', 'value')]
)
def fetch_data(n_clicks, mmsi, start_date, end_date, display_mode):
    if n_clicks > 0:
        start_request_time = time.time()
        api_endpoint = "latlon_by_date_by_mmsi.json" if display_mode == 'data_points' else "h3_by_date_by_mmsi.json"
        h3_resolution = "" if display_mode == 'data_points' else f"&h3r=h3_r{display_mode[-1]}"
        url = f"{TB_BASE_URL}{api_endpoint}?mmsis={mmsi}&startdate={start_date}&enddate={end_date}{h3_resolution}&token={TB_TOKEN}"

        response = requests.get(url)
        end_request_time = time.time()
        data = response.json().get('data', [])
        print(f"Requests data length: {len(data)}")

        return {
            'mode': display_mode,
            'data': data,
            'request_roundtrip_time': end_request_time - start_request_time,
            'statistics': response.json().get('statistics', {}),
            'cache_key': f"{display_mode}_{start_date}_{end_date}_{mmsi}"  # Unique key for caching
        }
    return {}

@app.callback(
    [Output('map-display', 'figure'), Output("performance-info", "children")],
    [Input('cached-data', 'data')]
)
def update_map(cached_data):
    if not cached_data or 'data' not in cached_data or not cached_data['data']:
        return go.Figure(), ''

    display_mode = cached_data.get('mode')
    print(f"Dislay mode: {display_mode}")
    print(f"Cache Key: {cached_data.get('cache_key')}")
    df = pd.DataFrame(cached_data['data'])
    fig = go.Figure()

    # Rendering logic based on display_mode
    if display_mode.startswith('h3'):
        # Render hexagons
        fig = render_hexagons(df, fig)
    elif display_mode == 'data_points':
        # Render lat/long points
        fig = render_latlong_points(df, fig)

    # Adjust viewport to fit the rendered data
    adjust_viewport(fig)

    performance_info = prepare_performance_info(cached_data)
    return fig, html.Div(performance_info, className='info')

def adjust_viewport(fig):
    # Attempt to automatically adjust the map's viewport to show all plotted data
    fig.update_layout(
        geo=dict(
            fitbounds="locations",  # This tells Plotly to fit the plotted locations
            projection_type="equirectangular"
        ),
        margin={"r":0, "t":0, "l":0, "b":0}
    )
    # Updating layout to include custom styling
    fig.update_layout(
        margin={"r":0, "t":0, "l":0, "b":0},
        geo=dict(
            scope='world',
            showland=True,
            landcolor="rgb(217, 217, 217)",  # This sets the land color
            showocean=True,
            oceancolor="rgb(224, 255, 255)",  # This sets the ocean color
            showcountries=True,
            countrycolor="DarkGrey",
            fitbounds="locations"  # Automatically adjusting viewport to fit the data
        ),
        title=dict(text="AIS Data Visualization", x=0.5)  # Center title
    )

def render_hexagons(df, fig):
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
    return fig

def render_latlong_points(df, fig):
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
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
