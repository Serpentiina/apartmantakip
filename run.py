from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    # Eğer VPS ortamında çalışıyorsa (örneğin bir çevre değişkeni ile kontrol edilebilir)
    if os.environ.get('ENVIRONMENT') == 'production':
        app.run(host='0.0.0.0', port=5000)
    else:
        # Yerel geliştirme ortamında 5001 portunu kullan
        app.run(debug=True, port=5001)
