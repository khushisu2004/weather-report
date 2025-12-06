import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from typing import List, Tuple

DB_PATH = "weather.db"


def init_db() -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            """
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL,
            humidity REAL
        )
        """
        )
        conn.commit()


def insert_observation(timestamp: str, temperature: float, humidity: float) -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT INTO observations (timestamp, temperature, humidity) VALUES (?, ?, ?)",
            (timestamp, temperature, humidity),
        )
        conn.commit()


def query_last_hours(hours: int = 48) -> List[Tuple[str, float, float]]:
    # return rows for last `hours`
    cutoff = datetime.now(timezone.utc).astimezone(timezone.utc).isoformat()
    # compute cutoff datetime in ISO by subtracting hours in SQL via datetime functions is messy; we'll compute in Python
    from datetime import timedelta

    cutoff_dt = datetime.now(timezone.utc) - timedelta(hours=hours)
    cutoff_iso = cutoff_dt.isoformat()
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.execute(
            "SELECT timestamp, temperature, humidity FROM observations WHERE timestamp >= ? ORDER BY timestamp ASC",
            (cutoff_iso,)
        )
        rows = cur.fetchall()
    return rows
