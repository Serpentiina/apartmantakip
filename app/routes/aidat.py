from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Aidat, Daire
from app.forms import AidatForm
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import func
from app.routes import aidat

@aidat.route('/aidat')
@login_required
def aidat_listesi():
    sakin_adi = request.args.get('sakin_adi', '')
    daire_no = request.args.get('daire_no', '')
    sort = request.args.get('sort', 'daire')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Bugünün tarihini al
    today = datetime.now()
    
    # Bu ayın son gününü hesapla
    if today.month == 12:
        ay_sonu = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        ay_sonu = date(today.year, today.month + 1, 1) - timedelta(days=1)

    # İstatistikleri hesapla - kullanıcıya özel
    toplam_aidat = db.session.query(func.sum(Aidat.miktar))\
        .join(Daire)\
        .filter(Daire.user_id == current_user.id)\
        .scalar() or 0
        
    odenen_aidat = db.session.query(func.sum(Aidat.miktar))\
        .join(Daire)\
        .filter(Daire.user_id == current_user.id, Aidat.odendi == True)\
        .scalar() or 0
        
    odenmemis_aidat = db.session.query(func.sum(Aidat.miktar))\
        .join(Daire)\
        .filter(Daire.user_id == current_user.id, Aidat.odendi == False)\
        .scalar() or 0

    # Sorguyu oluştur - kullanıcıya özel
    aidatlar = db.session.query(Aidat).join(Daire).filter(Daire.user_id == current_user.id)

    if sakin_adi:
        aidatlar = aidatlar.filter(Daire.sakin_adi.ilike(f'%{sakin_adi}%'))
    if daire_no:
        aidatlar = aidatlar.filter(Daire.daire_no == daire_no)

    # sort_order kontrolü
    current_sort_order = request.args.get('sort_order', 'asc')
    new_sort_order = 'desc' if current_sort_order == 'asc' else 'asc'
    
    # Sıralama mantığı
    if sort == 'daire':
        if current_sort_order == 'asc':
            aidatlar = aidatlar.order_by(Daire.daire_no.asc())
        else:
            aidatlar = aidatlar.order_by(Daire.daire_no.desc())

    # Sayfalandırma uygula
    pagination = aidatlar.paginate(page=page, per_page=per_page, error_out=False)
    aidatlar = pagination.items

    form = AidatForm()
    form.daire_id.choices = [(d.id, f"Daire {d.daire_no} - {d.sakin_adi}") for d in Daire.query.all()]
    daireler = Daire.query.all()

    # Borçlu daireleri hesapla
    borclu_daireler = []
    
    # Tüm daireleri döngüye al
    for daire in daireler:
        # Her daire için ödenmemiş aidatları bul
        odenmemis_aidatlar = Aidat.query.filter_by(
            daire_id=daire.id,
            odendi=False,
            user_id=current_user.id  # Kullanıcı ID'sine göre filtrele
        ).order_by(Aidat.son_odeme_tarihi).all()
        
        # Eğer ödenmemiş aidat varsa
        if odenmemis_aidatlar:
            toplam_borc = sum(aidat.miktar for aidat in odenmemis_aidatlar)
            en_eski_borc = min(aidat.son_odeme_tarihi for aidat in odenmemis_aidatlar)
            
            # Borç detaylarını hazırla
            borc_detaylari = []
            bugun = datetime.now().date()
            
            for aidat in odenmemis_aidatlar:
                son_odeme = aidat.son_odeme_tarihi.date() if isinstance(aidat.son_odeme_tarihi, datetime) else aidat.son_odeme_tarihi
                gecikme_suresi = (bugun - son_odeme).days
                
                borc_detaylari.append({
                    'donem': son_odeme.strftime('%B %Y'),
                    'miktar': aidat.miktar,
                    'son_odeme_tarihi': son_odeme,
                    'gecikme_suresi': max(0, gecikme_suresi)
                })
            
            # Borçlu daire bilgilerini listeye ekle
            borclu_daireler.append({
                'daire_no': daire.daire_no,
                'sakin_adi': daire.sakin_adi,
                'toplam_borc': toplam_borc,
                'odenmemis_aidat_sayisi': len(odenmemis_aidatlar),
                'en_eski_borc_tarihi': en_eski_borc,
                'borc_detaylari': borc_detaylari
            })
    
    # Borçlu daireleri en eski borç tarihine göre sırala
    borclu_daireler.sort(key=lambda x: x['en_eski_borc_tarihi'])

    return render_template('aidat.html',
                         aidatlar=aidatlar,
                         pagination=pagination,
                         form=form,
                         daireler=daireler,
                         sort=sort,
                         current_sort_order=current_sort_order,
                         new_sort_order=new_sort_order,
                         toplam_aidat="{:.2f}".format(toplam_aidat),
                         odenen_aidat="{:.2f}".format(odenen_aidat),
                         odenmemis_aidat="{:.2f}".format(odenmemis_aidat),
                         borclu_daireler=borclu_daireler,
                         today=today,
                         ay_sonu=ay_sonu)

