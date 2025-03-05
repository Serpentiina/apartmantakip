from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Daire, Aidat, Gider, Duyuru
from app.forms import LoginForm, RegistrationForm, AdminRegistrationForm

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    username = request.form.get('username')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        flash('Kullanıcı adı veya şifre hatalı!')
        return redirect(url_for('auth.login'))

    login_user(user, remember=remember)
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    apartman_ismi = request.form.get('apartman_ismi', 'Apartman')
    
    user = User.query.filter_by(email=email).first()
    if user:
        flash('Email adresi zaten kayıtlı!', 'danger')
        return redirect(url_for('auth.register'))
    
    # Kullanıcı adı kontrolü
    username_check = User.query.filter_by(username=username).first()
    if username_check:
        flash('Bu kullanıcı adı zaten kullanılıyor!', 'danger')
        return redirect(url_for('auth.register'))
    
    # İlk kullanıcıyı admin yap
    is_first_user = User.query.count() == 0
    
    new_user = User(username=username, email=email, apartman_ismi=apartman_ismi, is_admin=is_first_user)
    new_user.set_password(password)
    
    db.session.add(new_user)
    db.session.commit()
    
    if is_first_user:
        flash('İlk kullanıcı olarak admin yetkilerine sahipsiniz!', 'success')
    else:
        flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
    
    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/admin-register', methods=['GET', 'POST'])
@login_required
def admin_register():
    # Sadece mevcut admin kullanıcılar yeni admin hesabı oluşturabilir
    if not current_user.is_admin:
        flash('Bu işlem için yönetici yetkisi gereklidir!', 'danger')
        return redirect(url_for('main.index'))
    
    form = AdminRegistrationForm()
    if form.validate_on_submit():
        # Kullanıcı adı kontrolü
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Bu kullanıcı adı zaten kullanılıyor!', 'danger')
            return render_template('admin_register.html', form=form)
        
        # Email kontrolü
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('Bu email adresi zaten kullanılıyor!', 'danger')
            return render_template('admin_register.html', form=form)
        
        # Yeni admin kullanıcı oluştur
        new_admin = User(
            username=form.username.data,
            email=form.email.data,
            apartman_ismi=form.apartman_ismi.data,
            is_admin=True
        )
        new_admin.set_password(form.password.data)
        
        db.session.add(new_admin)
        db.session.commit()
        
        # Yeni admin için veri izolasyonu sağlamak için kullanıcı ID'sini al
        new_admin_id = new_admin.id
        
        flash('Yeni yönetici hesabı başarıyla oluşturuldu!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('admin_register.html', form=form)

# Kullanıcıya ait verileri getiren yardımcı fonksiyon
def get_user_data(user_id):
    """
    Belirli bir kullanıcıya ait verileri getirir.
    Bu fonksiyon, kullanıcılar arası veri izolasyonu sağlamak için kullanılır.
    """
    # Bu fonksiyon, ileride kullanıcıya özel veri filtreleme için kullanılacak
    # Şu an için basit bir yapı, ileride genişletilebilir
    return {
        'user_id': user_id
    }
