# === Built-in Modules ===
import csv
import hashlib
import io
import math
import os
import re
import shutil
import secrets
import traceback
import uuid
import json
import warnings
import sys
import smtplib
from email.mime.text import MIMEText
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# === Third-party Modules ===
import jwt
import numpy as np
import pandas as pd
from pmdarima import auto_arima
from statsmodels.tools.sm_exceptions import ValueWarning
from xhtml2pdf import pisa
import mysql.connector

# === FastAPI Modules ===
from fastapi import (
    FastAPI,
    Request,
    APIRouter,
    UploadFile,
    File,
    Form,
    Depends,
    HTTPException,
    Header,
    Body,
    Path,
    Query
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer

# === FastAPI Mail ===
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

# === Google Auth ===
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# === Pydantic & SQLAlchemy ===
from pydantic import BaseModel
from sqlalchemy.orm import Session

# === Local Modules ===
from passlib.context import CryptContext
from auth import router as auth_router
from database import get_db_connection

# === Warning Filters ===
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=ValueWarning)
warnings.filterwarnings("ignore")  # Ignore all other warnings


# --------- FastAPI App ---------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- Tentukan folder static hasil build Vue ---
static_dir = os.path.join(os.path.dirname(__file__), "static")

# Mount static folder
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/api/ping")
def ping():
    return {"msg": "pong"}


# --------- JWT Config ---------
SECRET_KEY = os.environ.get("SECRET_KEY", "ini_kunci_rahasia_default")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
GOOGLE_CLIENT_ID = "551825862751-iimpdde6vqho5l2ter279vp6len187kl.apps.googleusercontent.com"

# --------- Schemas ---------
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

# =====================
# Fungsi kirim notifikasi (async)
# =====================

def send_admin_notification(name, email):
    try:
        sender = "raisyawulan04@gmail.com"
        recipient = "raisyawulan04@gmail.com"  # email admin

        subject = "APLIKASI FEED PREDICT! Notifikasi Registrasi User Baru"

        # buat token unik (opsional, kalau mau dicek lebih aman)
        token = secrets.token_urlsafe(16)

        # ✅ Link verifikasi YA / TIDAK
        verify_yes = f"http://localhost:8000/api/admin/verify?email={email}&action=yes&token={token}"
        verify_no  = f"http://localhost:8000/api/admin/verify?email={email}&action=no&token={token}"

        body = f"""
        Halo Admin,

        Ada user baru yang registrasi:

        Nama  : {name}
        Email : {email}

        Silakan pilih salah satu:
        ✅ Verifikasi: {verify_yes}
        ❌ Tolak     : {verify_no}
        """

        msg = MIMEText(body)
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = subject

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, "sizr qxvt xgem ikin")  # App Password Gmail
            server.sendmail(sender, [recipient], msg.as_string())

        print("✅ Email notifikasi terkirim ke admin")

    except Exception as e:
        print(f"❌ Gagal mengirim email notifikasi: {e}")



# =====================
# Fungsi koneksi database
# =====================
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="prediksi_db"
    )

# --------- Dependency Cek User ---------

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
    
#===================
# Endpoint Register
#===================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from fastapi import BackgroundTasks

