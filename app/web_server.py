# app/web_server.py
from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import json
# Import CONTROL_DIR and TRIGGER_NEXT_STEP_FLAG from config.py for centralization
from config import LOG_FILE_PATH, VERSION, CONTROL_DIR, TRIGGER_NEXT_STEP_FLAG 
from utils import get_source_code_context

app = Flask(__name__)

# Define the user request file path, leveraging CONTROL_DIR from config
USER_REQUEST_FILE = os.path.join(CONTROL_DIR, "user_request.txt") 

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

    # New: Check for user request file and pass its content
    user_request_pending = False
    user_request_content = ""
    if os.path.exists(USER_REQUEST_FILE):
        user_request_pending = True
        try:
            with open(USER_REQUEST_FILE, "r", encoding="utf-8") as f:
                user_request_content = f.read()
        except Exception as e:
            print(f"❌ [Web Server] Lỗi khi đọc file yêu cầu người dùng: {e}")
            user_request_content = "Error reading request file."

    # Sử dụng render_template để load file index.html từ thư mục templates
    return render_template('index.html', 
                           log_entries=log_entries, 
                           version=VERSION, 
                           source_context=current_source_context,
                           is_waiting_for_trigger=is_waiting_for_trigger,
                           user_request_pending=user_request_pending, 
                           user_request_content=user_request_content)

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

@app.route('/api/submit_user_request', methods=['POST'])
def submit_user_request():
    """
    Nhận yêu cầu cải thiện từ người dùng và lưu vào file.
    """
    user_request = request.json.get('request_text')
    if not user_request:
        return jsonify({"status": "error", "message": "Yêu cầu không được để trống."}), 400
    
    try:
        os.makedirs(CONTROL_DIR, exist_ok=True)
        with open(USER_REQUEST_FILE, 'w', encoding='utf-8') as f:
            f.write(user_request.strip())
        print(f"✅ [Web Server] Đã lưu yêu cầu người dùng vào file: {USER_REQUEST_FILE}")
        return jsonify({"status": "success", "message": "Yêu cầu đã được gửi. AI Z sẽ xem xét trong lần lặp tiếp theo."}), 200
    except Exception as e:
        print(f"❌ [Web Server] Lỗi khi lưu yêu cầu người dùng: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/clear_user_request', methods=['POST'])
def clear_user_request():
    """
    Xóa file yêu cầu người dùng sau khi đã được xử lý hoặc nếu muốn hủy.
    """
    try:
        if os.path.exists(USER_REQUEST_FILE):
            os.remove(USER_REQUEST_FILE)
            print(f"✅ [Web Server] Đã xóa file yêu cầu người dùng: {USER_REQUEST_FILE}")
        return jsonify({"status": "success", "message": "Yêu cầu người dùng đã được xóa."}), 200
    except Exception as e:
        print(f"❌ [Web Server] Lỗi khi xóa file yêu cầu người dùng: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Đang khởi động AI Agent X Web Interface...")
    print("🌐 Truy cập tại: http://127.0.0.1:3000")
    # debug=True cho phép tự động tải lại khi có thay đổi code và cung cấp debugger
    app.run(debug=True, port=3000)
