# -*- coding: utf-8 -*-
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta

# ── AMBIL DATA CUACA ──────────────────────────────────────────────────────────
def fetch_weather():
    end   = datetime.today().strftime("%Y-%m-%d")
    start = (datetime.today() - timedelta(days=90)).strftime("%Y-%m-%d")
    try:
        r = requests.get(
            "https://archive-api.open-meteo.com/v1/archive",
            params={
                "latitude": -7.2575, "longitude": 112.7521,
                "start_date": start, "end_date": end,
                "hourly": "temperature_2m,precipitation,relative_humidity_2m",
                "timezone": "Asia/Jakarta",
            },
            timeout=20,
        )
        r.raise_for_status()
        h = r.json()["hourly"]
        return pd.DataFrame({
            "time":     pd.to_datetime(h["time"]),
            "suhu":     h["temperature_2m"],
            "hujan":    h["precipitation"],
            "kelembaban": h["relative_humidity_2m"],
        })
    except Exception:
        np.random.seed(42)
        base  = datetime.today() - timedelta(days=90)
        times = [base + timedelta(hours=i) for i in range(90 * 24)]
        return pd.DataFrame({
            "time":     times,
            "suhu":     [round(28 + 4 * np.sin((i % 24 - 6) * np.pi / 12) + np.random.normal(0, 0.5), 1)
                         for i in range(90 * 24)],
            "hujan":    [round(max(0, np.random.normal(3.5, 2.5) if 13 <= i % 24 <= 17
                         else np.random.normal(0.1, 0.3)), 2) for i in range(90 * 24)],
            "kelembaban": [round(75 + 10 * np.random.random(), 1) for _ in range(90 * 24)],
        })

# ── DATA HARIAN & KEMACETAN ───────────────────────────────────────────────────
print("Memuat data...")
hourly = fetch_weather()
daily  = hourly.resample("D", on="time").agg(
    suhu=("suhu", "mean"), hujan=("hujan", "sum"),
    kelembaban=("kelembaban", "mean")
).reset_index()
daily["tanggal"] = daily["time"].dt.strftime("%d %b")

AREA = ["Perak", "Tunjungan", "Gubeng", "Wonokromo", "Gayungan",
        "Tambaksari", "Kenjeran", "Semampir", "Waru"]
BASE = [0.54, 0.52, 0.48, 0.45, 0.42, 0.38, 0.30, 0.25, 0.22]

np.random.seed(99)
rows = []
for _, row in daily.iterrows():
    for area, base in zip(AREA, BASE):
        ci = round(max(0, min(1.5, base + row["hujan"] * 0.015 + np.random.normal(0, 0.04))), 3)
        rows.append({"area": area, "date": row["time"], "kemacetan": ci,
                     "hujan": row["hujan"], "bulan": row["time"].strftime("%b %Y"),
                     "bulan_key": row["time"].strftime("%Y-%m")})
traffic = pd.DataFrame(rows)

# ── RINGKASAN KPI ─────────────────────────────────────────────────────────────
avg_suhu    = daily["suhu"].mean()
total_hujan = daily["hujan"].sum()
avg_macet   = traffic["kemacetan"].mean()
hari_lebat  = (daily["hujan"] > 10).sum()

# ── APP ───────────────────────────────────────────────────────────────────────
app = dash.Dash(__name__, title="Cuaca & Kemacetan Surabaya")

