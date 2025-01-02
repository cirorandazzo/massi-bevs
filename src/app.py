# %%
import requests
from io import BytesIO

import numpy as np
import pandas as pd
import plotly
import plotly.express as px

from dash import Dash, html, dcc
import dash_bootstrap_components as dbc


# %% LOAD DATA FROM GOOGLE SHEETS

# google sheet info
key = "1axUmdj7sbmA7wn0gTVU-tr4bMiXoLd1ntRdXdEdQwOU"
sheet_url = f"https://docs.google.com/spreadsheets/d/{key}/export?format=csv&id={key}"

r = requests.get(sheet_url)

# load
if r.status_code == 200:
    data = r.content
    df = pd.read_csv(
        BytesIO(data),
        # Parse column values to datetime
        parse_dates=["Timestamp", "bev time"],
    )

    print(f"Loaded df: {len(df)} rows.")
else:
    ConnectionError(f"Failed to fetch data: status code {r.status_code}")

# %% FILL EMPTY TIMES FROM ENTRY TIMESTAMP
ii_fill_timestamp = df["bev time"].isna()
df.loc[ii_fill_timestamp, "bev time"] = df.loc[ii_fill_timestamp, "Timestamp"]

del ii_fill_timestamp

# %% PREPARE GRAPHS


def sandwich_series(series, start, end):
    return pd.concat([pd.Series(x) for x in (start, series, end)])


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

plotly.io.templates.default = "plotly_white"

graph_bar_type = px.histogram(
    df,
    title="TOTAL BEV COUNT",
    x="bev type",
    color="bev type",
)
graph_bar_type.update_layout(yaxis_title="bev count")

graph_time_count = plot_cumulative(
    df,
    title="BEV COUNT OVER TIME",
    yaxis_title="bev count"
    )

graph_time_cost = plot_cumulative(
    df,
    title="BEV COST OVER TIME",
    cumulative_function= lambda df: np.cumsum( df["bev cost"].fillna(0) ),
    yaxis_title="cost"
)

graph_by_hour = plot_time_of_day(df)


# %% MAKE APP
graph_width = 6  # 12 total per row
external_stylesheets = [dbc.themes.BOOTSTRAP]

app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = [
    dbc.Container(
        [
            # HEADER ROW
            dbc.Row(
                html.Div(
                    children=[html.H1("massi's bev tracker")],
                    style={"textAlign": "center", "color": "blue", "fontSize": 30, "fontFamily":"Optima, sans-serif"},
                ),
            ),
            # BUTTON ROW: TO ADD
            dbc.Row(),
            # GRAPH ROW 1
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=graph_bar_type), width=graph_width),
                    dbc.Col(dcc.Graph(figure=graph_time_count), width=graph_width),
                ]
            ),
            # GRAPH ROW 2
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=graph_by_hour), width=graph_width),
                    dbc.Col(dcc.Graph(figure=graph_time_cost), width=graph_width),
                ]
            ),
        ],
        fluid=True,
    )
]

if __name__ == "__main__":
    app.run(debug=True)
