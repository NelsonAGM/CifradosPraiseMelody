import os
import uuid
import logging
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory,session
from flask_sqlalchemy import SQLAlchemy # Importar SQLAlchemy
from dotenv import load_dotenv # Importar para cargar variables de entorno locales
from functools import wraps # Necesario para el decorador @wraps


# Cargar variables de entorno desde .env (útil para desarrollo local)
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
# Usar una variable de entorno para la clave secreta
# En Render, configurar SESSION_SECRET en las variables de entorno del servicio web.
# Para desarrollo local, puedes usar el .env o un valor por defecto.
app.secret_key = os.environ.get("SESSION_SECRET", "una_clave_secreta_muy_larga_y_aleatoria_para_desarrollo")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'Hacedores2025.') 
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '123qwe.') 

# --- Configuración de la Base de Datos PostgreSQL ---
# La URL de la base de datos se obtendrá de una variable de entorno en Render ('DATABASE_URL').
# Para desarrollo local, puedes configurar 'DATABASE_URL' en tu archivo .env.
# Ejemplo de formato: 'postgresql://user:password@host:port/dbname'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Recomendado para deshabilitar eventos de seguimiento de SQLAlchemy

db = SQLAlchemy(app) # Inicializar SQLAlchemy


def login_required_simple(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            flash('Por favor, inicia sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Has iniciado sesión exitosamente.', 'success')
            return redirect(url_for('index')) # Redirige a tu página principal después del login
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
    return render_template('login.html') # Asegúrate de tener este archivo HTML en tu carpeta 'templates'

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('index')) # Redirige a tu página principal después del logout



# --- Definición del Modelo de Datos (Tabla 'song') ---
class Song(db.Model):
    # Nombre de la tabla en la base de datos (opcional, por defecto es el nombre de la clase en minúsculas)
    __tablename__ = 'songs'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(255), nullable=False)
    lyrics = db.Column(db.Text, nullable=False)
    original_key = db.Column(db.String(10), nullable=True)
    audio_file = db.Column(db.String(255), nullable=True) # Nombre del archivo subido
    audio_url = db.Column(db.String(500), nullable=True)  # URL externa (ej. SoundCloud, otro host)
    youtube_id = db.Column(db.String(50), nullable=True)  # ID de YouTube
    tags = db.Column(db.String(500), nullable=True) # Almacenaremos tags como una cadena separada por comas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Song {self.title}>'

    def get_tags_list(self):
        """Convierte la cadena de tags a una lista."""
        return [tag.strip() for tag in (self.tags or '').split(',') if tag.strip()]

    def set_tags_list(self, tags_list):
        """Convierte la lista de tags a una cadena."""
        cleaned_tags = [tag.strip() for tag in tags_list if tag and tag.strip()]
        self.tags = ','.join(cleaned_tags) if cleaned_tags else None

# --- Configuración de Carga de Archivos ---
UPLOAD_FOLDER = 'static/uploads' # Los archivos se guardarán aquí
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Asegurarse de que la carpeta de carga exista
# Esto se ejecutará al inicio de la app, importante para desarrollo y para Render (si se usa disco persistente)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_youtube_id(url):
    """Extrae el ID de video de YouTube de varias URLs."""
    if not url:
        return None
    
    parsed_url = urlparse(url)
    if "youtube.com" in parsed_url.netloc or "youtu.be" in parsed_url.netloc:
        if parsed_url.netloc == "youtu.be":
            return parsed_url.path[1:].split('?')[0] # Extraer de youtu.be/VIDEO_ID
        elif parsed_url.path == '/watch':
            return parse_qs(parsed_url.query).get('v', [None])[0] # Extraer de youtube.com/watch?v=VIDEO_ID
        elif parsed_url.path.startswith('/embed/'):
            return parsed_url.path.split('/embed/')[1].split('?')[0] # Extraer de youtube.com/embed/VIDEO_ID
        elif parsed_url.path.startswith('/v/'):
            return parsed_url.path.split('/v/')[1].split('?')[0] # Extraer de youtube.com/v/VIDEO_ID
    return None

# --- Rutas de la Aplicación ---

@app.route('/')
def index():
    search_query = request.args.get('search', '').strip()
    tag_filter = request.args.get('tag', '').strip()

    query = Song.query

    if search_query:
        # Búsqueda insensible a mayúsculas/minúsculas por título o letra
        query = query.filter(
            (Song.title.ilike(f'%{search_query}%')) |
            (Song.lyrics.ilike(f'%{search_query}%'))
        )

    if tag_filter:
        # Búsqueda de tags: verifica si la cadena de tags contiene el tag filtrado
        query = query.filter(Song.tags.ilike(f'%{tag_filter}%'))

    # Ordenar por fecha de creación descendente y luego por título ascendente
    songs = query.order_by(Song.created_at.desc(), Song.title.asc()).all()

    # Obtener todos los tags únicos para el filtro de la UI
    all_tags_raw = db.session.query(Song.tags).filter(Song.tags.isnot(None)).distinct().all()
    all_tags_set = set()
    for tag_str_tuple in all_tags_raw:
        if tag_str_tuple[0]: # Asegurarse de que la cadena de tags no esté vacía
            for tag in tag_str_tuple[0].split(','):
                cleaned_tag = tag.strip()
                if cleaned_tag:
                    all_tags_set.add(cleaned_tag)
    all_tags = sorted(list(all_tags_set)) # Ordenar alfabéticamente

    return render_template('index.html', songs=songs, search=search_query, tag_filter=tag_filter, all_tags=all_tags)


