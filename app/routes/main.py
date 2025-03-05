from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Daire, Aidat, Gider, Duyuru, User
from app.forms import DaireForm, DuyuruForm, ApartmanForm
from app.routes import main

@main.route('/')
@login_required
def index():
    # Kullanıcıya ait daireleri getir
    daireler = Daire.query.filter_by(user_id=current_user.id).order_by(Daire.daire_no.asc()).all()
    
    # Her daire için aidat durumunu kontrol et
    for daire in daireler:
        # Dairenin ödenmemiş aidatlarını kontrol et
        odenmemis_aidat = Aidat.query.filter_by(
            daire_id=daire.id,
            odendi=False
        ).first()
        
        # Aidat durumunu güncelle
        daire.aidat_durumu = odenmemis_aidat is None
    
    # Değişiklikleri kaydet
    db.session.commit()
    
    # Diğer veriler - kullanıcıya özel
    toplam_aidat = Aidat.query.join(Daire).filter(Daire.user_id == current_user.id, Aidat.odendi == False).count()
    toplam_gider = Gider.query.filter_by(user_id=current_user.id).count()
    son_duyurular = Duyuru.query.filter_by(user_id=current_user.id).order_by(Duyuru.created_at.desc()).limit(5).all()
    
    # Kategori toplamlarını hesapla
    kategori_toplamlar = {
        'elektrik': 0,
        'su': 0,
        'temizlik': 0,
        'asansör': 0,
        'tamirat': 0,
        'diğer': 0
    }
    
    # Toplam ödenen aidat miktarı - kullanıcıya özel
    toplam_odenen_aidat = db.session.query(db.func.sum(Aidat.miktar))\
        .join(Daire)\
        .filter(Daire.user_id == current_user.id, Aidat.odendi == True)\
        .scalar() or 0
    
    # Her daire için ödenen toplam aidat
    daire_odemeleri = {}
    for daire in daireler:
        odenen_miktar = db.session.query(db.func.sum(Aidat.miktar))\
            .filter_by(daire_id=daire.id, odendi=True).scalar() or 0
        daire_odemeleri[daire.id] = odenen_miktar
    
    # Form nesnelerini oluştur
    daire_form = DaireForm()
    duyuru_form = DuyuruForm()
    
    return render_template('index.html', 
                         daireler=daireler,
                         toplam_aidat=toplam_aidat,
                         toplam_gider=toplam_gider,
                         duyurular=son_duyurular,
                         form=daire_form,
                         duyuru_form=duyuru_form,
                         toplam_odenen_aidat=toplam_odenen_aidat,
                         daire_odemeleri=daire_odemeleri,
                         kategori_toplamlar=kategori_toplamlar)

@main.route('/daire/ekle', methods=['GET', 'POST'])
@login_required
def daire_ekle():
    form = DaireForm()
    if form.validate_on_submit():
        daire = Daire(
            daire_no=form.daire_no.data,
            kat=form.kat.data,
            sakin_adi=form.sakin_adi.data,
            telefon=form.telefon.data,
            email=form.email.data,
            user_id=current_user.id
        )
        db.session.add(daire)
        db.session.commit()
        flash('Daire başarıyla eklendi!', 'success')
        return redirect(url_for('main.index'))
    return render_template('daire_form.html', form=form, title='Daire Ekle')

@main.route('/daire/duzenle/<int:id>', methods=['GET', 'POST'])
@login_required
def daire_duzenle(id):
    daire = Daire.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = DaireForm(obj=daire)
    if form.validate_on_submit():
        daire.daire_no = form.daire_no.data
        daire.kat = form.kat.data
        daire.sakin_adi = form.sakin_adi.data
        daire.telefon = form.telefon.data
        daire.email = form.email.data
        db.session.commit()
        flash('Daire bilgileri güncellendi!', 'success')
        return redirect(url_for('main.index'))
    return render_template('daire_form.html', form=form, title='Daire Düzenle')

