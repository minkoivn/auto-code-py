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

def clean_response_text(text: str) -> str:
    """Dọn dẹp văn bản phản hồi từ AI."""
    cleaned_text = text.replace("\u00A0", " ")
    cleaned_text = cleaned_text.replace("\r", "")
    return cleaned_text

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

def generate_diff_from_new_content(filepath: str, new_content: str):
    """
    So sánh nội dung mới với file gốc và tạo ra một bản vá diff đáng tin cậy.
    """
    print(f"⚙️ [DIFF GENERATOR] Đang tạo diff cho file: {filepath}")
    temp_filepath = filepath + ".new"
    try:
        with open(temp_filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        result = subprocess.run(
            ["git", "diff", "--no-index", "--", filepath, temp_filepath],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        return result.stdout
    finally:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

# --- CÁC HÀM TƯƠNG TÁC VỚI AI ---

def format_history_for_prompt(history_log: list, num_entries=5) -> str:
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
    Yêu cầu AI X trả về toàn bộ nội dung file mới, sau đó tự tạo diff.
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
        text = clean_response_text(response.text)
        match = re.search(r'<new_code filepath="([^"]+)">\s*(.*?)\s*</new_code>', text, re.DOTALL)
        
        if match:
            filepath = match.group(1).strip()
            new_content = match.group(2).strip()
            
            if not os.path.exists(filepath):
                return None, f"AI đề xuất sửa file không tồn tại: {filepath}"

            diff = generate_diff_from_new_content(filepath, new_content)
            if diff:
                print("🤖 [AI X] Đã tạo diff thành công từ nội dung file mới.")
                return diff, None
            else:
                 return None, "Nội dung AI đề xuất giống hệt file gốc."
        else:
            return None, "AI không trả về nội dung theo định dạng <new_code>..."

    except Exception as e:
        print(f"❌ Lỗi khi gọi Gemini API cho AI X: {e}")
        return None, str(e)

def invoke_ai_y(diff: str):
    """Hàm này không cần lịch sử, giữ nguyên."""
    print("🧐 [AI Y] Đang kết nối Gemini và kiểm duyệt thay đổi...")
    with open("orchestrator/prompts/y_prompt.txt", "r", encoding="utf-8") as f:
        prompt_template = f.read()
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"{prompt_template}\n\n{diff}"
    try:
        response = model.generate_content(prompt)
        text = clean_response_text(response.text)
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            print("🧐 [AI Y] Đã nhận được đánh giá.")
            return json.loads(json_match.group(0))
    except Exception as e:
        print(f"❌ Lỗi khi gọi Gemini API cho AI Y: {e}")
    return {"decision": "rejected", "reason": "Lỗi xử lý hoặc API."}

# --- CÁC HÀM VALIDATE, ROLLBACK, COMMIT ---

def validate_changes():
    print("🔍 [VALIDATOR] Đang kiểm tra tính hợp lệ của mã nguồn mới...")
    for root, _, files in os.walk("app"):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    py_compile.compile(filepath, doraise=True)
                except py_compile.PyCompileError as e:
                    print(f"❌ LỖI CÚ PHÁP trong file {filepath}: {e}")
                    return False
    print("✅ [VALIDATOR] Mã nguồn hợp lệ.")
    return True

def rollback_changes():
    print("🔙 [ROLLBACK] Phát hiện lỗi! Đang khôi phục phiên bản ổn định...")
    try:
        subprocess.run(["git", "reset", "--hard", "HEAD"], check=True, capture_output=True)
        print("🔙 [ROLLBACK] Khôi phục thành công.")
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode() if e.stderr else "Lỗi không xác định."
        print(f"❌ Lỗi khi rollback: {error_message}")

def apply_and_commit_changes(diff, reason):
    print("🚀 [Z] Bắt đầu quá trình thực thi...")
    patch_file = "change.patch"
    with open(patch_file, "w", encoding="utf-8") as f:
        f.write(diff)
    try:
        subprocess.run(["git", "apply", "--check", patch_file], check=True)
        subprocess.run(["git", "apply", patch_file], check=True)
        print("🚀 [Z] Áp dụng bản vá thành công.")
        if validate_changes():
            print("🚀 [Z] Thay đổi an toàn. Tiến hành commit...")
            subprocess.run(["git", "add", "."], check=True)
            commit_message = f"feat(AI): {reason}"
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            print(f"🚀 [Z] Đã tạo commit mới: '{commit_message}'")
            return "COMMITTED"
        else:
            rollback_changes()
            return "ROLLBACK_VALIDATION_FAILED"
    except subprocess.CalledProcessError as e:
        print("❌ Lỗi khi áp dụng bản vá.")
        error_message = e.stderr.decode() if e.stderr else "Lỗi không xác định."
        print(f"   Chi tiết lỗi: {error_message}")
        rollback_changes()
        return "ROLLBACK_APPLY_FAILED"
    finally:
        if os.path.exists(patch_file):
            os.remove(patch_file)

# --- LUỒNG CHÍNH VỚI TÍNH NĂNG GHI LOG VÀO TỆP ---

def main():
    """Hàm chính chứa vòng lặp và quản lý lịch sử bền vững."""
    setup()
    
    # Tải lịch sử từ file log nếu có
    history_log = []
    if os.path.exists(LOG_FILE_PATH):
        try:
            with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
                history_log = json.load(f)
            print(f"📚 Đã tải {len(history_log)} mục từ lịch sử.")
        except json.JSONDecodeError:
            print(f"⚠️ File log {LOG_FILE_PATH} bị lỗi, bắt đầu lịch sử mới.")
            history_log = []

    # Bắt đầu đếm từ lần lặp cuối cùng trong log
    iteration_count = len(history_log)

    try:
        while True:
            iteration_count += 1
            print("\n" + "="*50)
            print(f"🎬 BẮT ĐẦU CHU TRÌNH TIẾN HÓA LẦN THỨ {iteration_count}")
            print("="*50)
            
            log_entry = { "iteration": iteration_count, "status": "", "reason": "" }
            source_context = get_source_code_context()
            proposed_diff, failure_reason = invoke_ai_x(source_context, history_log)
            
            if proposed_diff:
                review = invoke_ai_y(proposed_diff)
                if review and review.get("decision") == "approved":
                    reason = review.get('reason', 'AI Y approved.')
                    status = apply_and_commit_changes(proposed_diff, reason)
                    log_entry["status"] = status
                    log_entry["reason"] = reason
                else:
                    reason = review.get('reason', 'No reason provided.')
                    print(f"❌ Thay đổi đã bị từ chối bởi AI Y. Lý do: {reason}")
                    log_entry["status"] = "REJECTED"
                    log_entry["reason"] = reason
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