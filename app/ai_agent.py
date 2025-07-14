import os
import json
import re
import google.generativeai as genai
from google.generativeai.types import StopCandidateException # Import specific exception
from config import PROMPT_FILE_PATH, AI_MODEL_NAME
from utils import format_history_for_prompt
from logging_setup import logger # Import the logger

def _process_ai_response_json(ai_raw_text: str) -> tuple[str, str, str]:
    """
    Xử lý chuỗi phản hồi thô từ AI, trích xuất JSON, kiểm tra cấu trúc
    và chuẩn hóa đường dẫn file.
    Raise ValueError nếu phản hồi không hợp lệ hoặc thiếu trường.
    """
    text = ai_raw_text.replace("\u00A0", " ").replace("\r", "")

    # Ưu tiên tìm khối JSON được bọc trong ```json
    match = re.search(r'```json\s*({.*?})\s*```', text, re.DOTALL)
    if not match:
        # Nếu không tìm thấy, thử tìm bất kỳ đối tượng JSON nào
        match = re.search(r'({.*?})', text, re.DOTALL)

    if not match:
        raise ValueError("AI không trả về nội dung theo định dạng JSON hợp lệ.")

    json_string = match.group(1)
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError:
        raise ValueError("AI trả về chuỗi không phải là JSON hợp lệ.")

    filepath = data.get("filepath")
    new_content = data.get("new_code")
    description = data.get("description")

    if not all([filepath, new_content, description]):
        missing_fields = []
        if not filepath: missing_fields.append("filepath")
        if not new_content: missing_fields.append("new_code")
        if not description: missing_fields.append("description")
        raise ValueError(f"JSON trả về thiếu các trường bắt buộc: {', '.join(missing_fields)}.")

    # Đảm bảo filepath bắt đầu bằng 'app/' nếu chưa có
    if filepath and not filepath.startswith("app/"):
        filepath = "app/" + filepath
        
    return filepath, new_content, description

def invoke_ai_x(context: str, history_log: list):
    """
    Yêu cầu AI X trả về một đối tượng JSON chứa nội dung file mới và mô tả.
    Trả về một tuple: (filepath, new_content, description, failure_reason)
    """
    logger.info("🤖 [AI X] Đang kết nối Gemini, đọc lịch sử và tạo đề xuất file mới...")
    with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
        prompt_template = f.read()
    
    # Sử dụng hàm format_history_for_prompt từ module utils
    history_context = format_history_for_prompt(history_log)
    prompt_filled_history = prompt_template.replace("{history_context}", history_context)
    prompt = f"{prompt_filled_history}\n\n{context}"
    
    # Log the prompt details before sending (at DEBUG level)
    logger.debug(f"🤖 [AI X] Gửi prompt tới Gemini. Độ dài: {len(prompt)} ký tự. 1000 ký tự đầu:\n{prompt[:1000]}...")
    
    model = genai.GenerativeModel(AI_MODEL_NAME)
    try:
        response = model.generate_content(prompt)
        
        # Log the raw response after receiving it (at DEBUG level)
        if response and hasattr(response, 'text'):
            logger.debug(f"🤖 [AI X] Đã nhận phản hồi thô từ Gemini (độ dài: {len(response.text)}): {response.text}")
        else:
            logger.debug(f"🤖 [AI X] Phản hồi từ Gemini không có thuộc tính 'text' hoặc rỗng.")
            
        # Bổ sung kiểm tra robust cho phản hồi API
        if not response.candidates:
            reason = "API Gemini trả về không có ứng cử viên (candidate). Có thể do bị chặn nội dung hoặc không tạo được phản hồi." 
            logger.error(f"❌ Lỗi khi gọi Gemini API cho AI X: {reason}")
            return None, None, None, reason
        
        if not response.text.strip():
            reason = "API Gemini trả về phản hồi rỗng hoặc chỉ chứa khoảng trắng sau khi tạo nội dung." 
            logger.error(f"❌ Lỗi khi gọi Gemini API cho AI X: {reason}")
            return None, None, None, reason
            
        try:
            filepath, new_content, description = _process_ai_response_json(response.text)
            logger.info("🤖 [AI X] Đã nhận được đề xuất JSON hợp lệ.")
            return filepath, new_content, description, None
        except ValueError as ve:
            # Lỗi từ hàm xử lý JSON
            return None, None, None, str(ve)

    except StopCandidateException as e:
        reason = f"Đề xuất bị chặn do chính sách an toàn hoặc lý do khác: {e}"
        logger.error(f"❌ Lỗi khi gọi Gemini API cho AI X (StopCandidateException): {reason}", exc_info=True)
        return None, None, None, reason
    except Exception as e:
        logger.error(f"❌ Lỗi khi gọi Gemini API cho AI X: {e}", exc_info=True)
        return None, None, None, str(e)
