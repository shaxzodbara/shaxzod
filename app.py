from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Admin sessiya uchun

UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

IP_LOG_FILE = 'ip_log.json'

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = '12345'  # xohlasangiz o'zgartiring

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # Maks 500MB fayl

def load_ip_logs():
    if not os.path.exists(IP_LOG_FILE):
        return []
    with open(IP_LOG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_ip_log(ip, video):
    logs = load_ip_logs()
    logs.append({
        "ip": ip,
        "video": video,
        "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    with open(IP_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=4, ensure_ascii=False)

@app.route('/')
def index():
    videos = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', videos=videos)

@app.route('/watch/<filename>')
def watch_video(filename):
    ip = request.remote_addr
    if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        return "Video topilmadi", 404
    save_ip_log(ip, filename)
    return render_template('watch.html', filename=filename)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            flash('Noto‘g‘ri login yoki parol', 'danger')
    return render_template('admin_login.html')

@app.route('/admin')
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    videos = os.listdir(app.config['UPLOAD_FOLDER'])
    logs = load_ip_logs()
    return render_template('admin.html', videos=videos, logs=logs)

@app.route('/admin/upload', methods=['POST'])
def upload_video():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    if 'video' not in request.files:
        flash('Video fayl tanlanmadi', 'warning')
        return redirect(url_for('admin_panel'))

    file = request.files['video']
    if file.filename == '':
        flash('Video fayl tanlanmadi', 'warning')
        return redirect(url_for('admin_panel'))

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    flash('Video muvaffaqiyatli yuklandi', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True)
