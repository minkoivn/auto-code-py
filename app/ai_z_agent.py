# app/ai_z_agent.py

import os
import google.generativeai as genai

# Đường dẫn đến prompt của AI Z và tên model AI.
# Lưu ý: Trong các bản cập nhật sau, các giá trị này có thể được chuyển vào config.py.
_Z_PROMPT_FILE_PATH = "app/prompts/z_prompt.txt"
_AI_MODEL_NAME = "gemini-2.5-flash" # Sử dụng cùng model với AI X để nhất quán

def invoke_ai_z():
    """
    Yêu cầu AI Z đề xuất một nhiệm vụ hoặc vấn đề nhỏ cho AI X.
    Trả về chuỗi mô tả nhiệm vụ được đề xuất hoặc None nếu có lỗi.
    """
    print("🧠 [AI Z] Đang kết nối Gemini, đọc prompt và tạo đề xuất nhiệm vụ...")
    try:
        if not os.path.exists(_Z_PROMPT_FILE_PATH):
            raise FileNotFoundError(f"File prompt cho AI Z không tìm thấy: {_Z_PROMPT_FILE_PATH}")

        with open(_Z_PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
            prompt = f.read()

        model = genai.GenerativeModel(_AI_MODEL_NAME)
        response = model.generate_content(prompt)
        
        task_suggestion = response.text.strip()
        print(f"🧠 [AI Z] Đã nhận được đề xuất nhiệm vụ: '{task_suggestion[:100]}...' [Tiếp theo: xem full đề xuất]")
        return task_suggestion
        
    except FileNotFoundError as e:
        print(f"❌ Lỗi: {e}")
        return None
    except Exception as e:
        print(f"❌ Lỗi khi gọi Gemini API cho AI Z: {e}")
        return None
