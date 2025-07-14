# config.py
import os
from dotenv import load_dotenv

# Tải các biến môi trường từ .env file trước tiên và chỉ một lần.
# (Lưu ý: main.py cũng gọi load_dotenv() ở đầu, điều này là an toàn và bất biến).
load_dotenv()

class AppConfig:
    """
    Một đối tượng cấu hình chuyên biệt để tập trung tất cả các cài đặt ứng dụng.
    Các cài đặt được tải từ các biến môi trường (bao gồm file .env)
    khi module được import.
    """
    # Đường dẫn
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    # Giả sử thư mục gốc của repo nằm một cấp trên app/
    REPO_DIR = os.path.dirname(APP_ROOT)

    # Các file điều khiển
    CONTROL_DIR = os.path.join(REPO_DIR, ".control")
    TRIGGER_NEXT_STEP_FLAG = os.path.join(CONTROL_DIR, "trigger_next_step")
    USER_REQUEST_FILE = os.path.join(CONTROL_DIR, "user_request.txt")

    # Biến môi trường và cài đặt cấu hình
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    # Xác thực GEMINI_API_KEY ngay lập tức khi tải config.py
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not set. Please set it in the .env file or system environment.")

    # Đường dẫn file log cụ thể
    APP_LOG_FILE_PATH = os.getenv('APP_LOG_FILE_PATH', 'app.log') # Dành cho log ứng dụng chung
    EVOLUTION_LOG_FILE_PATH = os.getenv('EVOLUTION_LOG_FILE_PATH', 'evolution_log.json') # Dành cho log lịch sử tiến hóa

    # LOG_FILE_PATH được import bởi orchestrator.py cho lịch sử.
    # Nó phải ánh xạ tới EVOLUTION_LOG_FILE_PATH để nhất quán với L71.
    LOG_FILE_PATH = EVOLUTION_LOG_FILE_PATH

    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

    # Các tham số AI cốt lõi
    MAX_AI_X_RETRIES = int(os.getenv('MAX_AI_X_RETRIES', 3))
    RETRY_SLEEP_SECONDS = int(os.getenv('RETRY_SLEEP_SECONDS', 5))
    SLEEP_BETWEEN_ITERATIONS_SECONDS = int(os.getenv('SLEEP_BETWEEN_ITERATIONS_SECONDS', 10))

    # Các cài đặt khác
    VERSION = "0.74.0" # Phiên bản hardcoded, lý tưởng là đọc từ git tags hoặc động
    INTERACTIVE_MODE = os.getenv('INTERACTIVE_MODE', 'False').lower() == 'true'

    # Các đường dẫn cần loại trừ khỏi bối cảnh mã nguồn (cho get_source_code_context)
    EXCLUDE_PATHS = [
        ".git",
        "__pycache__",
        ".idea",
        ".vscode",
        "*.pyc",
        "node_modules",
        "venv",
        ".env",
        CONTROL_DIR, # Loại trừ nội dung thư mục điều khiển
        APP_LOG_FILE_PATH, # Loại trừ file log ứng dụng chung khỏi bối cảnh
        EVOLUTION_LOG_FILE_PATH # Loại trừ file log lịch sử tiến hóa khỏi bối cảnh
    ]

# Tạo một instance duy nhất của đối tượng cấu hình để dễ dàng import
config = AppConfig()
