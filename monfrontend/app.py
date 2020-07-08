"""
Main dash app
"""
# pylint: disable=unused-argument
import logging
import os
from enum import Enum
from typing import Optional

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
from plotly.subplots import make_subplots

from monfrontend.config import (
    ALARMS_META,
    BOTTOM_BAR_MEASUREMENTS,
    MEASUREMENTS_META,
    PARAMETERS_META,
    PLOT_MEASUREMENTS,
    SIDE_BAR_MEASUREMENTS,
)
from monfrontend.influx import Influx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOGLEVEL", "INFO"))


INFLUXDB_HOST = os.environ.get("INFLUXDB_HOST", "localhost")
INFLUXDB_PORT = int(os.environ.get("INFLUXDB_PORT", 8086))
UPDATE_INTERVAL = float(os.environ.get("GRAPH_UPDATE_INTERVAL_SECONDS", "1"))
INFLUXDB_DATABASE = os.environ.get("INFLUXDB_DATABASE", "default")


influx = Influx(INFLUXDB_HOST, INFLUXDB_DATABASE, INFLUXDB_PORT)
app = dash.Dash(__name__)


# App layout
app = dash.Dash(__name__)
app.layout = html.Div(
    [
        # Top Bar
        html.Div([html.H2("VENT MODE", className="mode_box")],),
        html.Div(
            [
                html.H3("HDvent"),
                html.Img(
                    src=app.get_asset_url("HDvent-logo.png"), className="top_bar_img",
                ),
            ],
            className="top_bar",
        ),
        # Live Plots
        html.Div(
            [
                dcc.Graph(
                    id="live-graphs",
                    animate=False,
                    responsive=True,
                    config={"displayModeBar": False},
                    style=dict(height="100%", width="100%"),
                ),
            ],
            className="main_display",
        ),
        # Sidebar
        html.Div([], id="side-bar", className="side_bar",),
        # Bottom bar
        html.Div([], id="bottom-bar", className="bottom_bar",),
        # Bottom info box
        html.Div([], id="machine-status", className="info_box",),
        dcc.Interval(
            id="graph-update",
            interval=int(float(UPDATE_INTERVAL) * 1000),
            # disabled=True,
        ),
        dcc.Store(id="in-memory-storage", storage_type="memory"),
    ],
    className="app_container",
)


def get_server():
    """
    Callable to return Flask server object
    Use with
    $ gunicorn -b 0.0.0.0:8050 'app:get_server()'
    """
    return app.server


MetaType = Enum("MetaType", "MEASUREMENT, PARAMETER, ALARM")


def get_metainfo(meta_type: MetaType, identifier: str, key: str) -> Optional[str]:
    """
    Retrieve metainfo `key` (e.g. "display_name" for the measurement identified
    by `identifer` (e.g. "dpFLOW")
    """
    try:
        if meta_type == MetaType.MEASUREMENT:
            return MEASUREMENTS_META[identifier][key]
        if meta_type == MetaType.PARAMETER:
            return PARAMETERS_META[identifier][key]
        if meta_type == MetaType.ALARM:
            return ALARMS_META[identifier][key]
    except KeyError:
        pass
    return None


@app.callback(
    Output("in-memory-storage", "data"), [Input("graph-update", "n_intervals")],
)
def fetch_data(intervals):
    """
    called by graph-update timer
    uses influx client to fetch new data for all available measurements
    """
    measurements_data = {}
    for measurement in influx.get_measurements():
        data = list(influx.get_data(measurement, duration="30s", groupby_time="100ms"))

        measurements_data[measurement] = {
            "x": [d["time"] for d in data],
            "y": [d["mean_value"] for d in data],
        }
    return measurements_data


# Display live machine status on the right of the bottom bar (if this functionality is needed)
@app.callback(
    Output("machine-status", "children"), [Input("in-memory-storage", "data"),],
)
def live_status(data):
    """
    Generates 'machine-status' component
    """
    # Fetch machine status from influx here

    machine_status = 1
    return [html.H6(f"Status: {machine_status}")]


