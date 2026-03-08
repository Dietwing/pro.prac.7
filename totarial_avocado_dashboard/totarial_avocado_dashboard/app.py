import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px


DATA_PATH = "data/avocado.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, delimiter=";")
    df.columns = df.columns.str.strip()
    df["Date"] = pd.to_datetime(df["Date"], format="%d.%m.%Y", errors="coerce")
    df = df.dropna(subset=["Date"]).copy()
    df["year"] = df["year"].astype(int)
    df.sort_values("Date", inplace=True)
    return df


def build_empty_figure(title: str):
    fig = px.line(title=title)
    fig.update_layout(
        template="plotly_white",
        annotations=[
            {
                "text": "Нет данных для выбранных параметров",
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 16},
            }
        ],
    )
    return fig


DATA = load_data()
DEFAULT_REGION = sorted(DATA["region"].unique())[0]
DEFAULT_TYPE = sorted(DATA["type"].unique())[0]
DEFAULT_YEAR_RANGE = [int(DATA["year"].min()), int(DATA["year"].max())]

app = dash.Dash(__name__, title="Avocado Dashboard")
server = app.server

app.layout = html.Div(
    className="page",
    children=[
        html.Div(
            className="hero",
            children=[
                html.H1("Интерактивная панель анализа рынка авокадо"),
                html.P("Визуализация динамики средней цены и объема продаж по регионам США за 2015-2018 годы."),
            ],
        ),
        html.Div(
            className="controls-panel",
            children=[
                html.Div(
                    className="control",
                    children=[
                        html.Label("Регион"),
                        dcc.Dropdown(
                            id="region-dropdown",
                            options=[{"label": region, "value": region} for region in sorted(DATA["region"].unique())],
                            value=DEFAULT_REGION,
                            clearable=False,
                        ),
                    ],
                ),
                html.Div(
                    className="control",
                    children=[
                        html.Label("Тип продукции"),
                        dcc.Dropdown(
                            id="type-dropdown",
                            options=[{"label": item, "value": item} for item in sorted(DATA["type"].unique())],
                            value=DEFAULT_TYPE,
                            clearable=False,
                        ),
                    ],
                ),
                html.Div(
                    className="control",
                    children=[
                        html.Label("Период наблюдения"),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=DATA["Date"].min(),
                            max_date_allowed=DATA["Date"].max(),
                            start_date=DATA["Date"].min(),
                            end_date=DATA["Date"].max(),
                            display_format="DD.MM.YYYY",
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            className="summary-grid",
            children=[
                html.Div(className="summary-card", children=[html.Span("Средняя цена"), html.H3(id="avg-price-card")]),
                html.Div(className="summary-card", children=[html.Span("Суммарный объем"), html.H3(id="total-volume-card")]),
                html.Div(className="summary-card", children=[html.Span("Количество записей"), html.H3(id="records-card")]),
            ],
        ),
        html.Div(
            className="charts-grid",
            children=[
                html.Div(className="chart-card", children=[dcc.Graph(id="price-graph")]),
                html.Div(className="chart-card", children=[dcc.Graph(id="volume-graph")]),
                html.Div(className="chart-card chart-card-wide", children=[dcc.Graph(id="year-graph")]),
            ],
        ),
    ],
)


@app.callback(
    Output("price-graph", "figure"),
    Output("volume-graph", "figure"),
    Output("year-graph", "figure"),
    Output("avg-price-card", "children"),
    Output("total-volume-card", "children"),
    Output("records-card", "children"),
    Input("region-dropdown", "value"),
    Input("type-dropdown", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
)
def update_dashboard(selected_region: str, selected_type: str, start_date: str, end_date: str):
    filtered = DATA[
        (DATA["region"] == selected_region)
        & (DATA["type"] == selected_type)
        & (DATA["Date"] >= pd.to_datetime(start_date))
        & (DATA["Date"] <= pd.to_datetime(end_date))
    ].copy()

    if filtered.empty:
        empty_price = build_empty_figure("Динамика средней цены")
        empty_volume = build_empty_figure("Динамика объема продаж")
        empty_year = build_empty_figure("Средняя цена по годам")
        return empty_price, empty_volume, empty_year, "0", "0", "0"

    price_fig = px.line(
        filtered,
        x="Date",
        y="AveragePrice",
        markers=True,
        title=f"Динамика средней цены: {selected_region}, {selected_type}",
    )
    price_fig.update_layout(template="plotly_white", xaxis_title="Дата", yaxis_title="Цена, $")

    volume_fig = px.area(
        filtered,
        x="Date",
        y="Total Volume",
        title=f"Динамика объема продаж: {selected_region}, {selected_type}",
    )
    volume_fig.update_layout(template="plotly_white", xaxis_title="Дата", yaxis_title="Объем")

    by_year = (
        filtered.groupby("year", as_index=False)
        .agg(AveragePrice=("AveragePrice", "mean"))
        .sort_values("year")
    )
    year_fig = px.bar(
        by_year,
        x="year",
        y="AveragePrice",
        text_auto=".2f",
        title="Средняя цена по годам",
    )
    year_fig.update_layout(template="plotly_white", xaxis_title="Год", yaxis_title="Средняя цена, $")

    avg_price = f"{filtered['AveragePrice'].mean():.2f} $"
    total_volume = f"{filtered['Total Volume'].sum():,.0f}".replace(",", " ")
    records_count = f"{len(filtered)}"

    return price_fig, volume_fig, year_fig, avg_price, total_volume, records_count


if __name__ == "__main__":
    app.run(debug=True)
