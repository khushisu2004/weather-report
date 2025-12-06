import io
import base64
from datetime import datetime, timezone
import pandas as pd
import matplotlib

# use Agg backend for headless environments (no display)
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from . import db


def get_dataframe_last_48h() -> pd.DataFrame:
    rows = db.query_last_hours(48)
    if not rows:
        return pd.DataFrame(columns=["timestamp", "temperature", "humidity"])
    df = pd.DataFrame(rows, columns=["timestamp", "temperature", "humidity"])
    # timestamps returned from API are ISO strings in UTC; parse as datetimes (leave tz-naive)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def excel_bytes_from_df(df: pd.DataFrame) -> bytes:
    bio = io.BytesIO()
    # ensure timestamp column is present
    df.to_excel(bio, index=False, engine="openpyxl")
    bio.seek(0)
    return bio.read()


def pdf_bytes_from_df(df: pd.DataFrame, location_label: str = "Location") -> bytes:
    # create plot
    plt.figure(figsize=(8, 4.5))
    if df.empty:
        plt.text(0.5, 0.5, "No data available", ha="center", va="center")
    else:
        x = pd.to_datetime(df["timestamp"])
        fig, ax1 = plt.subplots(figsize=(8, 4.5))
        ax1.plot(x, df["temperature"], color="tab:red", label="Temperature (°C)")
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Temperature (°C)", color="tab:red")
        ax1.tick_params(axis="y", labelcolor="tab:red")

        ax2 = ax1.twinx()
        ax2.plot(x, df["humidity"], color="tab:blue", label="Relative Humidity (%)")
        ax2.set_ylabel("Relative Humidity (%)", color="tab:blue")
        ax2.tick_params(axis="y", labelcolor="tab:blue")

        fig.autofmt_xdate()

    # save plot to PNG
    png = io.BytesIO()
    plt.tight_layout()
    plt.savefig(png, format="png")
    plt.close("all")
    png.seek(0)
    img_b64 = base64.b64encode(png.read()).decode("ascii")

    # build simple HTML
    start = "-"
    end = "-"
    if not df.empty:
        start = pd.to_datetime(df["timestamp"]).min().strftime("%Y-%m-%d %H:%M")
        end = pd.to_datetime(df["timestamp"]).max().strftime("%Y-%m-%d %H:%M")

    html = f"""
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          body {{ font-family: Arial, sans-serif; margin: 20px; }}
          h1 {{ font-size: 18px; }}
          .meta {{ margin-bottom: 10px; }}
        </style>
      </head>
      <body>
        <h1>Weather Report - {location_label}</h1>
        <div class="meta">Period: {start} to {end} (UTC)</div>
        <img src="data:image/png;base64,{img_b64}" alt="chart" style="max-width:100%;height:auto;" />
      </body>
    </html>
    """

    # import WeasyPrint lazily so server can start even if system libs are missing
    try:
        from weasyprint import HTML
    except Exception as e:
        raise RuntimeError(
            "WeasyPrint is not available. PDF generation requires WeasyPrint and system libs (cairo, pango, gdk-pixbuf). "
            "On Windows install GTK/Cairo or use the provided Docker image. Original error: %s" % e
        )

    pdf = HTML(string=html).write_pdf()
    return pdf


def png_bytes_from_df(df: pd.DataFrame, location_label: str = "Location") -> bytes:
    """Generate a PNG chart without WeasyPrint (good for Windows/headless environments)."""
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    if df.empty:
        ax1.text(0.5, 0.5, "No data available", ha="center", va="center", transform=ax1.transAxes)
    else:
        x = pd.to_datetime(df["timestamp"])
        ax1.plot(x, df["temperature"], color="tab:red", label="Temperature (°C)", linewidth=2)
        ax1.set_xlabel("Time", fontsize=12)
        ax1.set_ylabel("Temperature (°C)", color="tab:red", fontsize=12)
        ax1.tick_params(axis="y", labelcolor="tab:red")
        
        ax2 = ax1.twinx()
        ax2.plot(x, df["humidity"], color="tab:blue", label="Relative Humidity (%)", linewidth=2)
        ax2.set_ylabel("Relative Humidity (%)", color="tab:blue", fontsize=12)
        ax2.tick_params(axis="y", labelcolor="tab:blue")
        
        fig.autofmt_xdate()
        ax1.set_title(f"Weather Report - {location_label}", fontsize=14, fontweight="bold")
    
    fig.tight_layout()
    png = io.BytesIO()
    fig.savefig(png, format="png", dpi=100)
    plt.close(fig)
    png.seek(0)
    return png.read()
