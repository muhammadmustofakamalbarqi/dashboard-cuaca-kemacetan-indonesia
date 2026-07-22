# -*- coding: utf-8 -*-
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta

# ── DATA WILAYAH: 38 PROVINSI (IBU KOTA) ──────────────────────────────────────
# (nama provinsi, latitude ibu kota, longitude ibu kota, baseline indeks kemacetan)
PROVINSI_INFO = [
    ("Aceh",                 5.5483,  95.3238, 0.30),
    ("Sumatera Utara",       3.5952,  98.6722, 0.42),
    ("Sumatera Barat",      -0.9471, 100.4172, 0.33),
    ("Riau",                 0.5071, 101.4478, 0.35),
    ("Kepulauan Riau",       0.9186, 104.4453, 0.30),
    ("Jambi",               -1.6101, 103.6131, 0.28),
    ("Sumatera Selatan",    -2.9761, 104.7754, 0.36),
    ("Bangka Belitung",     -2.1316, 106.1169, 0.22),
    ("Bengkulu",            -3.7928, 102.2608, 0.24),
    ("Lampung",             -5.4292, 105.2610, 0.34),
    ("DKI Jakarta",         -6.2088, 106.8456, 0.62),
    ("Jawa Barat",          -6.9175, 107.6191, 0.55),
    ("Banten",              -6.1200, 106.1500, 0.50),
    ("Jawa Tengah",         -6.9932, 110.4203, 0.44),
    ("DI Yogyakarta",       -7.7956, 110.3695, 0.40),
    ("Jawa Timur",          -7.2575, 112.7521, 0.48),
    ("Bali",                -8.6705, 115.2126, 0.46),
    ("Nusa Tenggara Barat", -8.5833, 116.1167, 0.26),
    ("Nusa Tenggara Timur",-10.1772, 123.6070, 0.20),
    ("Kalimantan Barat",    -0.0263, 109.3425, 0.27),
    ("Kalimantan Tengah",   -2.2090, 113.9213, 0.22),
    ("Kalimantan Selatan",  -3.3186, 114.5944, 0.30),
    ("Kalimantan Timur",    -0.5022, 117.1536, 0.33),
    ("Kalimantan Utara",     2.8371, 117.3667, 0.18),
    ("Sulawesi Utara",       1.4748, 124.8421, 0.28),
    ("Gorontalo",            0.5435, 123.0568, 0.18),
    ("Sulawesi Tengah",     -0.8917, 119.8707, 0.22),
    ("Sulawesi Barat",      -2.6786, 118.8877, 0.16),
    ("Sulawesi Selatan",    -5.1477, 119.4327, 0.38),
    ("Sulawesi Tenggara",   -3.9450, 122.4989, 0.20),
    ("Maluku",              -3.6954, 128.1814, 0.16),
    ("Maluku Utara",         0.7833, 127.3833, 0.14),
    ("Papua Barat",         -0.8615, 134.0620, 0.13),
    ("Papua Barat Daya",    -0.8762, 131.2558, 0.13),
    ("Papua",               -2.5337, 140.7181, 0.14),
    ("Papua Tengah",        -3.3667, 135.4833, 0.10),
    ("Papua Pegunungan",    -4.0847, 138.9450, 0.09),
    ("Papua Selatan",       -8.4667, 140.4000, 0.10),
]
PROVINSI    = {n: (lat, lon) for n, lat, lon, _ in PROVINSI_INFO}
BASE_MACET  = {n: b for n, _, _, b in PROVINSI_INFO}
NAMA_PROV   = list(PROVINSI.keys())

