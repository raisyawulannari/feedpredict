import os
import csv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from sklearn.linear_model import LinearRegression

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ganti dengan domain frontend saat production
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "dist")
app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")

def load_data(csv_path):
    periode = []
    umur_hari = []
    kebutuhan_pakan = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                # Pakai 'Umur_Hari' sebagai fitur dan 'Pakan_Pakai' sebagai target
                umur = int(row['Umur_Hari'])
                pakan = int(row['Pakan_Pakai'])
                periode.append(row['Periode'])
                umur_hari.append(umur)
                kebutuhan_pakan.append(pakan)
            except Exception:
                continue
    return periode, umur_hari, kebutuhan_pakan

@app.get("/api/prediksi")
async def prediksi_pakan(jumlah_periode: int = 7):
    csv_path = os.path.join(os.path.dirname(__file__), "data", "data_pakan_ayam.csv")

    try:
        periode, umur_hari, kebutuhan_pakan = load_data(csv_path)

        if not umur_hari or not kebutuhan_pakan:
            return JSONResponse(status_code=400, content={"detail": "Data CSV kosong atau salah format"})

        # Data fitur (umur hari) dan target (kebutuhan pakan)
        X = np.array(umur_hari).reshape(-1, 1)
        y = np.array(kebutuhan_pakan)

        # Buat model regresi linear dan latih
        model = LinearRegression()
        model.fit(X, y)

        # Prediksi kebutuhan pakan untuk periode berikutnya
        max_umur = max(umur_hari)
        next_umur = np.array([max_umur + i for i in range(1, jumlah_periode + 1)]).reshape(-1, 1)
        prediksi = model.predict(next_umur)
        prediksi = prediksi.round().astype(int).tolist()

        # Buat label periode baru (misal "Hari ke-XX")
        periode_baru = [f"Hari ke-{max_umur + i}" for i in range(1, jumlah_periode + 1)]

        return {"periode": periode_baru, "hasil": prediksi}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saat prediksi: {str(e)}")

@app.get("/{full_path:path}")
async def serve_vue_app(full_path: str):
    index_path = os.path.join(frontend_path, "index.html")
    return FileResponse(index_path)
