# backend/routes.py
from fastapi import APIRouter, HTTPException, Query
import numpy as np
import pandas as pd
import joblib
import os
from statsmodels.tsa.arima.model import ARIMAResults  # untuk type hint, model_fit adalah ARIMAResults

# Peta bulan Indonesia ke angka untuk parsing tanggal saat memuat historis
BULAN_MAP = {
    'Januari': 1, 'Februari': 2, 'Maret': 3, 'April': 4, 'Mei': 5,
    'Juni': 6, 'Juli': 7, 'Agustus': 8, 'September': 9,
    'Oktober': 10, 'November': 11, 'Desember': 12
}

def parse_tanggal_id(tgl_str):
    try:
        parts = tgl_str.strip().split()
        if len(parts) >= 3:
            day = int(parts[0])
            month_name = parts[1]
            year = int(parts[2])
            month = BULAN_MAP.get(month_name)
            if month is None:
                return pd.NaT
            return pd.Timestamp(year=year, month=month, day=day)
        else:
            return pd.to_datetime(tgl_str, dayfirst=True, errors='coerce')
    except:
        return pd.to_datetime(tgl_str, dayfirst=True, errors='coerce')

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model_pakan.joblib")
CSV_PATH = os.path.join(BASE_DIR, "data", "data_pakan_ayam.csv")

model_fit = None  # akan menampung ARIMAResults
df_data = None
rata_rata_umur_per_periode = {}  # menyimpan durasi rata-rata periode historis

def load_resources():
    global model_fit, df_data, rata_rata_umur_per_periode

    # Muat model ARIMA
    try:
        model_fit = joblib.load(MODEL_PATH)
        print("Model ARIMA berhasil dimuat dari:", MODEL_PATH)
    except FileNotFoundError:
        print(f"ERROR: Model ARIMA tidak ditemukan di {MODEL_PATH}. Jalankan train_model_arima.py dulu.")
        model_fit = None
    except Exception as e:
        print(f"ERROR: Gagal memuat model ARIMA: {e}")
        model_fit = None

    # Muat data historis (jika ada) untuk fitur prediksi per-periode
    try:
        df = pd.read_csv(CSV_PATH)
        # Parse Tanggal jika butuh, tapi di prediksi-periode kita hanya butuh kolom Periode dan Umur_Hari dan Pakan_Pakai
        df_data = df  # simpan raw, akan parse tanggal saat dibutuhkan
        # Hitung durasi rata-rata periode historis jika kolom Periode dan Umur_Hari ada
        if 'Periode' in df_data.columns and 'Umur_Hari' in df_data.columns:
            # Hitung durasi tiap periode: misal max Umur_Hari - min Umur_Hari + 1
            periode_umurs = df_data.groupby('Periode')['Umur_Hari'].agg(['min', 'max']).reset_index()
            periode_umurs['durasi'] = periode_umurs['max'] - periode_umurs['min'] + 1
            if not periode_umurs.empty:
                rata_rata_umur_per_periode['durasi'] = int(periode_umurs['durasi'].mean())
                print("Rata-rata durasi periode historis:", rata_rata_umur_per_periode['durasi'], "hari")
            else:
                rata_rata_umur_per_periode['durasi'] = 45
                print("Data periode historis kosong, gunakan default durasi 45 hari.")
        else:
            rata_rata_umur_per_periode['durasi'] = 45
            print("Kolom 'Periode' atau 'Umur_Hari' tidak ditemukan, gunakan default durasi 45 hari.")
        # Simpan df_data global
        globals()['df_data'] = df_data
    except Exception as e:
        print(f"WARNING: Gagal muat data historis dari CSV: {e}")
        globals()['df_data'] = None

# Panggil load_resources saat startup module diimport
load_resources()

