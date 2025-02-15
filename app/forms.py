from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, FloatField, SelectField, DateField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo, NumberRange, InputRequired

class LoginForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[DataRequired()])
    password = PasswordField('Şifre', validators=[DataRequired()])
    remember = BooleanField('Beni Hatırla')
    submit = SubmitField('Giriş Yap')

class RegistrationForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[
        DataRequired(),
        Length(min=4, max=25, message='Kullanıcı adı 4-25 karakter arasında olmalıdır')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Geçerli bir email adresi giriniz')
    ])
    password = PasswordField('Şifre', validators=[
        DataRequired(),
        Length(min=6, message='Şifre en az 6 karakter olmalıdır')
    ])
    password2 = PasswordField('Şifreyi Tekrarla', validators=[
        DataRequired(),
        EqualTo('password', message='Şifreler eşleşmiyor')
    ])
    submit = SubmitField('Kayıt Ol')

class DaireForm(FlaskForm):
    daire_no = IntegerField('Daire No', validators=[InputRequired(message='Bu alan zorunludur')])
    kat = IntegerField('Kat', validators=[
        InputRequired(message='Bu alan zorunludur'),
        NumberRange(min=0, message='Kat numarası 0 veya daha büyük olmalıdır')
    ])
    sakin_adi = StringField('Sakin Adı', validators=[InputRequired(message='Bu alan zorunludur')])
    telefon = StringField('Telefon', validators=[Optional()])
    email = StringField('Email', validators=[Optional(), Email(message='Geçerli bir email adresi giriniz')])
    submit = SubmitField('Kaydet')

class AidatForm(FlaskForm):
    daire_id = SelectField('Daire', coerce=int, validators=[DataRequired()])
    miktar = FloatField('Miktar (₺)', validators=[DataRequired()])
    son_odeme_tarihi = DateField('Son Ödeme Tarihi', validators=[DataRequired()])
    submit = SubmitField('Aidat Ekle')

class GiderForm(FlaskForm):
    baslik = StringField('Başlık', validators=[DataRequired()])
    kategori = SelectField('Kategori', choices=[
        ('elektrik', 'Elektrik'),
        ('su', 'Su'),
        ('temizlik', 'Temizlik'),
        ('asansör', 'Asansör'),
        ('tamirat', 'Tamirat'),
        ('diğer', 'Diğer')
    ])
    aciklama = TextAreaField('Açıklama')
    miktar = FloatField('Miktar (₺)', validators=[DataRequired()])
    submit = SubmitField('Gider Ekle')

class DuyuruForm(FlaskForm):
    baslik = StringField('Başlık', validators=[
        DataRequired(),
        Length(max=100, message='Başlık en fazla 100 karakter olabilir')
    ])
    icerik = TextAreaField('İçerik', validators=[DataRequired()])
    onemli = BooleanField('Önemli Duyuru')
    submit = SubmitField('Duyuru Ekle')