@app.post("/api/register")
def register(data: RegisterSchema, background_tasks: BackgroundTasks):
    # Validasi panjang password minimal 8 karakter
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password minimal 8 karakter")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Cek email sudah ada
    cursor.execute("SELECT * FROM users WHERE email=%s", (data.email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")

    # Hash password
    hashed_password = pwd_context.hash(data.password)

    # Simpan user, status belum terverifikasi
    cursor.execute(
        "INSERT INTO users (name, email, password, role, is_verified, created_at, updated_at) "
        "VALUES (%s, %s, %s, %s, %s, NOW(), NOW())",
        (data.name, data.email, hashed_password, "user", 0)
    )
    conn.commit()
    cursor.close()
    conn.close()

    # --- Kirim notifikasi ke admin di background ---
    background_tasks.add_task(send_admin_notification, data.name, data.email)

    return {"message": "User berhasil didaftarkan! Tunggu verifikasi admin sebelum login."}


# =========================
# Endpoint Login Manual
# =========================
@app.post("/api/login")
def login(data: dict):
    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Email tidak ditemukan")
    if not user['is_verified']:
        raise HTTPException(status_code=403, detail="Akun belum diverifikasi oleh admin")

    if not pwd_context.verify(password, user['password']):
        raise HTTPException(status_code=401, detail="Password salah")

    token = create_access_token({"user_id": user["id"], "role": user["role"]})
    return {"access_token": token, "role": user["role"], "name": user["name"]}


# =========================
# Endpoint Login Google
# =========================
@app.post("/api/login-google")
def login_google(data: dict):
    id_token_google = data.get("id_token")  
    if not id_token_google:
        raise HTTPException(status_code=400, detail="ID token Google diperlukan")

    try:
        # Verifikasi token Google
        idinfo = id_token.verify_oauth2_token(
            id_token_google,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
        email = idinfo.get("email")
        google_user_id = idinfo.get("sub")  # unik untuk akun Google

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if not user:
            # Bisa otomatis register atau tolak login
            raise HTTPException(status_code=401, detail="Email belum terdaftar")
        if not user['is_verified']:
            raise HTTPException(status_code=403, detail="Akun belum diverifikasi oleh admin")

        # Update google_id jika kosong
        if not user.get('google_id'):
            cursor.execute(
                "UPDATE users SET google_id=%s WHERE id=%s",
                (google_user_id, user["id"])
            )
            conn.commit()

        cursor.close()
        conn.close()

        # Buat JWT internal aplikasi
        token = create_access_token({"user_id": user["id"], "role": user["role"]})
        return {"access_token": token, "role": user["role"], "name": user["name"]}

    except ValueError:
        raise HTTPException(status_code=401, detail="Token Google tidak valid")

# =========================
# ENDPOINT VERIFIKASI VIA LINK
# =========================
@app.get("/api/admin/verify")
def verify_user(email: str, token: str, action: str):
    """
    action = "yes" → verifikasi
    action = "no"  → tolak
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    if action == "yes":
        cursor.execute("UPDATE users SET is_verified=1 WHERE email=%s", (email,))
        conn.commit()
        message = f"Akun {email} berhasil diverifikasi ✅"
    elif action == "no":
        cursor.execute("UPDATE users SET is_verified=0 WHERE email=%s", (email,))
        conn.commit()
        message = f"Akun {email} ditolak ❌"
    else:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Action tidak valid")

    cursor.close()
    conn.close()
    return {"message": message}


# schema
class ResetPasswordSchema(BaseModel):
    email: str
    new_password: str

@app.post("/api/reset-password")
def reset_password(data: ResetPasswordSchema):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # cek apakah email ada
    cursor.execute("SELECT * FROM users WHERE email=%s", (data.email,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Email tidak ditemukan")

    # hash password baru
    hashed_password = pwd_context.hash(data.new_password)

    # update password
    cursor.execute(
        "UPDATE users SET password=%s WHERE email=%s",
        (hashed_password, data.email)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "Password berhasil direset"}

#====================
# Endpoint Dashboard 
#====================
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

#===========================
# Ambil semua user (admin only)
#===========================
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


#==================
# Update role user
#==================
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

#============
# Hapus user
#============
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

@app.get("/api/admin/riwayat/{id}/detail")
def get_admin_riwayat_detail(id: int, user=Depends(get_current_user)):
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
                
        # ✅ Tambahkan baris ini agar mape_harian dikenali
        mape_harian = float(row.get("mape_harian") or 0)

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
            "mape_harian": mape_harian,
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
            "user_id": row.get("user_id") 
        }

        return response

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

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


def set_active_riwayat(riwayat_id, is_active: bool):
    try:
        conn = get_db_connection()
        with conn.cursor(buffered=True) as cursor:
            sql = "UPDATE riwayat SET is_active = %s WHERE id = %s"
            cursor.execute(sql, (int(is_active), riwayat_id))
            conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error set_active_riwayat:", e)
        return False

def get_active_riwayat(user_id):
    conn = get_db_connection()
    with conn.cursor(dictionary=True) as cursor:
        sql = "SELECT * FROM riwayat WHERE user_id=%s AND is_active=1"
        cursor.execute(sql, (user_id,))
        result = cursor.fetchall()
    conn.close()
    return result


# ====================
# Simpan riwayat user
# ====================
@app.post("/riwayat")
async def simpan_riwayat(data: dict, current_user: dict = Depends(get_current_user)):
    conn = cursor = None
    try:
        current_user_id = current_user.get("user_id")
        if not current_user_id:
            raise HTTPException(status_code=401, detail="User tidak valid")

        # --- Ambil data dari request ---
        prediksi_list = data.get("prediksi", [])
        aktual_list = data.get("data_aktual", [])
        mode_prediksi = data.get("mode_prediksi", "per_ayam")
        jumlah_ayam_awal_input = int(data.get("jumlah_ayam_awal") or 0)

        file_id = data.get("file_id") or "default"
        df, meta = load_data(file_id=file_id, user_id=current_user_id)
        print("DEBUG jumlah baris CSV:", len(df))
        nama_file = meta["nama_file"]
        asal_data = meta["asal_data"]
        
        print("DEBUG /riwayat - file_id:", file_id, "nama_file:", nama_file, "asal_data:", asal_data)


        # --- Jumlah ayam awal hanya dipakai per_ayam ---
        if mode_prediksi == "per_ayam" and jumlah_ayam_awal_input <= 0:
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

        # --- Standarisasi prediksi ---
        standar_prediksi = []
        for p in prediksi_list:
            if isinstance(p, dict):
                if mode_prediksi == "per_ayam":
                    per_ayam = float(p.get("per_ayam", 0))
                    ayam_hidup = int(p.get("ayam_hidup", jumlah_ayam_awal_input))
                    kg = per_ayam * ayam_hidup
                    y = kg
                else:
                    per_ayam = None
                    ayam_hidup = None
                    kg = round(float(p.get("kg") or p.get("y") or 0), 2)
                    y = round(float(p.get("y") or kg), 2)
                if kg <= 0:
                    continue
                x = p.get("x") or p.get("date") or "-"
                periode = p.get("periode")
            else:
                if mode_prediksi == "per_ayam":
                    per_ayam = float(p)
                    ayam_hidup = jumlah_ayam_awal_input
                    kg = per_ayam * ayam_hidup
                    y = kg
                else:
                    per_ayam = None
                    ayam_hidup = None
                    kg = float(p if p is not None else 0.0)
                    y = kg
                if kg <= 0:
                    continue
                x = "-"
                periode = None

            standar_prediksi.append({
                "x": x,
                "y": y,
                "kg": kg,
                "ayam_hidup": ayam_hidup,
                "per_ayam": per_ayam,
                "periode": periode
            })

        # --- Standarisasi data aktual ---
        standar_aktual = []
        for a in aktual_list:
            if isinstance(a, dict):
                raw_kg = a.get("kg") or a.get("y") or a.get("stok") or 0
                kg = round(float(raw_kg), 2)
                if kg <= 0:
                    continue
                x = a.get("x") or a.get("date") or "-"
                y = round(float(a.get("y") or kg), 2)
                periode = a.get("periode")
            else:
                kg = float(a if a is not None else 0.0)
                if kg <= 0:
                    continue
                x = "-"
                y = kg
                periode = None

            standar_aktual.append({
                "x": x,
                "y": y,
                "kg": kg,
                "periode": periode
            })

        if not standar_prediksi:
            raise HTTPException(status_code=400, detail="Prediksi kosong")

        # --- Hitung total pakan & karung ---
        total_pakan = round(sum([p["kg"] for p in standar_prediksi]), 2)
        total_karung = math.ceil(total_pakan / 50)
        jumlah_ayam_awal_db = jumlah_ayam_awal_input if mode_prediksi == "per_ayam" else None

        # --- Simpan ke DB (Insert baru setiap klik) ---
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)

        # --- Cek duplikat sebelum insert ---
        cursor.execute("""
            SELECT id FROM riwayat 
            WHERE user_id=%s AND tanggal_mulai=%s AND tanggal_selesai=%s
            AND mode_prediksi=%s AND nama_file=%s AND asal_data=%s
        """, (
            current_user_id,
            tanggal_mulai.strftime("%Y-%m-%d"),
            tanggal_selesai.strftime("%Y-%m-%d"),
            mode_prediksi,
            nama_file,
            asal_data
            
        ))
        existing = cursor.fetchone()
        if existing:
            return {"message": "Riwayat sudah ada, tidak disimpan lagi", "riwayat_id": existing[0]}

        activity = data.get("activity") or f"Prediksi {mode_prediksi} dari {tanggal_mulai.date()} sampai {tanggal_selesai.date()}"
        mape = data.get("mape") or None
        mape_harian = float(data.get("mape_harian") or 0) 
        is_active = bool(data.get("is_active", False))

        cursor.execute(
        """
        INSERT INTO riwayat
        (user_id, tanggal_mulai, tanggal_selesai, durasi, prediksi, data_aktual,
        total_pakan_kg, total_karung, mode_prediksi, jumlah_ayam_awal, activity,
        mape, mape_harian, asal_data, nama_file, is_active, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
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
            mape_harian,
            asal_data,
            nama_file,
            is_active
        )
    )

        conn.commit()
        riwayat_id = cursor.lastrowid

        # Ambil kembali data lengkap yang baru disimpan
        cursor.execute("SELECT * FROM riwayat WHERE id=%s", (riwayat_id,))
        row = cursor.fetchone()

        return {
            "message": "Riwayat berhasil disimpan",
            "riwayat": {
                "id": riwayat_id,
                "tanggal_mulai": tanggal_mulai.strftime("%Y-%m-%d"),
                "tanggal_selesai": tanggal_selesai.strftime("%Y-%m-%d"),
                "mode_prediksi": mode_prediksi,
                "nama_file": nama_file,
                "asal_data": asal_data,
                "mape": float(mape or 0),
                "mape_harian": float(mape_harian or 0),
                "total_pakan_kg": total_pakan,
                "total_karung": total_karung,
            }
        }


    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error menyimpan riwayat: {str(e)}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()




# ===============================
# Ambil semua riwayat user (lengkap)
# ===============================
@app.get("/riwayat")
async def get_riwayat(current_user: dict = Depends(get_current_user)):
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

            # --- MAPE Total & MAPE Harian ---
            mape = float(row.get("mape") or 0)
            mape_harian = float(row.get("mape_harian") or 0)  # ✅ ambil nilai MAPE Harian


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
                "mape_harian": mape_harian,
                "asal_data": asal_data,
                "nama_file": nama_file,
                "activity": activity,
                "created_at": created_at,
                "updated_at": updated_at,
                "is_active": bool(row.get("is_active", 0))
            })

        return {"riwayat": result}
    except Exception as e:
        if cursor: cursor.close()
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=f"Error ambil riwayat: {str(e)}")

    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# ===============================
# Ambil detail riwayat (lengkap)
# ===============================
@app.get("/riwayat/{id}/detail")
async def get_riwayat_detail(id: int, current_user: dict = Depends(get_current_user)):
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
        mape_harian = float(row.get("mape_harian") or 0)  
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
            "mape_harian": mape_harian,
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

#================
# delete riwayat
#================
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

# ===============================
# Hapus riwayat tertentu milik user
# ===============================
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