# callback to display multiple live machine parameters in the left of the bottom bar
@app.callback(
    Output("bottom-bar", "children"), [Input("in-memory-storage", "data"),],
)
def live_machine(data):
    """
    Generates components for the 'bottom-bar'
    """
    measurements = BOTTOM_BAR_MEASUREMENTS["debug"]
    # for now use all available measurements, instead data.keys?

    children = []

    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, b=0, t=0, pad=5),
        showlegend=False,
        font={"color": "white"},
    )

    for msmt in measurements:
        display_name = get_metainfo(MetaType.PARAMETER, msmt, "display_name")
        unit = get_metainfo(MetaType.PARAMETER, msmt, "unit")
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=data[msmt]["y"][-1],
                domain={"x": [0.2, 0.8], "y": [0, 0.8]},
                title=f"{display_name} [{unit}]",
                gauge={
                    # "axis": {"tickwidth": 1, "tickcolor": "darkblue",},
                    # "bar": {"color": "darkblue"},
                    # "bgcolor": "white",
                    # "borderwidth": 2,
                    # "bordercolor": "gray",
                },
            )
        )
        fig.update_layout(layout)

        children.append(
            dcc.Graph(figure=fig, config={"displayModeBar": False}, className="gauge")
        )

    return children


@app.callback(
    Output("side-bar", "children"), [Input("in-memory-storage", "data"),],
)
def live_boxes(data):
    """
    Generates components for the 'side-bar'
    """
    measurements = SIDE_BAR_MEASUREMENTS
    children = []
    for msmt in measurements:

        # FIXME: can we be sure this is a measurement?
        display_name = get_metainfo(MetaType.MEASUREMENT, msmt, "display_name")
        unit = get_metainfo(MetaType.MEASUREMENT, msmt, "unit")

        mean_ = sum(data[msmt]["y"]) / len(data[msmt]["y"])
        max_ = max(data[msmt]["y"])
        children.append(
            html.Div(
                [
                    html.H4(f"{MEASUREMENTS_META[msmt]['display_name']} [{MEASUREMENTS_META[msmt]['unit']}]", className="top_bar_title"),
                    html.H3(f"{data[msmt]['y'][-1]:.3g}", className="top_bar_title"),
                    html.H4(
                        f"mean: {mean_:.2f}  max: {max_:.2f}", className="top_bar_title"
                    ),
                ],
                className="status_box",
            )
        )
    return children


@app.callback(
    Output("live-graphs", "figure"), [Input("in-memory-storage", "data"),],
)
def live_graphs(data):
    """
    Generates live figure with subplots for each measurement
    """
    measurements = PLOT_MEASUREMENTS
    if not measurements:
        print("no measurements found in influxdb!")

    nrows = max(1, len(measurements))
    fig = make_subplots(rows=nrows, cols=1, shared_xaxes=True, vertical_spacing=0.05)

    # overall layout
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        # colorway=["#fff"],
        margin=dict(l=10, r=10, b=10, t=10, pad=0),
        xaxis=dict(zeroline=False, showgrid=False),
        xaxis2=dict(zeroline=False, showgrid=False),
        xaxis3=dict(
            title="TIME [s]",
            color="#fff",
            showgrid=False,
            zeroline=False,
            range=[-30, 0],  # 30 seconds in the past
        ),
        showlegend=False,
    )

    # add traces and setup axes for each measurement
    for n, measurement in enumerate(measurements):

        # FIXME: can we be sure this is a measurement?
        display_name = get_metainfo(MetaType.MEASUREMENT, measurement, "display_name")
        unit = get_metainfo(MetaType.MEASUREMENT, measurement, "unit")
        range = get_metainfo(MetaType.MEASUREMENT, measurement, "range")

        trace = go.Scatter(
            x=data[measurement]["x"],
            y=data[measurement]["y"],
            name=measurement,
            fill="tozeroy",
            mode="lines",
        )
        fig.add_trace(trace, row=n + 1, col=1)

        y_layout = dict(
            title=f"{display_name.upper()} [{unit}]",
            color="#fff",
            range=range,
            showgrid=False,
            zeroline=False,
            showline=False,
        )
        if n == 0:
            layout["yaxis"] = y_layout
        else:
            layout[f"yaxis{n+1}"] = y_layout
    # set layout and return figure
    fig.update_layout(layout)
    return fig


if __name__ == "__main__":
    client = influx._get_client()
    print(client.get_list_measurements())

    app.run_server(host="0.0.0.0", port=8050, debug=True)
