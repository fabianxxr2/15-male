from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
import time
from flask_socketio import SocketIO

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
socketio = SocketIO(app)

# Asegurarse de que la carpeta exista
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    allowed_extensions = {'jpg', 'jpeg', 'png', 'mp4', 'webm', 'ogg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in {'jpg', 'jpeg', 'png'}:
        return 'image'
    elif ext in {'mp4', 'webm', 'ogg'}:
        return 'video'
    return 'other'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'photo' not in request.files:
            return redirect(request.url)
        file = request.files['photo']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # Generar un nombre de archivo único usando timestamp
            filename = secure_filename(file.filename)
            name, ext = os.path.splitext(filename)
            unique_filename = f"{int(time.time()*1000)}{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            # Notificar a todos los clientes que hay una nueva foto
            socketio.emit('new_photo')
            return redirect(url_for('index'))
        # Si el archivo no es permitido, simplemente recarga la página (puedes mostrar un mensaje si quieres)
        return redirect(request.url)
    
    # Listar todas las fotos subidas y ordenarlas por fecha de modificación (más recientes primero)
    photos_dir = app.config['UPLOAD_FOLDER']
    files = [f for f in os.listdir(photos_dir) if os.path.isfile(os.path.join(photos_dir, f))]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(photos_dir, x)), reverse=True)
    # Genera una lista de diccionarios con url y tipo
    photos = [{
        'url': f'/static/uploads/{p}',
        'type': file_type(p)
    } for p in files]
    return render_template('index.html', photos=photos)

if __name__ == '__main__':
    # Cambia host='0.0.0.0' para que sea accesible en tu red local
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
