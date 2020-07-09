"""
Main dash app
"""
# pylint: disable=unused-argument
from enum import Enum

import plotly.graph_objs as go
from plotly.subplots import make_subplots
from .utils import get_metainfo, MetaType

from monfrontend.components.config import (
    PLOT_MEASUREMENTS,
)


def measurement_time_graphs():
    """
    Generates live figure with subplots for each measurement
    """
    measurements = PLOT_MEASUREMENTS

    nrows = max(1, len(measurements))
    fig = make_subplots(rows=nrows, cols=1, shared_xaxes=True, vertical_spacing=0.1)

    grid_style = dict(showgrid=True,
                      gridcolor='rgba(255,255,255,0.2)')
    # overall layout
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        # colorway=["#fff"],
        margin=dict(l=10, r=10, b=10, t=10, pad=0),
        xaxis=dict(zeroline=False, **grid_style),
        xaxis2=dict(zeroline=False, **grid_style),
        xaxis3=dict(
            title="time [s]",
            color="#fff",
            **grid_style,
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
        color = PLOT_MEASUREMENTS[measurement]['color']
        fillcolor = PLOT_MEASUREMENTS[measurement]['fillcolor']

        trace = go.Scatter(
            x=[-0,-1,-2,-3],
            y=[1,1,2,3],
            name=measurement,
            fill="tozeroy",
            mode="lines",
            fillcolor=fillcolor,
            line=dict(color=color, width=1)
        )

        fig.add_trace(trace, row=n + 1, col=1)

        y_layout = dict(
            title=f"{display_name} [{unit}]",
            color="#fff",
            range=range,
            **grid_style,
            #gridwith=0.5,
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
