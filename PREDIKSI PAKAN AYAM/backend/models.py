# models.py

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Ayam(db.Model):
    __tablename__ = 'ayam'
    id = db.Column(db.Integer, primary_key=True)
    jumlah_ayam = db.Column(db.Integer, nullable=False)
    ayam_mati = db.Column(db.Integer, default=0)
    pakan_id = db.Column(db.Integer, db.ForeignKey('pakan.id'))
    
    pakan = db.relationship('Pakan', backref=db.backref('ayam', lazy=True))
    
    def __repr__(self):
        return f"<Ayam {self.id}, Jumlah: {self.jumlah_ayam}>"

class Pakan(db.Model):
    __tablename__ = 'pakan'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    jumlah = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f"<Pakan {self.nama}, Jumlah: {self.jumlah}>"