@router.get("/prediksi")
async def prediksi_pakan(
    tipe: str = Query('harian', description="Pilihan: harian, mingguan, bulanan, periode"),
    max_periode_ke_depan: int = Query(3, ge=1, description="Jumlah periode ke depan untuk tipe 'periode'")
):
    """
    Endpoint untuk prediksi pakan. 
    - tipe='harian': prediksi pakan harian untuk steps tertentu (misal 45 hari ke depan).
    - tipe='mingguan': agregasi per 7 hari.
    - tipe='bulanan': agregasi per 30 hari.
    - tipe='periode': kombinasi historis + prediksi periode ke depan berdasarkan durasi rata-rata.
    Output: JSON {"periode": [...], "hasil": [...], "keterangan": "..."}.
    """
    if model_fit is None:
        raise HTTPException(status_code=500, detail="Model ARIMA belum tersedia. Jalankan training terlebih dahulu.")

    # Muat data historis untuk membuat deret waktu
    try:
        df = pd.read_csv(CSV_PATH)
        # Parse tanggal untuk deret waktu historis
        if 'Tanggal' in df.columns:
            df['Tanggal_parsed'] = df['Tanggal'].apply(parse_tanggal_id)
            df = df.dropna(subset=['Tanggal_parsed'])
            df = df.sort_values('Tanggal_parsed')
            # Buat series harian
            series = df.set_index('Tanggal_parsed')['Pakan_Pakai'].asfreq('D')
            # Tangani NaN
            if series.isna().sum() > 0:
                series = series.interpolate(method='linear').fillna(method='bfill').fillna(method='ffill')
        else:
            # Jika tidak ada kolom Tanggal, kita tidak punya deret waktu kontinu; 
            # tetapi untuk prediksi harian ARIMA butuh index waktu. 
            # Kita bisa raise error atau gunakan index integer sederhana.
            raise HTTPException(status_code=500, detail="Kolom 'Tanggal' tidak ditemukan dalam data historis untuk membangun deret waktu.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memuat data historis: {e}")

    hasil = []
    label = []

    # Fungsi bantu: konversi array forecast (nilai Pakan_Pakai dalam satuan sama seperti CSV, misal kg) 
    # menjadi list karung: bila ingin total, gunakan sum chunk lalu /50; bila rata-rata, gunakan mean chunk lalu /50.
    # Di sini kita tampilkan total pakan per periode, agar menggambarkan kebutuhan total.
    # Untuk harian, setiap nilai forecast adalah pakan untuk satu hari → bagi 50.
    # Untuk mingguan: sum 7 hari forecast, bagi 50.
    # Untuk bulanan: sum 30 hari forecast, bagi 50.
    # Untuk periode: sum durasi hari forecast, bagi 50.

    if tipe == 'harian':
        # Prediksi harian: misal 45 hari ke depan
        steps = 45
        try:
            forecast = model_fit.forecast(steps=steps)  # array length = steps
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gagal forecast ARIMA: {e}")
        for i, val in enumerate(forecast, start=1):
            # val adalah pakan_pakai prediksi dalam satuan sama dengan CSV (misal kg)
            karung = round(val / 50, 2)
            label.append(f"Hari {i}")
            hasil.append(karung)

    elif tipe == 'mingguan':
        # Misal kita prediksi 10 minggu ke depan, atau sesuai data historis panjang?
        # Di sini kita tetapkan steps = 7 * 10, lalu agregasi per minggu.
        # Jika ingin hanya 45 hari ke depan: steps = 45, lalu n_weeks = ceil(45/7)
        steps = 45
        try:
            forecast = model_fit.forecast(steps=steps)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gagal forecast ARIMA: {e}")
        import math
        n_weeks = math.ceil(len(forecast) / 7)
        for w in range(n_weeks):
            chunk = forecast[w*7 : (w+1)*7]
            if len(chunk) == 0:
                break
            total = np.sum(chunk)
            karung = round(total / 50, 2)
            label.append(f"Minggu {w+1}")
            hasil.append(karung)

    elif tipe == 'bulanan':
        # Prediksi 2 bulan ke depan atau 45 hari: kita gunakan steps=45
        steps = 60  # atau 45; jika 45, maka bulan ke-1 (30 hari) dan bulan ke-2 (15 hari)
        try:
            forecast = model_fit.forecast(steps=steps)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gagal forecast ARIMA: {e}")
        import math
        # Asumsi 1 bulan = 30 hari
        n_months = math.ceil(len(forecast) / 30)
        for m in range(n_months):
            chunk = forecast[m*30 : (m+1)*30]
            if len(chunk) == 0:
                break
            total = np.sum(chunk)
            karung = round(total / 50, 2)
            label.append(f"Bulan {m+1}")
            hasil.append(karung)

    elif tipe == 'periode':
        # Pertama, kumpulkan periode historis jika ada
        if df_data is None or 'Periode' not in df_data.columns or 'Pakan_Pakai' not in df_data.columns:
            raise HTTPException(status_code=500, detail="Data historis kolom 'Periode'/'Pakan_Pakai' tidak tersedia untuk tipe 'periode'.")
        # Hitung total pakan per periode historis:
        try:
            grp = df_data.groupby('Periode')['Pakan_Pakai'].sum().reset_index()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gagal aggregate historis: {e}")
        # Simpan historis ke hasil
        for _, row in grp.iterrows():
            periode_num = int(row['Periode'])
            total = row['Pakan_Pakai']
            karung = round(total / 50, 2)
            label.append(f"Periode {periode_num}")
            hasil.append(karung)
        # Prediksi periode ke depan: gunakan durasi rata-rata periode historis
        last_periode = int(grp['Periode'].max()) if not grp.empty else 0
        durasi = rata_rata_umur_per_periode.get('durasi', 45)
        # Forecast total hari ke depan = durasi * max_periode_ke_depan
        steps = durasi * max_periode_ke_depan
        try:
            forecast = model_fit.forecast(steps=steps)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gagal forecast ARIMA: {e}")
        # Bagi ke blok durasi
        for i in range(max_periode_ke_depan):
            chunk = forecast[i*durasi : (i+1)*durasi]
            if len(chunk) == 0:
                break
            total = np.sum(chunk)
            karung = round(total / 50, 2)
            label.append(f"Periode {last_periode + i + 1}")
            hasil.append(karung)

    else:
        raise HTTPException(status_code=400, detail="Tipe prediksi tidak dikenali. Pilihan: harian, mingguan, bulanan, periode.")

    return {
        "periode": label,
        "hasil": hasil,
        "keterangan": "Satuan: total pakan dalam karung (1 karung = 50 kg). Label menunjukkan periode/hari ke-n prediksi."
    }
