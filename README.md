# Weather Service (Take-home)

Small FastAPI backend that:

- Fetches past 48 hours of hourly temperature and relative humidity from Open-Meteo (MeteoSwiss endpoint)
- Stores observations in a local SQLite DB
- Exposes endpoints to fetch/store data, and to export an Excel (.xlsx) and PDF report (with chart)

Run locally

1. Create and activate venv (Windows PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run app with uvicorn:

```powershell
venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

Endpoints

- `GET /weather-report?lat={lat}&lon={lon}`: fetch past 48h from Open-Meteo and store in `weather.db`.
- `GET /export/excel`: returns last 48h as an Excel file.
- `GET /export/pdf`: returns a PDF report with a line chart (temperature & humidity vs time).

Docker

Build:

```powershell
docker build -t weather-service:latest .
```

Run:

```powershell
docker run -p 8000:8000 weather-service:latest
```

Notes

- WeasyPrint on Windows may need external system dependencies (Cairo, Pango, GDK-PixBuf). If PDF generation fails, see WeasyPrint docs or use the Docker image which includes libraries.
