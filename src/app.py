# %%
import requests
from io import BytesIO

import numpy as np
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go

from dash import Dash, html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc

from plot import plot_cumulative, plot_time_of_day

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

# %% SPLIT OUT CATEGORY/TYPE
a = np.vstack(df["bev type"].apply(lambda x: x.split("-")))
df["bev category"] = a[:, 0]
df["bev full type"] = df["bev type"]
df["bev type"] = a[:, 1]
df.set_index(["bev category", "bev type"], inplace=True)

# %% MAKE APP
graph_width = 6  # 12 total per row
external_stylesheets = [dbc.themes.BOOTSTRAP, "./assets/buttons.css"]

plotly.io.templates.default = "plotly_white"
app = Dash(
    __name__,
    title="massi's bevs",
    external_stylesheets=external_stylesheets,
)
server = app.server

app.layout = [
    dbc.Container(
        [
            # HEADER ROW
            dbc.Row(
                html.Div(
                    [html.Img(src="./assets/logo.svg", height=80)],
                    style={
                        "textAlign": "center",
                        "color": "blue",
                        "fontSize": 30,
                        "fontFamily": "Optima, sans-serif",
                        "padding-top": 10,
                        "padding-bottom": 10,
                    },
                ),
            ),
            # BUTTON ROW: TO ADD
            dbc.Row(
                dbc.RadioItems(
                    id="slicer-buttons",
                    options=[
                        {"label": "all bev types", "value": "all bev types"},
                        {"label": "by category", "value": "by category"},
                        {"label": "dc", "value": "DC"},
                        {"label": "coffee", "value": "Coffee"},
                        {"label": "other", "value": "other"},
                    ],
                    value="by category",
                    labelClassName="radio-buttongroup-labels",
                    labelCheckedClassName="radio-buttongroup-labels-checked",
                    inline=True,
                    className="custom-radio",
                ),
            ),
            # GRAPH ROW 1
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(figure={}, id="graph_bar_type"), width=graph_width
                    ),
                    dbc.Col(
                        dcc.Graph(figure={}, id="graph_time_count"), width=graph_width
                    ),
                ]
            ),
            # GRAPH ROW 2
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(figure={}, id="graph_by_hour"), width=graph_width
                    ),
                    dbc.Col(
                        dcc.Graph(figure={}, id="graph_time_cost"), width=graph_width
                    ),
                ]
            ),
        ],
        fluid=True,
    )
]

# %% INTERACTIVITY


def button_slice(df, how, known_categories=["DC", "Coffee"]):

    # use category name as type
    if how.lower() in ["by category", "category", "all_category"]:
        df_slice = df.reset_index()
        df_slice["bev type"] = df_slice["bev category"]

    # use all types regardless of category
    elif how.lower() in ["all bev types", "all", "all_type"]:
        df_slice = df.reset_index()
        df_slice["bev type"] = df_slice["bev full type"]  # include categories in name

    # unknown categories
    elif how.lower() == "other":
        ii_other = [
            x not in known_categories for x in df.index.get_level_values("bev category")
        ]
        df_slice = df.loc[ii_other].reset_index()
        df_slice["bev type"] = df_slice["bev full type"]  # include categories in name

    # only take bev category == how
    else:
        df_slice = df.xs(how)

    df_slice.reset_index(inplace=True)
    return df_slice


@callback(
    [
        Output(component_id="graph_bar_type", component_property="figure"),
        Output(component_id="graph_time_count", component_property="figure"),
        Output(component_id="graph_time_cost", component_property="figure"),
        Output(component_id="graph_by_hour", component_property="figure"),
    ],
    [Input(component_id="slicer-buttons", component_property="value")],
)
def update_graphs(slicer_keyword):
    df_slice = button_slice(df, slicer_keyword)

    # return 4 empty graphs with empty data
    if len(df_slice) == 0:
        return [go.Figure(data=[])] * 4

    graph_bar_type = px.histogram(
        df_slice,
        title="TOTAL BEV COUNT",
        x="bev type",
        color="bev type",
    )
    graph_bar_type.update_layout(yaxis_title="bev count")

    graph_time_count = plot_cumulative(
        df_slice, title="BEV COUNT OVER TIME", yaxis_title="bev count"
    )

    graph_time_cost = plot_cumulative(
        df_slice,
        title="BEV COST OVER TIME",
        cumulative_function=lambda df: np.cumsum(df["bev cost"].fillna(0)),
        yaxis_title="cost",
    )

    graph_by_hour = plot_time_of_day(df_slice)

    return (graph_bar_type, graph_time_count, graph_time_cost, graph_by_hour)


# %%
if __name__ == "__main__":
    app.run(debug=True)
