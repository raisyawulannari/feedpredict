import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
import joblib
import os

DATA_PATH = "data/data_pakan_ayam.csv"
MODEL_PATH = "models/model_arima.joblib"

# Load data
df = pd.read_csv(DATA_PATH)

# Mapping bulan Indo ke Inggris
bulan_mapping = {
    'Januari': 'January',
    'Februari': 'February',
    'Maret': 'March',
    'April': 'April',
    'Mei': 'May',
    'Juni': 'June',
    'Juli': 'July',
    'Agustus': 'August',
    'September': 'September',
    'Oktober': 'October',
    'November': 'November',
    'Desember': 'December'
}
for indo, eng in bulan_mapping.items():
    df['Tanggal'] = df['Tanggal'].str.replace(indo, eng, regex=False)

# Konversi ke datetime
df['Tanggal'] = pd.to_datetime(df['Tanggal'], format="%d %B %Y")
df.set_index('Tanggal', inplace=True)

# Kolom target: Pakan_Pakai
data = df['Pakan_Pakai']

# Latih model
model = ARIMA(data, order=(5, 1, 0))
model_fit = model.fit()

# Simpan model
os.makedirs("models", exist_ok=True)
joblib.dump(model_fit, MODEL_PATH)
print("✅ Model ARIMA disimpan ke:", os.path.abspath(MODEL_PATH))