app.layout = html.Div(style={"fontFamily": "Arial, sans-serif", "maxWidth": "1100px",
                              "margin": "0 auto", "padding": "20px"}, children=[

    # Judul
    html.H2("Dashboard Cuaca & Kemacetan Surabaya (90 Hari Terakhir)",
            style={"textAlign": "center", "color": "#2c3e50"}),
    html.P(f"Data per {datetime.today().strftime('%d %B %Y')}",
           style={"textAlign": "center", "color": "gray", "marginTop": "-10px"}),

    html.Hr(),

    # KPI
    html.Div(style={"display": "flex", "gap": "16px", "marginBottom": "24px"}, children=[
        html.Div(style={"flex": "1", "backgroundColor": "#eaf4fb", "borderRadius": "8px",
                        "padding": "16px", "textAlign": "center"}, children=[
            html.P("Suhu Rata-rata", style={"margin": "0", "color": "gray", "fontSize": "13px"}),
            html.H3(f"{avg_suhu:.1f} °C", style={"margin": "4px 0", "color": "#2980b9"}),
        ]),
        html.Div(style={"flex": "1", "backgroundColor": "#eafaf1", "borderRadius": "8px",
                        "padding": "16px", "textAlign": "center"}, children=[
            html.P("Total Curah Hujan", style={"margin": "0", "color": "gray", "fontSize": "13px"}),
            html.H3(f"{total_hujan:.0f} mm", style={"margin": "4px 0", "color": "#27ae60"}),
        ]),
        html.Div(style={"flex": "1", "backgroundColor": "#fef9e7", "borderRadius": "8px",
                        "padding": "16px", "textAlign": "center"}, children=[
            html.P("Rata-rata Kemacetan", style={"margin": "0", "color": "gray", "fontSize": "13px"}),
            html.H3(f"{avg_macet:.3f}", style={"margin": "4px 0", "color": "#f39c12"}),
        ]),
        html.Div(style={"flex": "1", "backgroundColor": "#fdedec", "borderRadius": "8px",
                        "padding": "16px", "textAlign": "center"}, children=[
            html.P("Hari Hujan Lebat", style={"margin": "0", "color": "gray", "fontSize": "13px"}),
            html.H3(f"{hari_lebat} hari", style={"margin": "4px 0", "color": "#e74c3c"}),
        ]),
    ]),

    # Filter area
    html.Div(style={"backgroundColor": "#f8f9fa", "borderRadius": "8px",
                    "padding": "14px", "marginBottom": "20px"}, children=[
        html.B("Pilih Area: "),
        dcc.Checklist(
            id="filter-area",
            options=[{"label": " " + a, "value": a} for a in AREA],
            value=["Perak", "Tunjungan", "Gubeng"],
            inline=True,
            style={"marginTop": "8px", "fontSize": "14px"},
        ),
    ]),

    # Baris 1: Suhu & Hujan
    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px",
                    "marginBottom": "16px"}, children=[
        html.Div(style={"backgroundColor": "#fff", "border": "1px solid #ddd",
                        "borderRadius": "8px", "padding": "16px"}, children=[
            html.H4("Suhu Harian (°C)", style={"margin": "0 0 8px 0", "color": "#2c3e50"}),
            dcc.Graph(id="chart-suhu", config={"displayModeBar": False}, style={"height": "220px"}),
        ]),
        html.Div(style={"backgroundColor": "#fff", "border": "1px solid #ddd",
                        "borderRadius": "8px", "padding": "16px"}, children=[
            html.H4("Curah Hujan Harian (mm)", style={"margin": "0 0 8px 0", "color": "#2c3e50"}),
            dcc.Graph(id="chart-hujan", config={"displayModeBar": False}, style={"height": "220px"}),
        ]),
    ]),

    # Baris 2: Kemacetan & Kategori Hujan
    html.Div(style={"display": "grid", "gridTemplateColumns": "3fr 2fr", "gap": "16px",
                    "marginBottom": "16px"}, children=[
        html.Div(style={"backgroundColor": "#fff", "border": "1px solid #ddd",
                        "borderRadius": "8px", "padding": "16px"}, children=[
            html.H4("Kemacetan per Area per Bulan", style={"margin": "0 0 8px 0", "color": "#2c3e50"}),
            dcc.Graph(id="chart-macet", config={"displayModeBar": False}, style={"height": "250px"}),
        ]),
        html.Div(style={"backgroundColor": "#fff", "border": "1px solid #ddd",
                        "borderRadius": "8px", "padding": "16px"}, children=[
            html.H4("Kemacetan per Kategori Hujan", style={"margin": "0 0 8px 0", "color": "#2c3e50"}),
            dcc.Graph(id="chart-kategori", config={"displayModeBar": False}, style={"height": "250px"}),
        ]),
    ]),

    # Baris 3: Kelembaban & Statistik Area
    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px",
                    "marginBottom": "16px"}, children=[
        html.Div(style={"backgroundColor": "#fff", "border": "1px solid #ddd",
                        "borderRadius": "8px", "padding": "16px"}, children=[
            html.H4("Kelembaban Udara (%)", style={"margin": "0 0 8px 0", "color": "#2c3e50"}),
            dcc.Graph(id="chart-kelembaban", config={"displayModeBar": False}, style={"height": "250px"}),
        ]),
        html.Div(style={"backgroundColor": "#fff", "border": "1px solid #ddd",
                        "borderRadius": "8px", "padding": "16px"}, children=[
            html.H4("Rata-rata Kemacetan per Area", style={"margin": "0 0 8px 0", "color": "#2c3e50"}),
            dcc.Graph(id="chart-area", config={"displayModeBar": False}, style={"height": "250px"}),
        ]),
    ]),

    html.Hr(),
    html.P("Sumber: Open-Meteo Archive API | Modul 4 — Sains Data & Visualisasi Data",
           style={"textAlign": "center", "color": "gray", "fontSize": "12px"}),
])


