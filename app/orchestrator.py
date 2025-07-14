# app/orchestrator.py
import os
import subprocess
import json
import time
import py_compile
from dotenv import load_dotenv
import google.generativeai as genai
from ai_agent import invoke_ai_x
from config import LOG_FILE_PATH, EXCLUDE_PATHS, MAX_AI_X_RETRIES, SLEEP_BETWEEN_ITERATIONS_SECONDS
from utils import get_source_code_context
from git_utils import add_and_commit

# --- CÁC HÀM TIỆN ÍCH VÀ CẤU HÌNH ---

def setup():
    """Tải biến môi trường và cấu hình API Key cho Gemini."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Please set it in the .env file.")
    genai.configure(api_key=api_key)
    print("✅ Đã cấu hình Gemini API Key.")

# Hàm get_source_code_context đã được chuyển sang app/utils.py và được nhập ở trên.

# --- CÁC HÀM TƯƠNG TÁC VỚI AI VÀ LOG ---

# Các hàm format_history_for_prompt và invoke_ai_x đã được chuyển sang app/ai_agent.py

# --- HÀM THỰC THI KIẾN TRÚC MỚI ---

def validate_and_commit_changes(filepath: str, new_content: str, description: str):
    """
    Kiểm tra cú pháp, nếu hợp lệ thì ghi đè/tạo mới và commit.
    Trả về một tuple: (status, final_reason).
    """
    print(f"🚀 [Z] Bắt đầu quá trình thực thi cho file: {filepath}")
    temp_filepath = filepath + ".tmp"
    is_new_file = not os.path.exists(filepath)
    
    try:
        # Đảm bảo thư mục cho file mới tồn tại
        dir_name = os.path.dirname(filepath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        with open(temp_filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        py_compile.compile(temp_filepath, doraise=True)
        print("✅ [VALIDATOR] Mã nguồn mới hợp lệ.")

        os.replace(temp_filepath, filepath);
        action_verb = "Tạo mới" if is_new_file else "Ghi đè"
        print(f"📝 {action_verb} thành công file: {filepath}")
        
        # Sử dụng hàm add_and_commit từ git_utils thay vì gọi subprocess trực tiếp
        commit_message = f"feat(AI): {description}"
        add_and_commit(filepath, commit_message)
        
        return "COMMITTED", description

    except py_compile.PyCompileError as e:
        error_reason = f"Lỗi cú pháp trong đề xuất mới: {e}"
        print(f"❌ [VALIDATOR] {error_reason}")
        return "REJECTED_VALIDATION_FAILED", error_reason
    except Exception as e:
        error_reason = f"Lỗi không xác định trong quá trình thực thi: {e}"
        print(f"❌ [Z] {error_reason}")
        return "EXECUTION_FAILED", error_reason
    finally:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)


# --- LUỒNG CHÍNH VỚI CƠ CHẾ THỬ LẠI (RETRY) ---

def main():
    """Hàm chính chứa vòng lặp, quản lý lịch sử và cơ chế thử lại."""
    setup()
    
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
        while True:
            iteration_count += 1
            print("\n" + "="*50)
            print(f"🎬 BẮT ĐẦU CHU TRÌNH TIẾN HÓA LẦN THỨ {iteration_count}")
            print("="*50)
            
            log_entry = { "iteration": iteration_count, "status": "", "reason": "" }
            source_context = get_source_code_context()
            
            filepath, new_content, description, failure_reason = None, None, None, ""
            for attempt in range(MAX_AI_X_RETRIES):
                print(f"  (Lần thử {attempt + 1}/{MAX_AI_X_RETRIES} cho AI X...)")
                filepath, new_content, description, failure_reason = invoke_ai_x(source_context, history_log)
                if filepath and new_content and description:
                    break 
                else:
                    print(f"  AI X thất bại lần {attempt + 1}. Lý do: {failure_reason}")
                    if attempt < MAX_AI_X_RETRIES - 1:
                        time.sleep(5)

            if filepath and new_content and description:
                status, final_reason = validate_and_commit_changes(filepath, new_content, description)
                log_entry["status"] = status
                log_entry["reason"] = final_reason
            else:
                final_failure_reason = f"AI X thất bại sau {MAX_AI_X_RETRIES} lần thử. Lý do cuối cùng: {failure_reason}"
                print(f"❌ {final_failure_reason}")
                log_entry["status"] = "NO_PROPOSAL"
                log_entry["reason"] = final_failure_reason
            
            history_log.append(log_entry)
            with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(history_log, f, indent=4, ensure_ascii=False)
            print(f"📝 Đã cập nhật log vào file: {LOG_FILE_PATH}")
            
            print(f"⏳ Tạm nghỉ {SLEEP_BETWEEN_ITERATIONS_SECONDS} giây...")
            time.sleep(SLEEP_BETWEEN_ITERATIONS_SECONDS)

    except KeyboardInterrupt:
        print("\n\n🛑 Đã nhận tín hiệu dừng.")
    except Exception as e:
        print(f"⛔ Đã xảy ra lỗi không xác định: {e}")

if __name__ == "__main__":
    main()