@app.put("/riwayat/{riwayat_id}/set_active")
async def set_active_riwayat(riwayat_id: int, current_user: dict = Depends(get_current_user)):
    conn = cursor = None
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User tidak valid")

        conn = get_db_connection()
        cursor = conn.cursor()

        # ✅ Set semua riwayat user ke nonaktif dulu
        cursor.execute("UPDATE riwayat SET is_active=0 WHERE user_id=%s", (user_id,))

        # ✅ Set hanya riwayat_id yg dipilih jadi aktif
        cursor.execute("UPDATE riwayat SET is_active=1 WHERE id=%s AND user_id=%s", (riwayat_id, user_id))
        conn.commit()

        return {"message": f"Riwayat {riwayat_id} berhasil dijadikan aktif"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error set aktif riwayat: {str(e)}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# Format tanggal bahasa Indonesia (Windows friendly)
def format_tanggal(tanggal_obj):
    bulan = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    return f"{tanggal_obj.day} {bulan[tanggal_obj.month-1]} {tanggal_obj.year}"

@app.get("/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User tidak valid")

    today = date.today()
    tomorrow = today + timedelta(days=1)
    notifications = []

    riwayat_list = get_active_riwayat(user_id)
    for r in riwayat_list:
        t_mulai = r["tanggal_mulai"]
        t_selesai = r["tanggal_selesai"]
        total_kg = r.get("total_pakan_kg", 0)
        karung_total = r.get("total_karung", 0)
        t_mulai_str = format_tanggal(t_mulai)
        t_selesai_str = format_tanggal(t_selesai)

        # 1️⃣ Prediksi sudah lewat
        if t_selesai < today:
            notifications.append({
                "id": r["id"],
                "message": f"Prediksi {t_mulai_str} - {t_selesai_str} sudah kadaluarsa. Sekarang tanggal {format_tanggal(today)}.",
                "created_at": r.get("created_at", datetime.now())
            })

        # 2️⃣ Prediksi belum mulai
        elif t_mulai > today:
            notifications.append({
                "id": r["id"],
                "message": f"Prediksi {t_mulai_str} - {t_selesai_str}: {total_kg} kg ({karung_total} karung) ⏳ (Belum mulai)",
                "created_at": r.get("created_at", datetime.now())
            })

        # 3️⃣ Prediksi aktif hari ini
        else:
            notifications.append({
                "id": r["id"],
                "message": f"Prediksi {t_mulai_str} - {t_selesai_str}: {total_kg} kg ({karung_total} karung) ✅ (Aktif)",
                "created_at": r.get("created_at", datetime.now())
            })

            # Notifikasi untuk besok → ambil dari kolom `prediksi` JSON
            try:
                prediksi_list = json.loads(r.get("prediksi", "[]"))
                prediksi_besok = next(
                    (item for item in prediksi_list if item["x"] == tomorrow.isoformat()),
                    None
                )
                if prediksi_besok:
                    kg_besok = prediksi_besok.get("kg", 0)
                    karung_besok = math.ceil(kg_besok / 50)
                    notifications.append({
                        "id": r["id"],
                        "message": f"Prediksi pakan untuk besok {format_tanggal(tomorrow)}: {kg_besok:.2f} kg ({karung_besok} karung) ⚠️ Siapkan pakan agar stok cukup.",
                        "created_at": r.get("created_at", datetime.now())
                    })
            except Exception as e:
                print("Error parsing prediksi JSON:", e)

    # Jika tidak ada notifikasi
    if not notifications:
        notifications.append({
            "id": 0,
            "message": "Belum ada riwayat prediksi aktif atau prediksi untuk besok.",
            "created_at": datetime.now()
        })

    # Urutkan terbaru dulu
    notifications.sort(key=lambda x: x["created_at"], reverse=True)
    return {"notifications": notifications}


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
DATA_DIR = "uploads/csv"
        
def save_to_csv(data: DataPakan):
    os.makedirs("data", exist_ok=True)  # pastikan folder ada
    file_exists = os.path.isfile(CSV_PATH)
    
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        
        # tulis header kalau file baru
        if not file_exists:
            writer.writerow(["tanggal_mulai", "tanggal_selesai", "jumlah_ayam_awal", "file_id"])
        
        # tulis baris data
        writer.writerow([data.tanggal_mulai, data.tanggal_selesai, data.jumlah_ayam_awal, data.file_id])

def simpan_riwayat(user_id, tanggal_mulai, durasi, jumlah_ayam_awal, hasil_prediksi, is_active=False):
    try:
        total_kg = sum([item.get("kg", 0) for item in hasil_prediksi])
        total_karung = math.ceil(total_kg / 50)  # ✅ lebih konsisten

        # --- LOG ---
        print("=== INFO simpan_riwayat ===")
        print(f"Jumlah data prediksi: {len(hasil_prediksi)}")
        print(f"Jumlah ayam awal: {jumlah_ayam_awal}")
        print(f"Durasi (hari): {durasi}")
        print(f"Total pakan (kg): {total_kg}")
        print(f"Total karung: {total_karung}")
        print(f"is_active: {is_active}")
        print("============================")

        conn = get_db_connection()
        with conn.cursor(buffered=True) as cursor:
            sql = """
                INSERT INTO riwayat (
                    user_id, tanggal_mulai, tanggal_selesai, durasi, prediksi, 
                    total_karung, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            val = (
                user_id,
                tanggal_mulai.strftime("%Y-%m-%d"),
                (tanggal_mulai + timedelta(days=durasi-1)).strftime("%Y-%m-%d"),
                durasi,
                json.dumps(hasil_prediksi),
                total_karung,
                int(is_active)  
            )
            cursor.execute(sql, val)
            conn.commit()

        conn.close()
        return True

    except Exception as e:
        traceback.print_exc()
        if 'conn' in locals():
            conn.close()
        return False


#=================
# FUNGSI LOAD DATA
#=================
# Konversi pakan ke kg
def konversi_pakan(nilai, satuan="kg"):
    if satuan == "karung":
        return nilai * 50  # 1 karung = 50 kg
    return nilai  # jika sudah kg

# --- Load CSV (default atau user upload) ---
def load_data(file_id=None, user_id=None):
    """
    Load data pakan ayam dari CSV default atau upload user
    Output: dataframe, metadata {'nama_file', 'asal_data'}
    """
    import pandas as pd
    import os

    print("load_data dipanggil dengan file_id:", file_id, "user_id:", user_id)

    file_path = CSV_PATH  # default CSV path
    nama_file = "Default"
    asal_data = "Default"

    # Ambil file upload user jika ada
    if file_id and file_id != "default":
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT file_name, file_path FROM data_pakan WHERE id=%s AND user_id=%s",
            (file_id, user_id)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row and row["file_path"] and os.path.exists(row["file_path"]):
            file_path = row["file_path"].replace("\\", "/")
            nama_file = row["file_name"]
            asal_data = "User Upload"

    print(f"load_data: pakai file '{nama_file}' dari '{asal_data}' → path: {file_path}")

    # --- Load CSV dengan ribuan dan desimal benar ---
    df = pd.read_csv(file_path, thousands='.', decimal=',')

    # Bersihkan nama kolom
    df.rename(columns=lambda x: x.strip().lower(), inplace=True)

    # --- Ganti nama bulan Indonesia ke English untuk parsing tanggal ---
    ind_to_eng_month = {
        'Januari': 'January', 'Februari': 'February', 'Maret': 'March',
        'April': 'April', 'Mei': 'May', 'Juni': 'June',
        'Juli': 'July', 'Agustus': 'August', 'September': 'September',
        'Oktober': 'October', 'November': 'November', 'Desember': 'December'
    }
    df['tanggal'] = df['tanggal'].astype(str)
    for ind, eng in ind_to_eng_month.items():
        df['tanggal'] = df['tanggal'].str.replace(ind, eng, regex=False)

    # --- Konversi tanggal ---
    df['tanggal'] = pd.to_datetime(df['tanggal'], format='%d %B %Y', errors='coerce')

    # --- Pastikan kolom penting ada ---
    for col in ['pakan_pakai', 'jumlah_ayam', 'jumlah_ayam_mati', 'pakan_pakai_karung']:
        if col not in df.columns:
            df[col] = 0.0

    # --- Filter baris valid ---
    df.dropna(subset=['tanggal'], inplace=True)
    df = df[(df['pakan_pakai'] > 0) & (df['jumlah_ayam'] > 0)]
    df.sort_values('tanggal', inplace=True)
    df.reset_index(drop=True, inplace=True)

    # --- Hitung pakan total ---
    if 'pakan_pakai_karung' in df.columns and df['pakan_pakai_karung'].sum() > 0:
        df['pakan_aktual_total'] = df.apply(
            lambda row: row['pakan_pakai_karung']*50 if row['pakan_pakai_karung']>0 else row['pakan_pakai'], axis=1
        )
    else:
        df['pakan_aktual_total'] = df['pakan_pakai']

    print(df[['tanggal', 'jumlah_ayam', 'pakan_pakai', 'pakan_aktual_total']])

    return df, {"nama_file": nama_file, "asal_data": asal_data}



# ========================
# Fungsi hitung MAPE stabil
# ========================
def hitung_mape_stabil(prediksi, aktual, min_aktual=50):
    """
    MAPE stabil: hindari nilai ekstrem saat aktual terlalu kecil
    prediksi : array-like
    aktual : array-like
    min_aktual : nilai minimal aktual untuk hindari pembagian 0
    """
    pred = np.array(prediksi)
    act = np.array(aktual)
    act_safe = np.maximum(act, min_aktual)
    mape = np.mean(np.abs((act - pred) / act_safe)) * 100
    return mape

# ========================
# Fungsi prediksi harian
# ========================
def prediksi_harian(series, jumlah_ayam, tanggal_index=None, smooth_window=3, debug=False):
    """
    Prediksi harian realistis dengan ARIMA per-ayam
    series : pandas Series total pakan (kg)
    jumlah_ayam : pandas Series jumlah ayam harian
    tanggal_index : pd.DatetimeIndex
    smooth_window : ukuran rolling mean
    debug : True/False
    """
    series = series.copy()
    jumlah_ayam = jumlah_ayam.copy()

    # Tangani missing / nol
    series.replace(0, np.nan, inplace=True)
    series.fillna(method='ffill', inplace=True)
    series.fillna(method='bfill', inplace=True)

    # Clip outlier 5%-95%
    lower, upper = series.quantile(0.05), series.quantile(0.95)
    series = series.clip(lower=lower, upper=upper)

    # Rolling smoothing ringan
    if len(series) >= smooth_window:
        series = series.rolling(window=smooth_window, min_periods=1).mean()

    # Index tanggal
    if tanggal_index is not None:
        series.index = pd.to_datetime(tanggal_index)
        jumlah_ayam.index = pd.to_datetime(tanggal_index)
    else:
        series.index = pd.date_range(start=pd.Timestamp.today(), periods=len(series), freq='D')
        jumlah_ayam.index = series.index

    # Tangani jumlah ayam 0 atau NaN
    jumlah_ayam_safe = jumlah_ayam.replace(0, np.nan).fillna(method='ffill').fillna(method='bfill')

    # Prediksi per ayam
    pakan_per_ayam = series / jumlah_ayam_safe

    # Latih ARIMA seluruh data historis
    try:
        model = auto_arima(
            pakan_per_ayam,
            seasonal=False,
            stepwise=True,
            suppress_warnings=True,
            error_action='ignore'
        )
        # Forecast sepanjang periode
        forecast_per_ayam = model.predict(n_periods=len(pakan_per_ayam))
    except Exception as e:
        if debug:
            print("ARIMA gagal, fallback rata-rata:", e)
        forecast_per_ayam = np.full(len(pakan_per_ayam), pakan_per_ayam.mean())
        model = None

    # Total pakan = per-ayam * jumlah ayam
    total_prediksi = forecast_per_ayam * jumlah_ayam_safe.values

    # Data prediksi harian
    data_prediksi = []
    total_kg = 0
    for i, p in enumerate(total_prediksi):
        kg = round(float(p), 2)
        karung = math.ceil(kg / 50)
        data_prediksi.append({
            "hari_ke": i + 1,
            "tanggal": str(series.index[i].date()),
            "kg": kg,
            "karung_50kg": karung,
            "per_ayam": round(forecast_per_ayam[i], 2),
            "jumlah_ayam": int(jumlah_ayam_safe.iloc[i])
        })
        total_kg += kg
    total_karung = math.ceil(total_kg / 50)

    # Evaluasi MAPE total keseluruhan
    total_aktual_kg = series.sum()
    mape_total_keseluruhan = abs(total_kg - total_aktual_kg) / total_aktual_kg * 100


    if debug:
        print("\n" + "="*60)
        print("            🚀 PREDIKSI HARIAN DIMULAI")
        print("="*60)
        print(f"Parameter ARIMA terpilih: {model.order if model else '-'}")
        print(f"MAPE total keseluruhan : {mape_total_keseluruhan:.2f}%")
        print("Forecast vs Aktual (sample 10):")
        for i in range(min(10, len(total_prediksi))): actual_value = series.iloc[i]
        print(f"{series.index[i].date()} | Prediksi: {total_prediksi[i]:.1f} kg | Aktual: {actual_value:.1f} kg | Selisih: {total_prediksi[i]-actual_value:.1f}")
        print("="*60)

    return data_prediksi, total_kg, total_karung, mape_total_keseluruhan, model, total_prediksi, series

# ========================
# Fungsi train_arima
# ========================
def train_arima(series, satuan="kg", smooth_window=3, debug=False):
    """
    Latih model ARIMA
    series : pandas Series (kg atau karung)
    satuan : "kg" atau "karung"
    smooth_window : ukuran rolling mean untuk smoothing
    debug : kalau True, print info tambahan
    """
    
    # Pastikan dalam kg
    series_kg = series.apply(lambda x: konversi_pakan(x, satuan))

    # Smoothing rolling mean
    if len(series_kg) >= smooth_window:
        series_kg = series_kg.rolling(window=smooth_window, min_periods=1).mean()

    if len(series_kg) < 10 or series_kg.nunique() <= 1:
        raise ValueError("Data tidak cukup atau terlalu seragam untuk ARIMA.")

    if not isinstance(series_kg.index, pd.DatetimeIndex):
        series_kg.index = pd.date_range(start=pd.Timestamp.today(), periods=len(series_kg), freq='D')

    train_size = int(len(series_kg) * 0.8)
    train, test = series_kg.iloc[:train_size], series_kg.iloc[train_size:]

    # 🔹 Auto ARIMA
    model = auto_arima(
        train,
        seasonal=False,
        stepwise=True,
        suppress_warnings=True,
        error_action='ignore'
    )

    forecast = model.predict(n_periods=len(test))
    mape = hitung_mape_stabil(list(forecast), list(test))

    print(f"Forecast vs Aktual (sample 5): {list(forecast[:5])} vs {list(test[:5])}")

    if debug:
        print(f"Train size: {len(train)}, Test size: {len(test)}")

    return model, forecast, test, mape

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






#==================================
# ENDPOINT UNTUK FITURE DATA PAKAN
#==================================
# Ambil semua data pakan (admin)
@app.get("/api/admin/data-pakan")
def get_all_data_pakan():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT dp.id, dp.user_id, u.name AS user_name, dp.file_name, dp.file_path, dp.upload_date
        FROM data_pakan dp
        JOIN users u ON dp.user_id = u.id
        ORDER BY dp.upload_date DESC
    """)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

