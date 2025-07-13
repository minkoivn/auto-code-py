# orchestrator/orchestrator.py
import os
import subprocess
import json
import re
import time
import py_compile
from dotenv import load_dotenv
import google.generativeai as genai

# --- HÀM TIỆN ÍCH MỚI ---
def clean_response_text(text: str) -> str:
    """
    Dọn dẹp văn bản phản hồi từ AI một cách triệt để:
    - Thay thế các ký tự khoảng trắng không chuẩn (non-breaking space).
    - Chuẩn hóa ký tự xuống dòng (loại bỏ \r).
    """
    # \u00A0 là ký tự non-breaking space
    cleaned_text = text.replace("\u00A0", " ")
    # Loại bỏ ký tự carriage return \r để chỉ còn \n
    cleaned_text = cleaned_text.replace("\r", "")
    return cleaned_text

# --- CÁC HÀM TƯƠNG TÁC VỚI AI ĐƯỢC NÂNG CẤP ---

def setup():
    """Tải biến môi trường và cấu hình API Key cho Gemini."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Please set it in the .env file.")
    genai.configure(api_key=api_key)
    print("✅ Đã cấu hình Gemini API Key.")

def get_source_code_context():
    """Đọc toàn bộ mã nguồn của thư mục 'app' để làm bối cảnh."""
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

def invoke_ai_x(context):
    """Gửi toàn bộ mã nguồn đến AI X và nhận về bản vá diff."""
    print("🤖 [AI X] Đang kết nối Gemini và tạo đề xuất...")
    with open("orchestrator/prompts/x_prompt.txt", "r", encoding="utf-8") as f:
        prompt_template = f.read()
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"{prompt_template}\n\n{context}"
    
    try:
        response = model.generate_content(prompt)
        # ÁP DỤNG HÀM DỌN DẸP
        text = clean_response_text(response.text)
        
        print("\n" + "-"*20 + " PHẢN HỒI THÔ TỪ GEMINI (AI X) " + "-"*20)
        print(text)
        print("-"*(42 + len(" PHẢN HỒI THÔ TỪ GEMINI (AI X) ")) + "\n")

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

def invoke_ai_y(diff):
    """Gửi bản vá diff đến AI Y để kiểm duyệt."""
    print("🧐 [AI Y] Đang kết nối Gemini và kiểm duyệt thay đổi...")
    with open("orchestrator/prompts/y_prompt.txt", "r", encoding="utf-8") as f:
        prompt_template = f.read()

    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"{prompt_template}\n\n{diff}"

    try:
        response = model.generate_content(prompt)
        # ÁP DỤNG HÀM DỌN DẸP
        text = clean_response_text(response.text)

        print("\n" + "-"*20 + " PHẢN HỒI THÔ TỪ GEMINI (AI Y) " + "-"*20)
        print(text)
        print("-"*(42 + len(" PHẢN HỒI THÔ TỪ GEMINI (AI Y) ")) + "\n")

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

# --- CÁC HÀM VALIDATE, ROLLBACK, COMMIT ĐƯỢC CẬP NHẬT ---

def validate_changes():
    """Kiểm tra xem mã nguồn trong thư mục 'app' có lỗi cú pháp không."""
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
    """Sử dụng Git để hủy bỏ tất cả các thay đổi chưa được commit."""
    print("🔙 [ROLLBACK] Phát hiện lỗi! Đang khôi phục phiên bản ổn định trước đó...")
    try:
        subprocess.run(["git", "reset", "--hard", "HEAD"], check=True, capture_output=True)
        print("🔙 [ROLLBACK] Khôi phục thành công.")
    except subprocess.CalledProcessError as e:
        # Cập nhật xử lý lỗi ở đây
        error_message = e.stderr.decode() if e.stderr else "Không có thông tin lỗi stderr."
        print(f"❌ Lỗi nghiêm trọng khi đang rollback: {error_message}")

def apply_and_commit_changes(diff, reason):
    """Áp dụng bản vá, kiểm tra lỗi, và commit nếu hợp lệ."""
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
        else:
            rollback_changes()

    except subprocess.CalledProcessError as e:
        print("❌ Lỗi khi áp dụng bản vá. Có thể do xung đột (conflict). Tiến hành rollback.")
        # Cập nhật xử lý lỗi ở đây
        error_message = e.stderr.decode() if e.stderr else "Không có thông tin lỗi stderr."
        print(f"   Chi tiết lỗi: {error_message}")
        rollback_changes()
    finally:
        if os.path.exists(patch_file):
            os.remove(patch_file)

# --- LUỒNG CHÍNH (KHÔNG ĐỔI) ---

def main():
    """Hàm chính chứa vòng lặp vô tận để hệ thống tự tiến hóa."""
    setup()
    iteration_count = 0
    try:
        while True:
            iteration_count += 1
            print("\n" + "="*50)
            print(f"🎬 BẮT ĐẦU CHU TRÌNH TIẾN HÓA LẦN THỨ {iteration_count}")
            print("="*50)
            
            source_context = get_source_code_context()
            proposed_diff = invoke_ai_x(source_context)
            
            if proposed_diff:
                review = invoke_ai_y(proposed_diff)
                
                if review and review.get("decision") == "approved":
                    apply_and_commit_changes(proposed_diff, review.get("reason"))
                else:
                    reason = review.get('reason', 'No reason provided.')
                    print(f"❌ Thay đổi đã bị từ chối bởi AI Y. Lý do: {reason}")
            else:
                print("❌ AI X không tạo ra đề xuất nào trong lần này.")
            
            print(f"⏳ Tạm nghỉ 15 giây trước khi bắt đầu chu trình tiếp theo...")
            time.sleep(15)

    except KeyboardInterrupt:
        print("\n\n🛑 Đã nhận tín hiệu dừng. Kết thúc chương trình.")
    except Exception as e:
        print(f"⛔ Đã xảy ra lỗi không xác định: {e}")

if __name__ == "__main__":
    main()