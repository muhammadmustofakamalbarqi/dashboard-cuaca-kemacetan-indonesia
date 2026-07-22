import os
import math
import requests
from io import BytesIO
from PIL import Image
import pandas as pd
from datetime import datetime

def latlon_to_tile(lat, lon, z):
    lat_rad = math.radians(lat)
    n = 2.0 ** z

    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)

    return x, y

def fetch_google_traffic_tile(z, x, y):
    url = f"https://mt1.google.com/vt/lyrs=h,traffic&x={x}&y={y}&z={z}"

    headers = {
        "User-Agent": "student-project/1.0"
    }

    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()

    return Image.open(BytesIO(r.content)).convert("RGB")

def traffic_congestion_score(img):
    pixels = img.getdata()

    red = orange = green = darkred = 0

    for (r, g, b) in pixels:

        if abs(r - g) < 10 and abs(g - b) < 10:
            continue

        if r > 180 and g < 80 and b < 80:
            red += 1

        elif r > 150 and 80 < g < 160 and b < 80:
            orange += 1

        elif g > 160 and r < 120 and b < 120:
            green += 1

        elif r > 120 and g < 40 and b < 40:
            darkred += 1

    total = red + orange + green + darkred

    if total == 0:
        return {
            "green_px": 0,
            "orange_px": 0,
            "red_px": 0,
            "darkred_px": 0,
            "congestion_index": 0.0
        }

    congestion_index = (
        0.0 * green +
        0.5 * orange +
        1.0 * red +
        1.2 * darkred
    ) / total

    return {
        "green_px": green,
        "orange_px": orange,
        "red_px": red,
        "darkred_px": darkred,
        "congestion_index": float(congestion_index),
    }

def collect_city_traffic_samples(city, center_lat, center_lon, z=14, radius_tiles=1):

    cx, cy = latlon_to_tile(center_lat, center_lon, z)

    out_dir = f"{city}_traffic_tiles"
    os.makedirs(out_dir, exist_ok=True)

    records = []

    for dx in range(-radius_tiles, radius_tiles + 1):

        for dy in range(-radius_tiles, radius_tiles + 1):

            x, y = cx + dx, cy + dy

            try:
                img = fetch_google_traffic_tile(z, x, y)

                tile_file = f"{out_dir}/z{z}_x{x}_y{y}.png"
                img.save(tile_file)

                score = traffic_congestion_score(img)

                records.append({
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "city": city,
                    "z": z,
                    "x": x,
                    "y": y,
                    "tile_file": tile_file,
                    **score
                })

                print(
                    "OK",
                    x,
                    y,
                    "congestion_index =",
                    score["congestion_index"]
                )

            except Exception as e:

                print("FAIL", x, y, str(e))

                records.append({
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "city": city,
                    "z": z,
                    "x": x,
                    "y": y,
                    "tile_file": None,
                    "green_px": None,
                    "orange_px": None,
                    "red_px": None,
                    "darkred_px": None,
                    "congestion_index": None,
                    "error": str(e)
                })

    return pd.DataFrame(records)

# Run for Surabaya — Tunjungan / City Center
surabaya_traffic = collect_city_traffic_samples(
    city="surabaya",
    center_lat=-7.2575,
    center_lon=112.7521,
    z=14,
    radius_tiles=1
)

surabaya_traffic.to_csv(
    "surabaya_traffic_tiles_proxy.csv",
    index=False
)

print("Saved: surabaya_traffic_tiles_proxy.csv")

print(surabaya_traffic.head())