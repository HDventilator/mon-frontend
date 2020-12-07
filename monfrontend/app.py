"""
Main dash app
"""
# pylint: disable=unused-argument
import logging
import os

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output

from monfrontend.components.config import (
    BOTTOM_BAR_MEASUREMENTS,
    MEASUREMENTS_META,
    PLOT_MEASUREMENTS,
    SIDE_BAR_MEASUREMENTS,
)
from monfrontend.components.influx import Influx
from monfrontend.components.utils import get_metainfo, MetaType
from monfrontend.components.figures import measurement_time_graphs

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

        html.Div(
            [
                html.H4("HDvent"),
                # html.Img(
                #     src=app.get_asset_url("HDvent-logo.png"), className="top_bar_img",
                # ),
            ],
            className="tile top_bar",
        ),

        # Time series plots

        html.Div(
            [
                dcc.Graph(
                    figure=measurement_time_graphs(),
                    id="live-graphs",
                    animate=False,
                    responsive=True,
                    config={"displayModeBar": False},
                    style=dict(height="100%", width="100%"),
                ),
            ],
            className="tile main_display",
        ),
        # Sidebar
        html.Div([], id="side-bar", className="tile side_bar", ),
        # Bottom bar
        html.Div([], id="bottom-bar", className="tile bottom_bar", ),
        # Bottom info box
        html.Div([], id="machine-status", className="tile info_box", ),
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
        data = list(influx.get_data(measurement, duration="32s", groupby_time="100ms"))

        measurements_data[measurement] = {
            "x": [d["time"] for d in data],
            "y": [d["mean_value"] for d in data],
        }
    return measurements_data


# Display live machine status on the right of the bottom bar (if this functionality is needed)
@app.callback(
    Output("machine-status", "children"), [Input("in-memory-storage", "data"), ],
)
def live_status(data):
    """
    Generates 'machine-status' component
    """
    # Fetch machine status from influx here

    machine_status = 1
    return [html.H6("VC open loop")]


# callback to display multiple live machine parameters in the left of the bottom bar
@app.callback(
    Output("bottom-bar", "children"), [Input("in-memory-storage", "data"), ],
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
        total_range = get_metainfo(MetaType.PARAMETER, msmt, "total_range")
        min_key = get_metainfo(MetaType.PARAMETER, msmt, "min_key")
        max_key = get_metainfo(MetaType.PARAMETER, msmt, "max_key")
        range_min = data[min_key]["y"][-1]
        range_max = data[max_key]["y"][-1]

        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=data[msmt]["y"][-1],
                domain={"x": [0.2, 0.8], "y": [0, 0.8]},
                title=f"{display_name} [{unit}]",
                gauge={
                    "axis": {
                        "range": total_range,
                        # "tickwidth": 1,
                        # "tickcolor": "darkblue",
                    },
                    "steps": [
                        {"range": [range_min, range_max], "color": "rgba(251, 163, 101, 0.2)"}
                    ],
                    "bar": {"color": "rgb(251, 163, 101)"},
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
    Output("side-bar", "children"), [Input("in-memory-storage", "data"), ],
)
def live_boxes(data):
    """
    Generates components for the 'side-bar'
    """
    measurements = SIDE_BAR_MEASUREMENTS
    children = []
    # Alarm set codes
    ALARM_CODES = {
        0: "none", 1: "low", 2: "high", 3: "both"
    }

    for msmt in measurements:
        #alarm_lower = data[MEASUREMENTS_META[msmt]['min_key']]

        # FIXME: can we be sure this is a measurement?
        display_name = get_metainfo(MetaType.MEASUREMENT, msmt, "display_name")
        unit = get_metainfo(MetaType.MEASUREMENT, msmt, "unit")
        low_alarm_key = get_metainfo(MetaType.MEASUREMENT, msmt, "low_alarm_key")
        high_alarm_key = get_metainfo(MetaType.MEASUREMENT, msmt, "high_alarm_key")
        alarm_set_key = get_metainfo(MetaType.MEASUREMENT, msmt, "alarm_set_key")

        low_alarm_threshold=None
        high_alarm_threshold=None

        low_alarm_string = ""
        high_alarm_string = ""
        alarm_format_string = "{0:.3g}"

        try:
            alarm_index = int(round(data[alarm_set_key]["y"][-1]))
            alarm_code = ALARM_CODES[alarm_index]
        except KeyError:
            alarm_code = "none"
            pass

        if alarm_code == "low":
            try:
                low_alarm_threshold = data[low_alarm_key]["y"][-1]
                low_alarm_string = alarm_format_string.format(low_alarm_threshold)
            except KeyError:
                #alarm_code = "none"
                pass

        if alarm_code == "high":
            try:
                high_alarm_threshold = data[high_alarm_key]["y"][-1]
                high_alarm_string = alarm_format_string.format(high_alarm_threshold)
            except KeyError:
                #alarm_code = "none"
                pass

        if alarm_code == "both":
            try:
                high_alarm_threshold = data[high_alarm_key]["y"][-1]
                low_alarm_threshold = data[low_alarm_key]["y"][-1]
                low_alarm_string = alarm_format_string.format(low_alarm_threshold)
                high_alarm_string = alarm_format_string.format(high_alarm_threshold)
            except KeyError:
                pass
                #alarm_code = "none"






        mean_ = sum(data[msmt]["y"]) / len(data[msmt]["y"])
        max_ = max(data[msmt]["y"])
        children.append(
            html.Div(
                [
                    html.H5(f"{MEASUREMENTS_META[msmt]['display_name']} [{MEASUREMENTS_META[msmt]['unit']}]",
                            className="top_bar_title"),
                    html.Div([
                        html.Div(html.H3(f"{data[msmt]['y'][-1]:.3g}", className="top_bar_title")
                                 , style={'width': '30%', 'display': 'inline-block'}),
                             html.Div([
                                 html.H6(
                                     high_alarm_string,
                                 ),
                                 html.H6(
                                     low_alarm_string,
                                 )]
                                 , style={'display': 'inline-block'})]),
                    html.H6(
                        f"mean: {mean_:.3g},  max: {max_:.3g}", className="top_bar_title"
                    ),
                ],
                className="status_box",
            )
        )
    return children


@app.callback(
    Output("live-graphs", "extendData"), [Input("in-memory-storage", "data"), ],
)
def live_graphs(data):
    """
    Generates live figure with subplots for each measurement
    """
    measurements = PLOT_MEASUREMENTS
    x = [data[measurement]["x"] for measurement in measurements]
    y = [data[measurement]["y"] for measurement in measurements]
    trace_indices = list(range(0, len(x)))
    return {'y': y, 'x': x}, trace_indices, len(x[0])


if __name__ == "__main__":
    client = influx._get_client()
    print(client.get_list_measurements())

    app.run_server(host="0.0.0.0", port=8050, debug=True, dev_tools_ui=True)
