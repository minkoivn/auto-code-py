# orchestrator/orchestrator.py
import os
import subprocess
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai

# --- CÁC HÀM TƯƠNG TÁC VỚI AI THẬT ---

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
    
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    prompt = f"{prompt_template}\n\n{context}"
    
    try:
        response = model.generate_content(prompt)
        # Trích xuất nội dung diff một cách an toàn
        diff_match = re.search(r'diff --git.*', response.text, re.DOTALL)
        if diff_match:
            print("🤖 [AI X] Đã nhận được đề xuất hợp lệ.")
            return diff_match.group(0)
        else:
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

    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    prompt = f"{prompt_template}\n\n{diff}"

    try:
        response = model.generate_content(prompt)
        # Trích xuất nội dung JSON từ phản hồi
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            print("🧐 [AI Y] Đã nhận được đánh giá.")
            return json.loads(json_match.group(0))
        else:
            print("🧐 [AI Y] Phản hồi không chứa định dạng JSON hợp lệ.")
            return {"decision": "rejected", "reason": "Invalid response format from reviewer AI."}
    except Exception as e:
        print(f"❌ Lỗi khi gọi Gemini API cho AI Y: {e}")
        return {"decision": "rejected", "reason": f"API call failed: {e}"}

# --- HÀM THỰC THI (KHÔNG ĐỔI) ---

def execute_z_commit_and_push(diff, reason):
    """Áp dụng bản vá và commit thay đổi."""
    print("🚀 [Z] Bắt đầu quá trình thực thi...")
    patch_file = "change.patch"
    with open(patch_file, "w", encoding="utf-8") as f:
        f.write(diff)

    try:
        subprocess.run(["git", "apply", patch_file], check=True, capture_output=True)
        print("🚀 [Z] Áp dụng bản vá thành công.")

        # `git add .` để tự động thêm các file đã thay đổi
        subprocess.run(["git", "add", "."], check=True)

        commit_message = f"feat(AI): {reason}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        print(f"🚀 [Z] Đã tạo commit mới với thông điệp: '{commit_message}'")

    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi thực thi Git: {e.stderr.decode()}")
    finally:
        if os.path.exists(patch_file):
            os.remove(patch_file)

# --- LUỒNG CHÍNH ---

def main():
    print("--- BẮT ĐẦU CHU TRÌNH TIẾN HÓA VỚI AI THẬT ---")
    
    try:
        setup()
        
        # 1. Lấy bối cảnh mã nguồn
        source_context = get_source_code_context()
        
        # 2. AI X tạo đề xuất
        proposed_diff = invoke_ai_x(source_context)
        
        # 3. AI Y kiểm duyệt
        if proposed_diff:
            review = invoke_ai_y(proposed_diff)
            
            # 4. Z thực thi nếu được chấp thuận
            if review and review.get("decision") == "approved":
                execute_z_commit_and_push(proposed_diff, review.get("reason"))
            else:
                reason = review.get('reason', 'No reason provided.')
                print(f"❌ Thay đổi đã bị từ chối. Lý do: {reason}")
        else:
            print("❌ Không có đề xuất nào được tạo.")
            
    except Exception as e:
        print(f"⛔ Đã xảy ra lỗi nghiêm trọng trong luồng chính: {e}")

    print("--- KẾT THÚC CHU TRÌNH ---")


if __name__ == "__main__":
    main()