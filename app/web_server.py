# app/web_server.py
from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import json
from config import LOG_FILE_PATH, VERSION
from utils import get_source_code_context

app = Flask(__name__)

# Define a path for a control file that orchestrator can check
CONTROL_DIR = "app/control"
TRIGGER_NEXT_STEP_FLAG = os.path.join(CONTROL_DIR, "trigger_next_step.flag")

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
    
    # Pass a flag to the template indicating if a trigger file exists
    is_waiting_for_trigger = os.path.exists(TRIGGER_NEXT_STEP_FLAG)

    # Sử dụng render_template để load file index.html từ thư mục templates
    return render_template('index.html', 
                           log_entries=log_entries, 
                           version=VERSION, 
                           source_context=current_source_context,
                           is_waiting_for_trigger=is_waiting_for_trigger)

@app.route('/api/trigger_next_step', methods=['POST'])
def trigger_next_step():
    """
    Tạo một file flag để báo hiệu cho orchestrator chạy bước tiếp theo.
    """
    try:
        os.makedirs(CONTROL_DIR, exist_ok=True)
        with open(TRIGGER_NEXT_STEP_FLAG, 'w') as f:
            f.write("triggered")
        print(f"✅ [Web Server] Đã tạo file trigger: {TRIGGER_NEXT_STEP_FLAG}")
        return jsonify({"status": "success", "message": "Trigger file created."}), 200
    except Exception as e:
        print(f"❌ [Web Server] Lỗi khi tạo file trigger: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/clear_trigger_flag', methods=['POST'])
def clear_trigger_flag():
    """
    Xóa file flag để reset trạng thái trigger. (Hữu ích khi debug hoặc reset)
    """
    try:
        if os.path.exists(TRIGGER_NEXT_STEP_FLAG):
            os.remove(TRIGGER_NEXT_STEP_FLAG)
            print(f"✅ [Web Server] Đã xóa file trigger: {TRIGGER_NEXT_STEP_FLAG}")
        return jsonify({"status": "success", "message": "Trigger file cleared."}), 200
    except Exception as e:
        print(f"❌ [Web Server] Lỗi khi xóa file trigger: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    print("🚀 Đang khởi động AI Agent X Web Interface...")
    print("🌐 Truy cập tại: http://127.0.0.1:3000")
    # debug=True cho phép tự động tải lại khi có thay đổi code và cung cấp debugger
    app.run(debug=True, port=3000)
