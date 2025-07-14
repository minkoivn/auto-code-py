# app/utils.py

import os
from config import EXCLUDE_PATHS, PROJECT_ROOT # Import PROJECT_ROOT
from logging_setup import logger # Import logger

# Định nghĩa kích thước tệp tối đa cho phép khi đọc mã nguồn.
# Giá trị này có thể được chuyển vào config.py trong các phiên bản sau để tập trung hóa cấu hình.
MAX_FILE_SIZE_MB = 1 # Ví dụ: giới hạn 1 MB
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

def get_source_code_context(relevant_files: list[str] = None):
    """Đọc mã nguồn để làm bối cảnh, loại trừ các file/thư mục không cần thiết.
    Nếu relevant_files được cung cấp, chỉ đọc các tệp đó.
    Bao gồm kiểm tra kích thước file để bỏ qua các file quá lớn.
    
    Args:
        relevant_files (list[str], optional): Danh sách các đường dẫn tệp (ví dụ: 'app/module.py')
                                            để giới hạn bối cảnh chỉ đọc các tệp này.
                                            Nếu None, sẽ đọc tất cả các tệp trong thư mục 'app'.
    Returns:
        str: Chuỗi chứa nội dung mã nguồn được định dạng.
    """
    context = ""
    files_to_process = []

    if relevant_files:
        # Sử dụng các tệp liên quan được cung cấp, đảm bảo chúng tồn tại và có thể truy cập
        for r_file in relevant_files:
            # Xây dựng đường dẫn tuyệt đối từ thư mục gốc của dự án để có tính ổn định
            # relevant_files được chuẩn hóa để bắt đầu bằng 'app/' bởi ai_z_agent
            abs_filepath = os.path.join(PROJECT_ROOT, r_file)
            if os.path.exists(abs_filepath) and os.path.isfile(abs_filepath):
                files_to_process.append((abs_filepath, r_file)) # Lưu (đường_dẫn_tuyệt_đối, đường_dẫn_hiển_thị)
            else:
                logger.warning(f"⚠️ [WARNING] AI Z đề xuất tệp không tồn tại hoặc không phải là tệp thông thường: {r_file}. Bỏ qua.")
    else:
        # Nếu không có tệp cụ thể nào được yêu cầu, duyệt toàn bộ thư mục 'app'
        for root, _, files in os.walk(os.path.join(PROJECT_ROOT, "app")):
            for file in files:
                abs_filepath = os.path.join(root, file)
                # Tính toán đường dẫn hiển thị tương đối so với PROJECT_ROOT để định dạng bối cảnh nhất quán
                display_filepath = os.path.relpath(abs_filepath, PROJECT_ROOT)
                files_to_process.append((abs_filepath, display_filepath))

    for abs_filepath, display_filepath in files_to_process:
        # Kiểm tra loại trừ dựa trên display_filepath (ví dụ: 'app/log.json')
        excluded = False
        for exclude_path in EXCLUDE_PATHS:
            if display_filepath == exclude_path: # Khớp chính xác
                excluded = True
                break
            # Kiểm tra nếu là thư mục cần loại trừ (ví dụ: 'app/prompts/')
            if exclude_path.endswith('/') and display_filepath.startswith(exclude_path):
                excluded = True
                break
        
        if excluded:
            continue

        # Hiện tại, chỉ xử lý các tệp Python
        if display_filepath.endswith(".py"):
            try:
                file_size = os.path.getsize(abs_filepath)
                if file_size > MAX_FILE_SIZE_BYTES:
                    logger.warning(f"⚠️ [WARNING] Bỏ qua file quá lớn: {display_filepath} ({file_size / (1024 * 1024):.2f} MB). Kích thước tối đa cho phép là {MAX_FILE_SIZE_MB} MB.")
                    continue
            except OSError as e:
                logger.error(f"❌ [ERROR] Không thể kiểm tra kích thước file {display_filepath}: {e}")
                continue

            try:
                context += f"--- File: {display_filepath} ---\n"
                with open(abs_filepath, "r", encoding="utf-8") as f:
                    context += f.read()
                context += "\n\n"
            except Exception as e:
                logger.error(f"❌ [ERROR] Không thể đọc nội dung file {display_filepath}: {e}")
                continue # Tiếp tục với tệp tiếp theo nếu đọc thất bại

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
