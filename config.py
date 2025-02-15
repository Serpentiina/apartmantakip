import os

class Config:
    SECRET_KEY = 'gizli-anahtariniz-buraya'  # Güvenlik için rastgele bir string kullanın
    SQLALCHEMY_DATABASE_URI = 'sqlite:///apartman.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
