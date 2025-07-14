# app/orchestrator.py
import os
import subprocess
import json
import time
import py_compile
import google.generativeai as genai
from ai_agent import invoke_ai_x
from config import (
    LOG_FILE_PATH,
    EXCLUDE_PATHS,
    MAX_AI_X_RETRIES,
    RETRY_SLEEP_SECONDS,
    SLEEP_BETWEEN_ITERATIONS_SECONDS,
    VERSION,
    INTERACTIVE_MODE,
    CONTROL_DIR,
    TRIGGER_NEXT_STEP_FLAG,
    GEMINI_API_KEY,
    USER_REQUEST_FILE,
    REPO_DIR # Import REPO_DIR để khởi tạo GitAgent
)
from utils import get_source_code_context
from git_utils import GitAgent # Thay đổi: Import lớp GitAgent
from ai_z_agent import invoke_ai_z
import threading
from web_server import app as flask_app
from logging_setup import logger

# --- CÁC HÀM TIỆN ÍCH VÀ CẤU HÌNH ---

def setup():
    """Cấu hình API Key cho Gemini."""
    if not GEMINI_API_KEY:
        logger.critical("GEMINI_API_KEY not found. Please set it in the .env file.", exc_info=True)
        raise ValueError("GEMINI_API_KEY not found. Please set it in the .env file.")
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Đã cấu hình Gemini API Key.")

def _run_web_server():
    """Chạy Flask web server trong một thread riêng."""
    logger.info("[Web Server] Đang khởi động AI Agent X Web Interface...")
    logger.info("Truy cập tại: http://127.0.0.1:3000")
    # debug=False và use_reloader=False khi chạy trong thread để tránh lỗi reloader
    flask_app.run(debug=False, port=3000, use_reloader=False)

# --- CÁC HÀM TƯƠNG TÁC VỚI AI VÀ LOG ---

def _invoke_ai_with_retries(context: str, history_log: list) -> tuple[str, str, str, str]:
    """
    Kêu gọi AI X với cơ chế thử lại.
    Trả về một tuple: (filepath, new_content, description, failure_reason)
    """
    filepath, new_content, description, failure_reason = None, None, None, ""
    for attempt in range(MAX_AI_X_RETRIES):
        logger.info(f"  (Lần thử {attempt + 1}/{MAX_AI_X_RETRIES} cho AI X...)")
        filepath, new_content, description, failure_reason = invoke_ai_x(context, history_log)
        if filepath and new_content and description:
            logger.info(f"  AI X đã đưa ra đề xuất thành công ở lần thử {attempt + 1}.")
            return filepath, new_content, description, None # Return None for failure_reason on success
        else:
            logger.warning(f"  AI X thất bại lần {attempt + 1}. Lý do: {failure_reason}")
            if attempt < MAX_AI_X_RETRIES - 1:
                time.sleep(RETRY_SLEEP_SECONDS) 
    
    # If all retries failed
    return None, None, None, f"AI X thất bại sau {MAX_AI_X_RETRIES} lần thử. Lý do cuối cùng: {failure_reason}"

def _invoke_ai_z_with_retries(user_request: str | None) -> tuple[str | None, list[str] | None]:
    """
    Kêu gọi AI Z với cơ chế thử lại.
    Trả về một tuple: (chuỗi mô tả nhiệm vụ, danh sách các tệp liên quan) hoặc (None, None) nếu có lỗi.
    """
    suggestion, relevant_files = None, None
    for attempt in range(MAX_AI_X_RETRIES): # Sử dụng cùng cấu hình thử lại với AI X
        logger.info(f"  (Lần thử {attempt + 1}/{MAX_AI_X_RETRIES} cho AI Z...)")
        suggestion, relevant_files = invoke_ai_z(user_request=user_request)
        if suggestion is not None and relevant_files is not None: # Kiểm tra cả hai phần
            logger.info(f"  AI Z đã đưa ra đề xuất thành công ở lần thử {attempt + 1}.")
            return suggestion, relevant_files
        else:
            logger.warning(f"  AI Z thất bại lần {attempt + 1}.")
            if attempt < MAX_AI_X_RETRIES - 1:
                time.sleep(RETRY_SLEEP_SECONDS)
    
    # Nếu tất cả các lần thử đều thất bại
    logger.error(f"AI Z thất bại sau {MAX_AI_X_RETRIES} lần thử.")
    return None, None

