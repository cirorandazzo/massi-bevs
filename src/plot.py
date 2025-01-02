# plot.py
# 

import numpy as np
import pandas as pd
import plotly
import plotly.express as px

def plot_cumulative(
    df,
    time_col="bev time",
    group_by_col="bev type",
    start_time=None,
    end_time=None,
    cumulative_function=lambda df: np.arange(1, len(df) + 1),
    plot_total=True,
    **layout_kwargs,
):
    import plotly.graph_objects as go

    fig = go.Figure()

    df = df.sort_values(by=time_col)

    if start_time is None:
        start_time = df[time_col].min()
    else:
        df = df.loc[df[time_col] >= start_time]

    if end_time is None:
        end_time = df[time_col].max()
    else:
        df = df.loc[df[time_col] <= end_time]

    for bev_type, group in df.groupby(group_by_col):
        cumulative = cumulative_function(group)
        fig.add_trace(
            go.Scatter(
                x=sandwich_series(group[time_col], start_time, end_time),
                y=sandwich_series(cumulative, 0, list(cumulative)[-1]),
                mode="lines",
                name=bev_type,
            )
        )

    fig.update_layout(
        xaxis_title="date",
        legend_title="BEV TYPE",
        **layout_kwargs
    )

    if plot_total:
        cumulative = cumulative_function(df)
        fig.add_trace(
            go.Scatter(
                x=sandwich_series(df[time_col], start_time, end_time),
                y=sandwich_series(cumulative, 0, list(cumulative)[-1]),
                mode="lines",
                name="Total",
                line=dict(color="black", dash="dash"),
            )
        )

    return fig

def plot_time_of_day(df):

    df["time of day"] = df["bev time"].dt.hour

    fig = px.histogram(
        df,
        title="TIME OF DAY",
        x="time of day",
        color="bev type",
        nbins=24, # 1 bin per hour
    )

    fig.update_layout(yaxis_title="count during range",    xaxis=dict(
        range=[0, 24]  # Set x-axis range from 0 to 6
    ))

    return fig

def sandwich_series(series, start, end):
    import pandas as pd
    
    return pd.concat([pd.Series(x) for x in (start, series, end)])