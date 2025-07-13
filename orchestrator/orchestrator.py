# orchestrator/orchestrator.py
import os
import subprocess
import json
import re
import time
import py_compile
from dotenv import load_dotenv
import google.generativeai as genai

# --- CÁC HÀM TIỆN ÍCH ---

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

# --- CÁC HÀM TƯƠNG TÁC VỚI AI ĐƯỢC NÂNG CẤP VỚI LOG ---

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
    """Gửi mã nguồn VÀ LỊCH SỬ đến AI X."""
    print("🤖 [AI X] Đang kết nối Gemini, đọc lịch sử và tạo đề xuất...")
    with open("orchestrator/prompts/x_prompt.txt", "r", encoding="utf-8") as f:
        prompt_template = f.read()
    
    # Định dạng lịch sử và điền vào prompt
    history_context = format_history_for_prompt(history_log)
    prompt_filled_history = prompt_template.replace("{history_context}", history_context)

    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"{prompt_filled_history}\n\n{context}"
    
    try:
        response = model.generate_content(prompt)
        text = clean_response_text(response.text)
        
        diff_match = re.search(r'```(?:diff)?\s*(diff --git.*)```', text, re.DOTALL)
        if diff_match:
            print("🤖 [AI X] Đã trích xuất diff từ khối markdown.")
            return diff_match.group(1).strip()

        diff_match = re.search(r'diff --git.*', text, re.DOTALL)
        if diff_match:
            print("🤖 [AI X] Đã nhận được đề xuất diff thuần túy.")
            return diff_match.group(0).strip()
            
        print("🤖 [AI X] Phản hồi không chứa định dạng diff hợp lệ.")
        return None
        
    except Exception as e:
        print(f"❌ Lỗi khi gọi Gemini API cho AI X: {e}")
        return None

def invoke_ai_y(diff: str):
    """Hàm này không cần lịch sử, giữ nguyên."""
    print("🧐 [AI Y] Đang kết nối Gemini và kiểm duyệt thay đổi...")
    # ... (giữ nguyên code của hàm invoke_ai_y)
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
        else:
            print("🧐 [AI Y] Phản hồi không chứa định dạng JSON hợp lệ.")
            return {"decision": "rejected", "reason": "Invalid response format from reviewer AI."}
    except Exception as e:
        print(f"❌ Lỗi khi gọi Gemini API cho AI Y: {e}")
        return {"decision": "rejected", "reason": f"API call failed: {e}"}


# --- CÁC HÀM VALIDATE, ROLLBACK, COMMIT (KHÔNG ĐỔI) ---

def validate_changes():
    # ... (giữ nguyên code của hàm validate_changes)
    print("🔍 [VALIDATOR] Đang kiểm tra tính hợp lệ của mã nguồn mới...")
    for root, _, files in os.walk("app"):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    py_compile.compile(filepath, doraise=True)
                except py_compile.PyCompileError as e:
                    print(f"❌ LỖI CÚ PHÁP NGHIÊM TRỌNG trong file {filepath}: {e}")
                    return False
    print("✅ [VALIDATOR] Mã nguồn hợp lệ.")
    return True

def rollback_changes():
    # ... (giữ nguyên code của hàm rollback_changes)
    print("🔙 [ROLLBACK] Phát hiện lỗi! Đang khôi phục phiên bản ổn định trước đó...")
    try:
        subprocess.run(["git", "reset", "--hard", "HEAD"], check=True, capture_output=True)
        print("🔙 [ROLLBACK] Khôi phục thành công.")
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode() if e.stderr else "Không có thông tin lỗi stderr."
        print(f"❌ Lỗi nghiêm trọng khi đang rollback: {error_message}")


def apply_and_commit_changes(diff, reason):
    """
    Hàm này giờ sẽ trả về trạng thái cuối cùng ('COMMITTED' hoặc 'ROLLBACK').
    """
    print("🚀 [Z] Bắt đầu quá trình thực thi...")
    patch_file = "change.patch"
    with open(patch_file, "w", encoding="utf-8") as f:
        f.write(diff)

    try:
        subprocess.run(["git", "apply", "--reject", "--whitespace=fix", patch_file], check=True)
        print("🚀 [Z] Tạm thời áp dụng bản vá.")

        if validate_changes():
            print("🚀 [Z] Thay đổi an toàn. Tiến hành commit...")
            subprocess.run(["git", "add", "."], check=True)
            commit_message = f"feat(AI): {reason}"
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            print(f"🚀 [Z] Đã tạo commit mới: '{commit_message}'")
            return "COMMITTED"
        else:
            rollback_changes()
            return "ROLLBACK"

    except subprocess.CalledProcessError as e:
        print("❌ Lỗi khi áp dụng bản vá. Có thể do xung đột (conflict). Tiến hành rollback.")
        error_message = e.stderr.decode() if e.stderr else "Không có thông tin lỗi stderr."
        print(f"   Chi tiết lỗi: {error_message}")
        rollback_changes()
        return "ROLLBACK"
    finally:
        if os.path.exists(patch_file):
            os.remove(patch_file)

# --- LUỒNG CHÍNH VỚI TÍNH NĂNG GHI LOG ---

def main():
    """Hàm chính chứa vòng lặp và quản lý lịch sử."""
    setup()
    iteration_count = 0
    history_log = [] # <<< KHỞI TẠO DANH SÁCH LỊCH SỬ

    try:
        while True:
            iteration_count += 1
            print("\n" + "="*50)
            print(f"🎬 BẮT ĐẦU CHU TRÌNH TIẾN HÓA LẦN THỨ {iteration_count}")
            print("="*50)
            
            log_entry = { "iteration": iteration_count, "status": "", "reason": "" }

            source_context = get_source_code_context()
            # Đưa lịch sử vào lời gọi AI X
            proposed_diff = invoke_ai_x(source_context, history_log) 
            
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
                print("❌ AI X không tạo ra đề xuất nào trong lần này.")
                log_entry["status"] = "NO_PROPOSAL"
                log_entry["reason"] = "AI X did not return a valid diff."
            
            # GHI LẠI LOG VÀO CUỐI MỖI CHU TRÌNH
            history_log.append(log_entry)
            
            print(f"⏳ Tạm nghỉ 15 giây trước khi bắt đầu chu trình tiếp theo...")
            time.sleep(15)

    except KeyboardInterrupt:
        print("\n\n🛑 Đã nhận tín hiệu dừng. Kết thúc chương trình.")
    except Exception as e:
        print(f"⛔ Đã xảy ra lỗi không xác định: {e}")

if __name__ == "__main__":
    main()