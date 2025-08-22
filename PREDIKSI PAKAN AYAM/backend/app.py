# --- Warnings ---
import pathlib
import warnings
from pydantic import BaseModel
from statsmodels.tools.sm_exceptions import ValueWarning

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=ValueWarning)
warnings.filterwarnings("ignore")  # Hati-hati, ini menonaktifkan semua peringatan

# --- Standard Library ---
import os
import io
import csv
import math
import json
import uuid
import hashlib
import traceback
from datetime import date, datetime, timedelta
from typing import List, Optional
import secrets

# --- Third-party Libraries ---
import jwt
import pandas as pd
import numpy as np
from pmdarima import auto_arima
from xhtml2pdf import pisa

# --- FastAPI Related ---
from fastapi import (
    FastAPI, Form, Request, UploadFile, File, Depends, HTTPException, Header, Body, Path
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer

# --- Local Modules ---
from auth import router as auth_router
from database import get_db_connection

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

#=================
# class datapakan
#=================
class DataPakan(BaseModel):
    tanggal_mulai: str
    tanggal_selesai: str
    jumlah_ayam_awal: int
    file_id: str = None

data_pakan_list: List[dict] = []

CSV_PATH = "data/data_pakan_ayam.csv"
DATA_DIR = "uploaded_csv"
META_FILE = "metadata.json"

file_storage = []

if os.path.exists(META_FILE):
    with open(META_FILE, "r") as f:
        file_storage = json.load(f)

# ----------------------------
# Fungsi save_metadata ditambahkan di sini
# ----------------------------
def save_metadata():
    os.makedirs(DATA_DIR, exist_ok=True)  # pastikan folder ada
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(file_storage, f, ensure_ascii=False, indent=2)

# Tentukan folder static hasil build Vue=
static_dir = os.path.join(os.path.dirname(__file__), "static")

# Mount static folder
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/api/ping")
def ping():
    return {"msg": "pong"}


# JWT Config
SECRET_KEY = os.environ.get("SECRET_KEY", "ini_kunci_rahasia_default")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# Schemas
class RegisterSchema(BaseModel):
    name: str
    email: str
    password: str

class LoginSchema(BaseModel):
    email: str
    password: str

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Dependency Cek User
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("user_id") is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        # Kembalikan full payload dari DB
        return payload  # misal: {"id": 1, "name": "Raisya", "email": "...", "role": "user"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token sudah kadaluarsa, silakan login lagi")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token tidak valid")
    
#========================
# Endpoint Register Akun
#========================
@app.post("/api/register")
def register(data: RegisterSchema):
    if len(data.password) != 8:
        raise HTTPException(status_code=400, detail="Password harus 8 karakter")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # cek email sudah ada?
    cursor.execute("SELECT * FROM users WHERE email=%s", (data.email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")

    # simpan password langsung, tanpa hash
    cursor.execute(
        "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
        (data.name, data.email, data.password, "user")  # langsung simpan 8 karakter
    )
    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "User berhasil didaftarkan!"}

#=====================
# Endpoint Login Akun
#=====================
@app.post("/api/login")
def login(data: LoginSchema):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (data.email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Email tidak ditemukan")
    if user['password'] != data.password:
        raise HTTPException(status_code=401, detail="Password salah")

    token = create_access_token(
        data={"user_id": user["id"], "role": user["role"]},
        expires_delta=timedelta(hours=1)
    )

    return {
        "access_token": token,
        "role": user["role"],
        "name": user["name"]
    }

#=====================
# Endpoint Dashboard 
#=====================
@app.get("/api/dashboard")
def dashboard(user: dict = Depends(get_current_user)):
    return {"msg": "Ini halaman dashboard", "user_id": user["user_id"], "role": user["role"]}

#===========================
# Endpoint Admin Dashboard
#===========================
@app.get("/api/admin/dashboard")
def admin_dashboard(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Hanya admin yang bisa akses")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # jumlah riwayat
    cursor.execute("SELECT COUNT(*) AS total FROM riwayat")
    riwayat_count = cursor.fetchone()["total"]

    # jumlah user
    cursor.execute("SELECT COUNT(*) AS total FROM users")
    users_count = cursor.fetchone()["total"]

#============================================
# Ambil semua user (admin only) table users
#============================================
@app.get("/api/admin/users")
def get_users(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Hanya admin yang bisa mengakses")
    conn = cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email, role FROM users ORDER BY id ASC")
        users = cursor.fetchall()
        return {"users": users}  # <-- dibungkus di object
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

#===========================================
# Update role user (admin only) table users
#===========================================
@app.put("/api/admin/users/{user_id}")
def update_user_role(user_id: int, payload: dict, user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Hanya admin yang bisa mengakses")
    new_role = payload.get("role")
    if new_role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Role tidak valid")

    conn = cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET role = %s WHERE id = %s", (new_role, user_id))
        conn.commit()
        return {"message": "Role berhasil diperbarui"}
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

#======================================
# Hapus user (admin only) table users
#======================================
@app.delete("/api/admin/users/{user_id}")
def delete_user(user_id: int, user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Hanya admin yang bisa mengakses")

    conn = cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        return {"message": "User berhasil dihapus"}
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

#========================
# Endpoint Admin Riwayat
#========================
@app.get("/api/admin/riwayat")
def get_admin_riwayat(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Hanya admin yang bisa mengakses")

    conn = cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT r.*, u.name AS user_name
            FROM riwayat r
            JOIN users u ON r.user_id = u.id
            ORDER BY r.created_at DESC
        """)
        data = cursor.fetchall()
        return {"data": data}  # tetap 'data' supaya Vue bisa baca
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

#===============================
# Endpoint Admin Riwayat detail
#===============================
@app.get("/api/admin/riwayat/{id}/detail")
def get_admin_riwayat_detail(id: int, user=Depends(get_current_user)):
    import json
    from datetime import datetime
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM riwayat WHERE id = %s", (id,))
        row = cursor.fetchone()

        if not row:
            return {"error": "Riwayat tidak ditemukan"}

        # Konversi tanggal ke datetime
        tanggal_mulai = row["tanggal_mulai"]
        tanggal_selesai = row["tanggal_selesai"]
        tgl_mulai_dt = datetime.combine(tanggal_mulai, datetime.min.time()) if tanggal_mulai else None
        tgl_selesai_dt = datetime.combine(tanggal_selesai, datetime.min.time()) if tanggal_selesai else None

        # Parse JSON
        try:
            pred_list_raw = json.loads(row.get("prediksi", "[]"))
        except:
            pred_list_raw = []

        try:
            aktual_raw = json.loads(row.get("data_aktual", "[]"))
        except:
            aktual_raw = []

        # Filter prediksi sesuai durasi
        prediksi = []
        total_kg = total_karung = total_per_ayam = 0
        for p in pred_list_raw:
            try:
                x_dt = datetime.fromisoformat(p.get("x", "").split("T")[0])
            except:
                continue
            if tgl_mulai_dt and tgl_selesai_dt and not (tgl_mulai_dt <= x_dt <= tgl_selesai_dt):
                continue

            kg = p.get("kg", 0) or 0
            y_val = p.get("y", kg) or 0
            per_ayam_val = p.get("per_ayam", 0) or 0
            ayam_hidup_val = p.get("ayam_hidup", 0) or 0
            prediksi.append({
                "x": x_dt.strftime("%Y-%m-%d"),
                "y": y_val,
                "kg": kg,
                "ayam_hidup": ayam_hidup_val,
                "per_ayam": per_ayam_val,
                "periode": p.get("periode")
            })
            total_kg += kg
            total_karung += math.ceil(kg / 50)
            total_per_ayam += per_ayam_val

        # Filter data aktual sesuai durasi
        data_aktual = []
        for a in aktual_raw:
            try:
                x_raw = a.get("x", "")
                x_dt = datetime.fromisoformat(x_raw.split("T")[0]) if x_raw else None
            except:
                x_dt = None

            if tgl_mulai_dt and tgl_selesai_dt and x_dt and not (tgl_mulai_dt <= x_dt <= tgl_selesai_dt):
                continue

            kg_val = a.get("kg") or a.get("y") or 0
            data_aktual.append({
                "x": x_dt.strftime("%Y-%m-%d") if x_dt else "",
                "y": kg_val,
                "kg": kg_val,
                "periode": a.get("periode")
            })

        # Sortir berdasarkan tanggal
        prediksi.sort(key=lambda p: p["x"])
        data_aktual.sort(key=lambda a: a["x"])

        # Hitung MAPE
        mape = None
        if prediksi and data_aktual:
            mapes = []
            aktual_dict = {d["x"]: d["kg"] for d in data_aktual}
            for p in prediksi:
                if p["x"] in aktual_dict and aktual_dict[p["x"]] != 0:
                    mapes.append(abs(p["kg"] - aktual_dict[p["x"]]) / aktual_dict[p["x"]])
            if mapes:
                mape = round(sum(mapes) / len(mapes) * 100, 2)

        # Tentukan mode prediksi
        mode_prediksi = row.get("mode_prediksi", "per_ayam")  # pastikan ada field mode_prediksi di table

        # Summary
        hari = row.get("durasi", len(prediksi))
        if mode_prediksi == "per_ayam":
            jumlah_ayam_awal = row.get("jumlah_ayam_awal", 0)  # ambil dari kolom DB
            perkiraan_akhir_ayam = prediksi[-1].get("ayam_hidup", 0) if prediksi else 0
        else:  # per_periode
            jumlah_ayam_awal = None
            perkiraan_akhir_ayam = None


        rata_per_ayam_kg_per_hari = round(total_per_ayam / hari, 4) if hari > 0 else 0

        summary = {
            "total_prediksi_kg": total_kg,
            "total_prediksi_karung": total_karung,
            "rata_per_ayam_kg_per_hari": rata_per_ayam_kg_per_hari,
            "jumlah_ayam_awal": jumlah_ayam_awal,
            "perkiraan_akhir_ayam": perkiraan_akhir_ayam,
            "durasi_hari": hari,
            "mape": mape,
            "catatan": row.get("catatan", "")
        }

        response = {
            "id": row["id"],
            "tanggal_mulai": tanggal_mulai.strftime("%Y-%m-%d") if tanggal_mulai else None,
            "tanggal_selesai": tanggal_selesai.strftime("%Y-%m-%d") if tanggal_selesai else None,
            "durasi": hari,
            "prediksi": prediksi,
            "data_aktual": data_aktual,
            "summary": summary,
            "nama_file": row.get("nama_file"),
            "asal_data": row.get("asal_data"),
            "user_id": row.get("user_id")  # bisa diganti join ke user table kalau mau nama
        }

        return response

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

#===============================
# Endpoint admin hapus riwayat 
#===============================
@app.delete("/api/admin/riwayat/{riwayat_id}")
def delete_admin_riwayat(riwayat_id: int, user=Depends(get_current_user)):
    conn = cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Cek dulu apakah riwayat ada
        cursor.execute("SELECT id FROM riwayat WHERE id = %s", (riwayat_id,))
        row = cursor.fetchone()
        if not row:
            return {"error": "Riwayat tidak ditemukan"}
        
        # Hapus riwayat
        cursor.execute("DELETE FROM riwayat WHERE id = %s", (riwayat_id,))
        conn.commit()
        return {"message": "Riwayat berhasil dihapus"}

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ===============================
# Fungsi sanitize JSON
# ===============================
def sanitize_json(obj):
    """Konversi semua value jadi tipe yang aman untuk JSON/MySQL"""
    if isinstance(obj, dict):
        return {k: sanitize_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_json(i) for i in obj]
    elif isinstance(obj, (int, float, str)) or obj is None:
        return obj
    else:
        return str(obj)

def get_db_connection():
    import mysql.connector
    return mysql.connector.connect(
        host="localhost", user="root", password="", database="prediksi_db"
    )

# ===============
# Simpan riwayat 
# ===============
@app.post("/riwayat")
async def simpan_riwayat(data: dict, current_user: dict = Depends(get_current_user)):
    import traceback, math, json
    from datetime import datetime
    conn = cursor = None
    try:
        current_user_id = current_user.get("user_id")
        if not current_user_id:
            raise HTTPException(status_code=401, detail="User tidak valid")

        prediksi_list = data.get("prediksi", [])
        aktual_list = data.get("data_aktual", [])
        mode_prediksi = data.get("mode_prediksi", "per_ayam")
        asal_data = data.get("asal_data") or "Default"
        nama_file = data.get("nama_file") or "Default"

        # --- Jumlah ayam awal hanya dipakai per_ayam ---
        jumlah_ayam_awal_input = int(data.get("jumlah_ayam_awal") or 0)
        if mode_prediksi == "per_ayam" and jumlah_ayam_awal_input <= 0:
            # jika input kosong, ambil dari prediksi_list (fallback)
            jumlah_ayam_awal_input = max(
                [int(p.get("ayam_hidup", 0)) for p in prediksi_list if isinstance(p, dict)],
                default=0
            )
        if mode_prediksi == "per_ayam" and jumlah_ayam_awal_input <= 0:
            raise HTTPException(status_code=400, detail="Jumlah ayam awal harus diisi untuk mode per_ayam")

        # --- Validasi tanggal ---
        tanggal_mulai = datetime.fromisoformat(data.get("tanggal_mulai"))
        tanggal_selesai = datetime.fromisoformat(data.get("tanggal_selesai"))
        durasi = (tanggal_selesai - tanggal_mulai).days + 1

        # --- Standarisasi prediksi dengan skip kg <= 0 ---
        standar_prediksi = []
        for p in prediksi_list:
            if isinstance(p, dict):
                if mode_prediksi == "per_ayam":
                    per_ayam = float(p.get("per_ayam", 0))
                    ayam_hidup = int(p.get("ayam_hidup", jumlah_ayam_awal_input))
                    kg = per_ayam * ayam_hidup
                else:  # per_periode
                    per_ayam = None
                    ayam_hidup = None
                    kg = float(p.get("kg") or p.get("y") or 0)
                if kg <= 0:
                    continue
                x = p.get("x") or p.get("date") or "-"
                periode = p.get("periode")
            else:
                if mode_prediksi == "per_ayam":
                    per_ayam = float(p)
                    ayam_hidup = jumlah_ayam_awal_input
                    kg = per_ayam * ayam_hidup
                else:
                    per_ayam = None
                    ayam_hidup = None
                    kg = float(p if p is not None else 0.0)
                if kg <= 0:
                    continue
                x = "-"
                periode = None

            standar_prediksi.append({
                "x": x,
                "y": kg,
                "kg": kg,
                "ayam_hidup": ayam_hidup,
                "per_ayam": per_ayam,
                "periode": periode
            })

        # --- Standarisasi data aktual dengan skip kg <= 0 ---
        standar_aktual = []
        for a in aktual_list:
            if isinstance(a, dict):
                raw_kg = a.get("kg") or a.get("y") or a.get("stok") or 0
                kg = float(raw_kg) if raw_kg is not None else 0.0
                if kg <= 0:
                    continue
                x = a.get("x") or a.get("date") or "-"
                periode = a.get("periode")
            else:
                kg = float(a) if a is not None else 0.0
                if kg <= 0:
                    continue
                x = "-"
                periode = None

            standar_aktual.append({
                "x": x,
                "y": kg,
                "kg": kg,
                "periode": periode
            })

        # --- Pastikan prediksi ada sebelum insert ---
        if not standar_prediksi:
            raise HTTPException(status_code=400, detail="Prediksi kosong, tidak bisa disimpan")

        # --- Hitung total pakan dan total karung ---
        total_pakan = sum([p["kg"] for p in standar_prediksi])
        total_karung = math.ceil(total_pakan / 50)
        total_pakan = float(total_pakan)
        total_karung = int(total_karung)

        # --- Gunakan input user untuk jumlah ayam awal di DB (None untuk per_periode) ---
        jumlah_ayam_awal_db = jumlah_ayam_awal_input if mode_prediksi == "per_ayam" else None

        # --- Simpan ke DB ---
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)

        activity = data.get("activity") or "Prediksi disimpan"
        mape = data.get("mape") or None

        cursor.execute(
            """
            INSERT INTO riwayat
            (user_id, tanggal_mulai, tanggal_selesai, durasi, prediksi, data_aktual,
            total_pakan_kg, total_karung, mode_prediksi, jumlah_ayam_awal, activity,
            mape, asal_data, nama_file, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """,
            (
                current_user_id,
                tanggal_mulai.strftime("%Y-%m-%d"),
                tanggal_selesai.strftime("%Y-%m-%d"),
                durasi,
                json.dumps(standar_prediksi),
                json.dumps(standar_aktual),
                total_pakan,
                total_karung,
                mode_prediksi,
                jumlah_ayam_awal_db,
                activity,
                mape,
                asal_data,
                nama_file
            )
        )

        riwayat_id = cursor.lastrowid
        conn.commit()

        print(f"✅ Riwayat ID {riwayat_id} berhasil disimpan!")

        return {"message": "Riwayat berhasil disimpan", "riwayat_id": riwayat_id}

    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ========================
# Ambil semua riwayat user 
# ========================
@app.get("/riwayat")
async def get_riwayat(current_user: dict = Depends(get_current_user)):
    import json, math

    conn = cursor = None
    try:
        current_user_id = current_user.get("user_id")
        if not current_user_id:
            return {"riwayat": []}

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM riwayat WHERE user_id=%s ORDER BY id DESC",
            (current_user_id,)
        )
        rows = cursor.fetchall()

        result = []
        for row in rows:
            # --- Prediksi & data aktual ---
            try:
                prediksi = json.loads(row.get("prediksi") or "[]")
            except:
                prediksi = []

            try:
                data_aktual = json.loads(row.get("data_aktual") or "[]")
            except:
                data_aktual = []

            # --- Total pakan & total karung ---
            total_pakan = float(row.get("total_pakan_kg") or 0)
            if total_pakan <= 0:
                jumlah_ayam_awal_db = row.get("jumlah_ayam_awal") or 1
                if row.get("mode_prediksi") == "per_ayam":
                    total_pakan = sum([
                        float(p.get("per_ayam", 0)) * max(int(p.get("ayam_hidup", jumlah_ayam_awal_db)), 1)
                        for p in prediksi
                    ])
                else:
                    total_pakan = sum([
                        float(p.get("kg", p.get("y", 0))) for p in prediksi
                    ])
            total_karung = float(math.ceil(total_pakan / 50))

            # --- MAPE ---
            mape = float(row.get("mape") or 0)

            # --- Asal data & nama file ---
            asal_data = row.get("asal_data") or "Default"
            nama_file = row.get("nama_file") or "Default"

            # --- Activity ---
            activity = row.get("activity") or f"Prediksi {row.get('mode_prediksi','-')} dari {row.get('tanggal_mulai','-')} sampai {row.get('tanggal_selesai','-')}"

            # --- Format tanggal ---
            tanggal_mulai = row.get("tanggal_mulai").strftime("%Y-%m-%d") if row.get("tanggal_mulai") else "-"
            tanggal_selesai = row.get("tanggal_selesai").strftime("%Y-%m-%d") if row.get("tanggal_selesai") else "-"
            created_at = row.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if row.get("created_at") else "-"
            updated_at = row.get("updated_at").strftime("%Y-%m-%d %H:%M:%S") if row.get("updated_at") else "-"

            # --- Perbaikan: tampilkan "-" jika jumlah_ayam_awal NULL untuk per_periode ---
            jumlah_ayam_awal_display = row.get("jumlah_ayam_awal")
            if jumlah_ayam_awal_display is None and row.get("mode_prediksi") == "per_periode":
                jumlah_ayam_awal_display = "-"
            elif jumlah_ayam_awal_display is None:
                jumlah_ayam_awal_display = 1

            result.append({
                "id": row["id"],
                "tanggal_mulai": tanggal_mulai,
                "tanggal_selesai": tanggal_selesai,
                "durasi": row.get("durasi") or 0,
                "mode_prediksi": row.get("mode_prediksi") or "-",
                "jumlah_ayam_awal": jumlah_ayam_awal_display,
                "prediksi": prediksi,
                "data_aktual": data_aktual,
                "total_pakan_kg": total_pakan,
                "total_karung": total_karung,
                "mape": mape,
                "asal_data": asal_data,
                "nama_file": nama_file,
                "activity": activity,
                "created_at": created_at,
                "updated_at": updated_at
            })

        return {"riwayat": result}

    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# =====================
# Ambil detail riwayat
# =====================
@app.get("/riwayat/{id}/detail")
async def get_riwayat_detail(id: int, current_user: dict = Depends(get_current_user)):
    import json, math
    from fastapi.responses import JSONResponse

    conn = cursor = None
    try:
        current_user_id = current_user.get("user_id")
        if not current_user_id:
            return JSONResponse(status_code=401, content={"error": "User tidak valid"})

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM riwayat WHERE id=%s AND user_id=%s", (id, current_user_id))
        row = cursor.fetchone()
        if not row:
            return JSONResponse(status_code=404, content={"error": "Riwayat tidak ditemukan"})

        # --- Load prediksi & data aktual ---
        try:
            pred_list = json.loads(row.get("prediksi") or "[]")
        except:
            pred_list = []

        try:
            aktual_raw = json.loads(row.get("data_aktual") or "[]")
        except:
            aktual_raw = []

        mode_prediksi = row.get("mode_prediksi") or "-"
        jumlah_ayam_awal_db = row.get("jumlah_ayam_awal")
        # Pastikan jumlah ayam awal selalu integer minimal 1
        jumlah_ayam_awal = int(jumlah_ayam_awal_db) if jumlah_ayam_awal_db is not None else 1
        jumlah_ayam_awal_display = jumlah_ayam_awal if mode_prediksi == "per_ayam" else "-"

        durasi = row.get("durasi") or max(len(pred_list), 1)

        # --- Proses prediksi ---
        prediksi = []
        total_pakan = float(row.get("total_pakan_kg") or 0)
        total_per_ayam = 0

        if total_pakan <= 0:
            for p in pred_list:
                x_str = p.get("x") or "-"
                per_ayam = float(p.get("per_ayam") or 0)
                ayam_hidup = int(p.get("ayam_hidup") or jumlah_ayam_awal)
                kg = float(p.get("kg") or p.get("y") or per_ayam * ayam_hidup or 0)
                periode = p.get("periode")

                prediksi.append({
                    "x": x_str,
                    "y": kg,
                    "kg": kg,
                    "ayam_hidup": ayam_hidup,
                    "per_ayam": per_ayam,
                    "periode": periode
                })

                if mode_prediksi == "per_ayam":
                    total_pakan += per_ayam * max(ayam_hidup, 1)
                else:
                    total_pakan += kg
                total_per_ayam += per_ayam
        else:
            for p in pred_list:
                kg = float(p.get("kg") or p.get("y") or 0)
                per_ayam = float(p.get("per_ayam") or 0)
                ayam_hidup = int(p.get("ayam_hidup") or jumlah_ayam_awal)
                prediksi.append({
                    "x": p.get("x") or "-",
                    "y": kg,
                    "kg": kg,
                    "ayam_hidup": ayam_hidup,
                    "per_ayam": per_ayam,
                    "periode": p.get("periode")
                })
                total_per_ayam += per_ayam

        total_karung = float(math.ceil(total_pakan / 50))

        # --- Proses data aktual ---
        data_aktual = []
        for a in aktual_raw:
            x_str = a.get("x") or "-"
            kg = float(a.get("kg") or a.get("y") or a.get("stok") or a.get("jumlah_pakan") or 0)
            data_aktual.append({
                "x": x_str,
                "y": kg,
                "kg": kg,
                "periode": a.get("periode")
            })

        if not data_aktual and prediksi:
            for p in prediksi:
                data_aktual.append({
                    "x": p["x"],
                    "y": 0,
                    "kg": 0,
                    "periode": p.get("periode")
                })

        prediksi.sort(key=lambda p: p["x"])
        data_aktual.sort(key=lambda a: a["x"])

        # --- MAPE ---
        mape = 0
        if prediksi and data_aktual:
            aktual_dict = {d["x"]: d["kg"] for d in data_aktual if d["kg"] > 0}
            mapes = [
                abs(p["kg"] - aktual_dict[p["x"]]) / aktual_dict[p["x"]]
                for p in prediksi if p["x"] in aktual_dict and aktual_dict[p["x"]] != 0
            ]
            if mapes:
                mape = round(sum(mapes) / len(mapes) * 100, 2)

        # --- Summary ---
        jumlah_ayam_awal_real = prediksi[0]["ayam_hidup"] if prediksi else jumlah_ayam_awal
        perkiraan_akhir_ayam = prediksi[-1]["ayam_hidup"] if prediksi else jumlah_ayam_awal
        rata_per_ayam_kg_per_hari = round(total_per_ayam / durasi, 4) if durasi > 0 else 0

        summary = {
            "total_prediksi_kg": total_pakan,
            "total_prediksi_karung": total_karung,
            "rata_per_ayam_kg_per_hari": rata_per_ayam_kg_per_hari,
            "jumlah_ayam_awal": jumlah_ayam_awal_display,
            "perkiraan_akhir_ayam": perkiraan_akhir_ayam,
            "durasi_hari": durasi,
            "mape": mape,
            "catatan": row.get("catatan") or f"Mode prediksi {mode_prediksi} menggunakan input jumlah ayam awal ({jumlah_ayam_awal_display} ekor)."
        }

        # --- Response ---
        response = {
            "id": row["id"],
            "tanggal_mulai": row.get("tanggal_mulai").strftime("%Y-%m-%d") if row.get("tanggal_mulai") else "-",
            "tanggal_selesai": row.get("tanggal_selesai").strftime("%Y-%m-%d") if row.get("tanggal_selesai") else "-",
            "durasi": durasi,
            "mode_prediksi": mode_prediksi,
            "jumlah_ayam_awal": jumlah_ayam_awal_display,
            "prediksi": prediksi,
            "data_aktual": data_aktual,
            "summary": summary,
            "nama_file": row.get("nama_file") or "Default",
            "asal_data": row.get("asal_data") or "Default",
            "activity": row.get("activity") or f"Prediksi {mode_prediksi} dari {row.get('tanggal_mulai','-')} sampai {row.get('tanggal_selesai','-')}",
            "created_at": row.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if row.get("created_at") else "-",
            "updated_at": row.get("updated_at").strftime("%Y-%m-%d %H:%M:%S") if row.get("updated_at") else "-"
        }

        return JSONResponse(content=response)

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

#=======================
# delete riwayat (user)
#========================
@app.delete("/riwayat")
async def hapus_semua_riwayat(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User tidak valid")

    conn = cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM riwayat WHERE user_id=%s", (user_id,))
        conn.commit()
        return {"message": "Semua data riwayat Anda berhasil dihapus"}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# =========================================
# Hapus riwayat tertentu milik user (user)
# =========================================
@app.delete("/riwayat/{riwayat_id}")
async def hapus_riwayat(
    riwayat_id: int = Path(..., description="ID riwayat yang ingin dihapus"),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User tidak valid")

    conn = cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM riwayat WHERE id=%s AND user_id=%s",
            (riwayat_id, user_id)
        )
        conn.commit()

        if cursor.rowcount == 0:
            return JSONResponse(
                status_code=404,
                content={"message": "Riwayat tidak ditemukan atau bukan milik Anda"}
            )

        return {"message": f"Data riwayat {riwayat_id} berhasil dihapus"}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            



def simpan_riwayat(user_id, tanggal_mulai, durasi, jumlah_ayam_awal, hasil_prediksi):
    try:
        total_karung = sum([item.get("y", 0) for item in hasil_prediksi])
        total_kg = sum([item.get("kg", 0) for item in hasil_prediksi])

        # --- LOG ---
        print("=== INFO simpan_riwayat ===")
        print(f"Jumlah data prediksi: {len(hasil_prediksi)}")
        print(f"Jumlah ayam awal: {jumlah_ayam_awal}")
        print(f"Durasi (hari): {durasi}")
        print(f"Total pakan (kg): {total_kg}")
        print(f"Total karung: {total_karung}")
        print("============================")

        conn = get_db_connection()
        with conn.cursor(buffered=True) as cursor:
            sql = """
                INSERT INTO riwayat (
                    user_id, tanggal_mulai, tanggal_selesai, durasi, prediksi, total_karung
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            val = (
                user_id,
                tanggal_mulai.strftime("%Y-%m-%d"),
                (tanggal_mulai + timedelta(days=durasi-1)).strftime("%Y-%m-%d"),
                durasi,
                json.dumps(hasil_prediksi),
                total_karung
            )
            cursor.execute(sql, val)
            conn.commit()

        conn.close()
        return True

    except Exception as e:
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.close()
        return False

def load_data(file_id=None):
    print("load_data dipanggil dengan file_id:", file_id)
    
    if not file_id or file_id == "default":
        file_path = CSV_PATH  # pakai data/data_pakan_ayam.csv
    else:
        file_path = os.path.join(DATA_DIR, str(file_id) + ".csv")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File data CSV '{file_path}' tidak ditemukan.")

    df_raw = pd.read_csv(file_path)
    df = df_raw.copy()
    df.rename(columns=lambda x: x.strip().lower(), inplace=True)

    # Ganti nama bulan dari Indonesia ke English
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

    df.dropna(subset=['tanggal', 'pakan_pakai', 'jumlah_ayam', 'jumlah_ayam_mati'], inplace=True)
    df.sort_values('tanggal', inplace=True)
    df.reset_index(drop=True, inplace=True)

    if 'periode' in df.columns:
        df['periode'] = df['periode'].replace(["", "nan", "NaN", "None"], np.nan)

        print(f"load_data: {len(df)} baris valid dari {file_path}")
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

def hitung_mape_kg(prediksi, aktual):
    """
    prediksi dan aktual adalah list dict dengan key 'kg'
    MAPE = rata-rata |prediksi - aktual| / aktual * 100
    """
    if not prediksi or not aktual:
        return 0.0

    # pastikan tanggal sama
    tanggal_prediksi = {p['x']: p['kg'] for p in prediksi}
    tanggal_aktual = {a['x']: a['kg'] for a in aktual}

    common_dates = set(tanggal_prediksi.keys()) & set(tanggal_aktual.keys())
    if not common_dates:
        return 0.0

    error_sum = 0
    n = 0
    for t in common_dates:
        actual_val = tanggal_aktual[t]
        if actual_val == 0:
            continue
        error_sum += abs(tanggal_prediksi[t] - actual_val) / actual_val
        n += 1

    if n == 0:
        return 0.0

    return round((error_sum / n) * 100, 2)

#==============================
# Mencari Model Arima Terbaik
#==============================
def train_arima(series):
    if len(series) < 10 or series.nunique() <= 1:
        raise ValueError("Data tidak cukup atau terlalu seragam untuk ARIMA.")
    
    # Pastikan index datetime
    if not isinstance(series.index, pd.DatetimeIndex):
        series.index = pd.date_range(start=pd.Timestamp.today(), periods=len(series), freq='D')
    
    model = auto_arima(
        series,
        seasonal=False,
        stepwise=True,
        suppress_warnings=True,
        error_action='ignore'
    )
    return model

# =======================
# FITUR DATA PAKAN (user)
# =======================
DATA_DIR = "data/uploaded_csv" 
os.makedirs(DATA_DIR, exist_ok=True)

# ==============================
# Upload CSV
# ==============================
@app.post("/upload_csv")
async def upload_csv(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    # validasi ekstensi
    if not file.filename.lower().endswith(".csv"):
        return JSONResponse(status_code=400, content={"error": "Hanya file CSV yang diperbolehkan"})

    # normalisasi nama file agar aman
    filename = pathlib.Path(file.filename.strip()).name

    # cek nama file sudah ada untuk user
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT COUNT(*) AS count FROM data_pakan WHERE user_id=%s AND nama_file=%s",
        (current_user["user_id"], filename)
    )
    result = cursor.fetchone()
    if result.get("count", 0) > 0:
        cursor.close()
        conn.close()
        return JSONResponse(status_code=400, content={"error": f"Nama file '{filename}' sudah ada, gunakan file lain"})

    # simpan file fisik
    try:
        file_path = os.path.join(DATA_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Gagal menyimpan file: {str(e)}"})

    # simpan metadata ke db
    try:
        cursor.execute("""
            INSERT INTO data_pakan (user_id, tanggal, nama_file)
            VALUES (%s, %s, %s)
        """, (current_user["user_id"], date.today(), filename))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        cursor.close()
        conn.close()

    return {"status": "sukses", "nama_file": filename}

# ===========================
# List CSV di fitur data pakan
# ===========================
@app.get("/list_csv_files")
async def list_csv_files(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, nama_file, tanggal, created_at
        FROM data_pakan
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (current_user["user_id"],))
    files = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"files": files}

# ==============================
# Update CSV
# ==============================
@app.put("/update_csv/{file_id}")
async def update_csv(file_id: int, file: UploadFile = File(None), current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # ambil data lama
        cursor.execute(
            "SELECT nama_file FROM data_pakan WHERE id=%s AND user_id=%s",
            (file_id, current_user["user_id"])
        )
        row = cursor.fetchone()
        if not row:
            return JSONResponse(status_code=404, content={"error": "Data tidak ditemukan"})

        old_filename = row["nama_file"]

        if file:
            # validasi ekstensi CSV
            if not file.filename.lower().endswith(".csv"):
                return JSONResponse(status_code=400, content={"error": "Hanya file CSV yang diperbolehkan"})

            new_filename = pathlib.Path(file.filename.strip()).name

            # cek duplikat nama file
            cursor.execute(
                "SELECT COUNT(*) AS count FROM data_pakan WHERE user_id=%s AND nama_file=%s AND id != %s",
                (current_user["user_id"], new_filename, file_id)
            )
            result = cursor.fetchone()
            if result.get("count", 0) > 0:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Nama file '{new_filename}' sudah ada, gunakan file lain"}
                )

            # hapus file lama jika ada
            old_path = os.path.join(DATA_DIR, old_filename)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception as e:
                    print(f"WARNING: gagal hapus file lama: {e}")

            # simpan file baru
            try:
                file_path = os.path.join(DATA_DIR, new_filename)
                with open(file_path, "wb") as f:
                    f.write(await file.read())
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": f"Gagal menyimpan file baru: {str(e)}"})

            # update database
            cursor.execute("""
                UPDATE data_pakan
                SET nama_file=%s
                WHERE id=%s AND user_id=%s
            """, (new_filename, file_id, current_user["user_id"]))
            conn.commit()

            return {"status": "sukses", "nama_file": new_filename}

        # jika tidak ada file baru, return data lama
        return {"status": "tidak ada perubahan", "nama_file": old_filename}

    finally:
        cursor.close()
        conn.close()

#===============================
# Delete CSV di fitur data pakan
#===============================
@app.delete("/delete_csv/{nama_file}")
async def delete_csv(nama_file: str, current_user: dict = Depends(get_current_user)):
    file_path = os.path.join(DATA_DIR, nama_file)
    if os.path.exists(file_path):
        os.remove(file_path)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM data_pakan
        WHERE user_id = %s AND nama_file = %s
    """, (current_user["user_id"], nama_file))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "Berhasil dihapus"}

#===========================================
# Download TEMPLATE CSV DI FITIR DATA PAKAN
#===========================================
@app.get("/download_csv/{nama_file}")
async def download_csv(nama_file: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT tanggal, pakan_kg, ayam_awal, ayam_akhir 
        FROM data_pakan
        WHERE user_id=%s AND nama_file=%s
    """, (user_id, nama_file))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        return JSONResponse(status_code=404, content={"error": "File tidak ditemukan"})

    df = pd.DataFrame(rows)
    file_path = os.path.join(DATA_DIR, f"{nama_file}_{user_id}.csv")
    df.to_csv(file_path, index=False)
    return FileResponse(file_path, filename=f"{nama_file}.csv", media_type="text/csv")

#================================
#  ENDPOINT PREDIKSI PER PERIODE
#================================
@app.post("/predict_periode")
async def predict_periode(request: Request, current_user: dict = Depends(get_current_user)):
    import traceback, math, json
    from datetime import datetime, timedelta
    import pandas as pd
    import numpy as np
    from fastapi.responses import JSONResponse

    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User tidak valid")

        body = await request.json()
        tanggal_mulai_str = body.get("tanggal_mulai")
        tanggal_selesai_str = body.get("tanggal_selesai")
        file_id = body.get("file_id")
        asal_data = body.get("asal_data", "Default")
        nama_file = body.get("nama_file", "Default")
        mode = "per_periode"

        if not tanggal_mulai_str or not tanggal_selesai_str:
            return JSONResponse(status_code=400, content={"error": "Tanggal mulai dan selesai wajib diisi"})

        tanggal_mulai = datetime.strptime(tanggal_mulai_str, "%Y-%m-%d")
        tanggal_selesai = datetime.strptime(tanggal_selesai_str, "%Y-%m-%d")
        n_periods = (tanggal_selesai - tanggal_mulai).days + 1

        # --- Load CSV ---
        df = load_data(file_id=file_id)
        if df.empty:
            return JSONResponse(status_code=400, content={"error": "Data CSV kosong"})
        df['tanggal'] = pd.to_datetime(df['tanggal'])
        df = df.set_index('tanggal').sort_index()
        df_train = df[df.index < tanggal_mulai].copy()
        if df_train.empty or len(df_train["pakan_pakai"]) < 10:
            return JSONResponse(status_code=400, content={"error": "Data tidak cukup untuk pelatihan model."})

        # --- Train ARIMA ---
        try:
            model = train_arima(df_train["pakan_pakai"])
            forecast = np.array(model.predict(n_periods=n_periods))
        except Exception as e:
            print("WARNING: ARIMA gagal, pakai rata-rata pakan", e)
            mean_value = df_train["pakan_pakai"].mean()
            forecast = np.full(n_periods, mean_value)

        # --- Data prediksi ---
        tanggal_prediksi = [tanggal_mulai + timedelta(days=i) for i in range(n_periods)]
        data_prediksi = []
        total_pakan = 0.0
        for t, p in zip(tanggal_prediksi, forecast):
            kg = round(float(p), 2) if not pd.isna(p) else 0.0
            data_prediksi.append({"x": t.strftime("%Y-%m-%d"), "kg": kg, "y": kg, "periode": None})
            total_pakan += kg

        total_karung = math.ceil(total_pakan / 50)

        # --- Mode per_periode tidak ada jumlah ayam ---
        jumlah_ayam_awal = None
        konsumsi_harian_per_ekor = None

        # --- Data aktual ---
        semua_data_aktual = []
        for idx, row in df.iterrows():
            pakan_kg = round(float(row['pakan_pakai']), 2) if 'pakan_pakai' in row else 0.0
            semua_data_aktual.append({
                "x": idx.strftime("%Y-%m-%d"),
                "kg": pakan_kg,
                "y": pakan_kg,
                "periode": int(row['periode']) if 'periode' in row and pd.notna(row['periode']) else None
            })

        catatan = (
            "Mode prediksi per periode tidak menggunakan input jumlah ayam.\n"
            "Pastikan pakan tersedia cukup untuk seluruh periode.\n"
            "Periksa fluktuasi pakan per hari untuk menghindari kekurangan."
        )

        # --- Print debug terminal ---
        print("=== PREDIKSI PERIODE ===")
        print(f"User ID: {user_id}")
        print(f"Tanggal mulai: {tanggal_mulai_str}")
        print(f"Tanggal selesai: {tanggal_selesai_str}")
        print(f"Jumlah data aktual: {len(semua_data_aktual)}")
        print(f"Jumlah data prediksi: {len(data_prediksi)}")
        print(f"ARIMA PDQ yang digunakan: {getattr(model, 'order', None)}")
        print(f"Durasi (hari): {n_periods}")
        print(f"Total Pakan (kg): {round(total_pakan,2)} kg")
        print(f"Total Karung (50kg): {total_karung} karung")
        print("Catatan:")
        print(catatan)
        print("====================")

        # --- Simpan/update ke DB ---
        riwayat_id = None
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM riwayat WHERE user_id=%s AND tanggal_mulai=%s AND tanggal_selesai=%s AND mode_prediksi=%s",
                    (user_id, tanggal_mulai_str, tanggal_selesai_str, mode)
                )
                existing = cursor.fetchone()
                if existing:
                    riwayat_id = existing[0]
                    cursor.execute(
                        """
                        UPDATE riwayat SET
                            prediksi=%s,
                            data_aktual=%s,
                            total_pakan_kg=%s,
                            total_karung=%s,
                            mode_prediksi=%s,
                            asal_data=%s,
                            nama_file=%s,
                            activity=%s,
                            mape=%s,
                            updated_at=NOW()
                        WHERE id=%s
                        """,
                        (
                            json.dumps(data_prediksi),
                            json.dumps(semua_data_aktual),
                            round(total_pakan,2),
                            total_karung,
                            mode,
                            asal_data,
                            nama_file,
                            f"Prediksi {mode} dari {tanggal_mulai_str} sampai {tanggal_selesai_str}",
                            0,
                            riwayat_id
                        )
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO riwayat
                        (user_id, tanggal_mulai, tanggal_selesai, durasi, jumlah_ayam_awal,
                         mode_prediksi, prediksi, data_aktual, total_pakan_kg, total_karung,
                         asal_data, nama_file, activity, mape, created_at, updated_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())
                        """,
                        (
                            user_id,
                            tanggal_mulai_str,
                            tanggal_selesai_str,
                            n_periods,
                            jumlah_ayam_awal,  # tetap None untuk per_periode
                            mode,
                            json.dumps(data_prediksi),
                            json.dumps(semua_data_aktual),
                            round(total_pakan,2),
                            total_karung,
                            asal_data,
                            nama_file,
                            f"Prediksi {mode} dari {tanggal_mulai_str} sampai {tanggal_selesai_str}",
                            0
                        )
                    )
                    riwayat_id = cursor.lastrowid
                conn.commit()
        finally:
            conn.close()

        summary = {
            "total_prediksi_kg": round(total_pakan,2),
            "total_prediksi_karung": total_karung,
            "jumlah_ayam_awal": None,  # tampil "-" di frontend
            "durasi_hari": n_periods,
            "konsumsi_harian_per_ekor": None,
            "catatan": catatan
        }

        return JSONResponse({
            "data_prediksi": data_prediksi,
            "data_aktual": semua_data_aktual,
            "summary": summary,
            "riwayat_id": riwayat_id
        })

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

#===========================
# ENDPOINT PREDIKSI PER AYAM
#===========================
@app.post("/predict_per_ayam")
async def predict_per_ayam(request: Request, data: DataPakan, current_user: dict = Depends(get_current_user)):
    try:
        # --- Validasi user ---
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User tidak valid")

        # --- Tanggal & hari ---
        tanggal_mulai = datetime.strptime(data.tanggal_mulai, "%Y-%m-%d")
        tanggal_selesai = datetime.strptime(getattr(data, "tanggal_selesai", data.tanggal_mulai), "%Y-%m-%d")
        hari = max((tanggal_selesai - tanggal_mulai).days + 1, 1)
        jumlah_ayam_awal = max(int(data.jumlah_ayam_awal or 1), 1)
        file_id = getattr(data, "file_id", None)
        mode = "per_ayam"
        asal_data = getattr(data, "asal_data", "Default")
        nama_file = getattr(data, "nama_file", "Default")

        # --- Load CSV ---
        df = load_data(file_id=file_id)
        if df.empty:
            return JSONResponse(status_code=400, content={"error": "Data CSV kosong"})
        df['tanggal'] = pd.to_datetime(df['tanggal'])
        df = df.set_index('tanggal').sort_index()

        # --- Data training ---
        df_train = df[df.index < tanggal_mulai].copy()
        if df_train.empty or len(df_train["pakan_pakai"]) < 10:
            return JSONResponse(status_code=400, content={"error": "Data tidak cukup untuk pelatihan model."})

        # --- Per ayam series ---
        per_ayam_series = df_train["pakan_pakai"] / df_train["jumlah_ayam"].replace(0, 1)
        per_ayam_series = per_ayam_series.fillna(per_ayam_series.mean())
        mean_per_ayam = float(per_ayam_series.mean())
        # print("DEBUG mean_per_ayam:", mean_per_ayam)

        # --- Train ARIMA dengan fallback ---
        try:
            model = train_arima(per_ayam_series)
            forecast = np.array(model.predict(n_periods=hari))
            # print("DEBUG ARIMA forecast:", forecast)
        except Exception as e:
            print("WARNING: ARIMA gagal, pakai rata-rata per_ayam", e)
            forecast = np.full(hari, mean_per_ayam)

        # --- Prediksi per hari ---
        tanggal_prediksi = [tanggal_mulai + timedelta(days=i) for i in range(hari)]
        hasil_prediksi = []
        ayam_hidup = jumlah_ayam_awal
        total_kg = 0.0
        rata_mati = df['jumlah_ayam_mati'].mean() if 'jumlah_ayam_mati' in df else 0
        # print("DEBUG rata_mati:", rata_mati)

        for i in range(hari):
            per_ayam = float(forecast[i]) if i < len(forecast) and not math.isnan(forecast[i]) else mean_per_ayam
            ayam_hidup = max(1, ayam_hidup - int(rata_mati))
            pakan = float(round(per_ayam * ayam_hidup, 2))  # pastikan float Python

            # print(f"DEBUG hari {i+1}: per_ayam={per_ayam}, ayam_hidup={ayam_hidup}, pakan={pakan}")

            hasil_prediksi.append({
                "x": tanggal_prediksi[i].strftime('%Y-%m-%d'),
                "y": pakan,
                "kg": pakan,
                "ayam_hidup": ayam_hidup,
                "per_ayam": round(per_ayam, 2)
            })
            total_kg += pakan

        # --- Total karung ---
        total_kg = float(round(total_kg, 2))
        total_karung = float(math.ceil(total_kg / 50))
        # print("DEBUG total_kg =", total_kg, "total_karung =", total_karung)

        # --- Data aktual ---
        semua_data_aktual = []
        for idx, row in df.iterrows():
            pakan_aktual = float(round(float(row.get('pakan_pakai', 0)), 2))
            semua_data_aktual.append({
                "x": idx.strftime("%Y-%m-%d"),
                "y": pakan_aktual,
                "kg": pakan_aktual
            })

        # --- Konsumsi harian per ekor ---
        konsumsi_harian_per_ekor = total_kg / (jumlah_ayam_awal * hari) if jumlah_ayam_awal > 0 else 0

        # --- Catatan ---
        catatan = (
            f"Mode prediksi per ayam menggunakan input jumlah ayam awal ({jumlah_ayam_awal} ekor).\n"
            "Pastikan pakan tersedia sesuai jumlah ayam harian.\n"
            "Periksa prediksi harian untuk mencegah kekurangan pakan."
        )

        # --- Print debug terminal lengkap ---
        print("==================== PREDIKSI PER AYAM ====================")
        print(f"User ID: {user_id}")
        print(f"Tanggal mulai: {tanggal_mulai.strftime('%Y-%m-%d')}")
        print(f"Tanggal selesai: {tanggal_selesai.strftime('%Y-%m-%d')}")
        print(f"Jumlah data aktual: {len(semua_data_aktual)}")
        print(f"Jumlah data prediksi: {len(hasil_prediksi)}")
        print(f"ARIMA PDQ yang digunakan: {getattr(model, 'order', None)}")
        print(f"Jumlah ayam awal: {jumlah_ayam_awal}")
        print(f"Durasi (hari): {hari}")
        print(f"Rata-rata ayam mati per hari: {rata_mati}")
        print(f"Total Pakan (kg): {total_kg} kg")
        print(f"Total Karung (50kg): {total_karung} karung")
        print(f"Konsumsi Harian per Ekor: {round(konsumsi_harian_per_ekor,2)} kg")
        print("Catatan:", catatan)
        print("==============================")

        # --- Simpan ke DB ---
        riwayat_id = None
        conn = get_db_connection()
        try:
            # Pastikan tipe float Python murni
            total_kg_db = float(round(total_kg, 2))
            total_karung_db = float(round(total_karung, 2))

            # print("DEBUG DB total_kg:", total_kg_db, type(total_kg))
            # print("DEBUG DB total_karung:", total_karung_db, type(total_karung))

            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM riwayat WHERE user_id=%s AND tanggal_mulai=%s AND tanggal_selesai=%s AND mode_prediksi=%s",
                    (user_id, tanggal_mulai.strftime('%Y-%m-%d'), tanggal_selesai.strftime('%Y-%m-%d'), mode)
                )
                existing = cursor.fetchone()
                if existing:
                    riwayat_id = existing[0]
                    cursor.execute(
                        """
                        UPDATE riwayat SET
                            prediksi=%s,
                            data_aktual=%s,
                            total_pakan_kg=%s,
                            total_karung=%s,
                            jumlah_ayam_awal=%s,
                            mode_prediksi=%s,
                            asal_data=%s,
                            nama_file=%s,
                            activity=%s,
                            mape=%s,
                            updated_at=NOW()
                        WHERE id=%s
                        """,
                        (
                            json.dumps(hasil_prediksi),
                            json.dumps(semua_data_aktual),
                            total_kg_db,          # <- pakai total_kg_db
                            total_karung_db,      # <- pakai total_karung_db
                            jumlah_ayam_awal,
                            mode,
                            asal_data,
                            nama_file,
                            f"Prediksi {mode} dari {tanggal_mulai.strftime('%Y-%m-%d')} sampai {tanggal_selesai.strftime('%Y-%m-%d')}",
                            0,
                            riwayat_id
                        )
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO riwayat
                        (user_id, tanggal_mulai, tanggal_selesai, durasi, jumlah_ayam_awal,
                        mode_prediksi, prediksi, data_aktual, total_pakan_kg, total_karung,
                        asal_data, nama_file, activity, mape, created_at, updated_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())
                        """,
                        (
                            user_id,
                            tanggal_mulai.strftime('%Y-%m-%d'),
                            tanggal_selesai.strftime('%Y-%m-%d'),
                            hari,
                            jumlah_ayam_awal,
                            mode,
                            json.dumps(hasil_prediksi),
                            json.dumps(semua_data_aktual),
                            total_kg_db,         # <- pakai total_kg_db
                            total_karung_db,     # <- pakai total_karung_db
                            asal_data,
                            nama_file,
                            f"Prediksi {mode} dari {tanggal_mulai.strftime('%Y-%m-%d')} sampai {tanggal_selesai.strftime('%Y-%m-%d')}",
                            0
                        )
                    )
                    riwayat_id = cursor.lastrowid
                conn.commit()
        finally:
            conn.close()

        # --- Summary ---
        summary = {
            "total_prediksi_kg": total_kg,
            "total_prediksi_karung": total_karung,
            "jumlah_ayam_awal": jumlah_ayam_awal,
            "durasi_hari": hari,
            "konsumsi_harian_per_ekor": round(konsumsi_harian_per_ekor, 2),
            "catatan": catatan
        }

        return JSONResponse({
            "data_prediksi": hasil_prediksi,
            "data_aktual": semua_data_aktual,
            "summary": summary,
            "riwayat_id": riwayat_id
        })

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})



#----------------------------------------------------------
# ENDPOINT UNTUK DOWNLOAD HASIL PREDIKSI di fitur prediksi
#----------------------------------------------------------
@app.post("/download-prediksi")
async def download_prediksi_csv(request: Request):
    try:
        data = await request.json()
        predicted_detail = data.get("predicted_detail", [])
        summary = data.get("summary", {})

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["Tanggal", "Prediksi (kg)", "Estimasi Karung"])
        for item in predicted_detail:
            # Gunakan key yang tersedia, fallback jika key utama tidak ada
            tanggal = item.get("x") or item.get("date") or ""
            try:
                kg = float(item.get("kg", item.get("value", 0)))
            except (ValueError, TypeError):
                kg = 0.0
            try:
                karung = float(item.get("y", item.get("karung", 0)))
            except (ValueError, TypeError):
                karung = 0.0

            writer.writerow([
                tanggal,
                f"{kg:.2f}",
                f"{karung:.2f}"
            ])

        writer.writerow([])
        writer.writerow(["Ringkasan"])
        for key, val in summary.items():
            writer.writerow([key, val])

        output.seek(0)
        headers = {
            "Content-Disposition": "attachment; filename=hasil_prediksi.csv"
        }
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/download-prediksi-pdf")
async def download_prediksi_pdf(request: Request):
    try:
        data = await request.json()
        predicted_detail = data.get("predicted_detail", [])
        summary = data.get("summary", {})
        tanggal_mulai = data.get("tanggal_mulai")
        tanggal_selesai = data.get("tanggal_selesai")

        # Validasi tanggal
        if not tanggal_mulai or not tanggal_selesai:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Tanggal mulai dan tanggal selesai harus diisi"}
            )

        start_date = datetime.fromisoformat(str(tanggal_mulai)).date()
        end_date = datetime.fromisoformat(str(tanggal_selesai)).date()

        # Mapping prediksi per tanggal
        prediksi_map = {}
        for item in predicted_detail:
            try:
                dt_key = datetime.fromisoformat(item.get("date")).date()
                val = float(item.get("value", 0))
                prediksi_map[dt_key] = val
            except Exception as e:
                print("Error parsing predicted_detail:", e)
                continue

        # Generate semua tanggal di range
        semua_tanggal = []
        current_date = start_date
        while current_date <= end_date:
            semua_tanggal.append(current_date)
            current_date += timedelta(days=1)

        # HTML PDF
        html_content = """
        <html>
        <head>
        <style>
            @page { margin: 20px; }
            body { font-family: Arial, sans-serif; font-size: 12px; color: #333; }
            h2 { text-align: center; color: #0a660a; }
            h3 { color: #0a660a; margin-top: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { border: 1px solid #ccc; padding: 5px; font-size: 11px; }
            th { background-color: #e0f7e0; text-align: center; }
            td { text-align: center; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            .summary-card { 
                border: 1px solid #28a745; 
                border-radius: 6px; 
                padding: 10px; 
                margin-top: 15px; 
                background-color: #f0fff0;
            }
            .summary-card h4 { margin: 0 0 5px 0; color: #28a745; text-align: center; }
            .summary-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            .summary-table th, .summary-table td { 
                border: 1px solid #ccc; 
                padding: 6px 10px; 
                font-size: 11px; 
            }
            .summary-table th { width: 40%; text-align: right; }
            .summary-table td { width: 60%; text-align: left; }
        </style>
        </head>
        <body>
            <h2>Hasil Prediksi Kebutuhan Pakan Ayam</h2>
            <h3>Data Prediksi</h3>
            <table>
                <tr>
                    <th>Tanggal</th>
                    <th>Prediksi (kg)</th>
                    <th>Estimasi Karung (50kg)</th>
                </tr>
        """

        for dt in semua_tanggal:
            val = prediksi_map.get(dt, 0)
            karung = math.ceil(val / 50)
            html_content += f"<tr><td>{dt.strftime('%d %B %Y')}</td><td>{val:.2f}</td><td>{karung}</td></tr>"

        html_content += "</table>"

        # Ringkasan
        html_content += '<div class="summary-card"><h4>Ringkasan</h4><table class="summary-table">'
        for key, val in summary.items():
            if isinstance(val, float):
                val_display = f"{val:.2f}"
            elif isinstance(val, int):
                val_display = f"{val:,}"
            else:
                val_display = val
            html_content += f"<tr><th>{key.replace('_',' ').capitalize()}</th><td>{val_display}</td></tr>"
        html_content += "</table></div>"

        html_content += "</body></html>"

        # Konversi ke PDF
        pdf_stream = io.BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_stream)
        if pisa_status.err:
            raise Exception("Gagal membuat PDF")
        pdf_stream.seek(0)

        headers = {"Content-Disposition": "attachment; filename=hasil_prediksi.pdf"}
        return StreamingResponse(pdf_stream, media_type="application/pdf", headers=headers)

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.get("/{full_path:path}")
async def serve_vue(full_path: str):
    requested = os.path.join(static_dir, full_path)
    if os.path.isfile(requested):
        return FileResponse(requested)
    return FileResponse(os.path.join(static_dir, "index.html"))

