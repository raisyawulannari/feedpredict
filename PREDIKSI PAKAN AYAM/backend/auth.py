from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database import get_db_connection
from datetime import datetime, timedelta
import jwt
from jwt import PyJWTError, ExpiredSignatureError
from fastapi.security import OAuth2PasswordBearer

# ------------------------
# Config
# ------------------------
SECRET_KEY = "secret123"  # ganti dengan key yang lebih aman
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

router = APIRouter(prefix="/api")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# ------------------------
# Schemas
# ------------------------
class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    name: str

# ------------------------
# Helper Functions
# ------------------------
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
    except PyJWTError:
            raise HTTPException(status_code=401, detail="Token invalid")


def admin_required(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")
    return current_user

# ------------------------
# Routes
# ------------------------

# REGISTER
@router.post("/register")
def register(user: UserRegister):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # cek email
    cursor.execute("SELECT * FROM users WHERE email=%s", (user.email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")

    # simpan user baru (default role=user)
    cursor.execute(
        "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
        (user.name, user.email, user.password, "user")
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Registrasi berhasil!"}

# LOGIN
@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (user.email,))
    db_user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not db_user:
        raise HTTPException(status_code=400, detail="Email tidak ditemukan")
    if user.password != db_user["password"]:
        raise HTTPException(status_code=400, detail="Password salah")

    # buat JWT token
    access_token = create_access_token(
        data={"sub": db_user["email"], "role": db_user["role"]}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": db_user["role"],
        "name": db_user["name"]
    }

# ------------------------
# Contoh Route Protected
# ------------------------
@router.get("/admin/dashboard")
def admin_dashboard(user: dict = Depends(admin_required)):
    return {"msg": f"Welcome Admin {user['sub']}!"}

@router.get("/user/dashboard")
def user_dashboard(current_user: dict = Depends(get_current_user)):
    return {"msg": f"Welcome {current_user['sub']} ({current_user['role']})!"}
