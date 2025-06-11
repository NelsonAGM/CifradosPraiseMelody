import os
import json
import uuid
import logging
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a'}
SONGS_FILE = 'songs.json'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_songs():
    """Load songs from JSON file"""
    try:
        if os.path.exists(SONGS_FILE):
            with open(SONGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"Error loading songs: {e}")
    return []

def save_songs(songs):
    """Save songs to JSON file"""
    try:
        with open(SONGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(songs, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"Error saving songs: {e}")
        return False

def extract_youtube_id(url):
    """Extract YouTube video ID from URL"""
    if not url:
        return None
    
    parsed_url = urlparse(url)
    if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query).get('v', [None])[0]
        elif parsed_url.path.startswith('/embed/'):
            return parsed_url.path.split('/')[2]
    elif parsed_url.hostname in ['youtu.be']:
        return parsed_url.path[1:]
    
    return None

@app.route('/')
def index():
    """Main page with song list"""
    songs = load_songs()
    search = request.args.get('search', '').strip()
    tag_filter = request.args.get('tag', '').strip()
    
    # Filter songs based on search and tag
    if search:
        songs = [song for song in songs if search.lower() in song.get('title', '').lower()]
    
    if tag_filter:
        songs = [song for song in songs if tag_filter.lower() in [tag.lower() for tag in song.get('tags', [])]]
    
    # Get all unique tags for filter dropdown
    all_tags = set()
    for song in load_songs():
        all_tags.update(song.get('tags', []))
    
    return render_template('index.html', songs=songs, search=search, tag_filter=tag_filter, all_tags=sorted(all_tags))

@app.route('/add', methods=['GET', 'POST'])
def add_song():
    """Add new song"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        lyrics = request.form.get('lyrics', '').strip()
        original_key = request.form.get('original_key', '').strip()
        audio_url = request.form.get('audio_url', '').strip()
        tags_str = request.form.get('tags', '').strip()
        
        if not title:
            flash('Title is required', 'error')
            return render_template('add_song.html')
        
        # Process tags
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
        
        # Handle file upload
        audio_file = None
        if 'audio_file' in request.files:
            file = request.files['audio_file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to avoid conflicts
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                audio_file = filename
        
        # Create new song
        song = {
            'id': str(uuid.uuid4()),
            'title': title,
            'lyrics': lyrics,
            'original_key': original_key,
            'current_key': original_key,  # For transposition
            'audio_file': audio_file,
            'audio_url': audio_url,
            'youtube_id': extract_youtube_id(audio_url),
            'tags': tags,
            'created_at': datetime.now().isoformat()
        }
        
        songs = load_songs()
        songs.append(song)
        
        if save_songs(songs):
            flash('Song added successfully!', 'success')
            return redirect(url_for('view_song', song_id=song['id']))
        else:
            flash('Error saving song', 'error')
    
    return render_template('add_song.html')

@app.route('/song/<song_id>')
def view_song(song_id):
    """View individual song"""
    songs = load_songs()
    song = next((s for s in songs if s['id'] == song_id), None)
    
    if not song:
        flash('Song not found', 'error')
        return redirect(url_for('index'))
    
    return render_template('view_song.html', song=song)

@app.route('/song/<song_id>/presentation')
def presentation_mode(song_id):
    """Presentation mode for live performance"""
    songs = load_songs()
    song = next((s for s in songs if s['id'] == song_id), None)
    
    if not song:
        flash('Song not found', 'error')
        return redirect(url_for('index'))
    
    return render_template('presentation.html', song=song)

@app.route('/song/<song_id>/transpose', methods=['POST'])
def transpose_song(song_id):
    """Transpose song chords"""
    direction = request.json.get('direction', 'up')
    semitones = 1 if direction == 'up' else -1
    
    songs = load_songs()
    song_index = next((i for i, s in enumerate(songs) if s['id'] == song_id), None)
    
    if song_index is None:
        return jsonify({'error': 'Song not found'}), 404
    
    # This will be handled on the frontend with JavaScript
    # We just return success here
    return jsonify({'success': True, 'direction': direction})

@app.route('/song/<song_id>/delete', methods=['POST'])
def delete_song(song_id):
    """Delete song"""
    songs = load_songs()
    song_index = next((i for i, s in enumerate(songs) if s['id'] == song_id), None)
    
    if song_index is None:
        flash('Song not found', 'error')
        return redirect(url_for('index'))
    
    # Delete associated audio file if exists
    song = songs[song_index]
    if song.get('audio_file'):
        try:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], song['audio_file'])
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logging.error(f"Error deleting audio file: {e}")
    
    songs.pop(song_index)
    
    if save_songs(songs):
        flash('Song deleted successfully', 'success')
    else:
        flash('Error deleting song', 'error')
    
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
