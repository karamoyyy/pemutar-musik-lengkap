import os
import json
import uuid
from flask import Flask, render_template, request, jsonify
import yt_dlp

app = Flask(__name__)

# Pengaturan Folder
MUSIC_FOLDER = 'static/music'
PLAYLIST_FILE = 'playlist.json'
os.makedirs(MUSIC_FOLDER, exist_ok=True)

def read_playlist():
    if not os.path.exists(PLAYLIST_FILE):
        return []
    try:
        with open(PLAYLIST_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_playlist(playlist):
    with open(PLAYLIST_FILE, 'w') as f:
        json.dump(playlist, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/songs', methods=['GET'])
def get_songs():
    return jsonify(read_playlist())

@app.route('/api/upload', methods=['POST'])
def upload_song():
    if 'file' not in request.files:
        return jsonify({'error': 'Tidak ada file'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'File kosong'}), 400
    
    song_id = str(uuid.uuid4())
    filename = f"{song_id}_{file.filename}"
    filepath = os.path.join(MUSIC_FOLDER, filename)
    file.save(filepath)
    
    playlist = read_playlist()
    new_song = {
        'id': song_id,
        'title': file.filename,
        'path': filepath
    }
    playlist.append(new_song)
    save_playlist(playlist)
    
    return jsonify(new_song)

@app.route('/api/add_youtube', methods=['POST'])
def add_youtube():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL tidak valid'}), 400

    song_id = str(uuid.uuid4())
    save_path = os.path.join(MUSIC_FOLDER, f"{song_id}.%(ext)s")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': save_path,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Lagu YouTube')
            ext = info.get('ext', 'webm')
            
            playlist = read_playlist()
            new_song = {
                'id': song_id,
                'title': title,
                'path': f"{MUSIC_FOLDER}/{song_id}.{ext}"
            }
            playlist.append(new_song)
            save_playlist(playlist)
            
            return jsonify(new_song)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rename', methods=['POST'])
def rename_song():
    data = request.json
    song_id = data.get('id')
    new_title = data.get('title')
    
    playlist = read_playlist()
    for song in playlist:
        if song['id'] == song_id:
            song['title'] = new_title
            save_playlist(playlist)
            return jsonify({'success': True})
            
    return jsonify({'error': 'Lagu tidak ditemukan'}), 404

@app.route('/api/delete', methods=['POST'])
def delete_song():
    data = request.json
    song_id = data.get('id')
    
    playlist = read_playlist()
    for song in playlist:
        if song['id'] == song_id:
            try:
                if os.path.exists(song['path']):
                    os.remove(song['path'])
            except Exception as e:
                pass
            
            playlist.remove(song)
            save_playlist(playlist)
            return jsonify({'success': True})
            
    return jsonify({'error': 'Lagu tidak ditemukan'}), 404

@app.route('/api/move', methods=['POST'])
def move_song():
    data = request.json
    song_id = data.get('id')
    direction = data.get('direction')
    
    playlist = read_playlist()
    idx = -1
    for i, song in enumerate(playlist):
        if song['id'] == song_id:
            idx = i
            break
            
    if idx != -1:
        if direction == 'up' and idx > 0:
            playlist[idx], playlist[idx-1] = playlist[idx-1], playlist[idx]
            save_playlist(playlist)
            return jsonify({'success': True})
        elif direction == 'down' and idx < len(playlist) - 1:
            playlist[idx], playlist[idx+1] = playlist[idx+1], playlist[idx]
            save_playlist(playlist)
            return jsonify({'success': True})
            
    return jsonify({'error': 'Lagu tidak dapat dipindahkan'}), 400

if __name__ == '__main__':
    app.run(debug=True)
