# Volatility Dashboard
import dash
from dash import dcc, html, callback_context
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from functions import hv_charts, get_dvol_data, vol_term_structure, vol_surface, draw_indicator, chart_card
import yfinance as yf

pd.set_option('display.max_columns', None)  # useful for testing

# Initialize the app
app = dash.Dash(title="Volatility Dashboard", external_stylesheets=[dbc.themes.DARKLY])

def fetch_data():
    # dvol data
    btc_dvol_candles, btc_iv_rank, btc_iv_percentile, eth_dvol_candles, eth_iv_rank, eth_iv_percentile, \
        dvol_ratio = get_dvol_data()
    # term structure
    btc_vol_term_structure = vol_term_structure('BTC')
    eth_vol_term_structure = vol_term_structure('ETH')
    # vol_surface
    btc_vol_surface = vol_surface('BTC')
    eth_vol_surface = vol_surface('ETH')
    return btc_dvol_candles, btc_iv_rank, btc_iv_percentile, eth_dvol_candles, eth_iv_rank, eth_iv_percentile, \
           dvol_ratio, btc_vol_term_structure, eth_vol_term_structure, btc_vol_surface, eth_vol_surface

btc_dvol_candles, btc_iv_rank, btc_iv_percentile, eth_dvol_candles, eth_iv_rank, eth_iv_percentile, \
    dvol_ratio, btc_vol_term_structure, eth_vol_term_structure, btc_vol_surface, eth_vol_surface = fetch_data()

def parkinson_volatility(high, low, window):
    factor = 1 / (4 * np.log(2))
    log_hl_ratio_squared = (np.log(high / low)) ** 2
    return np.sqrt((factor * log_hl_ratio_squared.rolling(window=window).mean()))

def fetch_historical_vol_data(currency, period):
    # pull historical price data
    btc = yf.Ticker(currency)
    currency_data = btc.history(period=period)
    currency_data['log_return'] = np.log(currency_data['Close'] / currency_data['Close'].shift(1))

    # Calculate the historical volatility
    time_frames = [7, 30, 90, 365]
    for days in time_frames:
        currency_data[f'{days}_day_close_vol'] = currency_data['log_return'].rolling(window=days).std() * np.sqrt(365) # Annualizing the volatility
        currency_data[f'{days}_day_park_vol'] = parkinson_volatility(currency_data['High'], currency_data['Low'], days) * np.sqrt(365) # Annualizing the volatility
        currency_data[f'{days}_day_park_close_ratio'] = currency_data[f'{days}_day_park_vol'] / currency_data[f'{days}_day_close_vol']

    close_vol_fig, park_vol_fig, close_park_ratio_fig, vol_cones_fig = hv_charts(currency_data, time_frames)
    return close_vol_fig, park_vol_fig, close_park_ratio_fig, vol_cones_fig

close_vol, park_vol, close_park_ratio, vol_cones = fetch_historical_vol_data('BTC-USD', '3y')

# DVOL tab layout
dvol_tab = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Badge(
                html.B("i"),
                color="primary",
                id="btc_dvol_info",
                pill=True,
                style={"position": "absolute", "top": "10px", "left": "20px", "zIndex": 2}
            ),
            dbc.Tooltip(
                "Daily candle chart for the Deribit bitcoin volatility index for the previous year.",
                target="btc_dvol_info",
            ),
            dbc.Row([dcc.Graph(id='btc_dvol_candles', figure=btc_dvol_candles)]),
        ], width=10, style={'position': 'relative'}),
        dbc.Col([
            dbc.Row([
                dcc.Graph(id='btc_iv_rank_indicator', figure=draw_indicator('magenta', 0, 100, 'IV Rank', btc_iv_rank, 250, 200))
            ]),
            dbc.Row([
                dcc.Graph(id='btc_iv_percentile_indicator', figure=draw_indicator('magenta', 0, 100, 'IV Rank', btc_iv_percentile, 250, 200))
            ])
        ], width=2)
    ], className="my-3"),
    dbc.Row([
        dbc.Col([
            dbc.Badge(
                html.B("i"),
                color="primary",
                id="eth_dvol_info",
                pill=True,
                style={"position": "absolute", "top": "10px", "left": "20px", "zIndex": 2}
            ),
            dbc.Tooltip(
                "Daily candle chart for the Deribit ethereum volatility index for the previous year.",
                target="eth_dvol_info",
            ),
            dbc.Row([dcc.Graph(id='eth_dvol_candles', figure=eth_dvol_candles)]),
        ], width=10, style={'position': 'relative'}),
        dbc.Col([
            dbc.Row([
                dcc.Graph(id='eth_iv_rank_indicator', figure=draw_indicator('magenta', 0, 100, 'IV Rank', eth_iv_rank, 250, 200))
            ]),
            dbc.Row([
                dcc.Graph(id='eth_iv_percentile_indicator', figure=draw_indicator('magenta', 0, 100, 'IV Rank', eth_iv_percentile, 250, 200))
            ])
        ], width=2)
    ], className="mb-3"),
    dbc.Row([
        dbc.Col([
            dbc.Badge(
                html.B("i"),
                color="primary",
                id="dvol_ratio_info",
                pill=True,
                style={"position": "absolute", "top": "10px", "left": "20px", "zIndex": 2}
            ),
            dbc.Tooltip(
                [html.P("The ratio between BTC DVOL and ETH DVOL. Calculated using close data from the daily candles."),
                 html.P("When ratio > 1, BTC vol is higher. When ratio < 1, ETH vol is higher.")],
                target="dvol_ratio_info",
            ),
            dbc.Row([dcc.Graph(id='dvol_ratio', figure=dvol_ratio)]),
        ], width=10, style={'position': 'relative'})
    ], className="mb-3")

], fluid=True)