def _apply_and_validate_file_content(filepath: str, new_content: str) -> tuple[bool, str]:
    """
    Áp dụng nội dung file mới vào hệ thống file, kiểm tra cú pháp nếu là Python.
    Trả về (thành công: bool, thông báo lỗi: str).
    """
    temp_filepath = filepath + ".tmp"
    is_new_file = not os.path.exists(filepath)

    try:
        dir_name = os.path.dirname(filepath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        with open(temp_filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        is_python_file = filepath.endswith(".py")
        
        if is_python_file:
            py_compile.compile(temp_filepath, doraise=True)
            logger.info("[VALIDATOR] Mã nguồn Python mới hợp lệ.")
        else:
            logger.warning(f"[VALIDATOR] File '{filepath}' không phải file Python, bỏ qua kiểm tra cú pháp.")

        os.replace(temp_filepath, filepath)
        action_verb = "Tạo mới" if is_new_file else "Ghi đè"
        logger.info(f"{action_verb} thành công file: {filepath}")
        return True, ""
        
    except py_compile.PyCompileError as e:
        logger.error(f"Lỗi cú pháp trong đề xuất file Python mới: {e}", exc_info=True)
        return False, f"Lỗi cú pháp trong đề xuất file Python mới: {e}"
    except Exception as e:
        logger.error(f"Lỗi không xác định khi áp dụng file: {e}", exc_info=True)
        return False, f"Lỗi không xác định khi áp dụng file: {e}"
    finally:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)


# --- HÀM THỰC THI KIẾN TRÚC MỚI ---

def validate_and_commit_changes(filepath: str, new_content: str, description: str):
    """
    Kiểm tra cú pháp (nếu là file Python), nếu hợp lệ thì ghi đè/tạo mới và commit.
    Sử dụng GitAgent để thực hiện các thao tác Git.
    Trả về một tuple: (status, final_reason).
    """
    # Khởi tạo GitAgent, sử dụng REPO_DIR từ config
    git_agent = GitAgent(REPO_DIR)

    logger.info(f"Bắt đầu quá trình thực thi cho file: {filepath}")
    
    success, validation_reason = _apply_and_validate_file_content(filepath, new_content)

    if not success:
        logger.error(f"[VALIDATOR] {validation_reason}")
        return "REJECTED_VALIDATION_FAILED", validation_reason
    
    try:
        commit_message = f"feat(AI): {description}"
        git_agent.add_and_commit(filepath, commit_message) # Sử dụng đúng instance GitAgent
        
        return "COMMITTED", description

    except Exception as e: # Bắt GitCommandError hoặc bất kỳ Exception nào khác từ GitAgent
        error_reason = f"Lỗi trong quá trình thực hiện Git commit: {e}"
        logger.error(f"[Z] {error_reason}", exc_info=True)
        return "EXECUTION_FAILED", error_reason

# --- CÁC BƯỚC TIẾN HÓA CỐT LÕI ---

def _execute_evolution_step(iteration_count: int, history_log: list) -> dict:
    """
    Thực hiện một bước tiến hóa duy nhất (gọi AI, xử lý phản hồi, xác thực và commit).
    Trả về một dictionary log_entry cho bước này.
    """
    log_entry = { "iteration": iteration_count, "status": "", "reason": "" }
    
    # 1. Lấy bối cảnh mã nguồn hiện tại
    # source_context = get_source_code_context()
    
    # 2. Đọc yêu cầu người dùng (nếu có)
    user_request = None
    if os.path.exists(USER_REQUEST_FILE):
        try:
            with open(USER_REQUEST_FILE, "r", encoding="utf-8") as f:
                user_request = f.read().strip()
            logger.info(f"Đã đọc yêu cầu người dùng từ '{USER_REQUEST_FILE}'.")
        except Exception as e:
            logger.error(f"Lỗi khi đọc file yêu cầu người dùng '{USER_REQUEST_FILE}': {e}", exc_info=True)
            user_request = None # Reset user_request if error occurs
    
    # 3. Gọi AI Z để lấy đề xuất nhiệm vụ (với cơ chế thử lại), truyền yêu cầu người dùng vào
    # Giải nén tuple từ kết quả gọi AI Z một cách chính xác
    ai_z_suggestion_text, relevant_files_from_z = _invoke_ai_z_with_retries(user_request)
    
    # 4. Xóa yêu cầu người dùng sau khi đã xử lý bởi AI Z
    if user_request and os.path.exists(USER_REQUEST_FILE):
        try:
            os.remove(USER_REQUEST_FILE)
            logger.info(f"Đã xóa file yêu cầu người dùng: {USER_REQUEST_FILE}")
        except Exception as e:
            logger.error(f"Lỗi khi xóa file yêu cầu người dùng '{USER_REQUEST_FILE}': {e}", exc_info=True)
    
    # 5. Tích hợp đề xuất của AI Z vào bối cảnh cho AI X
    # Quyết định bối cảnh mã nguồn cho AI X
    if ai_z_suggestion_text and relevant_files_from_z:
        # Sử dụng bối cảnh mục tiêu nếu AI Z cung cấp các tệp liên quan và có đề xuất
        source_code_for_ai_x = get_source_code_context(relevant_files=relevant_files_from_z)
        logger.info(f"AI X sẽ làm việc với bối cảnh mục tiêu dựa trên đề xuất của AI Z. Số lượng tệp: {len(relevant_files_from_z)}")
    else:
        # Quay về bối cảnh đầy đủ nếu AI Z không cung cấp tệp cụ thể hoặc có lỗi
        source_code_for_ai_x = get_source_code_context()
        logger.info("AI X sẽ làm việc với bối cảnh mã nguồn đầy đủ (AI Z không đưa ra tệp liên quan cụ thể hoặc có lỗi). ")

    # Thêm văn bản đề xuất của AI Z vào bối cảnh chung cho prompt của AI X
    context_for_ai_x = source_code_for_ai_x
    if ai_z_suggestion_text:
        context_for_ai_x = f"AI Z đã đưa ra đề xuất sau cho bạn: '{ai_z_suggestion_text}'. Hãy xem xét đề xuất này khi bạn đưa ra thay đổi tiếp theo để cải thiện dự án.\n\n{source_code_for_ai_x}"
        logger.info("Đề xuất của AI Z (văn bản) đã được thêm vào bối cảnh cho AI X.")
    else:
        logger.warning("Không nhận được đề xuất văn bản từ AI Z hoặc có lỗi xảy ra.")
    
    # 6. Gọi AI X với bối cảnh đã được cập nhật
    filepath, new_content, description, final_failure_reason = _invoke_ai_with_retries(context_for_ai_x, history_log)

    if filepath and new_content and description:
        status, final_reason = validate_and_commit_changes(filepath, new_content, description)
        log_entry["status"] = status
        log_entry["reason"] = final_reason
    else:
        logger.error(final_failure_reason)
        log_entry["status"] = "NO_PROPOSAL"
        log_entry["reason"] = final_failure_reason
    
    logger.info(f"KẾT THÚC CHU TRÌNH TIẾN HÓA LẦN THỨ {iteration_count} ({log_entry['status']}): {log_entry['reason']}")
        
    return log_entry

# --- CÁC HÀM QUẢN LÝ LỊCH SỬ ---

def _load_history() -> list:
    """Tải lịch sử tiến hóa từ LOG_FILE_PATH."""
    history_log = []
    if os.path.exists(LOG_FILE_PATH):
        try:
            with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
                history_log = json.load(f)
            logger.info(f"Đã tải {len(history_log)} mục từ lịch sử.")
        except json.JSONDecodeError:
            logger.warning(f"File log {LOG_FILE_PATH} bị lỗi hoặc trống, bắt đầu lịch sử mới.")
            history_log = []
    return history_log

def _save_history(history_log: list):
    """Lưu lịch sử tiến hóa vào LOG_FILE_PATH."""
    with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(history_log, f, indent=4, ensure_ascii=False)
    logger.info(f"Đã cập nhật log vào file: {LOG_FILE_PATH}")

# --- LUỒNG CHÍNH VỚI CƠ CHẾ THỬ LẠI (RETRY) ---

def main(max_iterations: int = None):
    """Hàm chính chứa vòng lặp, quản lý lịch sử và cơ chế thử lại.
    Args:
        max_iterations (int, optional): Số chu kỳ tiến hóa tối đa để chạy. 
                                        Nếu None, sẽ chạy vô thời hạn.
    """
    setup()
    
    logger.info(f"Khởi động AI Agent X - Phiên bản: {VERSION}")

    # Start the Flask web server in a separate thread
    web_thread = threading.Thread(target=_run_web_server, daemon=True)
    web_thread.start()
    
    history_log = _load_history()

    iteration_count = len(history_log)

    try:
        while max_iterations is None or iteration_count < max_iterations:
            iteration_count += 1
            logger.info("\n" + "="*50)
            logger.info(f"BẮT ĐẦU CHU TRÌNH TIẾN HÓA LẦN THỨ {iteration_count}")
            logger.info("="*50)
            
            # Gọi hàm trợ giúp mới để thực hiện một bước tiến hóa
            log_entry = _execute_evolution_step(iteration_count, history_log)
            
            history_log.append(log_entry)
            _save_history(history_log)
            
            if INTERACTIVE_MODE:
                logger.info("[CHẾ ĐỘ TƯƠNG TÁC] Đang chờ kích hoạt từ giao diện web...")
                os.makedirs(CONTROL_DIR, exist_ok=True) # Ensure control directory exists
                while not os.path.exists(TRIGGER_NEXT_STEP_FLAG):
                    print(".", end="", flush=True) # Keep print for progress dots (visual feedback)
                    time.sleep(1) # Check every second
                
                # Flag found, clear it and proceed
                os.remove(TRIGGER_NEXT_STEP_FLAG)
                logger.info("Đã nhận tín hiệu kích hoạt từ web. Tiếp tục chu trình.")
            else:
                logger.info(f"Tạm nghỉ {SLEEP_BETWEEN_ITERATIONS_SECONDS} giây...")
                # Hiển thị chỉ báo tiến độ trong thời gian tạm dừng
                for i in range(SLEEP_BETWEEN_ITERATIONS_SECONDS):
                    print(".", end="", flush=True) # Keep print for progress dots (visual feedback)
                    time.sleep(1)
                print() # Xuống dòng sau khi in các dấu chấm - keep print
            
            # Check the condition for exiting loop if max_iterations is set
            if max_iterations is not None and iteration_count >= max_iterations:
                logger.info(f"Đã đạt đến số lần lặp tối đa ({max_iterations}). Dừng.")
                break


    except KeyboardInterrupt:
        logger.critical("Đã nhận tín hiệu dừng.", exc_info=True)
    except Exception as e:
        logger.critical(f"Đã xảy ra lỗi không xác định: {e}", exc_info=True)

if __name__ == "__main__":
    main()
