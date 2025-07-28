import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import pandas as pd
import numpy as np
from pmdarima import auto_arima
from datetime import datetime, timedelta
import traceback
import uuid
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Sesuaikan origin jika perlu
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = "uploaded_csv"
META_FILE = "metadata.json"

# In-memory storage for metadata: {id, fileName, uploadDate, rows}
file_storage = []

# Load saved metadata on startup (optional persistence)
if os.path.exists(META_FILE):
    with open(META_FILE, "r") as f:
        file_storage = json.load(f)

def save_metadata():
    with open(META_FILE, "w") as f:
        json.dump(file_storage, f)

CSV_PATH = "data/data_pakan_ayam.csv"

# --- Fungsi Helper ---

def load_data(file_id=None):
    if file_id:
        file_path = os.path.join(DATA_DIR, file_id + ".csv")
    else:
        file_path = CSV_PATH  # Default fallback
    
    if not os.path.exists(file_path):
        raise FileNotFoundError("File data CSV tidak ditemukan.")

    df_raw = pd.read_csv(file_path)    
    
    print("Total data asli CSV:", len(df_raw)) 
    
    df = df_raw.copy()
    df.rename(columns=lambda x: x.strip().lower(), inplace=True)

    # Ganti bulan Indonesia ke Inggris
    ind_to_eng_month = {
        'Januari': 'January', 'Februari': 'February', 'Maret': 'March',
        'April': 'April', 'Mei': 'May', 'Juni': 'June',
        'Juli': 'July', 'Agustus': 'August', 'September': 'September',
        'Oktober': 'October', 'November': 'November', 'Desember': 'December'
    }

    df['tanggal'] = df['tanggal'].astype(str)
    for ind, eng in ind_to_eng_month.items():
        df['tanggal'] = df['tanggal'].str.replace(ind, eng, regex=False)

    df['tanggal'] = pd.to_datetime(df['tanggal'], format='%d %B %Y', errors='coerce')

    for col in ['pakan_pakai', 'jumlah_ayam', 'jumlah_ayam_mati']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df[df['pakan_pakai'] > 0]

    # Sebelum dropna, cari baris-baris bermasalah
    df_filtered = df.copy()
    mask_na = df_filtered[['tanggal', 'pakan_pakai', 'jumlah_ayam', 'jumlah_ayam_mati']].isna().any(axis=1)

    print("\n--- DATA DIBUANG KARENA NA ---")
    print(df_filtered[mask_na])
    print("Total baris dibuang karena NA:", mask_na.sum())

    df.dropna(subset=['tanggal', 'pakan_pakai', 'jumlah_ayam', 'jumlah_ayam_mati'], inplace=True)
    df.sort_values('tanggal', inplace=True)
    df.reset_index(drop=True, inplace=True)

    print("Data setelah pakan_pakai > 0 dan dropna:", len(df))
    print("Jumlah NA per kolom setelah filter:\n", df.isna().sum())

    if 'periode' in df.columns:
        df['periode'] = df['periode'].replace(["", "nan", "NaN", "None"], np.nan)

    return df

def get_periode_boundaries(df):
    if 'periode' in df.columns and df['periode'].notna().any():
        df = df.dropna(subset=["periode"])
        df["periode"] = df["periode"].astype(str)
        grouped = df.groupby("periode")["tanggal"]
        result = []
        for periode, group in grouped:
            result.append({
                "periode": periode,
                "start": group.min().strftime("%Y-%m-%d"),
                "end": group.max().strftime("%Y-%m-%d")
            })
        result.sort(key=lambda x: x['start'])
        return result
    return []

def get_periode_edge_indexes(df, labels, tanggal_mulai_prediksi, tanggal_selesai_prediksi):
    indexes = set()
    if 'periode' in df.columns:
        grouped = df.groupby("periode")["tanggal"]
        for _, group in grouped:
            tanggal_awal = group.min()
            tanggal_akhir = group.max()
            for t in [tanggal_awal, tanggal_akhir]:
                try:
                    idx = labels.index(t.strftime("%Y-%m-%d"))
                    indexes.add(idx)
                except ValueError:
                    pass
    for t in [tanggal_mulai_prediksi, tanggal_selesai_prediksi]:
        try:
            idx = labels.index(t.strftime("%Y-%m-%d"))
            indexes.add(idx)
        except ValueError:
            pass
    return sorted(indexes)

