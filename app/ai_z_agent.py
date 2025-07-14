import logging
import os
import google.generativeai as genai
from dotenv import load_dotenv

from . import config
from . import git_utils
from google.api_core.exceptions import ResourceExhausted, InternalServerError, Aborted, ClientError, DeadlineExceeded, RetryError, StopCandidateException

load_dotenv()
logger = logging.getLogger(__name__)

# Configure Gemini API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY environment variable not set.")
    raise ValueError("GEMINI_API_KEY environment variable not set.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

def invoke_ai_z(user_request: str = None) -> str:
    """
    Invokes AI Z to get a suggestion for project improvement,
    now incorporating recent Git commit history for better context.
    """
    logger.info("Invoking AI Z to get a suggestion...")
    
    # Fetch recent Git history
    try:
        git_history = git_utils.get_git_log(num_commits=5) # Get last 5 commits
        history_str = "\n".join([f"- {commit['hash']} ({commit['author']}): {commit['message']}" for commit in git_history])
        logger.info(f"Fetched recent Git history:\n{history_str}")
    except Exception as e:
        logger.error(f"Error fetching Git history: {e}")
        history_str = "Could not fetch recent Git history." # Fallback if history fetching fails

    # Base prompt for AI Z
    system_prompt = (
        "Bạn là AI Z, một AI cấp cao có nhiệm vụ giám sát dự án và đề xuất các cải tiến chiến lược "
        "để tối ưu hóa hiệu suất, khả năng bảo trì và thêm tính năng mới. "
        "Dựa trên bối cảnh dự án, lịch sử thay đổi gần đây và các yêu cầu từ người dùng (nếu có), "
        "hãy đưa ra MỘT đề xuất cụ thể để cải thiện dự án. "
        "Đề xuất này có thể là sửa một file hiện có hoặc tạo một file hoàn toàn mới. "
        "Hãy tập trung vào một thay đổi có ý nghĩa và có tác động lớn." 
        "Đề xuất của bạn phải là một câu duy nhất, trực tiếp và rõ ràng." # Added for conciseness
    )

    context_info = f"\nLỊCH SỬ CÁC THAY ĐỔI GẦN ĐÂY (Git Log):\n{history_str}\n"

    user_prompt = "Hãy đưa ra một đề xuất cải thiện dự án."
    if user_request:
        user_prompt += f"\nNgười dùng có yêu cầu đặc biệt: '{user_request}'"
        logger.info(f"User request provided: '{user_request}'")

    full_prompt = f"{system_prompt}{context_info}{user_prompt}"
    
    logger.info(f"Sending prompt to Gemini for AI Z: {full_prompt[:500]}...") # Log first 500 chars

    try:
        response = model.generate_content(full_prompt)
        
        if not response or not response.candidates:
            logger.warning("Gemini API returned an empty response or no candidates for AI Z.")
            return "AI Z could not generate a suggestion at this time (empty response)."

        if not hasattr(response.candidates[0], 'content') or not hasattr(response.candidates[0].content, 'parts') or not response.candidates[0].content.parts:
            logger.warning("Gemini API response for AI Z has no content parts.")
            return "AI Z could not generate a suggestion at this time (no content parts)."

        ai_z_suggestion = response.candidates[0].content.parts[0].text
        logger.info(f"AI Z's raw suggestion received: {ai_z_suggestion[:500]}...")
        return ai_z_suggestion

    except StopCandidateException as e:
        logger.error(f"Gemini API StopCandidateException for AI Z: {e.response.text if e.response else 'No response text'}")
        return "AI Z could not generate a suggestion due to content policy or safety reasons."
    except ResourceExhausted:
        logger.error("Gemini API ResourceExhausted for AI Z: You have exceeded your quota or rate limits.")
        return "AI Z could not generate a suggestion (quota/rate limit exceeded)."
    except InternalServerError as e:
        logger.error(f"Gemini API InternalServerError for AI Z: {e}")
        return "AI Z could not generate a suggestion (internal server error).";
    except Aborted as e:
        logger.error(f"Gemini API Aborted for AI Z: {e}")
        return "AI Z could not generate a suggestion (request aborted).";
    except ClientError as e:
        logger.error(f"Gemini API ClientError for AI Z: {e}")
        return "AI Z could not generate a suggestion (client-side error).";
    except DeadlineExceeded as e:
        logger.error(f"Gemini API DeadlineExceeded for AI Z: {e}")
        return "AI Z could not generate a suggestion (request timed out).";
    except RetryError as e:
        logger.error(f"Gemini API RetryError for AI Z: {e.cause if e.cause else 'Unknown retry error'}")
        return "AI Z could not generate a suggestion (retryable error occurred).";
    except Exception as e:
        logger.error(f"An unexpected error occurred during AI Z invocation: {e}", exc_info=True)
        return f"AI Z could not generate a suggestion due to an unexpected error: {e}"
