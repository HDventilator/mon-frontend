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
from plotly.subplots import make_subplots

from .influx import Influx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOGLEVEL", "INFO"))


INFLUXDB_HOST = os.environ.get("INFLUXDB_HOST", "localhost")
INFLUXDB_PORT = int(os.environ.get("INFLUXDB_PORT", 8086))
UPDATE_INTERVAL = float(os.environ.get("GRAPH_UPDATE_INTERVAL_SECONDS", 1))
INFLUXDB_DATABASE = os.environ.get("INFLUXDB_DATABASE", "default")


influx = Influx(INFLUXDB_HOST, INFLUXDB_DATABASE, INFLUXDB_PORT)
app = dash.Dash(__name__)


# App layout
app = dash.Dash(__name__)
app.layout = html.Div(
    [
        html.Div(
            [
                ## Top Bar
                html.Div(
                    [
                        html.Div(
                            [html.H4("MODE", className="top_bar_title"),],
                            className="one-third column top_bar_mode",
                        ),
                        html.Div(
                            [html.H4("HDvent", className="top_bar_title"),],
                            className="two-thirds column top_bar_info",
                        ),
                    ],
                    className="top_bar",
                ),
                ## Main Display Area
                html.Div(
                    [
                        # Live Plots
                        html.Div(
                            [
                                html.Div(
                                    [
                                        dcc.Graph(
                                            id="live-graphs",
                                            style={"height": "80vh"},
                                            animate=False,
                                        ),
                                    ],
                                    className="live_plot",
                                ),
                                dcc.Interval(id="graph-update", interval=1 * 1000),
                            ],
                            className="two-thirds column live_plots",
                        ),
                        # Status Boxes
                        html.Div(
                            [
                                # empty, to be filled when we get data
                            ],
                            id="status-boxes",
                            className="one-third column status_boxes",
                        ),
                    ],
                    className="main_display",
                ),
                ## Bottom Bar
                html.Div(
                    [
                        html.Div(
                            [html.H4("MACHINE PARAMETERS", className="top_bar_title"),],
                            className="two-thirds column machine_parameters",
                        ),
                        html.Div(
                            [html.H4("MACHINE STATUS", className="top_bar_title"),],
                            className="one-third column machine_status",
                        ),
                    ],
                    className="bottom_bar",
                ),
            ],
            className="app_content",
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
        data = list(influx.get_data(measurement, duration="30s"))

        measurements_data[measurement] = {
            "x": [d["time"] for d in data],
            "y": [d["value"] for d in data],
        }
    return measurements_data


@app.callback(
    Output("status-boxes", "children"), [Input("in-memory-storage", "data"),],
)
def live_boxes(data):
    """
    Generates live boxes as children of div 'status-boxes'
    """
    measurements = list(influx.get_measurements())
    # for now use all available measurements, instead data.keys?

    children = []
    for msmt in measurements:
        mean_ = sum(data[msmt]["y"]) / len(data[msmt]["y"])
        max_ = max(data[msmt]["y"])
        children.append(
            html.Div(
                [
                    html.H6(f"{msmt.upper()}", className="top_bar_title"),
                    html.H1(f"{data[msmt]['y'][-1]}", className="top_bar_title"),
                    html.H6(
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
    measurements = list(influx.get_measurements())
    nrows = len(measurements)
    fig = make_subplots(rows=nrows, cols=1, shared_xaxes=True, vertical_spacing=0.02,)

    # overall layout
    layout = dict(
        paper_bgcolor="#000",
        plot_bgcolor="#000",
        # colorway=["#fff"],
        xaxis3=dict(title="relative time [s]", color="#fff"),
        showlegend=False,
    )

    # add traces and setup axes for each measurement
    for n, measurement in enumerate(measurements):
        trace = go.Scatter(
            x=data[measurement]["x"],
            y=data[measurement]["y"],
            name=measurement,
            fill="tozeroy",
            mode="lines",
        )
        fig.add_trace(trace, row=n + 1, col=1)

        y_layout = dict(
            title=f"{measurement.upper()} [-]",
            color="#fff",
            range=[min(data[measurement]["y"]), max(data[measurement]["y"])],
            showgrid=False,
        )
        if n == 0:
            layout["yaxis"] = y_layout
        else:
            layout[f"yaxis{n+1}"] = y_layout

    # set layout and return figure
    fig.update_layout(layout)
    return fig


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