@aidat.route('/aidat/ekle', methods=['GET', 'POST'])
@login_required
def aidat_ekle():
    form = AidatForm()
    # Sadece kullanıcıya ait daireleri listele
    form.daire_id.choices = [(d.id, f"Daire {d.daire_no} - {d.sakin_adi}") 
                            for d in Daire.query.filter_by(user_id=current_user.id).all()]
    
    if form.validate_on_submit():
        # Dairenin kullanıcıya ait olup olmadığını kontrol et
        daire = Daire.query.filter_by(id=form.daire_id.data, user_id=current_user.id).first()
        if not daire:
            flash('Bu işlem için yetkiniz yok!', 'danger')
            return redirect(url_for('aidat.aidat_listesi'))
            
        aidat = Aidat(
            daire_id=form.daire_id.data,
            miktar=form.miktar.data,
            son_odeme_tarihi=form.son_odeme_tarihi.data,
            user_id=current_user.id  # Kullanıcı ID'sini ekle
        )
        db.session.add(aidat)
        db.session.commit()
        flash('Aidat başarıyla eklendi!', 'success')
        return redirect(url_for('aidat.aidat_listesi'))
    
    return render_template('aidat_form.html', form=form)

@aidat.route('/aidat/odendi/<int:id>')
@login_required
def aidat_odendi(id):
    # Kullanıcıya ait aidatı bul
    aidat = Aidat.query.join(Daire).filter(
        Aidat.id == id,
        Daire.user_id == current_user.id
    ).first_or_404()
    
    aidat.odendi = True
    aidat.odeme_tarihi = datetime.utcnow()
    db.session.commit()
    flash('Aidat ödemesi başarıyla kaydedildi!', 'success')
    return redirect(url_for('aidat.aidat_listesi'))