term_structure_tab = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Badge(
                html.B("i"),
                color="primary",
                id="btc_term_structure_info",
                pill=True,
                style={"position": "absolute", "top": "10px", "left": "20px", "zIndex": 2}
            ),
            dbc.Tooltip(
                html.P("Current at the money implied volatility per expiry."),
                target="btc_term_structure_info",
            ),
            dcc.Graph(id='btc_vol_term_structure', figure=btc_vol_term_structure),
        ], width=6, style={'position': 'relative'}),
    ], className="my-3"),
    dbc.Row([
        dbc.Col([
            dbc.Badge(
                html.B("i"),
                color="primary",
                id="eth_term_structure_info",
                pill=True,
                style={"position": "absolute", "top": "10px", "left": "20px", "zIndex": 2}
            ),
            dbc.Tooltip(
                html.P("Current at the money implied volatility per expiry."),
                target="eth_term_structure_info",
            ),
            dcc.Graph(id='eth_vol_term_structure', figure=eth_vol_term_structure)
        ], width=6, style={'position': 'relative'}),
    ], className="mb-3"),
], fluid=True)

vol_surface_tab = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Badge(
                html.B("i"),
                color="primary",
                id="btc_vol_surface_info",
                pill=True,
                style={"position": "absolute", "top": "10px", "left": "20px", "zIndex": 2}
            ),
            dbc.Tooltip(
                [html.P("3D implied volatility surface for BTC."),
                 html.P("Deltas of <0.01 and >0.99 have been dropped.")],
                target="btc_vol_surface_info",
            ),
            dcc.Graph(id='btc_vol_surface', figure=btc_vol_surface)
        ], width=6, style={'position': 'relative'}),
        dbc.Col([
            dbc.Badge(
                html.B("i"),
                color="primary",
                id="eth_vol_surface_info",
                pill=True,
                style={"position": "absolute", "top": "10px", "left": "20px", "zIndex": 2}
            ),
            dbc.Tooltip(
                [html.P("3D implied volatility surface for ETH."),
                 html.P("Deltas of <0.01 and >0.99 have been dropped.")],
                target="eth_vol_surface_info",
            ),
            dcc.Graph(id='eth_vol_surface', figure=eth_vol_surface)
        ], width=6, style={'position': 'relative'}),
    ], className="my-3"),
], fluid=True)

historical_vol_tab = dbc.Container([
    dbc.DropdownMenu(
        id="historical_vol_currency_dropdown",
        label="Select Currency",  # Initial label
        children=[
            dbc.DropdownMenuItem("BTC-USD", id="BTC-USD"),
            dbc.DropdownMenuItem("ETH-USD", id="ETH-USD"),
            dbc.DropdownMenuItem("SOL-USD", id="SOL-USD"),
        ],
        style={'margin-top': '2px'},
    ),
    html.Div(id='historical_vol_charts', children=[
        chart_card(
            'BTC-USD Close to Close Historical Volatility',
            dcc.Graph(id='close_vol', figure=close_vol),
            'Close to close historical volatility (daily data)'
        ),
        chart_card(
            'BTC-USD Parkinson Historical Volatility',
            dcc.Graph(id='park_vol', figure=park_vol),
            'Parkinson historical volatility (daily data)'
        ),
        chart_card(
            'BTC-USD Parkinson:C2C Ratio',
            dcc.Graph(id='close_park_ratio', figure=close_park_ratio),
            'The ratio of parkinson vol to close to close vol.'
        ),
        chart_card(
            'BTC-USD Parkinson Historical Volatility',
            dcc.Graph(id='vol_cones', figure=vol_cones),
            'Volatility cones for BTC-USD. Uses parkinson volatility.'
        ),
    ]),
], fluid=True)

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([html.H3(children='Crypto Volatility Dashboard')]),
        dbc.Col([
            html.Div(
                html.A("Trade on Deribit", href="https://www.deribit.com/?reg=1332.557&q=home", target="_blank"),
                style={'text-align': 'right'}
            ),
        ]),
        dbc.Col([
            html.Div(
                dbc.Button(
                    html.B("Refresh"),
                    color="info",
                    id="refresh_button",
                    className="my-1",
                    style={'width': '100px'}
                ),
                style={'text-align': 'right'}
            ),
        ])
    ]),
    dbc.Tabs([
        dbc.Tab(
            dvol_tab,
            label='DVOL',
            tab_id='dvol_tab',
            activeTabClassName='fw-bold',
            active_label_style={"color": "#00CFBE"},
        ),
        dbc.Tab(
            term_structure_tab,
            label='Term Structure',
            tab_id='term_structure_tab',
            activeTabClassName='fw-bold',
            active_label_style={"color": "#00CFBE"},
        ),
        dbc.Tab(
            vol_surface_tab,
            label='Vol Surface',
            tab_id='vol_surface_tab',
            activeTabClassName='fw-bold',
            active_label_style={"color": "#00CFBE"},
        ),
        dbc.Tab(
            historical_vol_tab,
            label='Historical Vol',
            tab_id='historical_vol_tab',
            activeTabClassName='fw-bold',
            active_label_style={"color": "#00CFBE"},
        ),

    ], id="tabs_main", active_tab="dvol_tab"
    ),
], fluid=True)

