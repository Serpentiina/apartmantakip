from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    apartman_ismi = db.Column(db.String(100), default="Apartman")
    
    # İlişkiler
    daireler = db.relationship('Daire', backref='yonetici', lazy='dynamic')
    giderler = db.relationship('Gider', backref='yonetici', lazy='dynamic')
    duyurular = db.relationship('Duyuru', backref='yonetici', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Daire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    daire_no = db.Column(db.Integer, nullable=False)
    kat = db.Column(db.Integer, nullable=False)
    sakin_adi = db.Column(db.String(100))
    telefon = db.Column(db.String(20))
    email = db.Column(db.String(120))
    aidat_durumu = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def __repr__(self):
        return f'<Daire {self.daire_no}>'

class Aidat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    daire_id = db.Column(db.Integer, db.ForeignKey('daire.id'), nullable=False)
    miktar = db.Column(db.Float, nullable=False)
    odeme_tarihi = db.Column(db.DateTime)
    son_odeme_tarihi = db.Column(db.DateTime, nullable=False)
    odendi = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    daire = db.relationship('Daire', backref='aidatlar')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class Gider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    baslik = db.Column(db.String(100), nullable=False)
    aciklama = db.Column(db.Text)
    miktar = db.Column(db.Float, nullable=False)
    tarih = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    kategori = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class Duyuru(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    baslik = db.Column(db.String(100), nullable=False)
    icerik = db.Column(db.Text, nullable=False)
    onemli = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
