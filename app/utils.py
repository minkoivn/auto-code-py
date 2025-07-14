# app/utils.py

import os
from config import config # Sửa: import đối tượng config
from logging_setup import logger

MAX_FILE_SIZE_MB = 1
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

def get_source_code_context(relevant_files: list[str] = None):
    """Đọc mã nguồn để làm bối cảnh."""
    context = ""
    files_to_process = []
    
    # Sửa: sử dụng config.PROJECT_ROOT và config.EXCLUDE_PATHS
    project_root = config.PROJECT_ROOT
    exclude_paths = config.EXCLUDE_PATHS

    if relevant_files:
        for r_file in relevant_files:
            abs_filepath = os.path.join(project_root, r_file)
            if os.path.exists(abs_filepath) and os.path.isfile(abs_filepath):
                files_to_process.append((abs_filepath, r_file))
            else:
                logger.warning(f"AI Z đề xuất tệp không tồn tại: {r_file}. Bỏ qua.")
    else:
        for root, _, files in os.walk(os.path.join(project_root, "app")):
            for file in files:
                abs_filepath = os.path.join(root, file)
                display_filepath = os.path.relpath(abs_filepath, project_root).replace('\\', '/')
                files_to_process.append((abs_filepath, display_filepath))

    for abs_filepath, display_filepath in files_to_process:
        excluded = any(ex in display_filepath for ex in exclude_paths)
        if excluded:
            continue

        if display_filepath.endswith(".py") or display_filepath.endswith(".html") or display_filepath.endswith(".txt"):
            try:
                if os.path.getsize(abs_filepath) > MAX_FILE_SIZE_BYTES:
                    logger.warning(f"Bỏ qua file quá lớn: {display_filepath}")
                    continue
                with open(abs_filepath, "r", encoding="utf-8") as f:
                    context += f"--- File: {display_filepath} ---\n"
                    context += f.read()
                    context += "\n\n"
            except Exception as e:
                logger.error(f"Không thể đọc file {display_filepath}: {e}")
    return context

def format_history_for_prompt(history_log: list, num_entries=10) -> str:
    """Định dạng lịch sử để đưa vào prompt."""
    if not history_log:
        return "Chưa có lịch sử."
    
    recent_history = history_log[-num_entries:]
    formatted_history = ""
    for entry in recent_history:
        iter_num = entry.get('iteration', 'N/A')
        status = entry.get('status', 'N/A')
        reason = entry.get('reason', 'N/A')
        formatted_history += f"- Lần {iter_num}: Trạng thái = {status}. Lý do = {reason}\n"
    return formatted_history