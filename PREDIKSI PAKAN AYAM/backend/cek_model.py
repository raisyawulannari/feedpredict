import joblib

# Load model dari file
model = joblib.load("model_pakan.joblib")

# Cek isi model
print("Model berhasil dimuat.")
print(model)

# Jika model ARIMA, kamu bisa cek summary
try:
    print("\nRingkasan Model ARIMA:")
    print(model.summary())
except Exception as e:
    print(f"Gagal menampilkan summary: {e}")
