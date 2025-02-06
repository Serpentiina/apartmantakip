from flask import Blueprint, render_template, request, send_file, jsonify
from flask_login import login_required
from app import db
from app.models import Aidat, Gider, Daire
from sqlalchemy import func
from datetime import datetime, timedelta
import pdfkit
import os
import locale
import traceback

# Blueprint tanımı
rapor = Blueprint('rapor', __name__)

# Türkçe ay adları için
locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')

# Yollar ve Konfigürasyon
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
PDF_DIR = os.path.join(BASE_DIR, 'static', 'pdf')
WKHTMLTOPDF_PATH = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'

# PDF klasörünü oluştur (eğer yoksa)
if not os.path.exists(PDF_DIR):
    os.makedirs(PDF_DIR)

@rapor.route('/rapor')
@login_required
def rapor_sayfasi():
    try:
        # Sabit tarih aralığı kullan (filtre kaldırıldığı için)
        baslangic = datetime.now() - timedelta(days=30)
        bitis = datetime.now()
        
        # Temel verileri hazırla
        toplam_aidat = db.session.query(func.sum(Aidat.miktar)).scalar() or 0
        odenen_aidat = db.session.query(func.sum(Aidat.miktar)).filter(Aidat.odeme_tarihi.isnot(None)).scalar() or 0
        toplam_gider = db.session.query(func.sum(Gider.miktar)).scalar() or 0
        
        # Daire bazlı aidat durumu
        daireler = Daire.query.all()
        daire_aidatlari = []
        for daire in daireler:
            toplam = db.session.query(func.sum(Aidat.miktar)).filter(Aidat.daire_id == daire.id).scalar() or 0
            odenen = db.session.query(func.sum(Aidat.miktar)).filter(
                Aidat.daire_id == daire.id,
                Aidat.odeme_tarihi.isnot(None)
            ).scalar() or 0
            
            daire_aidatlari.append({
                'daire_no': daire.daire_no,
                'toplam_aidat': toplam,
                'odenen': odenen,
                'kalan': toplam - odenen
            })

        # Son 12 ay verileri
        son_12_ay = []
        for i in range(12):
            tarih = datetime.now() - timedelta(days=30*i)
            ay_baslangic = datetime(tarih.year, tarih.month, 1)
            if tarih.month == 12:
                ay_bitis = datetime(tarih.year + 1, 1, 1)
            else:
                ay_bitis = datetime(tarih.year, tarih.month + 1, 1)
            
            aidat_toplam = db.session.query(func.sum(Aidat.miktar)).filter(
                Aidat.odeme_tarihi.between(ay_baslangic, ay_bitis)
            ).scalar() or 0
            
            gider_toplam = db.session.query(func.sum(Gider.miktar)).filter(
                Gider.tarih.between(ay_baslangic, ay_bitis)
            ).scalar() or 0
            
            son_12_ay.append({
                'ay': tarih.strftime('%B %Y'),
                'aidat': float(aidat_toplam),
                'gider': float(gider_toplam)
            })

        # Gider kategorileri
        gider_kategorileri = db.session.query(
            Gider.kategori,
            func.sum(Gider.miktar).label('toplam')
        ).group_by(Gider.kategori).all()

        gider_kategori_list = [
            {
                'kategori': k.kategori if k.kategori else 'Diğer',
                'toplam': float(k.toplam)
            }
            for k in gider_kategorileri
            if k.toplam > 0  # Sıfır tutarlı kategorileri filtrele
        ]

        # Tüm kategorileri al
        kategori_listesi = [k.kategori for k in gider_kategorileri]

        return render_template('rapor.html',
            baslangic=baslangic,
            bitis=bitis,
            toplam_aidat=toplam_aidat,
            odenen_aidat=odenen_aidat,
            toplam_gider=toplam_gider,
            daire_aidatlari=daire_aidatlari,
            son_12_ay=son_12_ay,
            gider_kategori_list=gider_kategori_list,
            kategori_listesi=kategori_listesi,
            daireler=daireler,
            daire_no='hepsi',
            kategori='hepsi'
        )
    except Exception as e:
        print("Rapor sayfası hatası:", str(e))
        print(traceback.format_exc())
        return "Rapor sayfası yüklenirken bir hata oluştu.", 500

