# orchestrator/orchestrator.py
import os
import subprocess
import json
import re
import time
import py_compile
from dotenv import load_dotenv
import google.generativeai as genai

# --- CÁC HÀM TIỆN ÍCH VÀ CẤU HÌNH ---

LOG_FILE_PATH = "orchestrator/evolution_log.json"

def setup():
    """Tải biến môi trường và cấu hình API Key cho Gemini."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Please set it in the .env file.")
    genai.configure(api_key=api_key)
    print("✅ Đã cấu hình Gemini API Key.")

def get_source_code_context():
    """Đọc mã nguồn thư mục 'app' để làm bối cảnh."""
    context = ""
    for root, _, files in os.walk("app"):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                context += f"--- File: {filepath} ---\n"
                with open(filepath, "r", encoding="utf-8") as f:
                    context += f.read()
                context += "\n\n"
    return context

# --- CÁC HÀM TƯƠNG TÁC VỚI AI VÀ LOG ---

def format_history_for_prompt(history_log: list, num_entries=10) -> str:
    """Định dạng các mục log gần đây nhất để đưa vào prompt."""
    if not history_log:
        return "Chưa có lịch sử."
    
    recent_history = history_log[-num_entries:]
    formatted_history = ""
    for entry in recent_history:
        formatted_history += f"- Lần {entry['iteration']}: Trạng thái = {entry['status']}. Lý do = {entry['reason']}\n"
    return formatted_history

def invoke_ai_x(context: str, history_log: list):
    """
    Yêu cầu AI X trả về một đối tượng JSON chứa nội dung file mới và mô tả.
    Trả về một tuple: (filepath, new_content, description, failure_reason)
    """
    print("🤖 [AI X] Đang kết nối Gemini, đọc lịch sử và tạo đề xuất file mới...")
    with open("orchestrator/prompts/x_prompt.txt", "r", encoding="utf-8") as f:
        prompt_template = f.read()
    
    history_context = format_history_for_prompt(history_log)
    prompt_filled_history = prompt_template.replace("{history_context}", history_context)
    prompt = f"{prompt_filled_history}\n\n{context}"
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("\u00A0", " ").replace("\r", "")
        
        # Cập nhật regex để tìm khối JSON
        match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if not match:
            match = re.search(r'(\{.*?\})', text, re.DOTALL)

        if match:
            json_string = match.group(1)
            try:
                data = json.loads(json_string)
                filepath = data.get("filepath")
                new_content = data.get("new_code")
                description = data.get("description")

                if not all([filepath, new_content, description]):
                    return None, None, None, "JSON trả về thiếu các trường bắt buộc (filepath, new_code, description)."

                # Nếu là file đã tồn tại, kiểm tra xem có thay đổi không
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        original_content = f.read()
                    if original_content == new_content:
                        return None, None, None, "Nội dung AI đề xuất giống hệt file gốc."

                print("🤖 [AI X] Đã nhận được đề xuất JSON hợp lệ.")
                return filepath, new_content, description, None
            except json.JSONDecodeError:
                return None, None, None, "AI trả về chuỗi không phải là JSON hợp lệ."
        else:
            return None, None, None, "AI không trả về nội dung theo định dạng JSON..."

    except Exception as e:
        print(f"❌ Lỗi khi gọi Gemini API cho AI X: {e}")
        return None, None, None, str(e)


# --- HÀM THỰC THI KIẾN TRÚC MỚI ---

def validate_and_commit_changes(filepath: str, new_content: str, description: str):
    """
    Kiểm tra cú pháp, nếu hợp lệ thì ghi đè/tạo mới và commit.
    Trả về một tuple (status, final_reason).
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

        os.replace(temp_filepath, filepath)
        action_verb = "Tạo mới" if is_new_file else "Ghi đè"
        print(f"📝 {action_verb} thành công file: {filepath}")
        
        subprocess.run(["git", "add", filepath], check=True)
        commit_message = f"feat(AI): {description}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        print(f"🚀 [Z] Đã tạo commit mới: '{commit_message}'")
        
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
    
    MAX_AI_X_RETRIES = 3

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
            
            print(f"⏳ Tạm nghỉ 15 giây...")
            time.sleep(15)

    except KeyboardInterrupt:
        print("\n\n🛑 Đã nhận tín hiệu dừng.")
    except Exception as e:
        print(f"⛔ Đã xảy ra lỗi không xác định: {e}")

if __name__ == "__main__":
    main()
