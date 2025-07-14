# config.py
import os
from dotenv import load_dotenv

# Tải các biến môi trường từ .env file trước tiên và chỉ một lần.
load_dotenv()

class AppConfig:
    """
    Một đối tượng cấu hình chuyên biệt để tập trung tất cả các cài đặt ứng dụng.
    Các cài đặt được tải từ các biến môi trường (bao gồm file .env)
    khi module được import.
    """
    # Đường dẫn
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    REPO_DIR = os.path.dirname(APP_ROOT)
    PROJECT_ROOT = REPO_DIR # Thêm PROJECT_ROOT để tương thích với utils.py

    # Các file điều khiển
    CONTROL_DIR = os.path.join(REPO_DIR, ".control")
    TRIGGER_NEXT_STEP_FLAG = os.path.join(CONTROL_DIR, "trigger_next_step")
    USER_REQUEST_FILE = os.path.join(CONTROL_DIR, "user_request.txt")

    # Biến môi trường và cài đặt cấu hình
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not set. Please set it in the .env file or system environment.")

    AI_MODEL_NAME = os.getenv('AI_MODEL_NAME', 'gemini-pro') # Thêm model name

    # Đường dẫn file log cụ thể
    APP_LOG_FILE_PATH = os.getenv('APP_LOG_FILE_PATH', 'app.log')
    EVOLUTION_LOG_FILE_PATH = os.getenv('EVOLUTION_LOG_FILE_PATH', 'evolution_log.json')
    LOG_FILE_PATH = EVOLUTION_LOG_FILE_PATH
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

    # Các tham số AI cốt lõi
    MAX_AI_X_RETRIES = int(os.getenv('MAX_AI_X_RETRIES', 3))
    RETRY_SLEEP_SECONDS = int(os.getenv('RETRY_SLEEP_SECONDS', 5))
    SLEEP_BETWEEN_ITERATIONS_SECONDS = int(os.getenv('SLEEP_BETWEEN_ITERATIONS_SECONDS', 10))

    # Các cài đặt khác
    VERSION = "0.74.1" # Cập nhật phiên bản
    INTERACTIVE_MODE = os.getenv('INTERACTIVE_MODE', 'False').lower() == 'true'

    # Các đường dẫn cần loại trừ
    EXCLUDE_PATHS = [
        ".git",
        "__pycache__",
        ".idea",
        ".vscode",
        "*.pyc",
        "node_modules",
        "venv",
        ".env",
        CONTROL_DIR,
        APP_LOG_FILE_PATH,
        EVOLUTION_LOG_FILE_PATH
    ]
    
    # Thêm đường dẫn prompt cho AI X
    PROMPT_FILE_PATH = os.path.join(APP_ROOT, "prompts", "x_prompt.txt")

# Tạo một instance duy nhất của đối tượng cấu hình
config = AppConfig()