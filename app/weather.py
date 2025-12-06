import requests
from datetime import datetime, timedelta, timezone
from typing import List
from . import db


def fetch_past_48h(lat: float, lon: float) -> dict:
    """
    Call Open-Meteo MeteoSwiss endpoint to get hourly temperature_2m and relative_humidity_2m
    for the past 48 hours.
    """
    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(hours=48)
    start_date = start_dt.date().isoformat()
    end_date = end_dt.date().isoformat()

    # Use the standard forecast endpoint and correct hourly parameter name
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        # note: parameter name is 'relativehumidity_2m' (no underscore)
        "hourly": "temperature_2m,relativehumidity_2m",
        "start_date": start_date,
        "end_date": end_date,
        "timezone": "UTC",
    }

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def store_from_api_response(data: dict) -> int:
    """Parse hourly arrays and store into DB. Returns number of rows stored."""
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    hums = hourly.get("relativehumidity_2m", [])
    count = 0
    if not (times and temps and hums):
        return 0

    db.init_db()
    for t, temp, hum in zip(times, temps, hums):
        # time already in UTC string if timezone param used
        try:
            db.insert_observation(t, float(temp) if temp is not None else None, float(hum) if hum is not None else None)
            count += 1
        except Exception:
            continue
    return count
