import logging
import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
from config import config
from git_utils import git_log_last_n_commits # Sửa: import đúng tên hàm
from google.api_core.exceptions import GoogleAPICallError, RetryError

load_dotenv()
logger = logging.getLogger(__name__)

genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel(config.AI_MODEL_NAME)

def _process_ai_z_response(response_text: str) -> tuple[str | None, list[str] | None]:
    """Trích xuất JSON từ phản hồi của AI Z."""
    match = re.search(r'```json\s*({.*?})\s*```', response_text, re.DOTALL)
    if not match:
        logger.error("AI Z không trả về JSON hợp lệ.")
        return None, None
    
    try:
        data = json.loads(match.group(1))
        suggestion = data.get("suggestion")
        relevant_files = data.get("relevant_files", [])
        if not suggestion or not isinstance(relevant_files, list):
            logger.error("JSON từ AI Z thiếu trường 'suggestion' hoặc 'relevant_files' không phải list.")
            return None, None
        return suggestion, relevant_files
    except json.JSONDecodeError:
        logger.error("Không thể giải mã JSON từ AI Z.", exc_info=True)
        return None, None

def invoke_ai_z(user_request: str | None = None) -> tuple[str | None, list[str] | None]:
    """
    Kêu gọi AI Z để nhận đề xuất và danh sách tệp liên quan.
    """
    logger.info("Đang gọi AI Z để lấy đề xuất...")
    
    try:
        # Sửa: gọi đúng tên hàm git_log_last_n_commits
        git_history = git_log_last_n_commits(n=10, repo_path=config.REPO_DIR) 
        history_str = "\n".join([f"- {commit['hash'][:7]}: {commit['message']}" for commit in git_history])
    except Exception as e:
        logger.error(f"Lỗi khi lấy lịch sử Git: {e}", exc_info=True)
        history_str = "Không thể lấy lịch sử Git."

    # Tải prompt từ file
    prompt_path = os.path.join(config.APP_ROOT, "prompts", "z_prompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    # Điền thông tin vào prompt
    from utils import get_source_code_context, format_history_for_prompt # Import local để tránh circular dependency
    source_context = get_source_code_context()
    history_context = format_history_for_prompt(git_history) # Sử dụng git_history đã lấy
    
    full_prompt = prompt_template.format(
        source_code_context=source_context,
        history_context=history_context,
        user_request=user_request if user_request else "Không có yêu cầu nào."
    )

    logger.debug(f"Gửi prompt tới AI Z (độ dài: {len(full_prompt)})...")

    try:
        response = model.generate_content(full_prompt)
        if not response.text:
            logger.warning("AI Z trả về phản hồi rỗng.")
            return None, None
        
        return _process_ai_z_response(response.text)

    except (GoogleAPICallError, RetryError) as e:
        logger.error(f"Lỗi API khi gọi AI Z: {e}", exc_info=True)
        return None, None
    except Exception as e:
        logger.error(f"Lỗi không xác định khi gọi AI Z: {e}", exc_info=True)
        return None, None