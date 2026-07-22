import pandas as pd

weather = pd.read_csv(
    "surabaya_weather_hourly.csv",
    parse_dates=["time"]
)

traffic = pd.read_csv(
    "surabaya_traffic_tiles_proxy.csv",
    parse_dates=["timestamp"]
)

# Round traffic timestamp down to nearest hour
traffic["hour"] = traffic["timestamp"].dt.floor("h")

# Merge on hour
combined = traffic.merge(
    weather,
    left_on="hour",
    right_on="time",
    how="left"
)

combined.to_csv(
    "surabaya_traffic_weather_combined.csv",
    index=False
)

print("Saved: surabaya_traffic_weather_combined.csv")

print(
    combined[
        [
            "timestamp",
            "congestion_index",
            "temperature_2m",
            "precipitation"
        ]
    ].head()
)