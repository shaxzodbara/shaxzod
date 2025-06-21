from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # Maks. 100 MB

IP_LOG_FILE = 'ip_log.txt'
VIDEO_FILENAME = 'video.mp4'

@app.route('/')
def index():
    user_ip = request.remote_addr
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(IP_LOG_FILE, 'a') as f:
        f.write(f"{time} - {user_ip}\n")
    return render_template("video_page.html", video_filename=VIDEO_FILENAME)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        file = request.files.get('video')
        if file:
            filename = secure_filename(VIDEO_FILENAME)  # doim video.mp4 bo‘lsin
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('admin'))

    # IP loglarini o‘qish
    if os.path.exists(IP_LOG_FILE):
        with open(IP_LOG_FILE, 'r') as f:
            ip_logs = f.readlines()
    else:
        ip_logs = []

    return render_template("admin.html", ip_logs=ip_logs)

if __name__ == '__main__':
    app.run(debug=True)