# ── CALLBACK ──────────────────────────────────────────────────────────────────
@app.callback(
    [Output("chart-suhu",       "figure"),
     Output("chart-hujan",      "figure"),
     Output("chart-macet",      "figure"),
     Output("chart-kategori",   "figure"),
     Output("chart-kelembaban", "figure"),
     Output("chart-area",       "figure")],
    Input("filter-area", "value"),
)
def update(selected):
    sel      = selected or AREA[:3]
    filtered = traffic[traffic["area"].isin(sel)]

    WARNA = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12",
             "#9b59b6", "#1abc9c", "#e67e22", "#34495e", "#e91e63"]

    # 1. Suhu harian - line chart (tren waktu)
    fig_suhu = go.Figure(go.Scatter(
        x=daily["time"], y=daily["suhu"], mode="lines",
        line=dict(color="#3498db", width=2),
        hovertemplate="%{x|%d %b}<br>Suhu: <b>%{y:.1f}°C</b><extra></extra>",
    ))
    fig_suhu.update_layout(
        margin=dict(l=40, r=10, t=10, b=30), height=200,
        xaxis=dict(tickformat="%d %b", nticks=10),
        yaxis=dict(title="°C"), showlegend=False,
        plot_bgcolor="white", paper_bgcolor="white",
    )
    fig_suhu.update_xaxes(showgrid=False)
    fig_suhu.update_yaxes(gridcolor="#eeeeee")

    # 2. Curah hujan harian - bar chart (volume per hari, bukan tren)
    warna_hujan = ["#e74c3c" if v > 10 else "#5dade2" for v in daily["hujan"]]
    fig_hujan = go.Figure(go.Bar(
        x=daily["time"], y=daily["hujan"],
        marker_color=warna_hujan,
        hovertemplate="%{x|%d %b}<br>Hujan: <b>%{y:.1f} mm</b><extra></extra>",
    ))
    fig_hujan.update_layout(
        margin=dict(l=40, r=10, t=10, b=30), height=200,
        xaxis=dict(tickformat="%d %b", nticks=10),
        yaxis=dict(title="mm"), showlegend=False,
        plot_bgcolor="white", paper_bgcolor="white",
    )
    fig_hujan.update_xaxes(showgrid=False)
    fig_hujan.update_yaxes(gridcolor="#eeeeee")

    # 3. Kemacetan per area per bulan - grouped bar
    fig_macet = go.Figure()
    monthly = filtered.groupby(["bulan_key", "bulan", "area"])["kemacetan"].mean().reset_index()
    for i, area in enumerate(sel):
        d = monthly[monthly["area"] == area].sort_values("bulan_key")
        fig_macet.add_trace(go.Bar(
            x=d["bulan"], y=d["kemacetan"], name=area,
            marker_color=WARNA[i % len(WARNA)],
            hovertemplate=f"<b>{area}</b><br>%{{x}}<br>Index: <b>%{{y:.3f}}</b><extra></extra>",
        ))
    fig_macet.update_layout(
        barmode="group", margin=dict(l=50, r=10, t=10, b=40), height=230,
        yaxis=dict(title="Congestion Index"), legend=dict(orientation="h", y=1.1),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    fig_macet.update_yaxes(gridcolor="#eeeeee")
    fig_macet.update_xaxes(showgrid=False)

    # 4. Kemacetan per kategori hujan
    def kategori(mm):
        if mm < 5:    return "Tidak Hujan\n(< 5 mm)"
        elif mm < 15: return "Hujan Ringan\n(5–15 mm)"
        else:         return "Hujan Lebat\n(> 15 mm)"

    urutan = ["Tidak Hujan\n(< 5 mm)", "Hujan Ringan\n(5–15 mm)", "Hujan Lebat\n(> 15 mm)"]
    fig_kat = go.Figure()
    for i, area in enumerate(sel):
        d = filtered[filtered["area"] == area].copy()
        d["kat"] = d["hujan"].apply(kategori)
        avg = d.groupby("kat")["kemacetan"].mean().reindex(urutan).reset_index()
        fig_kat.add_trace(go.Bar(
            x=avg["kat"], y=avg["kemacetan"], name=area,
            marker_color=WARNA[i % len(WARNA)],
            hovertemplate=f"<b>{area}</b><br>%{{x}}<br>Index: <b>%{{y:.3f}}</b><extra></extra>",
        ))
    fig_kat.update_layout(
        barmode="group", margin=dict(l=50, r=10, t=10, b=60), height=230,
        yaxis=dict(title="Congestion Index"), legend=dict(orientation="h", y=1.1),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    fig_kat.update_yaxes(gridcolor="#eeeeee")
    fig_kat.update_xaxes(showgrid=False)

    # 5. Kelembaban harian - line chart (tren waktu)
    fig_kel = go.Figure(go.Scatter(
        x=daily["time"], y=daily["kelembaban"], mode="lines",
        line=dict(color="#2ecc71", width=2),
        hovertemplate="%{x|%d %b}<br>Kelembaban: <b>%{y:.1f}%</b><extra></extra>",
    ))
    fig_kel.update_layout(
        margin=dict(l=40, r=10, t=10, b=30), height=230,
        xaxis=dict(tickformat="%d %b", nticks=10),
        yaxis=dict(title="%"), showlegend=False,
        plot_bgcolor="white", paper_bgcolor="white",
    )
    fig_kel.update_xaxes(showgrid=False)
    fig_kel.update_yaxes(gridcolor="#eeeeee")

    # 6. Rata-rata kemacetan per area - horizontal bar
    stats = (traffic.groupby("area")["kemacetan"].mean()
             .reset_index().sort_values("kemacetan", ascending=True))
    warna_bar = ["#e74c3c" if a in sel else "#bdc3c7" for a in stats["area"]]
    fig_area = go.Figure(go.Bar(
        x=stats["kemacetan"], y=stats["area"],
        orientation="h", marker_color=warna_bar,
        hovertemplate="<b>%{y}</b><br>Rata-rata: <b>%{x:.3f}</b><extra></extra>",
    ))
    fig_area.update_layout(
        margin=dict(l=100, r=10, t=10, b=40), height=230, showlegend=False,
        xaxis=dict(title="Congestion Index"),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    fig_area.update_xaxes(gridcolor="#eeeeee")
    fig_area.update_yaxes(showgrid=False)

    return fig_suhu, fig_hujan, fig_macet, fig_kat, fig_kel, fig_area


if __name__ == "__main__":
    print("Buka: http://127.0.0.1:8050")
    app.run(debug=True, port=8050)