@aidat.route('/toplu-aidat-ekle', methods=['POST'])
@login_required
def toplu_aidat_ekle():
    try:
        # Kullanıcıya ait daireleri getir
        daireler = Daire.query.filter_by(user_id=current_user.id).all()
        
        # Varsayılan miktar 700 TL
        miktar = float(request.form.get('miktar', 700))
        
        if request.form.get('son_odeme_tarihi'):
            son_odeme = datetime.strptime(request.form.get('son_odeme_tarihi'), '%Y-%m-%d')
        else:
            bugun = datetime.now()
            if bugun.month == 12:
                sonraki_ay = datetime(bugun.year + 1, 1, 1)
            else:
                sonraki_ay = datetime(bugun.year, bugun.month + 1, 1)
            son_odeme = sonraki_ay - timedelta(days=1)
        
        for daire in daireler:
            yeni_aidat = Aidat(
                daire_id=daire.id,
                miktar=miktar,
                son_odeme_tarihi=son_odeme,
                odendi=False,
                user_id=current_user.id  # Kullanıcı ID'sini ekle
            )
            db.session.add(yeni_aidat)
        
        db.session.commit()
        flash('Toplu aidat ekleme işlemi başarıyla tamamlandı!', 'success')
        
    except ValueError as e:
        db.session.rollback()
        flash('Lütfen geçerli bir miktar giriniz!', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Aidat eklenirken bir hata oluştu: {str(e)}', 'error')
    
    return redirect(url_for('aidat.aidat_listesi'))

@aidat.route('/aidat/sil/<int:daire_id>/<string:tarih>')
@login_required
def aidat_sil(daire_id, tarih):
    try:
        # Tarihi datetime formatına çevir
        tarih_obj = datetime.strptime(tarih, '%Y-%m')
        ay_baslangic = datetime(tarih_obj.year, tarih_obj.month, 1)
        if tarih_obj.month == 12:
            ay_bitis = datetime(tarih_obj.year + 1, 1, 1)
        else:
            ay_bitis = datetime(tarih_obj.year, tarih_obj.month + 1, 1)
        
        # Önce dairenin kullanıcıya ait olup olmadığını kontrol et
        daire = Daire.query.filter_by(id=daire_id, user_id=current_user.id).first()
        if not daire:
            flash('Bu işlem için yetkiniz yok!', 'danger')
            return redirect(url_for('aidat.aidat_listesi'))
        
        # Aidatı bul - belirli ay aralığındaki kayıtları bul
        aidat = Aidat.query.filter(
            Aidat.daire_id == daire_id,
            Aidat.son_odeme_tarihi >= ay_baslangic,
            Aidat.son_odeme_tarihi < ay_bitis,
            Aidat.user_id == current_user.id  # Kullanıcı ID'sine göre filtrele
        ).first()

        if not aidat:
            flash('Silinecek aidat bulunamadı!', 'error')
            return redirect(url_for('aidat.aidat_listesi'))
        
        # Aidatı sil (ödenmiş olup olmadığına bakmadan)
        db.session.delete(aidat)
        db.session.commit()
        flash('Aidat başarıyla silindi!', 'success')
            
    except ValueError:
        flash('Geçersiz tarih formatı!', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Aidat silinirken bir hata oluştu: {str(e)}', 'error')
    
    return redirect(url_for('aidat.aidat_listesi'))

@aidat.route('/secilenleri-sil', methods=['POST'])
@login_required
def secilenleri_sil():
    try:
        aidat_ids = request.form.get('aidat_ids', '').split(',')
        aidat_ids = [int(id) for id in aidat_ids if id]  # Boş değerleri filtrele ve integer'a çevir
        
        if not aidat_ids:
            flash('Silinecek aidat seçilmedi!', 'error')
            return redirect(url_for('aidat.aidat_listesi'))
        
        # Seçilen aidatları sil - kullanıcıya özel
        silinen_count = Aidat.query.filter(
            Aidat.id.in_(aidat_ids),
            Aidat.user_id == current_user.id
        ).delete(synchronize_session=False)
        db.session.commit()
        
        flash(f'{silinen_count} adet aidat başarıyla silindi!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Aidatlar silinirken bir hata oluştu: {str(e)}', 'error')
    
    return redirect(url_for('aidat.aidat_listesi'))

@aidat.route('/borclu-daireler')
@login_required
def borclu_daireler_listesi():
    # Kullanıcıya ait daireleri getir
    daireler = Daire.query.filter_by(user_id=current_user.id).all()
    borclu_daireler = []
    
    # Tüm daireleri döngüye al
    for daire in daireler:
        # Her daire için ödenmemiş aidatları bul
        odenmemis_aidatlar = Aidat.query.filter_by(
            daire_id=daire.id,
            odendi=False,
            user_id=current_user.id  # Kullanıcı ID'sine göre filtrele
        ).order_by(Aidat.son_odeme_tarihi).all()
        
        # Eğer ödenmemiş aidat varsa
        if odenmemis_aidatlar:
            toplam_borc = sum(aidat.miktar for aidat in odenmemis_aidatlar)
            en_eski_borc = min(aidat.son_odeme_tarihi for aidat in odenmemis_aidatlar)
            
            # Borç detaylarını hazırla
            borc_detaylari = []
            bugun = datetime.now().date()
            
            for aidat in odenmemis_aidatlar:
                son_odeme = aidat.son_odeme_tarihi.date() if isinstance(aidat.son_odeme_tarihi, datetime) else aidat.son_odeme_tarihi
                gecikme_suresi = (bugun - son_odeme).days
                
                borc_detaylari.append({
                    'donem': son_odeme.strftime('%B %Y'),
                    'miktar': aidat.miktar,
                    'son_odeme_tarihi': son_odeme,
                    'gecikme_suresi': max(0, gecikme_suresi)
                })
            
            # Borçlu daire bilgilerini listeye ekle
            borclu_daireler.append({
                'daire_no': daire.daire_no,
                'sakin_adi': daire.sakin_adi,
                'toplam_borc': toplam_borc,
                'odenmemis_aidat_sayisi': len(odenmemis_aidatlar),
                'en_eski_borc_tarihi': en_eski_borc,
                'borc_detaylari': borc_detaylari
            })
    
    # Borçlu daireleri en eski borç tarihine göre sırala
    borclu_daireler.sort(key=lambda x: x['en_eski_borc_tarihi'])
    
    return render_template('borclu_daireler.html', borclu_daireler=borclu_daireler)

@aidat.route('/aidat/kismi-odeme/<int:id>', methods=['POST'])
@login_required
def kismi_odeme(id):
    try:
        # Kullanıcıya ait aidatı bul
        aidat = Aidat.query.join(Daire).filter(
            Aidat.id == id,
            Daire.user_id == current_user.id
        ).first_or_404()
        
        odenen_miktar = float(request.form.get('odenen_miktar', 0))
        
        if odenen_miktar <= 0 or odenen_miktar > aidat.miktar:
            flash('Geçersiz ödeme miktarı!', 'error')
            return redirect(url_for('aidat.aidat_listesi'))
        
        # Kalan miktar için yeni aidat oluştur
        kalan_miktar = aidat.miktar - odenen_miktar
        if kalan_miktar > 0:
            yeni_aidat = Aidat(
                daire_id=aidat.daire_id,
                miktar=kalan_miktar,
                son_odeme_tarihi=aidat.son_odeme_tarihi,
                odendi=False,
                user_id=current_user.id  # Kullanıcı ID'sini ekle
            )
            db.session.add(yeni_aidat)
        
        # Mevcut aidatı güncelle
        aidat.miktar = odenen_miktar
        aidat.odendi = True
        aidat.odeme_tarihi = datetime.utcnow()
        
        db.session.commit()
        flash(f'{odenen_miktar:.2f} TL tutarında kısmi ödeme başarıyla kaydedildi!', 'success')
        
    except ValueError:
        flash('Geçersiz ödeme miktarı!', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Ödeme işlemi sırasında bir hata oluştu: {str(e)}', 'error')
    
    return redirect(url_for('aidat.aidat_listesi'))