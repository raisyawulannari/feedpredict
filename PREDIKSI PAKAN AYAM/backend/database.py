import mysql.connector
from mysql.connector.connection_cext import CMySQLConnection as MySQLConnection

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "prediksi_db"
}


def get_db_connection() -> MySQLConnection:
    """
    Membuka koneksi ke database MySQL.
    Gunakan `conn = get_db_connection()` lalu `conn.close()` setelah selesai.
    """
    return mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"]
    )


def init_db() -> None:
    """
    Inisialisasi database dan tabel-tabel utama.
    Jalankan sekali saja saat setup awal.
    """
    try:
        # Koneksi tanpa database (buat DB jika belum ada)
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        cursor = conn.cursor()

        # Buat database jika belum ada
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.execute(f"USE {DB_CONFIG['database']}")

        # Tabel users
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            role ENUM('admin','user') NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );
        """)

        # Tabel riwayat
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS riwayat (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            tanggal_mulai DATE NOT NULL,
            tanggal_selesai DATE NOT NULL,
            durasi INT NOT NULL,
            prediksi JSON NOT NULL,
            data_aktual JSON NULL,
            total_karung FLOAT DEFAULT 0,
            mape FLOAT NULL,
            asal_data VARCHAR(50) NULL,
            nama_file VARCHAR(50) NULL,
            activity VARCHAR(255) NULL, -- log aktivitas
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- waktu dibuat
        );
        """)

        # Tabel prediksi
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediksi (
            id INT AUTO_INCREMENT PRIMARY KEY,
            riwayat_id INT NOT NULL,
            tanggal_mulai DATE NOT NULL,
            tanggal_selesai DATE NOT NULL,
            mode_prediksi ENUM('per_ayam', 'periode') DEFAULT 'per_ayam',
            total_karung FLOAT DEFAULT 0,
            jumlah_ayam INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (riwayat_id) REFERENCES riwayat(id) ON DELETE CASCADE
        );
        """)

        # Commit & close
        conn.commit()
        cursor.close()
        conn.close()

        print("✅ Database dan tabel siap digunakan!")

    except mysql.connector.Error as e:
        print("❌ Gagal inisialisasi DB:", e)


# Jalankan init_db() sekali saja untuk setup awal
if __name__ == "__main__":
    init_db()
