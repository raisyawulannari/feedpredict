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
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )
        return conn
    except mysql.connector.Error as e:
        print("❌ Gagal koneksi ke database:", e)
        raise e  # jangan return None, biar error terlihat jelas

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

        # Tabel riwayat dengan kolom jumlah_ayam_awal
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS riwayat (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            tanggal_mulai DATE NOT NULL,
            tanggal_selesai DATE NOT NULL,
            durasi INT NOT NULL,
            jumlah_ayam_awal INT DEFAULT 0,  -- jumlah ayam awal untuk mode per_ayam
            mode_prediksi ENUM('per_ayam', 'per_periode') DEFAULT 'per_ayam',
            prediksi JSON NOT NULL,
            data_aktual JSON NULL,
            total_pakan_kg FLOAT DEFAULT 0,  -- total pakan dalam kg
            total_karung FLOAT DEFAULT 0,
            mape FLOAT NULL,
            asal_data VARCHAR(50) NULL,
            nama_file VARCHAR(50) NULL,
            activity VARCHAR(255) NULL, -- log aktivitas
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- waktu dibuat
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE

        );
        """)
        
        # Tabel data_pakan untuk simpan file CSV user
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_pakan (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            file_name VARCHAR(50) NOT NULL,
            file_path VARCHAR(100) NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """)


        conn.commit()
        cursor.close()
        conn.close()

        print("✅ Database dan tabel siap digunakan!")

    except mysql.connector.Error as e:
        print("❌ Gagal inisialisasi DB:", e)

if __name__ == "__main__":
    init_db()
