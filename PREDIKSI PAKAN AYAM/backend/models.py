from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base

class Riwayat(Base):
    __tablename__ = "riwayat"

    id = Column(Integer, primary_key=True, index=True)
    tanggal = Column(DateTime(timezone=True), server_default=func.now())
    durasi = Column(Integer)
    hasil_prediksi = Column(String(255))
