# app/utils.py

import os
from config import EXCLUDE_PATHS

# Định nghĩa kích thước tệp tối đa cho phép khi đọc mã nguồn.
# Giá trị này có thể được chuyển vào config.py trong các phiên bản sau để tập trung hóa cấu hình.
MAX_FILE_SIZE_MB = 1 # Ví dụ: giới hạn 1 MB
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

def get_source_code_context():
    """Đọc mã nguồn thư mục 'app' để làm bối cảnh, loại trừ các file/thư mục không cần thiết.
    Bao gồm kiểm tra kích thước file để bỏ qua các file quá lớn.
    """
    context = ""
    for root, _, files in os.walk("app"):
        for file in files:
            filepath = os.path.join(root, file)
            
            # Kiểm tra xem đường dẫn có nằm trong danh sách loại trừ không
            excluded = False
            for exclude_path in EXCLUDE_PATHS:
                if filepath == exclude_path: # Kiểm tra file cụ thể
                    excluded = True
                    break
                # Kiểm tra nếu là thư mục con (có dấu gạch chéo ở cuối)
                if exclude_path.endswith('/') and filepath.startswith(exclude_path):
                    excluded = True
                    break
            
            if excluded:
                continue

            if file.endswith(".py"):
                # Thêm kiểm tra kích thước tệp trước khi đọc
                try:
                    file_size = os.path.getsize(filepath)
                    if file_size > MAX_FILE_SIZE_BYTES:
                        print(f"⚠️ [WARNING] Bỏ qua file quá lớn: {filepath} ({file_size / (1024 * 1024):.2f} MB). Kích thước tối đa cho phép là {MAX_FILE_SIZE_MB} MB.")
                        continue # Bỏ qua file này
                except OSError as e:
                    print(f"❌ [ERROR] Không thể kiểm tra kích thước file {filepath}: {e}")
                    continue # Bỏ qua file này nếu không thể lấy kích thước

                context += f"--- File: {filepath} ---\n"
                with open(filepath, "r", encoding="utf-8") as f:
                    context += f.read()
                context += "\n\n"
    return context

def format_history_for_prompt(history_log: list, num_entries=10) -> str:
    """Định dạng các mục log gần đây nhất để đưa vào prompt."""
    if not history_log:
        return "Chưa có lịch sử."
    
    recent_history = history_log[-num_entries:]
    formatted_history = ""
    for entry in recent_history:
        formatted_history += f"- Lần {entry['iteration']}: Trạng thái = {entry['status']}. Lý do = {entry['reason']}\n"
    return formatted_history
