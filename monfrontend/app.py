"""
Main dash app
"""
# pylint: disable=unused-argument
import logging
import os
import math

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State

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

alarm_triggered_color = "rgb(255, 107, 107)"
text_color = "white"
font_weight = "normal"
thresholds_color = 'rgb(101, 251, 151)'
hi_alarm_format_string = "upper limit: {0:.3g}"
lo_alarm_format_string = "lower limit: {0:.3g}"

influx = Influx(INFLUXDB_HOST, INFLUXDB_DATABASE, INFLUXDB_PORT)
app = dash.Dash(__name__)

# App layout
app = dash.Dash(__name__)
app.layout = html.Div(
    [
        # Top Bar

        html.Div(
            [
                html.Img(
                    src=app.get_asset_url("logo-pi.png"), className="top_bar_img", style={'padding': '20px'}
                ),
                html.H4("HDvent2020", style={'padding': '0px'}),

            ],
            className="tile top_bar", style={'justify-content': 'left' }
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
        dcc.Store(id="last-value-storage", storage_type="memory"),
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


@app.callback(
    Output("last-value-storage", "data"), [Input("in-memory-storage", "data"), ],
    [State("last-value-storage", "data"), ]
)
def store_last_values(data, last_values):
    if last_values is None:
        last_values = dict()
    for key in data:
        if data[key]['x']:
            last_values[key] = {
                'x': data[key]['x'][-1],
                'y': data[key]['y'][-1]
            }
    return last_values


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
    Output("bottom-bar", "children"),
    [Input("in-memory-storage", "data")],
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


def round_like(x, ref, n_significant=3):
    d = int(math.ceil(math.log10(ref)))
    n = max(n_significant-d,0)
    return round(x, n)


@app.callback(
    Output("side-bar", "children"),
    [Input("in-memory-storage", "data"), Input("last-value-storage", "data")],
)
def live_boxes(data, last_values):
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
        # alarm_lower = data[MEASUREMENTS_META[msmt]['min_key']]

        # FIXME: can we be sure this is a measurement?
        display_name = get_metainfo(MetaType.MEASUREMENT, msmt, "display_name")
        unit = get_metainfo(MetaType.MEASUREMENT, msmt, "unit")
        range = get_metainfo(MetaType.MEASUREMENT, msmt, "range")
        low_alarm_key = get_metainfo(MetaType.MEASUREMENT, msmt, "low_alarm_key")
        high_alarm_key = get_metainfo(MetaType.MEASUREMENT, msmt, "high_alarm_key")
        alarm_set_key = get_metainfo(MetaType.MEASUREMENT, msmt, "alarm_set_key")
        alarm_trigger_key = get_metainfo(MetaType.MEASUREMENT, msmt, "alarm_trigger_key")

        # low_alarm_threshold = 0
        # high_alarm_threshold = 10

        low_alarm_string = "\200"
        high_alarm_string = "\200"

        try:
            alarm_index = int(round(last_values[alarm_set_key]["y"]))
            alarm_code = ALARM_CODES[alarm_index]
        except KeyError:
            alarm_code = "none"
            pass

        if alarm_code == "low":
            try:
                low_alarm_threshold = last_values[low_alarm_key]["y"]
                low_alarm_string = lo_alarm_format_string.format(low_alarm_threshold)
            except KeyError:
                # alarm_code = "none"
                pass

        if alarm_code == "high":
            try:
                high_alarm_threshold = last_values[high_alarm_key]["y"]
                high_alarm_string = hi_alarm_format_string.format(high_alarm_threshold)
            except KeyError:
                # alarm_code = "none"
                pass

        if alarm_code == "both":
            try:
                high_alarm_threshold = last_values[high_alarm_key]["y"]
                low_alarm_threshold = last_values[low_alarm_key]["y"]
                low_alarm_string = lo_alarm_format_string.format(low_alarm_threshold)
                high_alarm_string = hi_alarm_format_string.format(high_alarm_threshold)
            except KeyError:
                pass
                # alarm_code = "none"

        alarm_trigger_state = 0
        try:
            alarm_trigger_state = last_values[alarm_trigger_key]["y"]
            alarm_trigger_state = int(round(alarm_trigger_state))
        except KeyError:
            pass

        color_lo = thresholds_color
        color_hi = thresholds_color
        main_number_color = text_color
        font_weight = 'normal'

        if alarm_trigger_state == 1:  # low alarm triggered
            color_lo = alarm_triggered_color
            main_number_color = alarm_triggered_color
            font_weight = 'normal'
        elif alarm_trigger_state == 2:  # high alarm triggered
            color_hi = alarm_triggered_color
            main_number_color = alarm_triggered_color
            font_weight = 'normal'

        mean_ = sum(data[msmt]["y"]) / len(data[msmt]["y"])
        max_ = max(data[msmt]["y"])

        value = data[msmt]['y'][-1]
        value = round_like(value, range[-1])
        children.append(
            html.Div(
                [
                    html.H5(f"{MEASUREMENTS_META[msmt]['display_name']} [{MEASUREMENTS_META[msmt]['unit']}]",
                            className="top_bar_title"),
                    html.Div([
                        html.Div(html.H3(f"{value:.3g}", className="top_bar_title",
                                         style={"color": main_number_color})
                                 , style={
                                'width': '30%',
                                'vertical-align': 'middle',
                                # 'text-align': 'center',
                                # 'justify-content': 'center',
                                # 'align-items': 'center',
                                'margin': '10px',
                                'min-width': '100px',
                                'display': 'table-cell'
                            }),
                        html.Div([
                            html.Div([
                                html.H6(
                                    high_alarm_string,
                                    style={"color": color_hi, 'text-align': 'bottom', 'font-weight': font_weight}
                                )
                            ], style={'min-height': '100%'}),

                            html.Div([
                                html.H6(
                                    low_alarm_string,
                                    style={"color": color_lo, 'text-align': 'top', 'font-weight': font_weight}
                                )], style={'min-height': '100%'})
                        ]
                            , style={'display': 'table-cell',
                                     'vertical-align': 'middle'
                                     })]),
                    # html.H6(
                    #    f"mean: {mean_:.3g},  max: {max_:.3g}", className="top_bar_title"
                    # ),
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