def train_arima(series):
    if len(series) < 10 or series.nunique() <= 1:
        raise ValueError("Data tidak cukup atau terlalu seragam untuk ARIMA.")
    return auto_arima(series, seasonal=False, suppress_warnings=True, error_action='ignore')

# --- Endpoint ---
@app.post("/predict_periode")
async def predict_periode(request: Request):
    try:
        body = await request.json()
        tanggal_mulai = datetime.strptime(body["tanggal_mulai"], "%Y-%m-%d")
        tanggal_selesai = datetime.strptime(body["tanggal_selesai"], "%Y-%m-%d")
        file_id = body.get("file_id")  # Tambahan di sini
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Format tanggal tidak valid atau field tidak lengkap."})

    try:
        df = load_data(file_id=file_id)
        df = df.set_index("tanggal").sort_index()
        df_train = df[df.index < tanggal_mulai]

        if df_train.empty or len(df_train["pakan_pakai"]) < 10:
            return JSONResponse(status_code=400, content={"error": "Data tidak cukup untuk pelatihan model."})

        model = train_arima(df_train["pakan_pakai"])
        order = model.order  
        print("ARIMA order (p,d,q):", order)
        n_periods = (tanggal_selesai - tanggal_mulai).days + 1
        forecast = model.predict(n_periods=n_periods)
        tanggal_prediksi = [tanggal_mulai + timedelta(days=i) for i in range(n_periods)]

        data_prediksi = [
            {
                "x": t.strftime('%Y-%m-%d'),
                "y": round(float(p) / 50, 2),     
                "kg": round(float(p), 2),         
                "periode": None
            }
            for t, p in zip(tanggal_prediksi, forecast)
        ]

        df_reset = df.reset_index().copy()
        print("Jumlah data aktual dari CSV:", len(df_reset))

        semua_data_aktual = [
            {
                "x": row['tanggal'].strftime('%Y-%m-%d'),
                "y": round(row['pakan_pakai'], 2),               
                "kg": round(row['pakan_pakai'] * 50, 2),         
                "periode": int(row['periode']) if 'periode' in row and pd.notna(row['periode']) else None
            }
            for _, row in df_reset.iterrows()
        ]

        print("Jumlah data prediksi:", len(data_prediksi))
        labels = sorted(list(set(
            [row["x"] for row in semua_data_aktual] + [row["x"] for row in data_prediksi]
        )))
        periode_edges = get_periode_edge_indexes(df_reset, labels, tanggal_mulai, tanggal_selesai)
        periode_ranges = get_periode_boundaries(df_reset)

        rata_mati = df['jumlah_ayam_mati'].mean()
        if pd.isna(rata_mati): rata_mati = 0
        jumlah_hari = (tanggal_selesai - tanggal_mulai).days + 1
        total_kg = float(round(sum(forecast), 2))
        total_karung = float(round(total_kg / 50, 2))
        prediksi_jumlah_ayam = int(max(0, int(df['jumlah_ayam'].iloc[-1]) - int(rata_mati * jumlah_hari)))
        
        # print("\n========= DEBUG MAPE =========")
        # print("Data prediksi:", data_prediksi)
        # print("Data aktual:", semua_data_aktual)

        return JSONResponse(content={
            "data_prediksi": data_prediksi,
            "data_aktual": semua_data_aktual,
            "labels": labels,
            "periode_edges": periode_edges,
            "periode_ranges": periode_ranges,
            "summary": {
                "total_prediksi_kg": total_kg,
                "total_prediksi_karung": total_karung,
                "prediksi_jumlah_ayam": prediksi_jumlah_ayam,
                "rata_mati_per_hari": round(float(rata_mati), 2),
                "durasi_hari": jumlah_hari,
                "catatan": f"Sediakan minimal {round(total_karung, 2)} karung untuk {jumlah_hari} hari. Pantau stok harian dan kematian ayam."
            },
            "arima_order": {"p": order[0], "d": order[1], "q": order[2]}
        })

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"Terjadi error: {str(e)}"})