@app.route('/add', methods=['GET', 'POST'])
@login_required_simple
def add_song():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        lyrics = request.form.get('lyrics', '').strip()
        original_key = request.form.get('original_key', '').strip()
        audio_url = request.form.get('audio_url', '').strip()
        tags_str = request.form.get('tags', '').strip()

        if not title or not lyrics:
            flash('Title and lyrics are required!', 'error')
            return redirect(url_for('add_song'))

        youtube_id = extract_youtube_id(audio_url)
        audio_file_name = None # Renombrado para evitar confusión con el objeto 'file'

        if 'audio_file' in request.files:
            file = request.files['audio_file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                try:
                    file.save(file_path)
                    audio_file_name = filename # Solo guardamos el nombre del archivo para referenciarlo
                except Exception as e:
                    logging.error(f"Error saving audio file: {e}")
                    flash('Error uploading audio file', 'error')
                    # No redirigir aquí, dejar que el resto del código maneje la adición de la canción

        new_song = Song(
            title=title,
            lyrics=lyrics,
            original_key=original_key,
            audio_file=audio_file_name, # Usar el nombre del archivo guardado
            audio_url=audio_url,
            youtube_id=youtube_id,
            created_at=datetime.utcnow()
        )
        new_song.set_tags_list(tags_str.split(',')) # Usa el método set_tags_list

        try:
            db.session.add(new_song)
            db.session.commit()
            flash('Song added successfully!', 'success')
            return redirect(url_for('view_song', song_id=new_song.id))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error adding song to DB: {e}")
            flash('Error adding song', 'error')

    return render_template('add_song.html')

@app.route('/song/<string:song_id>') # Usar string para el tipo de ID
def view_song(song_id):
    song = Song.query.get_or_404(song_id) # Obtiene la canción o un error 404
    # Pasar los tags como una lista para el template si es necesario
    song.tags = song.get_tags_list()
    return render_template('view_song.html', song=song)

@app.route('/song/<string:song_id>/edit', methods=['GET', 'POST']) # Usar string para el tipo de ID
@login_required_simple 
def edit_song(song_id):
    song = Song.query.get_or_404(song_id)

    if request.method == 'POST':
        song.title = request.form.get('title', '').strip()
        song.lyrics = request.form.get('lyrics', '').strip()
        song.original_key = request.form.get('original_key', '').strip()
        song.audio_url = request.form.get('audio_url', '').strip()
        song.youtube_id = extract_youtube_id(song.audio_url)
        tags_str = request.form.get('tags', '').strip()
        song.set_tags_list(tags_str.split(','))

        # Manejo del archivo de audio
        if 'audio_file' in request.files:
            file = request.files['audio_file']
            if file and allowed_file(file.filename):
                # Eliminar archivo antiguo si existe antes de guardar el nuevo
                if song.audio_file and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], song.audio_file)):
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], song.audio_file))
                    except OSError as e:
                        logging.error(f"Error deleting old audio file {song.audio_file}: {e}")
                
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                try:
                    file.save(file_path)
                    song.audio_file = filename
                except Exception as e:
                    logging.error(f"Error saving new audio file: {e}")
                    flash('Error uploading new audio file', 'error')
            elif file.filename == '' and request.form.get('remove_audio_file') == 'on': # Si se marca para eliminar y no se sube uno nuevo
                if song.audio_file and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], song.audio_file)):
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], song.audio_file))
                    except OSError as e:
                        logging.error(f"Error deleting audio file on removal request: {e}")
                song.audio_file = None
            # Si no se subió un archivo y no se marcó para eliminar, el audio_file existente se mantiene

        try:
            db.session.commit()
            flash('Song updated successfully!', 'success')
            return redirect(url_for('view_song', song_id=song.id))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating song in DB: {e}")
            flash('Error updating song', 'error')

    # Para el GET request, asegurarse de pasar los tags como una cadena para el campo de texto
    song.tags_str = ', '.join(song.get_tags_list())
    return render_template('edit_song.html', song=song)

@app.route('/song/<string:song_id>/delete', methods=['POST']) # Usar string para el tipo de ID
@login_required_simple 
def delete_song(song_id):
    song = Song.query.get_or_404(song_id)

    try:
        # Eliminar el archivo de audio asociado si existe
        if song.audio_file and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], song.audio_file)):
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], song.audio_file))
            except OSError as e:
                logging.error(f"Error deleting audio file {song.audio_file}: {e}")

        db.session.delete(song)
        db.session.commit()
        flash('Song deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting song from DB: {e}")
        flash('Error deleting song', 'error')
    
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files from the UPLOAD_FOLDER"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/song/<string:song_id>/presentation') # Usar string para el tipo de ID
def presentation_mode(song_id):
    song = Song.query.get_or_404(song_id)
    # Los tags también se pueden pasar como lista si el template presentation.html los necesita así
    song.tags = song.get_tags_list()
    return render_template('presentation.html', song=song)


# Este bloque se usaba para ejecutar localmente con JSON.
# Con SQLAclhemy, solo usar para crear tablas en desarrollo local si no usas Alembic.
# En Render, se usará el 'Build Command' para db.create_all()
# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all() # Esto creará las tablas la primera vez que se ejecute
#     app.run(debug=True)