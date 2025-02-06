from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///apartman.db'
db = SQLAlchemy(app)

# Daire modeli
class Daire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    daire_no = db.Column(db.Integer, nullable=False)
    kat = db.Column(db.Integer, nullable=False)
    sakin_adi = db.Column(db.String(100))
    telefon = db.Column(db.String(15))
    aidat_durumu = db.Column(db.Boolean, default=True)
    tarih = db.Column(db.DateTime, default=datetime.utcnow)

# Ana sayfa
@app.route('/')
def ana_sayfa():
    daireler = Daire.query.all()
    return render_template('index.html', daireler=daireler)

# Daire ekleme
@app.route('/daire_ekle', methods=['POST'])
def daire_ekle():
    daire_no = request.form['daire_no']
    kat = request.form['kat']
    sakin_adi = request.form['sakin_adi']
    telefon = request.form['telefon']
    
    yeni_daire = Daire(
        daire_no=daire_no,
        kat=kat,
        sakin_adi=sakin_adi,
        telefon=telefon
    )
    
    db.session.add(yeni_daire)
    db.session.commit()
    
    return redirect(url_for('ana_sayfa'))

# Daire silme
@app.route('/daire_sil/<int:id>')
def daire_sil(id):
    daire = Daire.query.get_or_404(id)
    db.session.delete(daire)
    db.session.commit()
    return redirect(url_for('ana_sayfa'))

# Aidat durumu değiştirme
@app.route('/aidat_durum_degistir/<int:id>')
def aidat_durum_degistir(id):
    daire = Daire.query.get_or_404(id)
    daire.aidat_durumu = not daire.aidat_durumu
    db.session.commit()
    return redirect(url_for('ana_sayfa'))

# Veritabanını oluştur
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
