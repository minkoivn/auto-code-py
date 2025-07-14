# app/ai_agent.py (Đã nâng cấp để có AI Lập kế hoạch)
import os
import logging
import json
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# ... (phần code logging và load API key giữ nguyên) ...
logging.basicConfig(level=logging.INFO, format="%(asctime)s [AI_AGENT] [%(levelname)s] - %(message)s")
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY không được thiết lập trong tệp .env")
genai.configure(api_key=API_KEY)
# ...

APP_FILE = Path("app/application.py")
PLANNER_PROMPT_FILE = Path("app/prompts/planner_prompt.txt")

# --- HÀM MỚI ĐỂ GỌI AI LẬP KẾ HOẠCH ---
def invoke_planner_ai(user_goal: str, history: list[dict]) -> list[dict] | None:
    """Gọi AI Planner để phân rã mục tiêu lớn thành kế hoạch."""
    logging.info(f"Đang gọi AI Planner với mục tiêu: '{user_goal}'")
    
    current_code = APP_FILE.read_text(encoding="utf-8")
    history_str = json.dumps(history, indent=2, ensure_ascii=False)
    
    # Đọc prompt từ file
    prompt_template = PLANNER_PROMPT_FILE.read_text(encoding="utf-8")
    prompt = prompt_template.format(
        history_context=history_str,
        source_code_context=current_code,
        user_goal=user_goal
    )
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        response_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(response_text)
        
        plan = data.get("plan")
        if not plan or not isinstance(plan, list):
            logging.error("AI Planner không trả về một kế hoạch hợp lệ.")
            return None
            
        logging.info(f"AI Planner đã tạo ra một kế hoạch gồm {len(plan)} bước.")
        return plan
    except Exception as e:
        logging.critical(f"Lỗi khi gọi AI Planner: {e}", exc_info=True)
        return None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [AI_AGENT] [%(levelname)s] - %(message)s")

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY không được thiết lập trong tệp .env")

genai.configure(api_key=API_KEY)

APP_FILE = Path("app/application.py")

def _call_gemini_for_evolution(prompt: str) -> tuple[str, str]:
    """
    Hàm gọi Gemini để tiến hóa mã nguồn.
    Trả về một tuple: (new_code, description).
    """
    logging.info("Đang gửi yêu cầu tiến hóa đến Gemini...")
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)

    # AI được yêu cầu trả về một đối tượng JSON
    response_text = response.text.strip()
    try:
        # Loại bỏ markdown nếu có
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        
        data = json.loads(response_text)
        new_code = data.get("new_code")
        description = data.get("description")

        if not new_code or not description:
            raise ValueError("JSON trả về thiếu 'new_code' hoặc 'description'.")

        return new_code, description
    except (json.JSONDecodeError, ValueError) as e:
        logging.error(f"AI không trả về JSON hợp lệ. Lỗi: {e}. Phản hồi thô: {response.text}")
        raise ValueError("AI không trả về JSON hợp lệ.") from e


def modify_application_code(user_request: str, history: list[dict]):
    """Sử dụng AI để sửa đổi tệp application.py dựa trên yêu cầu và lịch sử."""
    logging.info(f"Đang xử lý yêu cầu: '{user_request}' với lịch sử thay đổi.")
    
    current_code = APP_FILE.read_text(encoding="utf-8")
    history_str = json.dumps(history, indent=2, ensure_ascii=False)

    prompt = f"""
    Bạn là một kỹ sư phần mềm AI cao cấp. Nhiệm vụ của bạn là liên tục cải tiến mã nguồn Python dưới đây dựa trên yêu cầu mới và lịch sử các thay đổi trước đó.

    **QUY TẮC TUYỆT ĐỐI:**
    1.  Phân tích kỹ lưỡng yêu cầu, mã nguồn hiện tại, và lịch sử thay đổi để hiểu rõ bối cảnh.
    2.  Trả về một đối tượng JSON DUY NHẤT chứa hai khóa:
        - "new_code": Toàn bộ mã nguồn Python mới của tệp.
        - "description": Một câu mô tả ngắn gọn (bằng tiếng Việt) về thay đổi bạn đã thực hiện.
    3.  KHÔNG trả về bất cứ thứ gì khác (không giải thích, không markdown bao quanh JSON).

    **LỊCH SỬ CÁC THAY ĐỔI TRƯỚC ĐÂY:**
    ```json
    {history_str}
    ```

    **YÊU CẦU MỚI TỪ NGƯỜI DÙNG:**
    "{user_request}"

    **MÃ NGUỒN HIỆN TẠI ĐỂ SỬA ĐỔI:**
    ```python
    {current_code}
    ```

    **ĐỐI TƯỢNG JSON CỦA BẠN:**
    """
    
    new_code, description = _call_gemini_for_evolution(prompt)
    APP_FILE.write_text(new_code, encoding="utf-8")
    logging.info(f"Đã cập nhật thành công '{APP_FILE}'.")
    return description


def fix_application_code(error_message: str):
    """Sử dụng AI để sửa lỗi trong tệp application.py. (Giữ nguyên, không đổi)"""
    logging.info("Bắt đầu quá trình sửa lỗi tự động...")
    try:
        failed_code = APP_FILE.read_text(encoding="utf-8")
        prompt = f"""
        Bạn là một chuyên gia gỡ lỗi Python. Mã nguồn dưới đây đã bị lỗi. Phân tích mã và thông báo lỗi, sau đó viết lại toàn bộ tệp với phiên bản đã sửa.
        QUY TẮC: Chỉ trả về mã nguồn Python hoàn chỉnh. KHÔNG giải thích, KHÔNG markdown.
        
        THÔNG BÁO LỖI:
        {error_message}
        
        MÃ NGUỒN LỖI:
        {failed_code}
        
        MÃ NGUỒN ĐÃ SỬA:
        """
        # Sử dụng hàm gọi Gemini đơn giản hơn cho việc sửa lỗi
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        fixed_code = response.text.strip().replace("```python", "").replace("```", "").strip()
        
        if not fixed_code:
            raise ValueError("AI trả về phản hồi rỗng khi sửa lỗi.")

        APP_FILE.write_text(fixed_code, encoding="utf-8")
        logging.info(f"AI đã thử sửa lỗi và cập nhật lại '{APP_FILE}'.")
    except Exception as e:
        logging.critical(f"Lỗi trong quá trình tự sửa lỗi của AI: {e}", exc_info=True)