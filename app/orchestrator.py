# app/orchestrator.py
import os
import subprocess
import json
import time
import py_compile
from dotenv import load_dotenv
import google.generativeai as genai
from ai_agent import invoke_ai_x
from config import LOG_FILE_PATH, EXCLUDE_PATHS, MAX_AI_X_RETRIES, SLEEP_BETWEEN_ITERATIONS_SECONDS, VERSION, INTERACTIVE_MODE
from utils import get_source_code_context
from git_utils import add_and_commit
from ai_z_agent import invoke_ai_z # Thêm import cho AI Z

# Constants for web interaction (will be moved to config.py in future iterations)
CONTROL_DIR = "app/control"
TRIGGER_NEXT_STEP_FLAG = os.path.join(CONTROL_DIR, "trigger_next_step.flag")

# --- CÁC HÀM TIỆN ÍCH VÀ CẤU HÌNH ---

def setup():
    """Tải biến môi trường và cấu hình API Key cho Gemini."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Please set it in the .env file.")
    genai.configure(api_key=api_key);
    print("✅ Đã cấu hình Gemini API Key.")

# --- CÁC HÀM TƯƠNG TÁC VỚI AI VÀ LOG ---

def _invoke_ai_with_retries(context: str, history_log: list) -> tuple[str, str, str, str]:
    """
    Kêu gọi AI X với cơ chế thử lại.
    Trả về một tuple: (filepath, new_content, description, failure_reason)
    """
    filepath, new_content, description, failure_reason = None, None, None, ""
    for attempt in range(MAX_AI_X_RETRIES):
        print(f"  (Lần thử {attempt + 1}/{MAX_AI_X_RETRIES} cho AI X...)")
        filepath, new_content, description, failure_reason = invoke_ai_x(context, history_log)
        if filepath and new_content and description:
            print(f"  AI X đã đưa ra đề xuất thành công ở lần thử {attempt + 1}.")
            return filepath, new_content, description, None # Return None for failure_reason on success
        else:
            print(f"  AI X thất bại lần {attempt + 1}. Lý do: {failure_reason}")
            if attempt < MAX_AI_X_RETRIES - 1:
                time.sleep(5) # Wait before retrying
    
    # If all retries failed
    return None, None, None, f"AI X thất bại sau {MAX_AI_X_RETRIES} lần thử. Lý do cuối cùng: {failure_reason}"

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
            print("✅ [VALIDATOR] Mã nguồn Python mới hợp lệ.")
        else:
            print(f"⚠️ [VALIDATOR] File '{filepath}' không phải file Python, bỏ qua kiểm tra cú pháp.")

        os.replace(temp_filepath, filepath);
        action_verb = "Tạo mới" if is_new_file else "Ghi đè"
        print(f"📝 {action_verb} thành công file: {filepath}")
        return True, ""
        
    except py_compile.PyCompileError as e:
        return False, f"Lỗi cú pháp trong đề xuất file Python mới: {e}"
    except Exception as e:
        return False, f"Lỗi không xác định khi áp dụng file: {e}"
    finally:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)


# --- HÀM THỰC THI KIẾN TRÚC MỚI ---

def validate_and_commit_changes(filepath: str, new_content: str, description: str):
    """
    Kiểm tra cú pháp (nếu là file Python), nếu hợp lệ thì ghi đè/tạo mới và commit.
    Trả về một tuple: (status, final_reason).
    """
    print(f"🚀 [Z] Bắt đầu quá trình thực thi cho file: {filepath}")
    
    success, validation_reason = _apply_and_validate_file_content(filepath, new_content)

    if not success:
        print(f"❌ [VALIDATOR] {validation_reason}")
        return "REJECTED_VALIDATION_FAILED", validation_reason
    
    try:
        commit_message = f"feat(AI): {description}"
        add_and_commit(filepath, commit_message)
        
        return "COMMITTED", description

    except RuntimeError as e:
        # Bắt lỗi từ git_utils.add_and_commit
        error_reason = f"Lỗi khi thực hiện Git commit: {e}"
        print(f"❌ [Z] {error_reason}")
        return "EXECUTION_FAILED", error_reason
    except Exception as e:
        error_reason = f"Lỗi không xác định trong quá trình commit: {e}"
        print(f"❌ [Z] {error_reason}")
        return "EXECUTION_FAILED", error_reason

# --- CÁC BƯỚC TIẾN HÓA CỐT LÕI ---

def _execute_evolution_step(iteration_count: int, history_log: list) -> dict:
    """
    Thực hiện một bước tiến hóa duy nhất (gọi AI, xử lý phản hồi, xác thực và commit).
    Trả về một dictionary log_entry cho bước này.
    """
    log_entry = { "iteration": iteration_count, "status": "", "reason": "" }
    
    # 1. Lấy bối cảnh mã nguồn hiện tại
    source_context = get_source_code_context()
    
    # 2. Gọi AI Z để lấy đề xuất nhiệm vụ
    task_suggestion = invoke_ai_z()
    
    # 3. Tích hợp đề xuất của AI Z vào bối cảnh cho AI X
    context_for_ai_x = source_context
    if task_suggestion:
        # Prepend the AI Z suggestion to the context in a clear format
        # Bọc task_suggestion trong dấu nháy đơn để tránh lỗi cú pháp nếu task_suggestion có dấu nháy kép
        context_for_ai_x = f"AI Z đã đưa ra đề xuất sau cho bạn: '{task_suggestion}'. Hãy xem xét đề xuất này khi bạn đưa ra thay đổi tiếp theo để cải thiện dự án.\n\n{source_context}"
        print(f"🧠 [AI Z] Đề xuất của AI Z đã được thêm vào bối cảnh cho AI X.")
    else:
        print("🧠 [AI Z] Không nhận được đề xuất từ AI Z hoặc có lỗi xảy ra.")
    
    # 4. Gọi AI X với bối cảnh đã được cập nhật
    filepath, new_content, description, final_failure_reason = _invoke_ai_with_retries(context_for_ai_x, history_log)

    if filepath and new_content and description:
        status, final_reason = validate_and_commit_changes(filepath, new_content, description)
        log_entry["status"] = status
        log_entry["reason"] = final_reason
    else:
        print(f"❌ {final_failure_reason}")
        log_entry["status"] = "NO_PROPOSAL"
        log_entry["reason"] = final_failure_reason
        
    return log_entry

# --- LUỒNG CHÍNH VỚI CƠ CHẾ THỬ LẠI (RETRY) ---

def main(max_iterations: int = None):
    """Hàm chính chứa vòng lặp, quản lý lịch sử và cơ chế thử lại.
    Args:
        max_iterations (int, optional): Số chu kỳ tiến hóa tối đa để chạy. 
                                        Nếu None, sẽ chạy vô thời hạn.
    """
    setup()
    
    print(f"🌟 Khởi động AI Agent X - Phiên bản: {VERSION}")
    
    history_log = []
    if os.path.exists(LOG_FILE_PATH):
        try:
            with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
                history_log = json.load(f)
            print(f"📚 Đã tải {len(history_log)} mục từ lịch sử.")
        except json.JSONDecodeError:
            print(f"⚠️ File log {LOG_FILE_PATH} bị lỗi, bắt đầu lịch sử mới.")
            history_log = []

    iteration_count = len(history_log)

    try:
        while max_iterations is None or iteration_count < max_iterations:
            iteration_count += 1
            print("\n" + "="*50)
            print(f"🎬 BẮT ĐẦU CHU TRÌNH TIẾN HÓA LẦN THỨ {iteration_count}")
            print("="*50)
            
            # Gọi hàm trợ giúp mới để thực hiện một bước tiến hóa
            log_entry = _execute_evolution_step(iteration_count, history_log)
            
            history_log.append(log_entry)
            with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(history_log, f, indent=4, ensure_ascii=False)
            print(f"📝 Đã cập nhật log vào file: {LOG_FILE_PATH}")
            
            if INTERACTIVE_MODE:
                print("\n[CHẾ ĐỘ TƯƠNG TÁC] Đang chờ kích hoạt từ giao diện web...")
                os.makedirs(CONTROL_DIR, exist_ok=True) # Ensure control directory exists
                while not os.path.exists(TRIGGER_NEXT_STEP_FLAG):
                    print(".", end="", flush=True)
                    time.sleep(1) # Check every second
                
                # Flag found, clear it and proceed
                os.remove(TRIGGER_NEXT_STEP_FLAG)
                print("\n✅ Đã nhận tín hiệu kích hoạt từ web. Tiếp tục chu trình.")
            else:
                print(f"⏳ Tạm nghỉ {SLEEP_BETWEEN_ITERATIONS_SECONDS} giây...")
                # Hiển thị chỉ báo tiến độ trong thời gian tạm dừng
                for i in range(SLEEP_BETWEEN_ITERATIONS_SECONDS):
                    print(".", end="", flush=True)
                    time.sleep(1)
                print() # Xuống dòng sau khi in các dấu chấm

    except KeyboardInterrupt:
        print("\n\n🛑 Đã nhận tín hiệu dừng.")
    except Exception as e:
        print(f"⛔ Đã xảy ra lỗi không xác định: {e}")

if __name__ == "__main__":
    main()
