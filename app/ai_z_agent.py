# app/ai_z_agent.py

import os
import google.generativeai as genai
from config import Z_PROMPT_FILE_PATH, AI_MODEL_NAME # Import từ config.py
from logging_setup import logger # Import the logger

def invoke_ai_z():
    """
    Yêu cầu AI Z đề xuất một nhiệm vụ hoặc vấn đề nhỏ cho AI X.
    Trả về chuỗi mô tả nhiệm vụ được đề xuất hoặc None nếu có lỗi.
    """
    logger.info("🧠 [AI Z] Đang kết nối Gemini, đọc prompt và tạo đề xuất nhiệm vụ...")
    try:
        if not os.path.exists(Z_PROMPT_FILE_PATH):
            logger.error(f"File prompt cho AI Z không tìm thấy: {Z_PROMPT_FILE_PATH}")
            raise FileNotFoundError(f"File prompt cho AI Z không tìm thấy: {Z_PROMPT_FILE_PATH}")

        with open(Z_PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
            prompt = f.read()

        model = genai.GenerativeModel(AI_MODEL_NAME)
        response = model.generate_content(prompt)
        
        task_suggestion = response.text.strip()
        logger.info(f"🧠 [AI Z] Đã nhận được đề xuất nhiệm vụ: '{task_suggestion[:100]}...' [Tiếp theo: xem full đề xuất]")
        return task_suggestion
        
    except FileNotFoundError as e:
        logger.error(f"❌ Lỗi: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Lỗi khi gọi Gemini API cho AI Z: {e}", exc_info=True)
        return None
