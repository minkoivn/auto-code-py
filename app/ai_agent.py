import os
import json
import re
import google.generativeai as genai

PROMPT_FILE_PATH = "app/prompts/x_prompt.txt"

def _format_history_for_prompt(history_log: list, num_entries=10) -> str:
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
    with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
        prompt_template = f.read()
    
    history_context = _format_history_for_prompt(history_log)
    prompt_filled_history = prompt_template.replace("{history_context}", history_context)
    prompt = f"{prompt_filled_history}\n\n{context}"
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("\u00A0", " ").replace("\r", "")
        
        # Cập nhật regex để tìm khối JSON
        match = re.search(r'```json\s*({.*?})\s*```', text, re.DOTALL)
        if not match:
            match = re.search(r'({.*?})', text, re.DOTALL)

        if match:
            json_string = match.group(1)
            try:
                data = json.loads(json_string)
                filepath =  data.get("filepath")
                # Đảm bảo filepath bắt đầu bằng 'app/' nếu chưa có
                if filepath and not filepath.startswith("app/"):
                    filepath = "app/" + filepath
                    
                new_content = data.get("new_code")
                description = data.get("description")

                if not all([filepath, new_content, description]):
                    return None, None, None, "JSON trả về thiếu các trường bắt buộc (filepath, new_code, description)."

                print("🤖 [AI X] Đã nhận được đề xuất JSON hợp lệ.")
                return filepath, new_content, description, None
            except json.JSONDecodeError:
                return None, None, None, "AI trả về chuỗi không phải là JSON hợp lệ."
        else:
            return None, None, None, "AI không trả về nội dung theo định dạng JSON..."

    except Exception as e:
        print(f"❌ Lỗi khi gọi Gemini API cho AI X: {e}")
        return None, None, None, str(e)