# Hapus data pakan
@app.delete("/api/admin/data-pakan/{id}")
def delete_data_pakan(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    # ambil file_path dulu
    cursor.execute("SELECT file_path FROM data_pakan WHERE id=%s", (id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Data tidak ditemukan")
    file_path = row[0]
    
    # hapus file fisik
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    
    # hapus dari database
    cursor.execute("DELETE FROM data_pakan WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Data pakan berhasil dihapus"}

#======================
# Folder upload (user)
#=====================
UPLOAD_DIR = "uploads/csv"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ========================
# HELPER FUNCTIONS
# ========================
def _secure_filename(name: str) -> str:
    base = os.path.basename(name)
    base = re.sub(r"[^A-Za-z0-9_.-]", "_", base)
    if not base.endswith(".csv"):
        base += ".csv"
    return base

def _unique_path(directory: str, filename: str) -> str:
    name, ext = os.path.splitext(filename)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate = f"{name}_{ts}{ext}"
    return os.path.join(directory, candidate)

# ========================
# UPLOAD CSV LANGSUNG (Frontend → DB)
# ========================
# ------------------- upload_csv.py -------------------
@app.post("/data_pakan/upload")
async def upload_csv(
    file: UploadFile = File(...), 
    satuan_data: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    import pandas as pd
    import os

    # --- Cek ekstensi file ---
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Hanya file CSV yang diperbolehkan")

    # --- Load CSV ---
    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal membaca CSV: {e}")

    # --- Kolom wajib dengan alias ---
    required_columns_alias = {
        "tanggal": ["tanggal", "tgl", "date"],
        "jumlah_ayam": ["jumlah_ayam_awal", "jumlah_ayam", "jml_ayam"],
        "pakan_pakai": ["pakan_kg", "pakan", "pakankg", "pakan_", "pakan_pakai", "Pakan_Pakai", "PakanPakai"],
        "jumlah_ayam_mati": ["jumlah_ayam_mati", "ayam_mati", "mati"]
    }

    # --- Mapping kolom ---
    column_map = {}
    for key, aliases in required_columns_alias.items():
        match = next((c for c in df.columns if c.lower() in [a.lower() for a in aliases]), None)
        if match:
            column_map[key] = match
        else:
            raise HTTPException(status_code=400, detail=f"Kolom wajib hilang: {key}")

    # --- Rename ke standar ---
    df.rename(columns={
        column_map["tanggal"]: "tanggal",
        column_map["jumlah_ayam"]: "jumlah_ayam",
        column_map["pakan_pakai"]: "pakan_pakai",
        column_map["jumlah_ayam_mati"]: "jumlah_ayam_mati"
    }, inplace=True)

    # --- Validasi jumlah baris minimal ---
    if len(df) < 30:
        raise HTTPException(status_code=400, detail=f"Minimal 30 baris, tapi file hanya {len(df)} baris")

    # --- Konversi dan validasi isi kolom ---
    for col in ["pakan_pakai", "jumlah_ayam", "jumlah_ayam_mati"]:
        try:
            df[col] = df[col].astype(str).str.replace(",", ".").astype(float)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Kolom {col} ada nilai tidak valid: {e}")

    # --- Cek nilai positif ---
    if (df["jumlah_ayam"] <= 0).any():
        raise HTTPException(
            status_code=400, 
            detail="Semua jumlah ayam harus valid (>0 atau >=0)"
        )

    # --- Simpan file fisik ---
    safe_filename = _secure_filename(file.filename)
    user_dir = os.path.join(UPLOAD_DIR, str(current_user["user_id"]))
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, safe_filename)
    df.to_csv(file_path, index=False)

    # --- Simpan info ke DB ---
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO data_pakan (user_id, file_name, file_path, satuan_data, upload_date) VALUES (%s,%s,%s,%s,NOW())",
        (current_user["user_id"], safe_filename, file_path, satuan_data)
    )
    conn.commit()
    file_id = cursor.lastrowid
    cursor.close()
    conn.close()

    return {"message": "CSV berhasil diupload", "file_id": file_id, "file_name": safe_filename}




# ========================
# GET ALL DATA PAKAN
# ========================
@app.get("/data_pakan/list")
async def get_data_pakan(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, file_name, upload_date, satuan_data FROM data_pakan WHERE user_id = %s ORDER BY upload_date DESC",
            (current_user["user_id"],)  # Hanya ambil data milik user ini
        )
        rows = cursor.fetchall()
        return rows or []
    finally:
        cursor.close()
        conn.close()

# ========================
# READ CSV BY UPLOAD ID
# ========================

@app.get("/data_pakan/{upload_id}/read_csv")
async def read_csv(upload_id: int, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    import os
    import pandas as pd

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT file_path FROM data_pakan WHERE id=%s AND user_id=%s",
            (upload_id, current_user["user_id"])
        )
        row = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="File tidak ditemukan atau bukan milik Anda.")

    # --- perbaiki path cross-platform ---
    file_path = os.path.abspath(row["file_path"].replace("\\", "/"))

    # --- cek keamanan path ---
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File tidak ada di disk: {file_path}")
    if ".." in file_path or not file_path.startswith(os.path.abspath(UPLOAD_DIR)):
        raise HTTPException(status_code=400, detail="File path tidak valid.")

    # --- baca CSV ---
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal membaca CSV: {e}")

    rows = df.astype(object).astype(str).values.tolist()
    headers = list(df.columns.astype(str))

    return {
        "headers": headers,
        "rows": rows[:200] if rows else []
    }
# ========================
# UPDATE DATA PAKAN (ubah nama file)
# ========================
@app.put("/data_pakan/{id}")
async def update_data_pakan(
    id: int,
    file_name: str = Form(...),
    satuan_data: str = Form(...),
    file: UploadFile | None = File(None),
    current_user: dict = Depends(get_current_user)
):
    import os
    import pandas as pd

    safe_name = _secure_filename(file_name)
    user_dir = os.path.join(UPLOAD_DIR, str(current_user["user_id"]))
    os.makedirs(user_dir, exist_ok=True)
    new_path = os.path.abspath(os.path.join(user_dir, safe_name))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # --- ambil data lama dulu ---
        cursor.execute(
            "SELECT file_path FROM data_pakan WHERE id=%s AND user_id=%s",
            (id, current_user["user_id"])
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Data tidak ditemukan atau bukan milik Anda.")

        old_path = os.path.abspath(row["file_path"].replace("\\", "/"))

        # --- jika upload CSV baru ---
        if file:
            try:
                df = pd.read_csv(file.file)
                df.to_csv(new_path, index=False)
                # hapus file lama jika berbeda
                if old_path != new_path and os.path.exists(old_path):
                    os.remove(old_path)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Gagal update CSV: {e}")
        else:
            # rename file lama jika perlu
            if old_path != new_path and os.path.exists(old_path):
                os.rename(old_path, new_path)

        # --- update DB ---
        cursor.execute(
            "UPDATE data_pakan SET file_name=%s, file_path=%s, satuan_data=%s WHERE id=%s AND user_id=%s",
            (safe_name, new_path, satuan_data, id, current_user["user_id"])
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return {"message": "Data berhasil diupdate.", "file_name": safe_name, "file_path": new_path, "satuan_data": satuan_data}


# ========================
# DELETE DATA PAKAN
# ========================
@app.delete("/data_pakan/{id}")
async def delete_data_pakan(id: int) -> Dict[str, str]:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT file_path FROM data_pakan WHERE id=%s", (id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Data tidak ditemukan.")

        if row["file_path"] and os.path.exists(row["file_path"]):
            try:
                os.remove(row["file_path"])
            except Exception:
                pass

        cursor.execute("DELETE FROM data_pakan WHERE id=%s", (id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return {"message": "Data berhasil dihapus."}

#=======================
# untuk di prediksi.vue 
#=======================
@app.get("/list_csv_files")
async def list_csv_files(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, file_name, upload_date FROM data_pakan WHERE user_id = %s ORDER BY upload_date DESC",
            (current_user["user_id"],)
        )
        files = cursor.fetchall()
        # ubah key supaya Vue bisa pakai camelCase
        files_vue = [
            {
                "id": f["id"],
                "fileName": f["file_name"],
                "uploadDate": f["upload_date"].strftime("%Y-%m-%d %H:%M:%S")
            } for f in files
        ]
        return {"files": files_vue}
    finally:
        cursor.close()
        conn.close()

# =========================================
# Download template CSV di fitur data pakan
# =========================================
DATA_DIR = "static/template/"
os.makedirs(DATA_DIR, exist_ok=True)

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

# ===========================
# Download template Excel
# ===========================
@app.get("/download_template_excel")
async def download_template_excel():
    file_path = os.path.join(DATA_DIR, "template_data_pakan.xlsx")
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"error": "File Excel tidak ditemukan"})

    return FileResponse(
        file_path,
        filename="template_data_pakan.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
# ===== Endpoint predict_periode ===== 
def get_file_name(file_id, user_id):
    file_path = f"static/uploads/{user_id}/{file_id}.csv"
    if os.path.exists(file_path):
        return os.path.basename(file_path)  
    return "Default"

#========================
# Mode Prediksi Per Periode
#========================
@app.post("/predict_periode")
async def predict_periode(request: Request, current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User tidak valid")

        body = await request.json()
        tanggal_mulai_str = body.get("tanggal_mulai")
        tanggal_selesai_str = body.get("tanggal_selesai")
        file_id = body.get("file_id", "default")

        if not tanggal_mulai_str or not tanggal_selesai_str:
            return JSONResponse(status_code=400, content={"error": "Tanggal mulai dan selesai wajib diisi"})

        tanggal_mulai = datetime.strptime(tanggal_mulai_str, "%Y-%m-%d")
        tanggal_selesai = datetime.strptime(tanggal_selesai_str, "%Y-%m-%d")
        n_periods = (tanggal_selesai - tanggal_mulai).days + 1
        mode = "per_periode"

        df, meta = load_data(file_id=file_id, user_id=user_id)
        nama_file = meta["nama_file"]
        asal_data = meta["asal_data"]

        df['tanggal'] = pd.to_datetime(df['tanggal'])
        df = df.set_index('tanggal').sort_index()
        df_train = df[df.index < tanggal_mulai].copy()

        print(f"DEBUG baris sebelum filter: {len(df)}")
        print(f"DEBUG baris setelah filter: {len(df_train)}")

        if df_train.empty or len(df_train["pakan_pakai"]) < 10:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Data tidak cukup untuk pelatihan model.",
                    "detail": f"Total baris awal: {len(df)}, setelah filter: {len(df_train)}"
                }
            )

        # 🔹 Latih ARIMA
        try:
            model, forecast_train, test, _ = train_arima(df_train["pakan_pakai"])
            forecast = np.array(model.predict(n_periods=n_periods))
        except Exception as e:
            print("WARNING: ARIMA gagal, pakai rata-rata pakan", e)
            mean_value = df_train["pakan_pakai"].mean()
            forecast = np.full(n_periods, mean_value)

        # 🔹 Buat prediksi harian
        tanggal_prediksi = [tanggal_mulai + timedelta(days=i) for i in range(n_periods)]
        data_prediksi = []
        total_pakan = 0.0

        for t, p in zip(tanggal_prediksi, forecast):
            kg = round(float(p), 2) if not pd.isna(p) else 0.0
            data_prediksi.append({"x": t.strftime("%Y-%m-%d"), "kg": kg, "y": kg, "periode": None})
            total_pakan += kg

        # 🔹 Ambil data aktual untuk periode input
        df_aktual_periode = df[(df.index >= tanggal_mulai) & (df.index <= tanggal_selesai)]
        semua_data_aktual = []
        for idx, row in df.iterrows():
            pakan_aktual = round(float(row.get('pakan_pakai', 0)), 2)
            semua_data_aktual.append({"x": idx.strftime("%Y-%m-%d"), "y": pakan_aktual, "kg": pakan_aktual})

        total_aktual = sum(item["kg"] for item in semua_data_aktual)
        total_karung_aktual = math.ceil(total_aktual / 50)
        total_karung = math.ceil(total_pakan / 50)

        # 🔹 Hitung MAPE untuk periode input
        if not df_aktual_periode.empty:
            forecast_trimmed = forecast[:len(df_aktual_periode)]
            actual_values = df_aktual_periode["pakan_pakai"].values
            with np.errstate(divide='ignore', invalid='ignore'):
                mape_array = np.abs((actual_values - forecast_trimmed) / actual_values)
                mape_array = mape_array[~np.isnan(mape_array)]
                mape = float(np.mean(mape_array) * 100) if len(mape_array) > 0 else None
                if mape is not None:
                    mape = min(mape, 100)
        else:
            mape = None
            
            
        # --- Hitung MAPE harian rata-rata ---
        aktual_col = "pakan_pakai"

        # Gabungkan prediksi dan aktual berdasarkan tanggal
        df_pred = pd.DataFrame(data_prediksi)
        df_pred.set_index("x", inplace=True)

        df_aktual = df_aktual_periode.copy()
        df_aktual.index = df_aktual.index.strftime("%Y-%m-%d")

        df_merge = df_pred.join(df_aktual, how="inner")

        mape_harian_list = []
        for idx, row in df_merge.iterrows():
            pred = row['kg']
            act = row[aktual_col]
            act_safe = max(act, 50)  # hindari pembagian nol
            mape_harian_list.append(abs(pred - act) / act_safe * 100)

        if len(mape_harian_list) > 0:
            mape_harian = round(sum(mape_harian_list) / len(mape_harian_list), 3)
        else:
            mape_harian = None


        # 🔹 Print prediksi vs aktual
        print("===== DETAIL HARIAN =====")
        print(f"{'Tanggal':<12} | {'Prediksi (kg)':>12} | {'Aktual (kg)':>12} | {'Selisih (kg)':>14}")
        print("-" * 60)
        for item in data_prediksi:
            tgl = item["x"]
            pred_kg = item["kg"]
            row_aktual = df_aktual_periode[df_aktual_periode.index == pd.to_datetime(tgl)]
            aktual_kg = float(row_aktual["pakan_pakai"].values[0]) if not row_aktual.empty else None
            selisih = pred_kg - aktual_kg if aktual_kg is not None else None
            print(f"{tgl:<12} | {pred_kg:12.2f} | {aktual_kg if aktual_kg is not None else '-':12} | {selisih if selisih is not None else '-':14}")
        print("-" * 60)
        # print(f"Total Prediksi (kg): {total_pakan} | Total Aktual (kg): {total_aktual} | MAPE: {mape}")
        print(f"Total Prediksi (kg): {total_pakan} | Total Aktual (kg): {total_aktual} ")


        catatan = "Mode prediksi per periode tidak menggunakan input jumlah ayam.\nPastikan pakan tersedia cukup untuk seluruh periode."

        # 🔹 Simpan ke DB
        riwayat_id = None
        conn = get_db_connection()
        try:
            with conn.cursor(buffered=True) as cursor:
                cursor.execute("""
                    INSERT INTO riwayat
                    (user_id, tanggal_mulai, tanggal_selesai, durasi, jumlah_ayam_awal,
                    mode_prediksi, prediksi, data_aktual, total_pakan_kg, total_karung,
                    asal_data, nama_file, activity, mape, mape_harian, created_at, updated_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())
                """, (
                    user_id, tanggal_mulai_str, tanggal_selesai_str, n_periods, None,
                    mode, json.dumps(data_prediksi), json.dumps(semua_data_aktual),
                    total_pakan, total_karung, asal_data, nama_file,
                    f"Prediksi {mode} dari {tanggal_mulai_str} sampai {tanggal_selesai_str}",
                    mape, mape_harian
                ))
                riwayat_id = cursor.lastrowid
                conn.commit()
        finally:
            conn.close()


        summary = {
            "total_prediksi_kg": round(total_pakan, 2),
            "total_prediksi_karung": total_karung,
            "total_aktual_kg": round(total_aktual, 2),
            "total_aktual_karung": total_karung_aktual,
            "jumlah_ayam_awal": None,
            "durasi_hari": n_periods,
            "konsumsi_harian_per_ekor": None,
            "mape": round(mape, 2) if mape is not None else None,
            "mape_harian": round(mape_harian, 2) if mape_harian is not None else None,
            "catatan": catatan
        }

        return JSONResponse({
            "data_prediksi": data_prediksi,
            "data_aktual": semua_data_aktual,
            "summary": summary,
            "riwayat_id": riwayat_id,
            "mape": mape
        })

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})



