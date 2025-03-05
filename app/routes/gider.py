from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Gider, Aidat, Daire
from app.forms import GiderForm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from app.routes import gider
from collections import defaultdict
import calendar

@gider.route('/gider')
@login_required
def gider_listesi():
    # Son 12 ayın tarih aralığını hesapla
    bugun = datetime.now()
    baslangic_tarihi = (bugun - relativedelta(months=11)).replace(day=1)
    
    # Giderleri getir - kullanıcıya özel
    giderler = Gider.query.filter(
        Gider.tarih >= baslangic_tarihi,
        Gider.user_id == current_user.id
    ).order_by(Gider.tarih.desc()).all()

    # Aidatları getir - kullanıcıya özel
    aidatlar = Aidat.query.join(Daire).filter(
        Aidat.son_odeme_tarihi >= baslangic_tarihi,
        Daire.user_id == current_user.id
    ).all()

    form = GiderForm()

    # Kategori bazlı toplam giderler
    kategori_toplamlar = {}
    for kategori in ['elektrik', 'su', 'temizlik', 'asansör', 'tamirat', 'diğer']:
        toplam = sum(g.miktar for g in giderler if g.kategori == kategori)
        kategori_toplamlar[kategori] = toplam

    # Aylık gider ve aidat verilerini hazırla
    aylik_veriler = defaultdict(lambda: {"gider": 0, "aidat": 0})
    
    # Giderleri aylara göre topla
    for gider in giderler:
        ay_yil = gider.tarih.strftime('%Y-%m')
        aylik_veriler[ay_yil]["gider"] += gider.miktar

    # Aidatları aylara göre topla
    for aidat in aidatlar:
        ay_yil = aidat.son_odeme_tarihi.strftime('%Y-%m')
        # Sadece ödenen aidatları topla
        if aidat.odendi:
            aylik_veriler[ay_yil]["aidat"] += aidat.miktar

    # Son 12 ayın listesini oluştur
    son_12_ay = []
    for i in range(12):
        tarih = bugun - relativedelta(months=i)
        ay_yil = tarih.strftime('%Y-%m')
        ay_adi = calendar.month_name[tarih.month] + " " + str(tarih.year)
        
        veriler = aylik_veriler[ay_yil]
        son_12_ay.append((ay_adi, veriler["gider"], veriler["aidat"]))

    # Listeyi tarihe göre sırala (eskiden yeniye)
    son_12_ay.reverse()

    # Grafik verilerini hazırla
    chart_data = {
        'aylik_toplam': {
            'labels': [ay[0] for ay in son_12_ay],  # Ay adları
            'giderler': [ay[1] for ay in son_12_ay],  # Giderler
            'aidatlar': [ay[2] for ay in son_12_ay]  # Aidatlar
        },
        'kategori_dagilim': {
            'labels': list(kategori_toplamlar.keys()),
            'data': list(kategori_toplamlar.values())
        }
    }

    # Debug için verileri kontrol et
    print("Chart data:", chart_data)

    return render_template('gider.html', 
                         giderler=giderler, 
                         form=form,
                         kategori_toplamlar=kategori_toplamlar,
                         chart_data=chart_data)

@gider.route('/gider/ekle', methods=['GET', 'POST'])
@login_required
def gider_ekle():
    form = GiderForm()
    if form.validate_on_submit():
        gider = Gider(
            baslik=form.baslik.data,
            kategori=form.kategori.data,
            aciklama=form.aciklama.data,
            miktar=form.miktar.data,
            tarih=datetime.utcnow(),
            user_id=current_user.id
        )
        db.session.add(gider)
        db.session.commit()
        flash('Gider başarıyla eklendi!', 'success')
        return redirect(url_for('gider.gider_listesi'))
    return render_template('gider_form.html', form=form)

@gider.route('/gider/sil/<int:id>')
@login_required
def gider_sil(id):
    gider = Gider.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(gider)
    db.session.commit()
    flash('Gider silindi!', 'success')
    return redirect(url_for('gider.gider_listesi'))

@gider.route('/gider/toplu-sil', methods=['POST'])
@login_required
def toplu_gider_sil():
    try:
        gider_ids = request.form.get('gider_ids', '').split(',')
        gider_ids = [int(id) for id in gider_ids if id]  # Boş değerleri filtrele ve integer'a çevir
        
        if not gider_ids:
            flash('Silinecek gider seçilmedi!', 'error')
            return redirect(url_for('gider.gider_listesi'))
        
        # Seçilen giderleri sil - kullanıcıya özel
        silinen_count = Gider.query.filter(
            Gider.id.in_(gider_ids),
            Gider.user_id == current_user.id
        ).delete(synchronize_session=False)
        db.session.commit()
        
        flash(f'{silinen_count} adet gider başarıyla silindi!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Giderler silinirken bir hata oluştu: {str(e)}', 'error')
    
    return redirect(url_for('gider.gider_listesi'))
