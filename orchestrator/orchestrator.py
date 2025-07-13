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
    Yêu cầu AI X trả về toàn bộ nội dung file mới.
    Trả về một tuple: (filepath, new_content, failure_reason)
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
        match = re.search(r'<new_code filepath="([^"]+)">\s*(.*?)\s*</new_code>', text, re.DOTALL)
        
        if match:
            filepath = match.group(1).strip()
            new_content = match.group(2).strip()
            
            if not os.path.exists(filepath):
                return None, None, f"AI đề xuất sửa file không tồn tại: {filepath}"
            
            # Kiểm tra xem có thay đổi thực sự không
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()
            if original_content == new_content:
                return None, None, "Nội dung AI đề xuất giống hệt file gốc."

            print("🤖 [AI X] Đã nhận được đề xuất nội dung file mới.")
            return filepath, new_content, None
        else:
            return None, None, "AI không trả về nội dung theo định dạng <new_code>..."

    except Exception as e:
        print(f"❌ Lỗi khi gọi Gemini API cho AI X: {e}")
        return None, None, str(e)


# --- HÀM THỰC THI KIẾN TRÚC MỚI ---

def validate_and_commit_changes(filepath: str, new_content: str):
    """
    Kiểm tra cú pháp của nội dung mới, nếu hợp lệ thì ghi đè và commit.
    Trả về một tuple (status, final_reason).
    """
    print(f"🚀 [Z] Bắt đầu quá trình thực thi cho file: {filepath}")
    temp_filepath = filepath + ".tmp"
    try:
        # 1. Ghi nội dung mới vào file tạm để kiểm tra
        with open(temp_filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        # 2. Kiểm tra cú pháp trên file tạm
        py_compile.compile(temp_filepath, doraise=True)
        print("✅ [VALIDATOR] Mã nguồn mới hợp lệ.")

        # 3. Ghi đè file gốc và commit
        os.replace(temp_filepath, filepath)
        print(f"📝 Đã ghi đè thành công file: {filepath}")
        
        subprocess.run(["git", "add", filepath], check=True)
        commit_message = f"feat(AI): Tự động cải tiến file {os.path.basename(filepath)}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        print(f"🚀 [Z] Đã tạo commit mới: '{commit_message}'")
        
        return "COMMITTED", commit_message

    except py_compile.PyCompileError as e:
        # Nếu lỗi cú pháp, chỉ cần xóa file tạm
        error_reason = f"Lỗi cú pháp trong đề xuất mới: {e}"
        print(f"❌ [VALIDATOR] {error_reason}")
        return "REJECTED_VALIDATION_FAILED", error_reason
    except Exception as e:
        # Xử lý các lỗi khác
        error_reason = f"Lỗi không xác định trong quá trình thực thi: {e}"
        print(f"❌ [Z] {error_reason}")
        return "EXECUTION_FAILED", error_reason
    finally:
        # Luôn đảm bảo file tạm được xóa
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)


# --- LUỒNG CHÍNH ĐƯỢC ĐƠN GIẢN HÓA ---

def main():
    """Hàm chính chứa vòng lặp và quản lý lịch sử bền vững."""
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
            filepath, new_content, failure_reason = invoke_ai_x(source_context, history_log)
            
            if filepath and new_content:
                # Với kiến trúc mới, chúng ta không cần AI Y nữa.
                # Việc kiểm tra cú pháp đã là một "người kiểm duyệt" máy móc hiệu quả.
                status, final_reason = validate_and_commit_changes(filepath, new_content)
                log_entry["status"] = status
                log_entry["reason"] = final_reason
            else:
                print(f"❌ AI X không tạo ra đề xuất hợp lệ. Lý do: {failure_reason}")
                log_entry["status"] = "NO_PROPOSAL"
                log_entry["reason"] = failure_reason
            
            # Cập nhật lịch sử trong bộ nhớ và ghi ra tệp
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