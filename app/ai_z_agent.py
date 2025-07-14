# app/ai_z_agent.py

import os
import json
import re
import google.generativeai as genai
from google.generativeai.types import StopCandidateException # Import specific exception
from config import Z_PROMPT_FILE_PATH, AI_MODEL_NAME # Import từ config.py
from logging_setup import logger # Import the logger

def _process_ai_z_response_json(ai_raw_text: str) -> tuple[str, list[str]]:
    """
    Xử lý chuỗi phản hồi thô từ AI Z, trích xuất JSON, kiểm tra cấu trúc
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
        raise ValueError("AI Z không trả về nội dung theo định dạng JSON hợp lệ.")

    json_string = match.group(1)
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError:
        raise ValueError("AI Z trả về chuỗi không phải là JSON hợp lệ.")

    suggestion = data.get("suggestion")
    relevant_files = data.get("relevant_files")

    if not all([suggestion, relevant_files is not None]): # Check relevant_files explicitly for None, as it can be empty list
        missing_fields = []
        if not suggestion: missing_fields.append("suggestion")
        if relevant_files is None: missing_fields.append("relevant_files") # Check if key is missing/None
        raise ValueError(f"JSON từ AI Z thiếu các trường bắt buộc: {', '.join(missing_fields)}.")
    
    if not isinstance(relevant_files, list):
        raise ValueError("Trường 'relevant_files' trong JSON của AI Z phải là một danh sách.")

    # Chuẩn hóa đường dẫn file trong relevant_files
    normalized_files = []
    for filepath in relevant_files:
        if isinstance(filepath, str):
            # Đảm bảo filepath bắt đầu bằng 'app/' nếu chưa có
            if not filepath.startswith("app/") and not filepath.startswith("./app/"):
                filepath = "app/" + filepath
            normalized_files.append(filepath)
        else:
            logger.warning(f"File path '{filepath}' trong relevant_files không phải là chuỗi. Bỏ qua.")

    return suggestion, normalized_files

def invoke_ai_z(user_request: str = None) -> tuple[str | None, list[str] | None]:
    """
    Yêu cầu AI Z đề xuất một nhiệm vụ hoặc vấn đề nhỏ cho AI X và danh sách các tệp liên quan.
    Có thể bao gồm yêu cầu cụ thể từ người dùng.
    Trả về một tuple: (chuỗi mô tả nhiệm vụ, danh sách các tệp liên quan) hoặc (None, None) nếu có lỗi.
    """
    logger.info("🧠 [AI Z] Đang kết nối Gemini, đọc prompt và tạo đề xuất nhiệm vụ...")
    try:
        if not os.path.exists(Z_PROMPT_FILE_PATH):
            logger.error(f"File prompt cho AI Z không tìm thấy: {Z_PROMPT_FILE_PATH}")
            raise FileNotFoundError(f"File prompt cho AI Z không tìm thấy: {Z_PROMPT_FILE_PATH}")

        with open(Z_PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
            prompt = f.read()
        
        # Add user request to the prompt if provided
        if user_request:
            logger.info(f"🧠 [AI Z] Đang tích hợp yêu cầu người dùng vào prompt: '{user_request[:50]}...' [Tiếp theo: xem full yêu cầu]")
            # Định dạng rõ ràng để AI Z nhận diện yêu cầu từ người dùng
            prompt += f"\n\n--- YÊU CẦU CẢI THIỆN TỪ NGƯỜI DÙNG ---\n{user_request}\n---------------------------------------\nHãy xem xét yêu cầu này khi đưa ra đề xuất cải tiến tiếp theo."
        
        # Thêm hướng dẫn AI Z về định dạng JSON và việc chọn file
        prompt += "\n\nHãy trả về đề xuất của bạn dưới dạng đối tượng JSON với hai trường: 'suggestion' (mô tả nhiệm vụ) và 'relevant_files' (một danh sách các đường dẫn tệp bạn nghĩ AI X nên tập trung xem xét, ví dụ: ['app/file1.py', 'app/utils/helper.py']. Nếu không có tệp cụ thể nào, hãy trả về danh sách rỗng []). Bọc JSON trong ```json...```."


        model = genai.GenerativeModel(AI_MODEL_NAME)
        response = model.generate_content(prompt)
        
        # Bổ sung kiểm tra robust cho phản hồi API
        if not response.candidates:
            reason = "API Gemini trả về không có ứng cử viên (candidate). Có thể do bị chặn nội dung hoặc không tạo được phản hồi." 
            logger.error(f"❌ Lỗi khi gọi Gemini API cho AI Z: {reason}")
            return None, None
        
        if not response.text.strip():
            reason = "API Gemini trả về phản hồi rỗng hoặc chỉ chứa khoảng trắng sau khi tạo nội dung." 
            logger.error(f"❌ Lỗi khi gọi Gemini API cho AI Z: {reason}")
            return None, None
        
        try:
            suggestion, relevant_files = _process_ai_z_response_json(response.text)
            logger.info(f"🧠 [AI Z] Đã nhận được đề xuất nhiệm vụ: '{suggestion[:100]}...' [Tiếp theo: xem full đề xuất]")
            logger.info(f"🧠 [AI Z] Các tệp liên quan được đề xuất: {relevant_files}")
            return suggestion, relevant_files
        except ValueError as ve:
            logger.error(f"❌ Lỗi khi xử lý JSON từ AI Z: {ve}")
            return None, None

    except StopCandidateException as e:
        reason = f"Đề xuất bị chặn do chính sách an toàn hoặc lý do khác: {e}"
        logger.error(f"❌ Lỗi khi gọi Gemini API cho AI Z (StopCandidateException): {reason}", exc_info=True)
        return None, None
    except FileNotFoundError as e:
        logger.error(f"❌ Lỗi: {e}")
        return None, None
    except Exception as e:
        logger.error(f"❌ Lỗi khi gọi Gemini API cho AI Z: {e}", exc_info=True)
        return None, None