@app.post("/predict_per_ayam")
async def predict_per_ayam(request: Request):
    try:
        body = await request.json()
        print("DEBUG Payload dari Vue:", body)

        if not body.get("tanggal_mulai") or not body.get("tanggal_selesai"):
            return JSONResponse(status_code=400, content={"error": "Tanggal mulai dan selesai wajib diisi"})

        tanggal_mulai = datetime.strptime(body.get("tanggal_mulai"), "%Y-%m-%d")
        tanggal_selesai = datetime.strptime(body.get("tanggal_selesai"), "%Y-%m-%d")
        file_id = body.get("file_id")

        hari = (tanggal_selesai - tanggal_mulai).days + 1
        if hari <= 0:
            return JSONResponse(status_code=400, content={"error": "Tanggal selesai harus setelah tanggal mulai."})

        jumlah_ayam_awal_raw = body.get("jumlah_ayam_awal")
        if jumlah_ayam_awal_raw is None:
            return JSONResponse(status_code=400, content={"error": "jumlah_ayam_awal is required"})

        try:
            jumlah_ayam_awal = int(jumlah_ayam_awal_raw)
        except ValueError:
            return JSONResponse(status_code=400, content={"error": "jumlah_ayam_awal harus berupa angka."})

        if jumlah_ayam_awal <= 0:
            return JSONResponse(status_code=400, content={"error": "Jumlah ayam harus lebih dari 0."})

        df = load_data(file_id=file_id)
        df["pakan_per_ayam"] = df["pakan_pakai"] / df["jumlah_ayam"]

        model = train_arima(df['pakan_per_ayam'])
        order = model.order
        print("ARIMA order (p,d,q):", order) 
        prediksi = model.predict(n_periods=hari).tolist()

        hasil_prediksi = []
        ayam_hidup = jumlah_ayam_awal
        tanggal = tanggal_mulai
        total_kg = 0
        total_per_ayam = 0

        rata_mati = df['jumlah_ayam_mati'].mean()
        if pd.isna(rata_mati): rata_mati = 0

        for i in range(hari):
            per_ayam = round(prediksi[i], 4)
            pakan = round(per_ayam * ayam_hidup, 2)

            hasil_prediksi.append({
                "x": tanggal.strftime('%Y-%m-%d'),
                "y": round(pakan / 50, 2),  # karung
                "kg": pakan,
                "ayam_hidup": ayam_hidup,
                "per_ayam": per_ayam,
                "periode": None
            })

            tanggal += timedelta(days=1)
            ayam_hidup = max(0, ayam_hidup - int(rata_mati))
            total_kg += pakan
            total_per_ayam += per_ayam

        df_reset = df.reset_index().copy()
        semua_data_aktual = [
            {
                "x": row['tanggal'].strftime('%Y-%m-%d'),
                "y": round(row['pakan_pakai'], 2),
                "kg": round(row['pakan_pakai'] * 50, 2),
                "periode": int(row['periode']) if 'periode' in row and pd.notna(row['periode']) else None
            }
            for _, row in df_reset.iterrows()
        ]
        print("Jumlah data aktual dari CSV:", len(semua_data_aktual))
        print("Jumlah data prediksi:", len(hasil_prediksi))

        labels = sorted(list(set(
            [row["x"] for row in semua_data_aktual] + [row["x"] for row in hasil_prediksi]
        )))
        periode_edges = get_periode_edge_indexes(df, labels, tanggal_mulai, tanggal_selesai)
        periode_ranges = get_periode_boundaries(df)

        summary = {
            "total_prediksi_kg": round(total_kg, 2),
            "total_prediksi_karung": round(total_kg / 50, 2),
            "rata_per_ayam_kg_per_hari": round(total_per_ayam / hari, 4) if hari > 0 else 0,
            "jumlah_ayam_awal": jumlah_ayam_awal,
            "rata_mati_per_hari": round(float(rata_mati), 2),
            "perkiraan_akhir_ayam": ayam_hidup,
            "durasi_hari": hari,
            "catatan": f"Pastikan stok minimal {round(total_kg / 50, 2)} karung. Biar aman, tambahkan stok pakan 5–10% lebih banyak dari prediksi."
        }
        
        # print("\n========= DEBUG MAPE =========")
        # print("Data prediksi:", hasil_prediksi)
        # print("Data aktual:", semua_data_aktual)

        return JSONResponse(content={
            "data_prediksi": hasil_prediksi,
            "data_aktual": semua_data_aktual,
            "labels": labels,
            "periode_edges": periode_edges,
            "periode_ranges": periode_ranges,
            "summary": summary,
            "arima_order": {"p": order[0], "d": order[1], "q": order[2]}
        })

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"Terjadi kesalahan: {str(e)}"})

