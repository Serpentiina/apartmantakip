from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Daire, Aidat, Gider, Duyuru
from app.forms import DaireForm, DuyuruForm
from app.routes import main

@main.route('/')
@login_required
def index():
    daireler = Daire.query.order_by(Daire.daire_no.asc()).all()
    toplam_aidat = Aidat.query.filter_by(odendi=False).count()
    toplam_gider = Gider.query.count()
    son_duyurular = Duyuru.query.order_by(Duyuru.created_at.desc()).limit(5).all()
    
    # Kategori toplamlarını hesapla
    kategori_toplamlar = {
        'elektrik': 0,
        'su': 0,
        'temizlik': 0,
        'asansör': 0,
        'tamirat': 0,
        'diğer': 0
    }
    
    # Toplam ödenen aidat miktarı
    toplam_odenen_aidat = db.session.query(db.func.sum(Aidat.miktar)).filter_by(odendi=True).scalar() or 0
    
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
            email=form.email.data
        )
        db.session.add(daire)
        db.session.commit()
        flash('Daire başarıyla eklendi!', 'success')
        return redirect(url_for('main.index'))
    return render_template('daire_form.html', form=form, title='Daire Ekle')

@main.route('/daire/duzenle/<int:id>', methods=['GET', 'POST'])
@login_required
def daire_duzenle(id):
    daire = Daire.query.get_or_404(id)
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
    daire = Daire.query.get_or_404(id)
    
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
            onemli=form.onemli.data
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
@login_required  # Sadece giriş yapmış kullanıcılar
def duyuru_sil(id):
    duyuru = Duyuru.query.get_or_404(id)
    db.session.delete(duyuru)
    db.session.commit()
    flash('Duyuru başarıyla silindi!', 'success')
    return redirect(url_for('main.index'))