# ── AMBIL DATA CUACA SELURUH PROVINSI (1x panggilan API multi-lokasi) ────────
def fetch_weather_all():
    end   = datetime.today().strftime("%Y-%m-%d")
    start = (datetime.today() - timedelta(days=90)).strftime("%Y-%m-%d")
    try:
        lats = ",".join(str(v[0]) for v in PROVINSI.values())
        lons = ",".join(str(v[1]) for v in PROVINSI.values())
        r = requests.get(
            "https://archive-api.open-meteo.com/v1/archive",
            params={
                "latitude": lats, "longitude": lons,
                "start_date": start, "end_date": end,
                "hourly": "temperature_2m,precipitation,relative_humidity_2m",
                "timezone": "Asia/Jakarta",
            },
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict):
            data = [data]
        frames = {}
        for name, d in zip(NAMA_PROV, data):
            h = d["hourly"]
            frames[name] = pd.DataFrame({
                "time":       pd.to_datetime(h["time"]),
                "suhu":       h["temperature_2m"],
                "hujan":      h["precipitation"],
                "kelembaban": h["relative_humidity_2m"],
            })
        return frames
    except Exception:
        base_date = datetime.strptime(start, "%Y-%m-%d")
        times = [base_date + timedelta(hours=i) for i in range(90 * 24)]
        frames = {}
        for idx, name in enumerate(NAMA_PROV):
            lat, _ = PROVINSI[name]
            rng   = np.random.RandomState(1000 + idx)
            t_base = 27 - abs(lat) * 0.15
            suhu  = [round(t_base + 4 * np.sin((i % 24 - 6) * np.pi / 12) + rng.normal(0, 0.6), 1)
                     for i in range(90 * 24)]
            hujan = [round(max(0, rng.normal(3.5, 2.5) if 13 <= i % 24 <= 17
                     else rng.normal(0.1, 0.3)), 2) for i in range(90 * 24)]
            kelembaban = [round(70 + 15 * rng.random(), 1) for _ in range(90 * 24)]
            frames[name] = pd.DataFrame({"time": times, "suhu": suhu,
                                          "hujan": hujan, "kelembaban": kelembaban})
        return frames

# ── DATA HARIAN PER PROVINSI, NASIONAL & KEMACETAN ────────────────────────────
print("Memuat data seluruh provinsi Indonesia...")
weather_frames = fetch_weather_all()

daily_list = []
for name, df in weather_frames.items():
    d = df.resample("D", on="time").agg(
        suhu=("suhu", "mean"), hujan=("hujan", "sum"), kelembaban=("kelembaban", "mean")
    ).reset_index()
    d["provinsi"] = name
    daily_list.append(d)
daily_all = pd.concat(daily_list, ignore_index=True)

nasional = daily_all.groupby("time").agg(
    suhu=("suhu", "mean"), hujan=("hujan", "mean"), kelembaban=("kelembaban", "mean")
).reset_index()
nasional["tanggal"] = nasional["time"].dt.strftime("%d %b")

rng_macet = np.random.RandomState(99)
rows = []
for _, row in daily_all.iterrows():
    base = BASE_MACET[row["provinsi"]]
    ci = round(max(0, min(1.5, base + row["hujan"] * 0.02 + rng_macet.normal(0, 0.05))), 3)
    rows.append({"provinsi": row["provinsi"], "date": row["time"], "kemacetan": ci,
                 "hujan": row["hujan"], "bulan": row["time"].strftime("%b %Y"),
                 "bulan_key": row["time"].strftime("%Y-%m")})
traffic = pd.DataFrame(rows)

stats_all = traffic.groupby("provinsi")["kemacetan"].mean().reset_index()
stats_all["lat"] = stats_all["provinsi"].map(lambda n: PROVINSI[n][0])
stats_all["lon"] = stats_all["provinsi"].map(lambda n: PROVINSI[n][1])

# ── RINGKASAN KPI ─────────────────────────────────────────────────────────────
avg_suhu      = nasional["suhu"].mean()
avg_hujan     = nasional["hujan"].mean()
avg_macet     = traffic["kemacetan"].mean()
top_prov      = stats_all.sort_values("kemacetan", ascending=False).iloc[0]

DEFAULT_SEL = ["DKI Jakarta", "Jawa Barat", "Jawa Timur", "Sumatera Utara", "Bali"]

# ── APP ───────────────────────────────────────────────────────────────────────
app = dash.Dash(__name__, title="Cuaca & Kemacetan Indonesia")

