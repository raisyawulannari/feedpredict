# app/config.py
class Config:
    # Menggunakan MySQL, pastikan sesuaikan dengan kredensial MySQL kamu
    SQLALCHEMY_DATABASE_URI = 'mysql://username:password@localhost/nama_database'
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Menonaktifkan peringatan dari SQLAlchemy
