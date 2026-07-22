import requests
import pandas as pd

def fetch_weather(lat, lon, forecast_days=3, timezone="Asia/Jakarta"):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation,wind_speed_10m,relative_humidity_2m",
        "forecast_days": forecast_days,
        "timezone": timezone,
    }

    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()

    hourly = r.json()["hourly"]

    df = pd.DataFrame({
        "time": pd.to_datetime(hourly["time"]),
        "temperature_2m": hourly["temperature_2m"],
        "precipitation": hourly["precipitation"],
        "wind_speed_10m": hourly["wind_speed_10m"],
        "relative_humidity_2m": hourly["relative_humidity_2m"],
    })

    return df

surabaya_weather = fetch_weather(
    lat=-7.2575,
    lon=112.7521,
    forecast_days=3
)

surabaya_weather.to_csv("surabaya_weather_hourly.csv", index=False)

print(surabaya_weather.head())
print("Saved: surabaya_weather_hourly.csv")