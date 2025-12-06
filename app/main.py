from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.responses import StreamingResponse, RedirectResponse, FileResponse
import os
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from . import weather, report, db
import io

app = FastAPI(title="Weather Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# mount static frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def startup():
    db.init_db()


@app.get("/weather-report")
def fetch_and_store(lat: float = Query(...), lon: float = Query(...)):
    try:
        data = weather.fetch_past_48h(lat, lon)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error calling upstream API: {e}")
    stored = weather.store_from_api_response(data)
    return {"stored_rows": stored}


@app.get("/export/excel")
def export_excel():
    df = report.get_dataframe_last_48h()
    if df.empty:
        raise HTTPException(status_code=404, detail="No data for last 48 hours")
    data = report.excel_bytes_from_df(df)
    return StreamingResponse(io.BytesIO(data), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=weather_data.xlsx"})


@app.get("/export/pdf")
def export_pdf(location: Optional[str] = Query("Location")):
    df = report.get_dataframe_last_48h()
    if df.empty:
        raise HTTPException(status_code=404, detail="No data for last 48 hours")
    data = report.pdf_bytes_from_df(df, location_label=location)
    return Response(content=data, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=weather_report.pdf"})


@app.get("/export/png")
def export_png(location: Optional[str] = Query("Location")):
    """Fallback endpoint for charts when WeasyPrint/system libs are unavailable (Windows)."""
    df = report.get_dataframe_last_48h()
    if df.empty:
        raise HTTPException(status_code=404, detail="No data for last 48 hours")
    png_bytes = report.png_bytes_from_df(df, location_label=location)
    return Response(content=png_bytes, media_type="image/png", headers={"Content-Disposition": "attachment; filename=weather_chart.png"})



@app.get("/")
def root():
    # redirect to the static frontend
    return RedirectResponse(url="/static/index.html")


@app.get('/download/zip')
def download_zip():
    """Serve the deliverables ZIP from project root if present."""
    zip_path = os.path.join(os.getcwd(), 'deliverables.zip')
    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail='deliverables.zip not found. Generate files first or use /export endpoints')
    return FileResponse(zip_path, media_type='application/zip', filename='deliverables.zip')