@app.callback(
    [
        Output('btc_dvol_candles', 'figure'),
        Output('btc_iv_rank_indicator', 'figure'),
        Output('btc_iv_percentile_indicator', 'figure'),
        Output('eth_dvol_candles', 'figure'),
        Output('eth_iv_rank_indicator', 'figure'),
        Output('eth_iv_percentile_indicator', 'figure'),
        Output('dvol_ratio', 'figure'),
        Output('btc_vol_term_structure', 'figure'),
        Output('eth_vol_term_structure', 'figure'),
        Output('btc_vol_surface', 'figure'),
        Output('eth_vol_surface', 'figure'),
    ],
    Input('refresh_button', 'n_clicks'),
)
def refresh_data(n_clicks):
    print('button presses: ', n_clicks)

    btc_dvol_candles, btc_iv_rank, btc_iv_percentile, eth_dvol_candles, eth_iv_rank, eth_iv_percentile, \
    dvol_ratio, btc_vol_term_structure, eth_vol_term_structure, btc_vol_surface, eth_vol_surface = fetch_data()

    btc_iv_rank_indicator = draw_indicator('magenta', 0, 100, 'IV Rank', btc_iv_rank, 250, 200)
    btc_iv_percentile_indicator = draw_indicator('magenta', 0, 100, 'IV Percentile', btc_iv_percentile, 250, 200)
    eth_iv_rank_indicator = draw_indicator('magenta', 0, 100, 'IV Rank', eth_iv_rank, 250, 200)
    eth_iv_percentile_indicator = draw_indicator('magenta', 0, 100, 'IV Percentile', eth_iv_percentile, 250, 200)

    return btc_dvol_candles, btc_iv_rank_indicator, btc_iv_percentile_indicator, eth_dvol_candles, \
           eth_iv_rank_indicator, eth_iv_percentile_indicator, dvol_ratio, btc_vol_term_structure, \
           eth_vol_term_structure, btc_vol_surface, eth_vol_surface

@app.callback(
    Output('historical_vol_charts', 'children'),
    Output("historical_vol_currency_dropdown", "label"),
    [Input("BTC-USD", "n_clicks"),
     Input("ETH-USD", "n_clicks"),
     Input("SOL-USD", "n_clicks")],
    prevent_initial_call=True
)
def historical_price_data(*args):
    # Determine which button was clicked
    ctx = callback_context
    if not ctx.triggered:
        # Default to BTC-USD if nothing was clicked yet
        selected_currency = 'BTC-USD'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        selected_currency = button_id

    # fetch data for the selected currency, and calculate the new data
    close_vol, park_vol, close_park_ratio, vol_cones = fetch_historical_vol_data(selected_currency, '3y')
    new_content = [
        chart_card(
            f'{selected_currency} Close to Close Historical Volatility',
            dcc.Graph(id='close_vol', figure=close_vol),
            'Close to close historical volatility (daily data)'
        ),
        chart_card(
            f'{selected_currency} Parkinson Historical Volatility',
            dcc.Graph(id='park_vol', figure=park_vol),
            'Parkinson historical volatility (daily data)'
        ),
        chart_card(
            f'{selected_currency} Parkinson:C2C Ratio',
            dcc.Graph(id='close_park_ratio', figure=close_park_ratio),
            'The ratio of parkinson vol to close to close vol.'
        ),
        chart_card(
            f'{selected_currency} Volatility Cones',
            dcc.Graph(id='vol_cones', figure=vol_cones),
            'Volatility cones for {selected_currency}. Uses parkinson volatility.'
        ),
    ]
    return new_content, selected_currency


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)