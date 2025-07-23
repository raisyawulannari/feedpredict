from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import pandas as pd
import numpy as np
from pmdarima import auto_arima
from datetime import datetime, timedelta
import os

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CSV_PATH = "data/data_pakan_ayam.csv"

# Load dataset
def load_data():
    df = pd.read_csv(CSV_PATH)
    df.rename(columns=lambda x: x.strip().lower(), inplace=True)
    df['tanggal'] = pd.to_datetime(df['tanggal'], errors='coerce')
    df['pakan_pakai'] = pd.to_numeric(df['pakan_pakai'], errors='coerce')
    df.dropna(subset=['tanggal', 'pakan_pakai'], inplace=True)
    df.sort_values('tanggal', inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

# Ambil tanggal awal dan akhir per periode
def get_periode_boundaries(df):
    if 'periode' in df.columns:
        grouped = df.groupby('periode')['tanggal']
        return pd.concat([grouped.min(), grouped.max()]).drop_duplicates().sort_values().to_list()
    return df['tanggal'].drop_duplicates().to_list()

# Latih ARIMA

def train_arima(series):
    if len(series) < 10:
        raise ValueError("Data terlalu sedikit untuk ARIMA.")
    return auto_arima(series, seasonal=False, suppress_warnings=True, error_action='ignore')

# === 1. Prediksi berdasarkan Periode ===
# === 1. Prediksi berdasarkan Periode ===
@app.post("/predict_periode")
async def predict_periode(request: Request):
    body = await request.json()
    try:
        tanggal_mulai = datetime.strptime(body["tanggal_mulai"], "%Y-%m-%d")
        tanggal_selesai = datetime.strptime(body["tanggal_selesai"], "%Y-%m-%d")
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Format tanggal tidak valid."})

    df = load_data()
    df.set_index("tanggal", inplace=True)
    df_train = df[df.index < tanggal_mulai]
    if df_train.empty:
        return JSONResponse(status_code=400, content={"error": "Data tidak cukup untuk pelatihan model."})

    try:
        model = train_arima(df_train["pakan_pakai"])
        n_periods = (tanggal_selesai - tanggal_mulai).days + 1
        forecast = model.predict(n_periods=n_periods)
        tanggal_prediksi = [tanggal_mulai + timedelta(days=i) for i in range(n_periods)]
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Gagal memprediksi: {str(e)}"})

    data_prediksi = [
        {"x": t.strftime('%Y-%m-%d'), "y": round(float(p), 2)}
        for t, p in zip(tanggal_prediksi, forecast)
    ]

    df_reset = df.reset_index()
    boundaries = get_periode_boundaries(df_reset)
    data_aktual = df_reset[df_reset['tanggal'].isin(boundaries)]
    data_aktual = [
        {"x": row['tanggal'].strftime('%Y-%m-%d'), "y": round(row['pakan_pakai'], 2)}
        for _, row in data_aktual.iterrows()
    ]

    total_kg = round(sum(forecast), 2)
    total_karung = round(total_kg / 50, 2)

    # 💡 Prediksi jumlah ayam (sederhana)
    jumlah_hari = (tanggal_selesai - tanggal_mulai).days + 1
    prediksi_jumlah_ayam = 100 + jumlah_hari * 2  # Bisa kamu ubah sesuai logikamu

    return JSONResponse(content={
        "data_prediksi": data_prediksi,
        "data_aktual": data_aktual,
        "summary": {
            "total_prediksi_kg": total_kg,
            "total_prediksi_karung": total_karung,
            "prediksi_jumlah_ayam": prediksi_jumlah_ayam  # kirim ke frontend
        }
    })

# === 2. Prediksi berdasarkan jumlah Ayam ===
@app.post("/predict_per_ayam")
async def predict_per_ayam(request: Request):
    body = await request.json()
    tanggal_mulai = pd.to_datetime(body.get("tanggal_mulai"))
    tanggal_selesai = pd.to_datetime(body.get("tanggal_selesai"))
    jumlah_ayam_awal = body.get("jumlah_ayam_awal")

    if not tanggal_mulai or not tanggal_selesai:
        return JSONResponse(status_code=400, content={"message": "Tanggal wajib diisi."})

    if not jumlah_ayam_awal or jumlah_ayam_awal <= 0:
        return JSONResponse(status_code=400, content={"message": "Jumlah ayam harus lebih dari 0."})

    hari = (tanggal_selesai - tanggal_mulai).days + 1
    if hari <= 0:
        return JSONResponse(status_code=400, content={"message": "Tanggal selesai harus setelah mulai."})

    df = load_data()
    try:
        model = train_arima(df['pakan_pakai'])
        prediksi = model.predict(n_periods=hari).tolist()
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Prediksi gagal: {str(e)}"})

    hasil_prediksi = []
    ayam_hidup = jumlah_ayam_awal
    tanggal = tanggal_mulai
    total_kg = 0
    total_per_ayam = 0

    for i in range(hari):
        pakan = round(float(prediksi[i]), 2)
        per_ayam = round(pakan / ayam_hidup, 4) if ayam_hidup else 0
        hasil_prediksi.append({
            "x": tanggal.strftime('%Y-%m-%d'),
            "y": pakan,
            "karung": round(pakan / 50, 2),
            "ayam_hidup": ayam_hidup,
            "per_ayam": per_ayam
        })
        tanggal += timedelta(days=1)
        ayam_hidup = max(0, ayam_hidup - np.random.randint(0, 3))
        total_kg += pakan
        total_per_ayam += per_ayam

    boundaries = get_periode_boundaries(df)
    data_aktual = df[df['tanggal'].isin(boundaries)]
    data_aktual = [
        {"x": row['tanggal'].strftime('%Y-%m-%d'), "y": round(row['pakan_pakai'], 2)}
        for _, row in data_aktual.iterrows()
    ]

    summary = {
        "total_prediksi_kg": round(total_kg, 2),
        "total_prediksi_karung": round(total_kg / 50, 2),
        "rata_per_ayam_kg_per_hari": round(total_per_ayam / hari, 4) if hari > 0 else 0
    }

    return JSONResponse(content={
        "data_prediksi": hasil_prediksi,
        "data_aktual": data_aktual,
        "summary": summary
    })

# Vue static
@app.get("/{full_path:path}")
async def serve_vue(full_path: str):
    build_dir = os.path.join(os.path.dirname(__file__), "static")
    file_path = os.path.join(build_dir, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(build_dir, "index.html"))
