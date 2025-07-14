# app/web_server.py
from flask import Flask, render_template
import os
import json
from config import LOG_FILE_PATH, VERSION
from utils import get_source_code_context

app = Flask(__name__)

@app.route('/')
def index():
    log_entries = []
    if os.path.exists(LOG_FILE_PATH):
        try:
            with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
                log_entries = json.load(f)
            log_entries.reverse() # Hiển thị mục gần đây nhất trước
        except json.JSONDecodeError:
            print(f"⚠️ [Web Server] File log {LOG_FILE_PATH} bị lỗi hoặc trống, bắt đầu lịch sử mới trên web.")
            log_entries = []
    
    current_source_context = get_source_code_context()
    
    # Sử dụng render_template để load file index.html từ thư mục templates
    return render_template('index.html', log_entries=log_entries, version=VERSION, source_context=current_source_context)

if __name__ == '__main__':
    print("🚀 Đang khởi động AI Agent X Web Interface...")
    print("🌐 Truy cập tại: http://127.0.0.1:3000")
    # debug=True cho phép tự động tải lại khi có thay đổi code và cung cấp debugger
    app.run(debug=True, port=3000)
