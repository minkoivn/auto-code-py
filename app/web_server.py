# app/web_server.py
from flask import Flask, render_template_string
import os
import json
from config import LOG_FILE_PATH, VERSION
from utils import get_source_code_context # NEW IMPORT

app = Flask(__name__)

# Basic HTML structure for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Agent X Interface</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; line-height: 1.6; }
        .container { max-width: 900px; margin: auto; background-color: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #0056b3; margin-bottom: 10px; }
        h2 { color: #0056b3; border-bottom: 1px solid #eee; padding-bottom: 5px; margin-top: 20px; }
        .version { font-size: 0.9em; color: #666; margin-top: -10px; margin-bottom: 20px; }
        .log-entry { background-color: #e9e9e9; padding: 10px; margin-bottom: 8px; border-radius: 5px; }
        .log-entry strong { color: #0056b3; }
        .log-entry.committed { background-color: #d4edda; border-left: 5px solid #28a745; }
        .log-entry.rejected_validation_failed, .log-entry.execution_failed { background-color: #f8d7da; border-left: 5px solid #dc3545; }
        .log-entry.no_proposal { background-color: #fff3cd; border-left: 5px solid #ffc107; }
        .footer { margin-top: 30px; text-align: center; color: #666; font-size: 0.9em; }
        ul { list-style-type: none; padding: 0; }
        pre { background-color: #eee; padding: 10px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Chào mừng đến với AI Agent X!</h1>
        <div class="version">Phiên bản Agent: {{ version }}</div>
        <p>Đây là giao diện web để theo dõi và tương tác với AI Agent X của bạn.</p>
        <p>AI Agent X sẽ tự động chạy trong nền và các cập nhật mới nhất sẽ xuất hiện ở đây.</p>

        <h2>Bối cảnh mã nguồn hiện tại của Agent X</h2>
        <pre>{{ source_context }}</pre>

        <h2>Lịch sử tiến hóa gần đây</h2>
        {% if log_entries %}
            <ul>
                {% for entry in log_entries %}
                    <li class="log-entry {{ entry.status | lower | replace(' ', '_') }}">
                        <strong>Lần {{ entry.iteration }}:</strong> Trạng thái = {{ entry.status }}. Lý do = {{ entry.reason }}
                    </li>
                {% endfor %}
            </ul>
        {% else %}
            <p>Chưa có lịch sử tiến hóa nào được ghi lại.</p>
        {% endif %}
    </div>
    <div class="footer">
        Đang chạy trên localhost:3000
    </div>
</body>
</html>
"""

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
    
    # NEW: Get source code context for display
    current_source_context = get_source_code_context()
    
    return render_template_string(HTML_TEMPLATE, log_entries=log_entries, version=VERSION, source_context=current_source_context)

if __name__ == '__main__':
    print("🚀 Đang khởi động AI Agent X Web Interface...")
    print("🌐 Truy cập tại: http://127.0.0.1:3000")
    app.run(debug=True, port=3000)
