import warnings
from statsmodels.tools.sm_exceptions import ValueWarning
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=ValueWarning)
warnings.filterwarnings("ignore")

import os
from xhtml2pdf import pisa
import io
import csv
import math
import json
import uuid
import hashlib
import json
import traceback
from datetime import datetime, timedelta
from typing import List
import jwt
from typing import Optional
import secrets
import pandas as pd
import numpy as np
from pmdarima import auto_arima
from fastapi import (
    FastAPI, Request, UploadFile, File, Depends, HTTPException, Header, Body, Path
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from auth import router as auth_router
from database import get_db_connection
from fastapi.responses import JSONResponse, FileResponse
import pandas as pd
import numpy as np
from pmdarima import auto_arima
from datetime import datetime, timedelta
import traceback
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from fastapi import HTTPException
from fastapi.templating import Jinja2Templates 
from auth import router as auth_router
from database import get_db_connection
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

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

@app.get("/api/ping")
def ping():
    return {"msg": "pong"}


# --------- JWT Config ---------
SECRET_KEY = os.environ.get("SECRET_KEY", "ini_kunci_rahasia_default")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# --------- Schemas ---------
class RegisterSchema(BaseModel):
    name: str
    email: str
    password: str

class LoginSchema(BaseModel):
    email: str
    password: str

# --------- Hash Password ---------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# --------- Dependency Cek User ---------
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("user_id") is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload  # sekarang return full payload, bukan cuma user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token sudah kadaluarsa, silakan login lagi")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token tidak valid")

# --------- Endpoint Register ---------
@app.post("/api/register")
def register(data: RegisterSchema):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # cek email sudah ada?
    cursor.execute("SELECT * FROM users WHERE email=%s", (data.email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")

    hashed = hash_password(data.password)
    cursor.execute(
        "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
        (data.name, data.email, hashed, "user")  # default role = user
    )
    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "User berhasil didaftarkan!"}

# --------- Endpoint Login ---------
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
    if user['password'] != hash_password(data.password):
        raise HTTPException(status_code=401, detail="Password salah")

    # 🔑 pakai helper create_access_token
    token = create_access_token(
        data={"user_id": user["id"], "role": user["role"]},
        # expires_delta=timedelta(seconds=40)  
        expires_delta=timedelta(hours=1)
    )

    return {
        "access_token": token,
        "role": user["role"],
        "name": user["name"]
    }

# --------- Endpoint Dashboard ---------
@app.get("/api/dashboard")
def dashboard(user: dict = Depends(get_current_user)):
    return {"msg": "Ini halaman dashboard", "user_id": user["user_id"], "role": user["role"]}

# --------- Endpoint Admin Dashboard ---------
@app.get("/api/admin/dashboard")
def admin_dashboard(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Hanya admin yang bisa akses")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # jumlah prediksi
    cursor.execute("SELECT COUNT(*) AS total FROM prediksi")
    prediksi_count = cursor.fetchone()["total"]

    # jumlah riwayat
    cursor.execute("SELECT COUNT(*) AS total FROM riwayat")
    riwayat_count = cursor.fetchone()["total"]

    # jumlah user
    cursor.execute("SELECT COUNT(*) AS total FROM users")
    users_count = cursor.fetchone()["total"]

    # ambil 5 aktivitas terakhir
    cursor.execute("SELECT activity, created_at FROM riwayat ORDER BY created_at DESC LIMIT 5")
    recent = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "stats": {
            "prediksi": prediksi_count,
            "riwayat": riwayat_count,
            "users": users_count
        },
        "recent": [
            {"activity": r["activity"], "time": str(r["created_at"])}
            for r in recent
        ]
    }

# ----- Endpoint Ambil Semua User -----
@app.get("/api/users")
def get_users(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":  # hanya admin yang boleh
        raise HTTPException(status_code=403, detail="Akses ditolak")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email, role, created_at, updated_at FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users

# ----- Endpoint Update Role User -----
@app.put("/api/users/{user_id}")
def update_user_role(user_id: int, data: dict, user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Akses ditolak")

    new_role = data.get("role")
    if new_role not in ["admin", "user"]:
        raise HTTPException(status_code=400, detail="Role tidak valid")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id=%s", (user_id,))
    if cursor.fetchone() is None:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    cursor.execute("UPDATE users SET role=%s WHERE id=%s", (new_role, user_id))
    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "Role user berhasil diperbarui"}

# ----- Endpoint Ambil Semua User (hanya admin) -----
@app.get("/api/admin/users")
def get_all_users(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Hanya admin yang bisa mengakses")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email, role FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users

# ----- Endpoint Update Role User -----
@app.put("/api/admin/users/{user_id}")
def update_user_role(user_id: int, data: dict, user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Hanya admin yang bisa mengubah role")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role=%s WHERE id=%s", (data["role"], user_id))
    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "Role berhasil diperbarui"}

#---Endpoint Admin Riwayat---#
@app.get("/api/admin/riwayat")
def get_admin_riwayat(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Hanya admin yang bisa mengakses")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.id, r.tanggal_mulai, r.tanggal_selesai, r.durasi, r.mape, r.total_karung,
               u.name AS user_name
        FROM riwayat r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.created_at DESC
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return {"data": data}  # harus 'data' supaya Vue bisa baca

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

        # Filter prediksi & data aktual sesuai durasi
        prediksi = []
        total_kg = total_karung = total_per_ayam = 0
        for p in pred_list_raw:
            try:
                x_dt = datetime.fromisoformat(p.get("x", "").split("T")[0])
            except:
                continue
            if tgl_mulai_dt and tgl_selesai_dt and not (tgl_mulai_dt <= x_dt <= tgl_selesai_dt):
                continue
            kg = p.get("kg", 0)
            prediksi.append({
                "x": p.get("x", ""),
                "y": kg,
                "kg": kg,
                "ayam_hidup": p.get("ayam_hidup", 0),
                "per_ayam": p.get("per_ayam", 0),
                "periode": p.get("periode")
            })
            total_kg += kg
            total_karung += p.get("y", 0)
            total_per_ayam += p.get("per_ayam", 0)

        data_aktual = []
        for a in aktual_raw:
            try:
                x_raw = a.get("x", "")
                x_dt = datetime.fromisoformat(x_raw.split("T")[0]) if x_raw else None
            except:
                x_dt = None

            if tgl_mulai_dt and tgl_selesai_dt and x_dt and not (tgl_mulai_dt <= x_dt <= tgl_selesai_dt):
                continue

            kg = a.get("kg", a.get("y", 0)) or 0  # fallback ke 0 jika kosong
            data_aktual.append({
                "x": x_dt.strftime("%Y-%m-%d") if x_dt else "",
                "y": kg,
                "kg": kg,
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

        hari = row.get("durasi", len(prediksi))
        jumlah_ayam_awal = prediksi[0].get("ayam_hidup", 0) if prediksi else 0
        perkiraan_akhir_ayam = prediksi[-1].get("ayam_hidup", 0) if prediksi else 0
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
            "user_name": row.get("user_id")  # bisa diganti dengan join ke table user kalau mau nama
        }

        return response

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.delete("/api/admin/riwayat/{riwayat_id}")
def delete_admin_riwayat(riwayat_id: int, user=Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM riwayat WHERE id = %s", (riwayat_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Riwayat berhasil dihapus"}

@app.get("/api/admin/prediksi")
def get_admin_prediksi(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Hanya admin yang bisa mengakses")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.id, p.riwayat_id, p.tanggal_mulai, p.tanggal_selesai,
               p.mode_prediksi, p.total_karung, p.jumlah_ayam,
               u.name AS user_name
        FROM prediksi p
        JOIN riwayat r ON p.riwayat_id = r.id
        JOIN users u ON r.user_id = u.id
        ORDER BY p.created_at DESC
    """)
    prediksi = cursor.fetchall()
    cursor.close()
    conn.close()

    return {"prediksi": prediksi}


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

@app.post("/riwayat")
async def simpan_riwayat(data: dict, current_user: dict = Depends(get_current_user)):
    current_user_id = current_user.get("user_id")
    conn = None
    cursor = None
    try:
        # Ambil prediksi dan data aktual
        prediksi_list = data.get("prediksi", [])
        data_aktual_list = data.get("data_aktual", [])

        # Hitung total karung
        total_karung = sum(float(item.get("y", 0)) for item in prediksi_list)

        # Tanggal dan durasi
        tanggal_mulai = datetime.fromisoformat(data.get("tanggal_mulai"))
        tanggal_selesai = datetime.fromisoformat(data.get("tanggal_selesai"))
        durasi = (tanggal_selesai - tanggal_mulai).days + 1

        # MAPE
        mape_value = float(data.get("mape", 0))

        # Koneksi DB
        conn = get_db_connection()
        # buffered=True supaya tidak ada unread result
        cursor = conn.cursor(dictionary=True, buffered=True)

        # Cek duplikasi
        cursor.execute(
            "SELECT id FROM riwayat WHERE tanggal_mulai=%s AND tanggal_selesai=%s AND user_id=%s",
            (tanggal_mulai.strftime("%Y-%m-%d"), tanggal_selesai.strftime("%Y-%m-%d"), current_user_id)
        )
        existing = cursor.fetchone()
        if existing:
            return JSONResponse(
                content={"message": "Riwayat untuk periode ini sudah ada", "id": existing["id"]}
            )

        # Insert ke tabel riwayat
        sql_riwayat = """
            INSERT INTO riwayat 
            (user_id, tanggal_mulai, tanggal_selesai, durasi, prediksi, data_aktual, total_karung, mape)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        val_riwayat = (
            current_user_id,
            tanggal_mulai.strftime("%Y-%m-%d"),
            tanggal_selesai.strftime("%Y-%m-%d"),
            durasi,
            json.dumps(prediksi_list),
            json.dumps(data_aktual_list),
            total_karung,
            mape_value
        )
        cursor.execute(sql_riwayat, val_riwayat)
        conn.commit()
        riwayat_id = cursor.lastrowid

        # Simpan prediksi per hari ke tabel prediksi
        for p in prediksi_list:
            tanggal = p.get("x")
            if isinstance(tanggal, dict):
                tanggal = tanggal.get("tanggal")
            if not tanggal:
                continue

            mode = p.get("mode_prediksi", "per_ayam")
            total = float(p.get("y", 0))
            jumlah_ayam = int(p.get("jumlah_ayam", 0))

            sql_pred = """
                INSERT INTO prediksi 
                (riwayat_id, tanggal_mulai, tanggal_selesai, mode_prediksi, total_karung, jumlah_ayam)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            val_pred = (
                riwayat_id,
                tanggal,
                tanggal,
                mode,
                total,
                jumlah_ayam
            )
            cursor.execute(sql_pred, val_pred)

        conn.commit()
        return {"message": "Data riwayat berhasil disimpan", "id": riwayat_id}

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.get("/riwayat")
async def get_riwayat(current_user: dict = Depends(get_current_user)):
    current_user_id = current_user.get("user_id")
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM riwayat WHERE user_id=%s ORDER BY id DESC", 
            (current_user_id,)
        )
        rows = cursor.fetchall()

        result = []
        for row in rows:
            # Parsing JSON dengan aman
            try:
                prediksi = json.loads(row.get('prediksi') or '[]')
            except (TypeError, json.JSONDecodeError):
                prediksi = []

            try:
                data_aktual = json.loads(row.get('data_aktual') or '[]')
            except (TypeError, json.JSONDecodeError):
                data_aktual = []

            result.append({
                "id": row['id'],
                "tanggal_mulai": row['tanggal_mulai'].strftime("%Y-%m-%d") if row['tanggal_mulai'] else None,
                "tanggal_selesai": row['tanggal_selesai'].strftime("%Y-%m-%d") if row['tanggal_selesai'] else None,
                "durasi": row.get('durasi') or 0,
                "prediksi": prediksi,
                "data_aktual": data_aktual,
                "total_karung": row.get('total_karung') if row.get('total_karung') is not None else sum([p.get('y', 0) for p in prediksi]),
                "mape": row.get('mape') or 0,
                "asal_data": row.get('asal_data') or 'Default',
                "nama_file": row.get('nama_file') or 'Default',
            })

        return {"riwayat": result}

    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# ===============================
# Hapus semua riwayat user
# ===============================
@app.delete("/riwayat")
async def hapus_semua_riwayat(current_user: dict = Depends(get_current_user)):
    current_user_id = current_user.get("user_id")
    if not current_user_id:
        raise HTTPException(status_code=401, detail="User tidak valid")

    conn = cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM riwayat WHERE user_id=%s", (current_user_id,))
        conn.commit()
        return {"message": "Semua data riwayat Anda berhasil dihapus"}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ===============================
# Hapus riwayat tertentu milik user
# ===============================
@app.delete("/riwayat/{riwayat_id}")
async def hapus_riwayat(
    riwayat_id: int = Path(..., description="ID riwayat yang ingin dihapus"),
    current_user: dict = Depends(get_current_user)
):
    current_user_id = current_user.get("user_id")
    if not current_user_id:
        raise HTTPException(status_code=401, detail="User tidak valid")

    conn = cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM riwayat WHERE id=%s AND user_id=%s",
            (riwayat_id, current_user_id)
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
        if cursor: cursor.close()
        if conn: conn.close()

# ===============================
# Ambil detail riwayat milik user
# ===============================
@app.get("/riwayat/{id}/detail")
async def get_riwayat_detail(id: int, current_user: dict = Depends(get_current_user)):
    current_user_id = current_user.get("user_id")
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM riwayat WHERE id=%s AND user_id=%s", (id, current_user_id))
        row = cursor.fetchone()

        if not row:
            return JSONResponse(status_code=404, content={"error": "Riwayat tidak ditemukan"})

        # Konversi tanggal
        tanggal_mulai = row['tanggal_mulai']
        tanggal_selesai = row['tanggal_selesai']
        tgl_mulai_dt = datetime.combine(tanggal_mulai, datetime.min.time()) if tanggal_mulai else None
        tgl_selesai_dt = datetime.combine(tanggal_selesai, datetime.min.time()) if tanggal_selesai else None

        # Parse JSON
        try:
            pred_list = json.loads(row.get('prediksi', '[]'))
        except:
            pred_list = []
        try:
            aktual_raw = json.loads(row.get("data_aktual", "[]"))
        except:
            aktual_raw = []

        # Filter prediksi & aktual sesuai rentang tanggal
        prediksi = []
        total_kg = total_karung = total_per_ayam = 0
        for p in pred_list:
            try:
                x_dt = datetime.fromisoformat(p.get("x", "").split("T")[0])
            except:
                continue
            if tgl_mulai_dt and tgl_selesai_dt and not (tgl_mulai_dt <= x_dt <= tgl_selesai_dt):
                continue
            kg = p.get("kg", 0)
            prediksi.append({
                "x": p.get("x", ""),
                "y": kg,
                "kg": kg,
                "ayam_hidup": p.get("ayam_hidup", 0),
                "per_ayam": p.get("per_ayam", 0),
                "periode": p.get("periode")
            })
            total_kg += kg
            total_karung += p.get("y", 0)
            total_per_ayam += p.get("per_ayam", 0)

        data_aktual = []
        for a in aktual_raw:
            try:
                x_dt = datetime.fromisoformat(a.get("x", "").split("T")[0])
            except:
                continue
            if tgl_mulai_dt and tgl_selesai_dt and not (tgl_mulai_dt <= x_dt <= tgl_selesai_dt):
                continue
            # Ambil nilai kg sesuai semua kemungkinan key dari CSV
            kg = a.get("kg") or a.get("y") or a.get("stok") or a.get("jumlah_pakan") or 0
            data_aktual.append({
                "x": a.get("x", ""),
                "y": kg,
                "kg": kg,
                "periode": a.get("periode")
            })

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

        hari = row.get("durasi", len(prediksi))
        jumlah_ayam_awal = prediksi[0]["ayam_hidup"] if prediksi else 0
        perkiraan_akhir_ayam = prediksi[-1]["ayam_hidup"] if prediksi else 0
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
            "id": row['id'],
            "tanggal_mulai": tanggal_mulai.strftime("%Y-%m-%d") if tanggal_mulai else None,
            "tanggal_selesai": tanggal_selesai.strftime("%Y-%m-%d") if tanggal_selesai else None,
            "durasi": hari,
            "prediksi": prediksi,
            "data_aktual": data_aktual,
            "summary": summary,
            "nama_file": row.get('nama_file'),
            "asal_data": row.get('asal_data')
        }

        return JSONResponse(content=response)

    finally:
        if cursor: cursor.close()
        if conn: conn.close()
        
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

# ================================
# ENDPOINT UNTUK FITUR DATA PAKAN
# ================================
DATA_KELOLA_PAKAN = "data/kelola_pakan.json"
os.makedirs("data", exist_ok=True)

# ===== Helper Functions =====
def load_kelola_pakan():
    if not os.path.exists(DATA_KELOLA_PAKAN):
        return []
    with open(DATA_KELOLA_PAKAN, "r") as f:
        return json.load(f)

def save_kelola_pakan(data):
    with open(DATA_KELOLA_PAKAN, "w") as f:
        json.dump(data, f, indent=2)


# ===========================
# Endpoint Untuk Data Pakan
# ===========================
@app.post("/save_csv_preview")
async def save_csv_preview(request: Request, current_user: int = Depends(get_current_user)):
    body = await request.json()
    file_name = body.get("fileName")
    upload_date = body.get("uploadDate")
    rows = body.get("rows", [])

    if not file_name or not upload_date or not rows:
        return JSONResponse(status_code=400, content={"error": "Data tidak lengkap"})

    new_id = str(uuid.uuid4())
    os.makedirs(DATA_DIR, exist_ok=True)
    file_path = os.path.join(DATA_DIR, new_id + ".csv")

    df = pd.DataFrame(rows)
    df.to_csv(file_path, index=False)

    file_entry = {
        "id": new_id,
        "fileName": file_name,
        "uploadDate": upload_date,
        "dataCSV": rows,
        "user_id": current_user  # <-- perbaikan di sini
    }
    file_storage.append(file_entry)
    save_metadata()

    return {"status": "Berhasil disimpan", "id": new_id}


#---endpoint update csv yang di upload di data pakan vue---
@app.post("/update_csv_preview")
async def update_csv_preview(request: Request, current_user: int = Depends(get_current_user)):
    body = await request.json()
    file_id = body.get("id")
    file_name = body.get("fileName")
    upload_date = body.get("uploadDate")
    rows = body.get("rows", [])

    if not file_id or not file_name or not upload_date or not rows:
        return JSONResponse(status_code=400, content={"error": "Data tidak lengkap"})

    # cari file sesuai user
    index = next((i for i, f in enumerate(file_storage)
                  if f["id"] == file_id and f["user_id"] == current_user), None)
    if index is None:
        return JSONResponse(status_code=404, content={"error": "File tidak ditemukan atau bukan milik user"})

    # simpan CSV
    file_path = os.path.join(DATA_DIR, str(file_id) + ".csv")
    df = pd.DataFrame(rows)
    df.to_csv(file_path, index=False)

    # update metadata
    file_storage[index]["fileName"] = file_name
    file_storage[index]["uploadDate"] = upload_date
    file_storage[index]["dataCSV"] = rows
    save_metadata()

    return {"status": "Berhasil diperbarui"}

#---endpoint list csv di data pakan vue---
@app.get("/list_csv_files")
async def list_csv_files(current_user: dict = Depends(get_current_user)):
    user_files = [f for f in file_storage if f.get("user_id") == current_user["user_id"]]
    return {"files": user_files}


#---endpoint delete csv di data pakan vue---
@app.delete("/delete_csv/{file_id}")
async def delete_csv(file_id: str, current_user: int = Depends(get_current_user)):
    index = next(
        (i for i, f in enumerate(file_storage)
         if f["id"] == file_id and f["user_id"] == current_user),  # <-- ganti di sini
        None
    )
    if index is None:
        return JSONResponse(status_code=404, content={"error": "File tidak ditemukan atau bukan milik user"})

    file_path = os.path.join(DATA_DIR, file_id + ".csv")
    if os.path.exists(file_path):
        os.remove(file_path)

    file_storage.pop(index)
    save_metadata()
    return {"status": "File berhasil dihapus"}

@app.get("/download_csv/{file_id}")
async def download_csv(file_id: str):
    file_path = os.path.join(DATA_DIR, f"{file_id}.csv")
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"error": "File tidak ditemukan"})

    return FileResponse(
        file_path,
        filename=f"hasil_prediksi_{file_id}.csv",
        media_type='text/csv'
    )
# ==========================================
# Endpoint Kelola Pakan di Fitur Data Pakan
# ===========================================
@app.post("/kelola_pakan")
async def input_update_kelola_pakan(
    data: dict = Body(...),
    user_id: str = Header(None)  # bisa None jika tidak dikirim
):
    if not user_id:
        user_id = "default_user"  # fallback supaya tidak 422

    tanggal = data.get("tanggal")
    stok = data.get("stok")
    jumlah_ayam = data.get("jumlahAyam")

    if not tanggal or stok is None or jumlah_ayam is None:
        return {"error": "Field tanggal, stok, dan jumlahAyam wajib diisi"}

    kelola_data = load_kelola_pakan()

    # Cari record yang sama untuk user ini
    index = next(
        (i for i, item in enumerate(kelola_data)
         if item["tanggal"] == tanggal and item.get("user_id") == user_id),
        None
    )

    if index is not None:
        kelola_data[index]["stok"] = stok
        kelola_data[index]["jumlahAyam"] = jumlah_ayam
    else:
        kelola_data.append({
            "tanggal": tanggal,
            "stok": stok,
            "jumlahAyam": jumlah_ayam,
            "user_id": user_id
        })

    kelola_data.sort(key=lambda x: x["tanggal"])
    save_kelola_pakan(kelola_data)

    user_data = [d for d in kelola_data if d.get("user_id") == user_id]

    return {"status": "Berhasil input/update kelola pakan", "data": user_data}

@app.get("/kelola_pakan")
async def get_kelola_pakan(user_id: str = Header(None)):
    if not user_id:
        user_id = "default_user"

    kelola_data = load_kelola_pakan()
    kelola_data.sort(key=lambda x: x["tanggal"])
    # Filter per user
    user_data = [d for d in kelola_data if d.get("user_id") == user_id]
    return user_data

# ===== Endpoint Notif Stok Pakan =====
@app.get("/notif_stok_pakan")
async def notif_stok_pakan(user_id: str = Header(None)):
    if not user_id:
        user_id = "default_user"

    kelola_data = load_kelola_pakan()
    # Filter data user ini
    kelola_data = [d for d in kelola_data if d.get("user_id") == user_id]

    if not kelola_data:
        return {"error": "Data kelola pakan kosong"}

    terakhir = kelola_data[-1]
    stok_karung_terakhir = terakhir.get("stok", 0)
    jumlah_ayam_terakhir = terakhir.get("jumlahAyam", 0)
    tanggal_terakhir = terakhir.get("tanggal")

    try:
        df = load_data()
    except Exception:
        return {"error": "Gagal load data pakan ayam"}

    if df.empty or jumlah_ayam_terakhir == 0:
        return {"error": "Data pakan atau jumlah ayam tidak valid"}

    konsumsi_per_ayam_per_hari = (df["pakan_pakai"] / df["jumlah_ayam"]).mean()

    if konsumsi_per_ayam_per_hari == 0 or konsumsi_per_ayam_per_hari is None or np.isnan(konsumsi_per_ayam_per_hari):
        return {"error": "Data konsumsi pakan per ayam tidak valid"}

    kebutuhan_pakan_harian_kg = konsumsi_per_ayam_per_hari * jumlah_ayam_terakhir
    kebutuhan_pakan_harian_karung = kebutuhan_pakan_harian_kg / 50

    if kebutuhan_pakan_harian_karung == 0:
        return {"error": "Kebutuhan pakan per hari tidak valid"}

    hari_stok_cukup = math.floor(stok_karung_terakhir / kebutuhan_pakan_harian_karung)

    return {
        "tanggal": tanggal_terakhir,
        "stok_karung": stok_karung_terakhir,
        "jumlah_ayam": jumlah_ayam_terakhir,
        "konsumsi_per_ayam_per_hari_kg": round(konsumsi_per_ayam_per_hari, 2),
        "kebutuhan_pakan_harian_karung": round(kebutuhan_pakan_harian_karung, 2),
        "estimasi_hari_stok_cukup": hari_stok_cukup,
        "pesan": f"Stok pakan cukup untuk sekitar {hari_stok_cukup} hari berdasarkan jumlah ayam dan konsumsi rata-rata"
    }
    
# ----- Endpoint predict_periode -----
# ----- Endpoint predict_periode -----
# ----- Endpoint predict_periode -----
@app.post("/predict_periode")
async def predict_periode(request: Request):
    try:
        # --- Authorization ---
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            raise HTTPException(status_code=401, detail="Token format salah")
        payload = get_current_user(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User tidak valid")

        # --- Request body ---
        body = await request.json()
        tanggal_mulai_str = body.get("tanggal_mulai")
        tanggal_selesai_str = body.get("tanggal_selesai")
        file_id = body.get("file_id")

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
        model = train_arima(df_train["pakan_pakai"])
        print(f"[PERIODE] ARIMA PDQ yang digunakan: {model.order}")
        print(f"[PERIODE] Jumlah kolom NaN pada data training: {df_train['pakan_pakai'].isna().sum()}")

        # --- Prediksi ---
        forecast = model.predict(n_periods=n_periods)
        forecast = np.array(forecast)  # aman untuk indexing
        print(f"[PERIODE] Jumlah data pakan yang diprediksi: {len(forecast)}")
        print(f"[PERIODE] Jumlah data aktual: {len(df)}")
        print(f"[PERIODE] Durasi prediksi: {n_periods} hari")
        print(f"[PERIODE] Tanggal mulai: {tanggal_mulai_str}, tanggal selesai: {tanggal_selesai_str}")

        # --- Data prediksi ---
        tanggal_prediksi = [tanggal_mulai + timedelta(days=i) for i in range(n_periods)]
        data_prediksi = []
        for t, p in zip(tanggal_prediksi, forecast):
            kg = round(float(p),2) if not pd.isna(p) else 0.0
            karung = round(kg/50,2)
            data_prediksi.append({
                "x": t.strftime("%Y-%m-%d"),
                "y": karung,
                "kg": kg,
                "periode": None
            })

        # --- Data aktual ---
        semua_data_aktual = [
            {
                "x": idx.strftime("%Y-%m-%d"),
                "y": round(float(row['pakan_pakai'])/50,2) if 'pakan_pakai' in row else 0.0,
                "kg": round(float(row['pakan_pakai']),2) if 'pakan_pakai' in row else 0.0,
                "periode": int(row['periode']) if 'periode' in row and pd.notna(row['periode']) else None
            }
            for idx, row in df.iterrows()
        ]

        # --- Summary ---
        total_kg = sum(f["kg"] for f in data_prediksi)
        total_karung = sum(f["y"] for f in data_prediksi)
        rata_mati = df['jumlah_ayam_mati'].mean() if 'jumlah_ayam_mati' in df else 0
        prediksi_jumlah_ayam = int(max(0, df['jumlah_ayam'].iloc[-1] - rata_mati*n_periods))

        # --- Print summary di terminal ---
        print(f"[PERIODE] Total Pakan\t{round(total_kg,2)} kg")
        print(f"[PERIODE] Total Karung (50kg)\t{round(total_karung,2)} karung")

        # --- Simpan ke DB ---
        riwayat_id = None
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO riwayat (user_id,tanggal_mulai,tanggal_selesai,durasi,prediksi,data_aktual,total_karung)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """
                val = (
                    user_id,
                    tanggal_mulai.strftime("%Y-%m-%d"),
                    tanggal_selesai.strftime("%Y-%m-%d"),
                    n_periods,
                    json.dumps(data_prediksi),
                    json.dumps(semua_data_aktual),
                    total_karung
                )
                cursor.execute(sql, val)
                conn.commit()
                riwayat_id = cursor.lastrowid
        finally:
            conn.close()

        # --- Return response frontend ---
        return JSONResponse({
            "data_prediksi": data_prediksi,
            "data_aktual": semua_data_aktual,
            "summary": {
                "total_prediksi_kg": round(total_kg,2),
                "total_prediksi_karung": round(total_karung,2),
                "prediksi_jumlah_ayam": prediksi_jumlah_ayam,
                "rata_mati_per_hari": round(float(rata_mati),2),
                "durasi_hari": n_periods
            },
            "riwayat_id": riwayat_id
        })

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})




# ----- Endpoint predict_per_ayam -----
@app.post("/predict_per_ayam")
async def predict_per_ayam(request: Request, data: DataPakan):
    try:
        # --- Authorization ---
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            raise HTTPException(status_code=401, detail="Token format salah")
        payload = get_current_user(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User tidak valid")

        # --- Parsing tanggal ---
        tanggal_mulai = datetime.strptime(data.tanggal_mulai, "%Y-%m-%d")
        tanggal_selesai = datetime.strptime(getattr(data, "tanggal_selesai", data.tanggal_mulai), "%Y-%m-%d")
        hari = (tanggal_selesai - tanggal_mulai).days + 1
        jumlah_ayam_awal = int(data.jumlah_ayam_awal)
        file_id = getattr(data, "file_id", None)

        # --- Load CSV & Training ---
        df = load_data(file_id=file_id)
        df['tanggal'] = pd.to_datetime(df['tanggal'])
        df = df.set_index('tanggal').sort_index()
        df_train = df[df.index < tanggal_mulai].copy()

        if df_train.empty or len(df_train["pakan_pakai"]) < 10:
            return JSONResponse(status_code=400, content={"error": "Data tidak cukup untuk pelatihan model."})

        # --- Train ARIMA per ayam ---
        per_ayam_series = df_train["pakan_pakai"] / df_train["jumlah_ayam"].replace(0,1)
        model = train_arima(per_ayam_series)
        print(f"[PER_AYAM] ARIMA PDQ yang digunakan: {model.order}")
        print(f"[PER_AYAM] Jumlah kolom NaN pada data training: {per_ayam_series.isna().sum()}")

        # --- Prediksi ---
        forecast = model.predict(n_periods=hari)
        forecast = np.array(forecast)
        print(f"[PER_AYAM] Jumlah data pakan yang diprediksi: {len(forecast)}")
        print(f"[PER_AYAM] Jumlah data aktual: {len(df)}")
        print(f"[PER_AYAM] Durasi prediksi: {hari} hari")
        print(f"[PER_AYAM] Tanggal mulai: {tanggal_mulai.strftime('%Y-%m-%d')}, tanggal selesai: {tanggal_selesai.strftime('%Y-%m-%d')}")
        print(f"[PER_AYAM] Jumlah ayam awal: {jumlah_ayam_awal}")

        tanggal_prediksi = [tanggal_mulai + timedelta(days=i) for i in range(hari)]
        hasil_prediksi = []
        ayam_hidup = jumlah_ayam_awal
        total_kg = 0
        total_karung = 0
        rata_mati = df['jumlah_ayam_mati'].mean() if 'jumlah_ayam_mati' in df else 0

        for i in range(hari):
            per_ayam = float(forecast[i]) if not math.isnan(forecast[i]) else 0.0
            pakan = per_ayam * ayam_hidup
            karung = round(pakan / 50, 2)
            hasil_prediksi.append({
                "x": tanggal_prediksi[i].strftime('%Y-%m-%d'),
                "y": karung,
                "kg": round(pakan, 2),
                "ayam_hidup": ayam_hidup,
                "per_ayam": per_ayam
            })
            ayam_hidup = max(0, ayam_hidup - int(rata_mati))
            total_kg += pakan
            total_karung += karung

        # --- Print summary di terminal ---
        print(f"[PER_AYAM] Total Pakan\t{round(total_kg,2)} kg")
        print(f"[PER_AYAM] Total Karung (50kg)\t{round(total_karung,2)} karung")

        # --- Data aktual ---
        semua_data_aktual = [
            {
                "x": idx.strftime('%Y-%m-%d'),
                "y": round(float(row.get('pakan_pakai',0))/50,2),
                "kg": round(float(row.get('pakan_pakai',0)),2)
            }
            for idx, row in df.iterrows()
        ]

        # --- Simpan ke DB ---
        riwayat_id = None
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO riwayat (user_id,tanggal_mulai,tanggal_selesai,durasi,prediksi,data_aktual,total_karung)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """
                val = (
                    user_id,
                    tanggal_mulai.strftime("%Y-%m-%d"),
                    tanggal_selesai.strftime("%Y-%m-%d"),
                    hari,
                    json.dumps(hasil_prediksi),
                    json.dumps(semua_data_aktual),
                    total_karung
                )
                cursor.execute(sql, val)
                conn.commit()
                riwayat_id = cursor.lastrowid
        finally:
            conn.close()

        # --- Summary untuk frontend ---
        summary = {
            "total_prediksi_kg": round(total_kg,2),
            "total_prediksi_karung": round(total_karung,2),
            "prediksi_jumlah_ayam": ayam_hidup,
            "rata_mati_per_hari": round(float(rata_mati),2),
            "durasi_hari": hari
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

