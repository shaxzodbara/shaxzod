from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Xavfsiz kalit qo‘ying

# 📁 Papkalar va fayllar yo‘llari
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
THUMBNAIL_FOLDER = os.path.join(BASE_DIR, 'static', 'thumbnails')
DATA_FOLDER = os.path.join(BASE_DIR, 'data')

VIDEOS_JSON = os.path.join(DATA_FOLDER, 'videos.json')
VIEWS_JSON = os.path.join(DATA_FOLDER, 'views.json')
USERS_JSON = os.path.join(BASE_DIR, 'users.json')

# Papkalarni yaratish (agar mavjud bo‘lmasa)
os.makedirs(VIDEO_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

# JSON fayllarni o‘qish va yozish uchun umumiy funksiyalar
def safe_load_json(path, default):
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(default, f, indent=4)
        return default
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(default, f, indent=4)
        return default

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def load_videos():
    return safe_load_json(VIDEOS_JSON, [])

def save_videos(videos):
    save_json(VIDEOS_JSON, videos)

def load_views():
    return safe_load_json(VIEWS_JSON, [])

def save_views(views):
    save_json(VIEWS_JSON, views)

def load_users():
    return safe_load_json(USERS_JSON, {"admin": "admin123"})

# Global IP olish
def get_client_ip():
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
    return request.remote_addr

# Video ko‘rilganini logga yozish
def log_view(video_title):
    log_entry = {
        "video": video_title,
        "ip": get_client_ip(),
        "port": request.environ.get('REMOTE_PORT'),
        "user_agent": request.headers.get('User-Agent'),
        "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    logs = load_views()
    logs.append(log_entry)
    save_views(logs)

# Bosh sahifa (videolar ro‘yxati)
@app.route('/')
def index():
    videos = load_videos()
    return render_template('index.html', videos=videos)

# Video ko‘rish sahifasi
@app.route('/video/<filename>')
def video(filename):
    videos = load_videos()
    video = next((v for v in videos if v['filename'] == filename), None)
    if not video:
        return "Video topilmadi", 404
    log_view(video['title'])
    return render_template('video.html', video=video)

# Login sahifasi
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_users()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username in users and users[username] == password:
            session['admin'] = username
            flash(f"Xush kelibsiz, {username}!", "success")
            return redirect(url_for('admin'))
        else:
            flash("Login yoki parol noto‘g‘ri!", "danger")
    return render_template('login.html')

# Admin panel (video va thumbnail yuklash)
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'admin' not in session:
        flash("Iltimos, avval tizimga kiring.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        desc = request.form.get('desc', '').strip()
        video_file = request.files.get('video')
        thumb_file = request.files.get('thumbnail')

        if not title or not desc or not video_file or not thumb_file:
            flash("Barcha maydonlarni to‘ldiring.", "warning")
            return redirect(url_for('admin'))

        video_filename = secure_filename(video_file.filename)
        thumb_filename = secure_filename(thumb_file.filename)

        if not video_filename.lower().endswith('.mp4'):
            flash("Faqat .mp4 formatdagi video fayllarga ruxsat berilgan.", "danger")
            return redirect(url_for('admin'))

        if not thumb_filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            flash("Thumbnail rasm .jpg, .jpeg yoki .png formatda bo‘lishi kerak.", "danger")
            return redirect(url_for('admin'))

        videos = load_videos()
        if any(v['filename'] == video_filename for v in videos):
            flash("Bu nomdagi video allaqachon mavjud.", "warning")
        else:
            video_path = os.path.join(VIDEO_FOLDER, video_filename)
            thumb_path = os.path.join(THUMBNAIL_FOLDER, thumb_filename)

            video_file.save(video_path)
            thumb_file.save(thumb_path)

            videos.append({
                "title": title,
                "desc": desc,
                "filename": video_filename,
                "thumbnail": thumb_filename
            })
            save_videos(videos)
            flash("✅ Video va rasm muvaffaqiyatli yuklandi!", "success")

    videos = load_videos()
    return render_template('admin.html', videos=videos)

# Loglarni ko‘rish sahifasi
@app.route('/admin/logs')
def logs():
    if 'admin' not in session:
        flash("Iltimos, tizimga kiring.", "warning")
        return redirect(url_for('login'))
    logs = load_views()
    return render_template('logs.html', logs=logs[::-1])

# Logout
@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash("Tizimdan chiqdingiz.", "info")
    return redirect(url_for('login'))

# Video fayllarni serverdan jo‘natish
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(VIDEO_FOLDER, filename)

# Thumbnail fayllarni serverdan jo‘natish
@app.route('/thumbnails/<filename>')
def thumbnail_file(filename):
    return send_from_directory(THUMBNAIL_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