@main.route('/daire/sil/<int:id>')
@login_required
def daire_sil(id):
    daire = Daire.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    # Daireye bağlı tüm aidatları sil
    Aidat.query.filter_by(daire_id=daire.id).delete()
    
    # Daireyi sil
    db.session.delete(daire)
    db.session.commit()
    
    flash('Daire ve bağlı aidatlar silindi!', 'success')
    return redirect(url_for('main.index'))

@main.route('/duyuru/ekle', methods=['GET', 'POST'])
@login_required
def duyuru_ekle():
    form = DuyuruForm()
    if form.validate_on_submit():
        duyuru = Duyuru(
            baslik=form.baslik.data,
            icerik=form.icerik.data,
            onemli=form.onemli.data,
            user_id=current_user.id
        )
        db.session.add(duyuru)
        db.session.commit()
        flash('Duyuru eklendi!', 'success')
        return redirect(url_for('main.index'))
    return render_template('duyuru_form.html', form=form)

@main.route('/aidat-durum-degistir/<int:id>')
@login_required
def aidat_durum_degistir(id):
    daire = Daire.query.get_or_404(id)
    daire.aidat_durumu = not daire.aidat_durumu
    db.session.commit()
    flash(f'{daire.daire_no} nolu dairenin aidat durumu güncellendi!', 'success')
    return redirect(url_for('main.index'))

@main.route('/duyuru/sil/<int:id>')
@login_required
def duyuru_sil(id):
    duyuru = Duyuru.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(duyuru)
    db.session.commit()
    flash('Duyuru başarıyla silindi!', 'success')
    return redirect(url_for('main.index'))

@main.route('/apartmanlar')
@login_required
def apartmanlar():
    # Sadece admin kullanıcılar apartmanları görebilir
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok!', 'danger')
        return redirect(url_for('main.index'))
    
    # Tüm apartmanları (kullanıcıları) getir
    apartmanlar = User.query.filter_by(is_admin=True).all()
    
    return render_template('apartmanlar.html', apartmanlar=apartmanlar)

@main.route('/apartman/duzenle/<int:id>', methods=['GET', 'POST'])
@login_required
def apartman_duzenle(id):
    # Sadece admin kullanıcılar apartmanları düzenleyebilir
    if not current_user.is_admin:
        flash('Bu işlem için yetkiniz yok!', 'danger')
        return redirect(url_for('main.index'))
    
    apartman = User.query.get_or_404(id)
    form = ApartmanForm(obj=apartman)
    
    if form.validate_on_submit():
        apartman.apartman_ismi = form.apartman_ismi.data
        db.session.commit()
        flash('Apartman bilgileri güncellendi!', 'success')
        return redirect(url_for('main.apartmanlar'))
    
    return render_template('apartman_form.html', form=form, apartman=apartman)

@main.route('/apartman/sil/<int:id>')
@login_required
def apartman_sil(id):
    # Sadece admin kullanıcılar apartmanları silebilir
    if not current_user.is_admin:
        flash('Bu işlem için yetkiniz yok!', 'danger')
        return redirect(url_for('main.index'))
    
    # Kendini silmeyi engelle
    if id == current_user.id:
        flash('Kendi hesabınızı silemezsiniz!', 'danger')
        return redirect(url_for('main.apartmanlar'))
    
    apartman = User.query.get_or_404(id)
    
    # Apartmana ait tüm verileri sil
    Duyuru.query.filter_by(user_id=apartman.id).delete()
    Gider.query.filter_by(user_id=apartman.id).delete()
    Aidat.query.filter_by(user_id=apartman.id).delete()
    
    # Daireleri sil
    Daire.query.filter_by(user_id=apartman.id).delete()
    
    # Kullanıcıyı sil
    db.session.delete(apartman)
    db.session.commit()
    
    flash('Apartman ve tüm verileri silindi!', 'success')
    return redirect(url_for('main.apartmanlar'))