# POST: Save new CSV preview
@app.post("/save_csv_preview")
async def save_csv_preview(request: Request):
    body = await request.json()
    file_name = body.get("fileName")
    upload_date = body.get("uploadDate")
    rows = body.get("rows", [])

    if not file_name or not upload_date or not rows:
        return JSONResponse(status_code=400, content={"error": "Data tidak lengkap"})

    new_id = str(uuid.uuid4())
    file_path = os.path.join(DATA_DIR, new_id + ".csv")
    os.makedirs(DATA_DIR, exist_ok=True)

    df = pd.DataFrame(rows)
    df.to_csv(file_path, index=False)

    file_entry = {
        "id": new_id,
        "fileName": file_name,
        "uploadDate": upload_date,
        "dataCSV": rows  # Untuk frontend
    }
    file_storage.append(file_entry)
    save_metadata()

    return {"status": "Berhasil disimpan", "id": new_id}

# POST: Update existing CSV preview
@app.post("/update_csv_preview")
async def update_csv_preview(request: Request):
    body = await request.json()
    file_id = body.get("id")
    file_name = body.get("fileName")
    upload_date = body.get("uploadDate")
    rows = body.get("rows", [])

    if not file_id or not file_name or not upload_date or not rows:
        return JSONResponse(status_code=400, content={"error": "Data tidak lengkap"})

    index = next((i for i, f in enumerate(file_storage) if f["id"] == file_id), None)
    if index is None:
        return JSONResponse(status_code=404, content={"error": "File tidak ditemukan"})

    file_path = os.path.join(DATA_DIR, file_id + ".csv")
    df = pd.DataFrame(rows)
    df.to_csv(file_path, index=False)

    file_storage[index]["fileName"] = file_name
    file_storage[index]["uploadDate"] = upload_date
    file_storage[index]["dataCSV"] = rows
    save_metadata()

    return {"status": "Berhasil diupdate"}

# GET: List all uploaded CSV metadata
@app.get("/list_csv_files")
async def list_csv_files():
    return {"files": file_storage}

# DELETE: Delete a file by id
@app.delete("/delete_csv/{file_id}")
async def delete_csv(file_id: str):
    index = next((i for i, f in enumerate(file_storage) if f["id"] == file_id), None)
    if index is None:
        return JSONResponse(status_code=404, content={"error": "File tidak ditemukan"})

    file_path = os.path.join(DATA_DIR, file_id + ".csv")
    if os.path.exists(file_path):
        os.remove(file_path)

    file_storage.pop(index)
    save_metadata()
    return {"status": "File berhasil dihapus"}

# (Opsional) Download CSV by file id
@app.get("/download_csv/{file_id}")
async def download_csv(file_id: str):
    file_path = os.path.join(DATA_DIR, file_id + ".csv")
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"error": "File tidak ditemukan"})

    return FileResponse(file_path, filename=f"{file_id}.csv", media_type='text/csv')

@app.get("/{full_path:path}")
async def serve_vue(full_path: str):
    build_dir = os.path.join(os.path.dirname(__file__), "static")
    file_path = os.path.join(build_dir, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(build_dir, "index.html"))
