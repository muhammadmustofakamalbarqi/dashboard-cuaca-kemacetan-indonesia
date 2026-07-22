# Dashboard Cuaca & Kemacetan Indonesia

Dashboard interaktif berbasis [Dash](https://dash.plotly.com/) yang memvisualisasikan hubungan antara cuaca (suhu, curah hujan, kelembaban) dan indeks kemacetan lalu lintas. Dibuat untuk tugas Modul 4 mata kuliah Sains Data & Visualisasi Data.

Repo ini berisi dua dashboard:

| Folder | Cakupan | Port |
| --- | --- | --- |
| [`web.py`](web.py) | Kota Surabaya (9 area/kecamatan) | `8050` |
| [`web_indonesia/web.py`](web_indonesia/web.py) | Seluruh 38 provinsi Indonesia + peta sebaran | `8060` |

## Fitur

- Data cuaca real-time dari [Open-Meteo Archive API](https://open-meteo.com/) (90 hari terakhir), dengan fallback ke data simulasi jika API tidak dapat diakses.
- Indeks kemacetan simulatif per wilayah, dipengaruhi oleh curah hujan.
- Filter interaktif per area/provinsi.
- Versi Indonesia menampilkan peta sebaran kemacetan (scattergeo) untuk seluruh provinsi.

## Instalasi

```bash
pip install dash plotly pandas numpy requests
```

## Menjalankan

Dashboard Surabaya:

```bash
python web.py
# buka http://127.0.0.1:8050
```

Dashboard seluruh Indonesia:

```bash
cd web_indonesia
python web.py
# buka http://127.0.0.1:8060
```

Kedua dashboard bisa dijalankan bersamaan karena menggunakan port yang berbeda.

## Struktur Data & Skrip Pendukung

- `cuacaSby.py` — mengambil data cuaca Surabaya dari Open-Meteo dan menyimpannya ke `surabaya_weather_hourly.csv`.
- `lalulintas.py` — mengambil/mengolah data proxy kemacetan lalu lintas dari tile peta (`surabaya_traffic_tiles/`) menjadi `surabaya_traffic_tiles_proxy.csv`.
- `pengabungan.py` — menggabungkan data cuaca dan kemacetan per jam menjadi `surabaya_traffic_weather_combined.csv`.
- File `.csv` lainnya adalah hasil ekstraksi/gabungan data cuaca & kemacetan untuk periode 3 bulan.

## Sumber Data

- Cuaca: [Open-Meteo Archive API](https://open-meteo.com/)
- Kemacetan: data simulasi berbasis pola curah hujan (bukan data lalu lintas real-time resmi)