app.layout = html.Div(style={"fontFamily": "Arial, sans-serif", "maxWidth": "1100px",
                              "margin": "0 auto", "padding": "20px"}, children=[

    html.H2("Dashboard Cuaca & Kemacetan Seluruh Indonesia (90 Hari Terakhir)",
            style={"textAlign": "center", "color": "#2c3e50"}),
    html.P(f"38 Provinsi | Data per {datetime.today().strftime('%d %B %Y')}",
           style={"textAlign": "center", "color": "gray", "marginTop": "-10px"}),

    html.Hr(),

    # KPI
    html.Div(style={"display": "flex", "gap": "16px", "marginBottom": "24px"}, children=[
        html.Div(style={"flex": "1", "backgroundColor": "#eaf4fb", "borderRadius": "8px",
                        "padding": "16px", "textAlign": "center"}, children=[
            html.P("Suhu Rata-rata Nasional", style={"margin": "0", "color": "gray", "fontSize": "13px"}),
            html.H3(f"{avg_suhu:.1f} °C", style={"margin": "4px 0", "color": "#2980b9"}),
        ]),
        html.Div(style={"flex": "1", "backgroundColor": "#eafaf1", "borderRadius": "8px",
                        "padding": "16px", "textAlign": "center"}, children=[
            html.P("Curah Hujan Rata-rata", style={"margin": "0", "color": "gray", "fontSize": "13px"}),
            html.H3(f"{avg_hujan:.1f} mm/hari", style={"margin": "4px 0", "color": "#27ae60"}),
        ]),
        html.Div(style={"flex": "1", "backgroundColor": "#fef9e7", "borderRadius": "8px",
                        "padding": "16px", "textAlign": "center"}, children=[
            html.P("Rata-rata Kemacetan Nasional", style={"margin": "0", "color": "gray", "fontSize": "13px"}),
            html.H3(f"{avg_macet:.3f}", style={"margin": "4px 0", "color": "#f39c12"}),
        ]),
        html.Div(style={"flex": "1", "backgroundColor": "#fdedec", "borderRadius": "8px",
                        "padding": "16px", "textAlign": "center"}, children=[
            html.P("Provinsi Kemacetan Tertinggi", style={"margin": "0", "color": "gray", "fontSize": "13px"}),
            html.H3(top_prov["provinsi"], style={"margin": "4px 0", "color": "#e74c3c", "fontSize": "18px"}),
        ]),
    ]),

    # Filter provinsi
    html.Div(style={"backgroundColor": "#f8f9fa", "borderRadius": "8px",
                    "padding": "14px", "marginBottom": "20px"}, children=[
        html.B("Pilih Provinsi (untuk grafik detail): "),
        dcc.Dropdown(
            id="filter-provinsi",
            options=[{"label": n, "value": n} for n in NAMA_PROV],
            value=DEFAULT_SEL,
            multi=True,
            style={"marginTop": "8px", "fontSize": "14px"},
        ),
    ]),

    # Baris 1: Suhu & Hujan nasional
    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px",
                    "marginBottom": "16px"}, children=[
        html.Div(style={"backgroundColor": "#fff", "border": "1px solid #ddd",
                        "borderRadius": "8px", "padding": "16px"}, children=[
            html.H4("Suhu Harian Nasional (°C)", style={"margin": "0 0 8px 0", "color": "#2c3e50"}),
            dcc.Graph(id="chart-suhu", config={"displayModeBar": False}, style={"height": "220px"}),
        ]),
        html.Div(style={"backgroundColor": "#fff", "border": "1px solid #ddd",
                        "borderRadius": "8px", "padding": "16px"}, children=[
            html.H4("Curah Hujan Harian Nasional (mm)", style={"margin": "0 0 8px 0", "color": "#2c3e50"}),
            dcc.Graph(id="chart-hujan", config={"displayModeBar": False}, style={"height": "220px"}),
        ]),
    ]),

    # Baris 2: Peta sebaran kemacetan seluruh Indonesia
    html.Div(style={"backgroundColor": "#fff", "border": "1px solid #ddd", "borderRadius": "8px",
                    "padding": "16px", "marginBottom": "16px"}, children=[
        html.H4("Peta Sebaran Kemacetan Seluruh Indonesia", style={"margin": "0 0 8px 0", "color": "#2c3e50"}),
        dcc.Graph(id="chart-map", config={"displayModeBar": False}, style={"height": "430px"}),
    ]),

    # Baris 3: Kemacetan & Kategori Hujan
    html.Div(style={"display": "grid", "gridTemplateColumns": "3fr 2fr", "gap": "16px",
                    "marginBottom": "16px"}, children=[
        html.Div(style={"backgroundColor": "#fff", "border": "1px solid #ddd",
                        "borderRadius": "8px", "padding": "16px"}, children=[
            html.H4("Kemacetan per Provinsi per Bulan", style={"margin": "0 0 8px 0", "color": "#2c3e50"}),
            dcc.Graph(id="chart-macet", config={"displayModeBar": False}, style={"height": "250px"}),
        ]),
        html.Div(style={"backgroundColor": "#fff", "border": "1px solid #ddd",
                        "borderRadius": "8px", "padding": "16px"}, children=[
            html.H4("Kemacetan per Kategori Hujan", style={"margin": "0 0 8px 0", "color": "#2c3e50"}),
            dcc.Graph(id="chart-kategori", config={"displayModeBar": False}, style={"height": "250px"}),
        ]),
    ]),

    # Baris 4: Kelembaban nasional
    html.Div(style={"backgroundColor": "#fff", "border": "1px solid #ddd", "borderRadius": "8px",
                    "padding": "16px", "marginBottom": "16px"}, children=[
        html.H4("Kelembaban Udara Nasional (%)", style={"margin": "0 0 8px 0", "color": "#2c3e50"}),
        dcc.Graph(id="chart-kelembaban", config={"displayModeBar": False}, style={"height": "230px"}),
    ]),

    # Baris 5: Rata-rata kemacetan seluruh provinsi
    html.Div(style={"backgroundColor": "#fff", "border": "1px solid #ddd", "borderRadius": "8px",
                    "padding": "16px", "marginBottom": "16px"}, children=[
        html.H4("Rata-rata Kemacetan per Provinsi (38 Provinsi)", style={"margin": "0 0 8px 0", "color": "#2c3e50"}),
        dcc.Graph(id="chart-provinsi", config={"displayModeBar": False}, style={"height": "750px"}),
    ]),

    html.Hr(),
    html.P("Sumber: Open-Meteo Archive API (per ibu kota provinsi) | Data kemacetan simulasi | "
           "Modul 4 — Sains Data & Visualisasi Data",
           style={"textAlign": "center", "color": "gray", "fontSize": "12px"}),
])