@rapor.route('/rapor/pdf')
@login_required
def rapor_pdf():
    try:
        baslangic = datetime.now() - timedelta(days=30)
        bitis = datetime.now()
        
        # Verileri hazırla
        aidat_toplam = db.session.query(func.sum(Aidat.miktar)).scalar() or 0
        odenen_aidat = db.session.query(func.sum(Aidat.miktar)).filter(
            Aidat.odeme_tarihi.isnot(None)
        ).scalar() or 0
        gider_toplam = db.session.query(func.sum(Gider.miktar)).scalar() or 0
        
        # Daire bazlı aidat durumu
        daireler = Daire.query.all()
        daire_aidatlari = []
        for daire in daireler:
            toplam = db.session.query(func.sum(Aidat.miktar)).filter(
                Aidat.daire_id == daire.id
            ).scalar() or 0
            odenen = db.session.query(func.sum(Aidat.miktar)).filter(
                Aidat.daire_id == daire.id,
                Aidat.odeme_tarihi.isnot(None)
            ).scalar() or 0
            
            daire_aidatlari.append({
                'daire_no': daire.daire_no,
                'toplam_aidat': toplam,
                'odenen': odenen,
                'kalan': toplam - odenen
            })
        
        # Gider kategorileri
        gider_kategorileri = db.session.query(
            Gider.kategori,
            func.sum(Gider.miktar).label('toplam')
        ).group_by(Gider.kategori).all()
        
        # HTML'i oluştur
        html = render_template('rapor_pdf.html',
            baslangic=baslangic,
            bitis=bitis,
            aidat_toplam=aidat_toplam,
            odenen_aidat=odenen_aidat,
            gider_toplam=gider_toplam,
            daire_aidatlari=daire_aidatlari,
            gider_kategorileri=gider_kategorileri,
            datetime=datetime
        )
        
        # PDF dosya adını oluştur
        pdf_adi = f'rapor_{baslangic.strftime("%Y%m%d")}_{bitis.strftime("%Y%m%d")}.pdf'
        pdf_yolu = os.path.join(PDF_DIR, pdf_adi)
        
        # PDF oluştur
        pdfkit.from_string(html, pdf_yolu, configuration=pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH))
        
        # PDF dosyasını gönder
        return send_file(
            pdf_yolu,
            as_attachment=True,
            download_name=f'Apartman_Raporu_{baslangic.strftime("%d_%m_%Y")}-{bitis.strftime("%d_%m_%Y")}.pdf'
        )
        
    except Exception as e:
        print("PDF oluşturma hatası:", str(e))
        print(traceback.format_exc())
        return f"PDF oluşturulurken bir hata oluştu: {str(e)}", 500

@rapor.route('/rapor/aidat-grafik')
@login_required
def aidat_grafik_data():
    try:
        # Son 12 ay için aidat verilerini hazırla
        son_12_ay = []
        for i in range(12):
            tarih = datetime.now() - timedelta(days=30*i)
            ay_baslangic = datetime(tarih.year, tarih.month, 1)
            if tarih.month == 12:
                ay_bitis = datetime(tarih.year + 1, 1, 1)
            else:
                ay_bitis = datetime(tarih.year, tarih.month + 1, 1)
            
            aidat_toplam = db.session.query(func.sum(Aidat.miktar))\
                .filter(Aidat.odeme_tarihi.between(ay_baslangic, ay_bitis))\
                .scalar() or 0
            
            son_12_ay.append({
                'ay': tarih.strftime('%B %Y'),
                'miktar': float(aidat_toplam)
            })
        
        return jsonify(son_12_ay[::-1])
    except Exception as e:
        print("Grafik verisi hatası:", str(e))
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