#========================
# Mode Prediksi Per Ayam
#========================
@app.post("/predict_per_ayam")
async def predict_per_ayam(request: Request, current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User tidak valid")

        # --- Ambil input ---
        body = await request.json()
        tanggal_mulai_str = body.get("tanggal_mulai")
        tanggal_selesai_str = body.get("tanggal_selesai", tanggal_mulai_str)
        file_id = body.get("file_id", "default")

        # Jumlah ayam awal aman
        try:
            jumlah_ayam_awal = int(body.get("jumlah_ayam_awal", 1))
            if jumlah_ayam_awal < 1:
                jumlah_ayam_awal = 1
        except (ValueError, TypeError):
            jumlah_ayam_awal = 1

        # --- Load data CSV ---
        df, meta = load_data(file_id=file_id, user_id=user_id)
        nama_file = meta["nama_file"]
        asal_data = meta["asal_data"]

        # --- Koreksi skala ayam jika anomali (DEBUG saja) ---
        if 'jumlah_ayam' in df.columns and 'pakan_pakai' in df.columns:
            mean_ayam = df['jumlah_ayam'].mean()
            mean_pakan = df['pakan_pakai'].mean()
            if mean_ayam < 1000 and mean_pakan > 100 and mean_pakan / mean_ayam > 5:
                print("DEBUG: Data ayam tampaknya kecil dibanding pakan, tapi angka sudah dikonversi.")

        # --- Konversi tanggal ---
        tanggal_mulai = datetime.strptime(tanggal_mulai_str, "%Y-%m-%d")
        tanggal_selesai = datetime.strptime(tanggal_selesai_str, "%Y-%m-%d")
        hari = max((tanggal_selesai - tanggal_mulai).days + 1, 1)

        df['tanggal'] = pd.to_datetime(df['tanggal'])
        df = df.set_index('tanggal').sort_index()
        df_train = df[df.index < tanggal_mulai].copy()

        if df_train.empty or len(df_train["pakan_pakai"]) < 10:
            return JSONResponse(status_code=400, content={"error": "Data tidak cukup untuk pelatihan model."})

        # --- Fungsi parsing angka ribuan dan desimal ---
        def parse_number(x):
            if pd.isna(x):
                return 0.0
            x = str(x).strip()
            x = x.replace('.', '').replace(',', '.')  # titik ribuan dibuang, koma jadi desimal
            try:
                return float(x)
            except:
                return 0.0

        # --- Bersihkan angka di train ---
        for col in ['pakan_pakai','jumlah_ayam','jumlah_ayam_mati']:
            if col in df_train.columns:
                df_train[col] = df_train[col].apply(parse_number)
            else:
                df_train[col] = 0.0

        # --- Hitung ayam hidup ---
        if 'jumlah_ayam_mati' in df_train.columns:
            df_train["ayam_hidup"] = df_train["jumlah_ayam"] - df_train["jumlah_ayam_mati"].fillna(0)
            mean_ayam_mati_per_hari = df_train["jumlah_ayam_mati"].mean()
            print(f"Rata-rata ayam mati per hari (historis): {mean_ayam_mati_per_hari:.2f}")
        else:
            df_train["ayam_hidup"] = df_train["jumlah_ayam"]
            mean_ayam_mati_per_hari = 0

        df_train["ayam_hidup"] = df_train["ayam_hidup"].apply(lambda x: max(x, 1))

        # --- Hitung konsumsi per ayam & smoothing ---
        per_ayam_series = df_train["pakan_pakai"] / df_train["ayam_hidup"]
        per_ayam_series = per_ayam_series.fillna(per_ayam_series.mean())
        per_ayam_series = per_ayam_series.rolling(window=3, min_periods=1).mean()
        mean_per_ayam = float(per_ayam_series.mean())
        konsumsi_harian_per_ekor = mean_per_ayam

        # --- Latih ARIMA ---
        try:
            model, forecast_train, test, mape_train = train_arima(per_ayam_series, debug=True)
            forecast_per_ayam = np.array(model.predict(n_periods=hari))
            print(f"\n===== ARIMA INFO =====")
            print(f"Parameter ARIMA (p,d,q): {model.order if model else '-'}")
            print("=======================")
            print(f"Forecast vs Aktual (sample 5): {forecast_train[:5]} vs {test[:5]}")
        except Exception as e:
            print("WARNING: ARIMA gagal, pakai rata-rata per_ayam", e)
            forecast_per_ayam = np.full(hari, mean_per_ayam)


        # --- Hitung prediksi harian ---
        tanggal_prediksi = [tanggal_mulai + timedelta(days=i) for i in range(hari)]
        hasil_prediksi = []
        total_kg = 0.0
        ayam_hidup_prev = jumlah_ayam_awal

        # pastikan index hanya tanggal
        df.index = pd.to_datetime(df.index.date)

        # Pakai total pakan harian sebagai dasar prediksi
        # forecast_total = model.predict(n_periods=hari)  # ARIMA total pakan
        for i, tgl in enumerate(tanggal_prediksi):
            tgl_only = tgl.date()
            if tgl_only in df.index:
                ayam_hidup = max(df.loc[tgl_only, "jumlah_ayam"] - df.loc[tgl_only, "jumlah_ayam_mati"], 1)
                pakan_total = df.loc[tgl_only, aktual_col]  # langsung pakai data aktual
                per_ayam = pakan_total / ayam_hidup
            else:
                ayam_hidup = max(ayam_hidup_prev - (mean_ayam_mati_per_hari if mean_ayam_mati_per_hari > 0 else 1), 1)
                per_ayam = mean_per_ayam
                pakan_total = per_ayam * ayam_hidup

            total_kg += pakan_total
            hasil_prediksi.append({
                "x": tgl.strftime('%Y-%m-%d'),
                "y": pakan_total,
                "kg": pakan_total,
                "ayam_hidup": round(ayam_hidup, 2),
                "per_ayam": round(per_ayam, 2)
            })
            ayam_hidup_prev = ayam_hidup

        # --- Hitung total aktual (pakai pakan_aktual_total jika ada) ---
        aktual_col = 'pakan_aktual_total' if 'pakan_aktual_total' in df.columns else 'pakan_pakai'
        semua_data_aktual = [
            {"x": idx.strftime("%Y-%m-%d"),
             "y": float(row.get(aktual_col, 0)),
             "kg": float(row.get(aktual_col, 0))}
            for idx, row in df.iterrows()
        ]
        total_aktual = sum(item["kg"] for item in semua_data_aktual)
        total_karung_aktual = math.ceil(total_aktual / 50)
        total_kg = round(total_kg, 2)
        total_karung = math.ceil(total_kg / 50)

        # --- Hitung MAPE per ayam dan total ---
        df_aktual_periode = df[(df.index >= tanggal_mulai) & (df.index <= tanggal_selesai)].copy()
        if not df_aktual_periode.empty:
            df_pred = pd.DataFrame(hasil_prediksi).set_index('x')
            df_actual = df_aktual_periode[[aktual_col, 'jumlah_ayam']].copy()
            df_actual.index = df_actual.index.strftime('%Y-%m-%d')
            df_merge = df_pred.join(df_actual, how='inner')

            forecast_per_ayam_values = df_merge['per_ayam'].values
            actual_per_ayam = (df_merge[aktual_col] / df_merge['ayam_hidup']).values
            mape_per_ayam = hitung_mape_stabil(forecast_per_ayam_values, actual_per_ayam)

            # --- Hitung MAPE total keseluruhan ---
            total_prediksi_keseluruhan = df_merge['kg'].sum()
            total_aktual_keseluruhan = df_merge[aktual_col].sum()
            mape_total = abs(total_prediksi_keseluruhan - total_aktual_keseluruhan) / total_aktual_keseluruhan * 100

            # --- Hitung MAPE harian rata-rata ---
            mape_harian_list = []
            for idx, row in df_merge.iterrows():
                pred = row['kg']
                act = row[aktual_col]
                act_safe = max(act, 50)  # hindari pembagian nol
                mape_harian_list.append(abs(pred - act) / act_safe * 100)

            if len(mape_harian_list) > 0:
                mape_harian = round(sum(mape_harian_list) / len(mape_harian_list), 3)
            else:
                mape_harian = None
        else:
            # Kalau tidak ada data aktual di periode itu
            mape_per_ayam = None
            mape_total = None
            mape_harian = None


        # --- Print summary & detail harian ---
        print("\n===== SUMMARY PREDIKSI PER AYAM =====")
        print(f"Total pakan aktual     : {total_aktual:.2f} kg | {total_karung_aktual} karung")
        print(f"Total pakan prediksi   : {total_kg:.2f} kg | {total_karung} karung")
        print(f"Durasi hari            : {hari} hari")
        print(f"Konsumsi harian/ekor   : {mean_per_ayam:.2f} kg/ekor")
        print(f"MAPE per ayam          : {mape_per_ayam}")
        print(f"MAPE total pakan       : {mape_total}\n")
        print("===== DETAIL HARIAN =====")
        print(f"{'Tanggal':<12} | {'Prediksi (kg)':>12} | {'Aktual (kg)':>12} | {'Selisih (kg)':>14}")
        print("-" * 60)
        for item in hasil_prediksi:
            tgl = item["x"]
            prediksi_kg = item["kg"]
            tgl_only = pd.to_datetime(tgl).date()
            if tgl_only in df.index.date:
                aktual_kg = float(df.loc[df.index.date == tgl_only, aktual_col].iloc[0])
                selisih_kg = prediksi_kg - aktual_kg
            else:
                aktual_kg = None
                selisih_kg = None
            print(f"{tgl:<12} | {prediksi_kg:12.2f} | {aktual_kg if aktual_kg is not None else '-':12} | {selisih_kg if selisih_kg is not None else '-':14}")
        print("-" * 60)

        # --- Simpan ke DB ---
        catatan = f"Mode prediksi per ayam menggunakan input jumlah ayam awal ({jumlah_ayam_awal} ekor)."
        summary = {
            "total_prediksi_kg": total_kg,
            "total_prediksi_karung": total_karung,
            "total_aktual_kg": round(total_aktual, 2),
            "total_aktual_karung": total_karung_aktual,
            "jumlah_ayam_awal": jumlah_ayam_awal,
            "durasi_hari": hari,
            "konsumsi_harian_per_ekor": round(konsumsi_harian_per_ekor, 2),
            "catatan": catatan,
            "mape": round(mape_total, 2) if mape_total is not None else None,
            "mape_harian": round(mape_harian, 2) if mape_harian is not None else None
        }

        riwayat_id = None
        conn = get_db_connection()
        try:
            with conn.cursor(buffered=True) as cursor:
                cursor.execute("""
                INSERT INTO riwayat (
                    user_id, tanggal_mulai, tanggal_selesai, durasi, jumlah_ayam_awal, 
                    mode_prediksi, prediksi, data_aktual, total_pakan_kg, total_karung, 
                    asal_data, nama_file, activity, mape, mape_harian, created_at, updated_at
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())
            """, (
                user_id,
                tanggal_mulai_str,
                tanggal_selesai_str,
                hari,
                jumlah_ayam_awal,
                "per_ayam",
                json.dumps(hasil_prediksi),
                json.dumps(semua_data_aktual),
                total_kg,
                total_karung,
                asal_data,
                nama_file,
                f"Prediksi per_ayam {tanggal_mulai_str} s/d {tanggal_selesai_str}",
                mape_total,
                mape_harian
            ))

                riwayat_id = cursor.lastrowid
                conn.commit()
        finally:
            conn.close()

        return JSONResponse({
            "data_prediksi": hasil_prediksi,
            "data_aktual": semua_data_aktual,
            "summary": summary,
            "riwayat_id": riwayat_id,
            "mape_per_ayam": mape_per_ayam,
            "mape_total": mape_total
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
        html_content = f"""
        <html>
        <head>
        <style>
            @page {{ margin: 20px; }}
            body {{ font-family: 'Helvetica', 'Arial', sans-serif; font-size: 12px; color: #333; }}
            h2 {{
                text-align: center; 
                font-family: 'Georgia', serif; 
                font-size: 28px; 
                font-weight: bold; 
                margin-bottom: 5px; 
                color: #155724; 
                text-shadow: 1px 1px #a8d5ba;
            }}
            h3 {{
                text-align: center; 
                font-size: 14px; 
                color: #155724; 
                margin-top: 0;
            }}
            h4 {{ 
                margin-top: 20px; 
                font-size: 16px; 
                color: #155724; 
                font-weight: bold; 
                border-bottom: 2px solid #28a745;
                padding-bottom: 3px;
            }}
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin-top: 10px; 
                font-size: 12px;
            }}
            th, td {{ 
                border: 1px solid #28a745; 
                padding: 8px; 
            }}
            th {{ 
                background-color: #28a745; 
                color: #fff; 
                text-align: center; 
            }}
            td {{ 
                text-align: center; 
            }}
            tr:nth-child(even) td {{ 
                background-color: #eafaf1; 
            }}
            .summary-table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin-top: 5px; 
                font-size: 12px;
            }}
            .summary-table th, .summary-table td {{ 
                border: 1px solid #28a745; 
                padding: 6px 10px; 
                color: #155724;
            }}
            .summary-table th {{ 
                width: 50%; 
                text-align: right; 
                background-color: #d4edda;
            }}
            .summary-table td {{ 
                width: 50%; 
                text-align: left; 
                background-color: #f9fff9;
            }}
        </style>
        </head>
        <body>
            <h2>Hasil Prediksi Kebutuhan Pakan Ayam</h2>
            <h3>{start_date.strftime('%d %B %Y')} - {end_date.strftime('%d %B %Y')}</h3>

            <!-- Tabel Data Prediksi -->
            <h4>Data Prediksi</h4>
            <table>
                <tr>
                    <th>Tanggal</th>
                    <th>Prediksi (kg)</th>
                    <th>Estimasi Karung (50kg)</th>
                </tr>
        """

        # isi tabel prediksi
        for dt in semua_tanggal:
            val = prediksi_map.get(dt, 0)
            karung = math.ceil(val / 50)
            html_content += f"<tr><td>{dt.strftime('%d %B %Y')}</td><td>{val:.2f}</td><td>{karung}</td></tr>"

        html_content += "</table>"

        # Ringkasan Prediksi
        html_content += "<h4>Ringkasan Prediksi</h4>"
        html_content += '<table class="summary-table">'

        # isi ringkasan
        for key, val in summary.items():
            if isinstance(val, float):
                val_display = f"{val:.2f}"
            elif isinstance(val, int):
                val_display = f"{val:,}"
            else:
                val_display = val
            html_content += f"<tr><th>{key.replace('_',' ').capitalize()}</th><td>{val_display}</td></tr>"

        html_content += "</table>"
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