# ── CALLBACK ──────────────────────────────────────────────────────────────────
@app.callback(
    [Output("chart-suhu",       "figure"),
     Output("chart-hujan",      "figure"),
     Output("chart-map",        "figure"),
     Output("chart-macet",      "figure"),
     Output("chart-kategori",   "figure"),
     Output("chart-kelembaban", "figure"),
     Output("chart-provinsi",   "figure")],
    Input("filter-provinsi", "value"),
)
def update(selected):
    sel      = selected or DEFAULT_SEL
    filtered = traffic[traffic["provinsi"].isin(sel)]

    WARNA = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6",
             "#1abc9c", "#e67e22", "#34495e", "#e91e63", "#16a085"]

    # 1. Suhu harian nasional - line chart
    fig_suhu = go.Figure(go.Scatter(
        x=nasional["time"], y=nasional["suhu"], mode="lines",
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

    # 2. Curah hujan harian nasional - bar chart
    warna_hujan = ["#e74c3c" if v > 10 else "#5dade2" for v in nasional["hujan"]]
    fig_hujan = go.Figure(go.Bar(
        x=nasional["time"], y=nasional["hujan"],
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

    # 3. Peta sebaran kemacetan - scattergeo seluruh Indonesia
    size  = [26 if p in sel else 13 for p in stats_all["provinsi"]]
    color = ["#e74c3c" if p in sel else "#3498db" for p in stats_all["provinsi"]]
    fig_map = go.Figure(go.Scattergeo(
        lon=stats_all["lon"], lat=stats_all["lat"],
        text=stats_all["provinsi"], customdata=stats_all["kemacetan"],
        mode="markers",
        marker=dict(size=size, color=color, line=dict(width=1, color="white"), opacity=0.85),
        hovertemplate="<b>%{text}</b><br>Kemacetan: <b>%{customdata:.3f}</b><extra></extra>",
    ))
    fig_map.update_geos(
        resolution=50, showcountries=True, countrycolor="#bbbbbb",
        showland=True, landcolor="#f4f4f4", showocean=True, oceancolor="#eaf4fb",
        showlakes=False, lataxis_range=[-11, 7], lonaxis_range=[94, 142],
        projection_type="mercator",
    )
    fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=430, paper_bgcolor="white")

    # 4. Kemacetan per provinsi per bulan - grouped bar
    fig_macet = go.Figure()
    monthly = filtered.groupby(["bulan_key", "bulan", "provinsi"])["kemacetan"].mean().reset_index()
    for i, prov in enumerate(sel):
        d = monthly[monthly["provinsi"] == prov].sort_values("bulan_key")
        fig_macet.add_trace(go.Bar(
            x=d["bulan"], y=d["kemacetan"], name=prov,
            marker_color=WARNA[i % len(WARNA)],
            hovertemplate=f"<b>{prov}</b><br>%{{x}}<br>Index: <b>%{{y:.3f}}</b><extra></extra>",
        ))
    fig_macet.update_layout(
        barmode="group", margin=dict(l=50, r=10, t=10, b=40), height=230,
        yaxis=dict(title="Congestion Index"), legend=dict(orientation="h", y=1.15),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    fig_macet.update_yaxes(gridcolor="#eeeeee")
    fig_macet.update_xaxes(showgrid=False)

    # 5. Kemacetan per kategori hujan
    def kategori(mm):
        if mm < 5:    return "Tidak Hujan\n(< 5 mm)"
        elif mm < 15: return "Hujan Ringan\n(5–15 mm)"
        else:         return "Hujan Lebat\n(> 15 mm)"

    urutan = ["Tidak Hujan\n(< 5 mm)", "Hujan Ringan\n(5–15 mm)", "Hujan Lebat\n(> 15 mm)"]
    fig_kat = go.Figure()
    for i, prov in enumerate(sel):
        d = filtered[filtered["provinsi"] == prov].copy()
        d["kat"] = d["hujan"].apply(kategori)
        avg = d.groupby("kat")["kemacetan"].mean().reindex(urutan).reset_index()
        fig_kat.add_trace(go.Bar(
            x=avg["kat"], y=avg["kemacetan"], name=prov,
            marker_color=WARNA[i % len(WARNA)],
            hovertemplate=f"<b>{prov}</b><br>%{{x}}<br>Index: <b>%{{y:.3f}}</b><extra></extra>",
        ))
    fig_kat.update_layout(
        barmode="group", margin=dict(l=50, r=10, t=10, b=60), height=230,
        yaxis=dict(title="Congestion Index"), legend=dict(orientation="h", y=1.15),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    fig_kat.update_yaxes(gridcolor="#eeeeee")
    fig_kat.update_xaxes(showgrid=False)

    # 6. Kelembaban harian nasional - line chart
    fig_kel = go.Figure(go.Scatter(
        x=nasional["time"], y=nasional["kelembaban"], mode="lines",
        line=dict(color="#2ecc71", width=2),
        hovertemplate="%{x|%d %b}<br>Kelembaban: <b>%{y:.1f}%</b><extra></extra>",
    ))
    fig_kel.update_layout(
        margin=dict(l=40, r=10, t=10, b=30), height=200,
        xaxis=dict(tickformat="%d %b", nticks=10),
        yaxis=dict(title="%"), showlegend=False,
        plot_bgcolor="white", paper_bgcolor="white",
    )
    fig_kel.update_xaxes(showgrid=False)
    fig_kel.update_yaxes(gridcolor="#eeeeee")

    # 7. Rata-rata kemacetan per provinsi (38 provinsi) - horizontal bar
    stats_sorted = stats_all.sort_values("kemacetan", ascending=True)
    warna_bar = ["#e74c3c" if p in sel else "#bdc3c7" for p in stats_sorted["provinsi"]]
    fig_prov = go.Figure(go.Bar(
        x=stats_sorted["kemacetan"], y=stats_sorted["provinsi"],
        orientation="h", marker_color=warna_bar,
        hovertemplate="<b>%{y}</b><br>Rata-rata: <b>%{x:.3f}</b><extra></extra>",
    ))
    fig_prov.update_layout(
        margin=dict(l=160, r=10, t=10, b=40), height=750, showlegend=False,
        xaxis=dict(title="Congestion Index"),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    fig_prov.update_xaxes(gridcolor="#eeeeee")
    fig_prov.update_yaxes(showgrid=False)

    return fig_suhu, fig_hujan, fig_map, fig_macet, fig_kat, fig_kel, fig_prov


if __name__ == "__main__":
    print("Buka: http://127.0.0.1:8060")
    app.run(debug=True, port=8060)
