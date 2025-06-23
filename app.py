from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Xavfsiz kalit qo‘ying

# Papkalar va fayllar yo‘llari
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
DATA_FOLDER = os.path.join(BASE_DIR, 'data')
VIDEOS_JSON = os.path.join(DATA_FOLDER, 'videos.json')
VIEWS_JSON = os.path.join(DATA_FOLDER, 'views.json')
USERS_JSON = os.path.join(BASE_DIR, 'users.json')

# Papkalarni yaratish
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(VIDEO_FOLDER, exist_ok=True)

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

def load_videos():
    return safe_load_json(VIDEOS_JSON, [])

def save_videos(videos):
    with open(VIDEOS_JSON, 'w', encoding='utf-8') as f:
        json.dump(videos, f, indent=4)

def load_views():
    return safe_load_json(VIEWS_JSON, [])

def save_views(views):
    with open(VIEWS_JSON, 'w', encoding='utf-8') as f:
        json.dump(views, f, indent=4)

def load_users():
    return safe_load_json(USERS_JSON, {"admin": "admin123"})

def save_users(users):
    with open(USERS_JSON, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4)

def get_client_ip():
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
    else:
        ip = request.remote_addr
    return ip

def log_view(video_title, request):
    ip = get_client_ip()
    port = request.environ.get('REMOTE_PORT')
    agent = request.headers.get('User-Agent')
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    log_entry = {
        "video": video_title,
        "ip": ip,
        "port": port,
        "user_agent": agent,
        "time": time
    }

    logs = load_views()
    logs.append(log_entry)
    save_views(logs)

@app.route('/')
def index():
    videos = load_videos()
    return render_template('index.html', videos=videos)

@app.route('/video/<filename>')
def video(filename):
    videos = load_videos()
    video = next((v for v in videos if v['filename'] == filename), None)
    if not video:
        return "Video topilmadi", 404
    log_view(video['title'], request)
    return render_template('video.html', video=video)

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

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'admin' not in session:
        flash("Iltimos, avval tizimga kiring.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        desc = request.form.get('desc', '').strip()
        file = request.files.get('video')

        if not title or not desc:
            flash("Sarlavha va ta'rifni kiriting.", "warning")
            return redirect(url_for('admin'))

        if file and file.filename != '':
            filename = secure_filename(file.filename)
            if filename.endswith('.mp4'):
                save_path = os.path.join(VIDEO_FOLDER, filename)
                file.save(save_path)

                videos = load_videos()
                if any(v['filename'] == filename for v in videos):
                    flash("Bu nomdagi video allaqachon yuklangan.", "warning")
                else:
                    videos.append({
                        "title": title,
                        "desc": desc,
                        "filename": filename
                    })
                    save_videos(videos)
                    flash("✅ Video muvaffaqiyatli yuklandi!", "success")
            else:
                flash("❌ Faqat .mp4 formatdagi fayllarni yuklash mumkin.", "danger")
        else:
            flash("Iltimos, video faylni tanlang.", "warning")

    videos = load_videos()
    return render_template('admin.html', videos=videos)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash("Tizimdan chiqdingiz.", "info")
    return redirect(url_for('login'))

@app.route('/admin/logs')
def logs():
    if 'admin' not in session:
        flash("Iltimos, avval tizimga kiring.", "warning")
        return redirect(url_for('login'))

    logs = load_views()
    return render_template('logs.html', logs=logs[::-1])

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(VIDEO_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
