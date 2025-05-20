from fastapi import APIRouter

router = APIRouter()

# Mendefinisikan rute untuk prediksi atau API lainnya
@router.get("/predict")
async def predict():
    return {"message": "API untuk prediksi pakan ayam"}
