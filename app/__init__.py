from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from flask_apscheduler import APScheduler
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from sqlalchemy import func

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

scheduler = APScheduler()

def toplu_aidat_ekle_task():
    with app.app_context():
        try:
            daireler = Daire.query.all()
            sonraki_ay = datetime.now() + relativedelta(months=1)
            son_odeme_tarihi = date(sonraki_ay.year, sonraki_ay.month, 27)
            
            for daire in daireler:
                mevcut_aidat = Aidat.query.filter(
                    Aidat.daire_id == daire.id,
                    func.extract('month', Aidat.son_odeme_tarihi) == son_odeme_tarihi.month,
                    func.extract('year', Aidat.son_odeme_tarihi) == son_odeme_tarihi.year
                ).first()
                
                if not mevcut_aidat:
                    yeni_aidat = Aidat(
                        daire_id=daire.id,
                        miktar=700.00,
                        son_odeme_tarihi=son_odeme_tarihi,
                        odendi=False,
                        created_at=datetime.now()
                    )
                    db.session.add(yeni_aidat)
            
            db.session.commit()
            print(f"Toplu aidat ekleme başarılı: {datetime.now()}")
        except Exception as e:
            db.session.rollback()
            print(f"Toplu aidat ekleme hatası: {str(e)}")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Veritabanı konfigürasyonu
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///apartman.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Secret key ekliyoruz (önemli!)
    app.config['SECRET_KEY'] = 'your-secret-key-here'  # Güvenli bir secret key kullanın

    db.init_app(app)
    login_manager.init_app(app)
    scheduler.init_app(app)
    scheduler.start()

    # Her ayın 27'sinde saat 00:01'de çalışacak
    scheduler.add_job(
        id='toplu_aidat_ekle',
        func=toplu_aidat_ekle_task,
        trigger='cron',
        day=27,
        hour=0,
        minute=1
    )

    from app.routes import main, auth, aidat, gider, rapor  # rapor eklendi
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(aidat)
    app.register_blueprint(gider)
    app.register_blueprint(rapor)  # rapor blueprint'i kaydedildi

    with app.app_context():
        db.create_all()

    return app