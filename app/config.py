# app/config.py
import os
from dotenv import load_dotenv

# Tải các biến môi trường từ file .env khi module này được import.
# Điều này đảm bảo rằng các biến môi trường sẽ sẵn sàng trước khi chúng được sử dụng.
load_dotenv()

def _get_env_variable(key: str, default: any = None, required: bool = False, var_type: type = str):
    """
    Truy xuất một biến môi trường một cách an toàn.
    - key (str): Tên của biến môi trường.
    - default (any, optional): Giá trị mặc định nếu biến không tồn tại. Mặc định là None.
    - required (bool): Nếu True và biến không tìm thấy, sẽ báo lỗi ValueError.
    - var_type (type): Kiểu dữ liệu mong muốn của biến (str, int, bool, ...).
      Hỗ trợ chuyển đổi chuỗi 'true', '1', 't', 'y', 'yes' thành True cho kiểu bool.
    Raises ValueError nếu biến là bắt buộc mà không tìm thấy hoặc chuyển đổi kiểu thất bại.
    """
    value = os.getenv(key)
    if value is None:
        if required:
            raise ValueError(f"Biến môi trường '{key}' là bắt buộc nhưng không tìm thấy.")
        return default
    
    try:
        if var_type == bool:
            # Chuyển đổi giá trị boolean từ chuỗi một cách linh hoạt
            return value.lower() in ('true', '1', 't', 'y', 'yes')
        return var_type(value)
    except ValueError:
        raise ValueError(f"Giá trị của biến môi trường '{key}' ('{value}') không thể chuyển đổi sang kiểu {var_type.__name__}.")

# Cấu hình API Key cho Gemini (BẮT BUỘC)
# AI Agent sẽ sử dụng giá trị này để cấu hình thư viện genai.
GEMINI_API_KEY = _get_env_variable("GEMINI_API_KEY", required=True)

# Cấu hình đường dẫn và file
LOG_FILE_PATH = "app/evolution_log.json"

# Đường dẫn cho tệp log hoạt động chính của ứng dụng AI Agent
APP_LOG_FILE_PATH = _get_env_variable("APP_LOG_FILE_PATH", default="app/agent.log")

# Đường dẫn cho tệp prompt của AI Agent X và AI Agent Z
PROMPT_FILE_PATH = _get_env_variable("AI_X_PROMPT_FILE", default="app/prompts/x_prompt.txt")
Z_PROMPT_FILE_PATH = _get_env_variable("AI_Z_PROMPT_FILE", default="app/prompts/z_prompt.txt")

# Cấu hình cho việc điều khiển thông qua giao diện web
CONTROL_DIR = _get_env_variable("CONTROL_DIR", default="app/control")
TRIGGER_NEXT_STEP_FLAG = os.path.join(CONTROL_DIR, "trigger_next_step.flag")
USER_REQUEST_FILE = os.path.join(CONTROL_DIR, "user_request.txt") # Đã chuyển từ web_server.py

# Xác định thư mục gốc của dự án (thư mục cha của 'app')
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
# REPO_DIR: Thư mục gốc của kho mã nguồn mà AI Agent đang quản lý/phân tích.
# Mặc định là thư mục gốc của dự án nếu không được cấu hình qua biến môi trường.
REPO_DIR = _get_env_variable("REPO_DIR", default=PROJECT_ROOT)


# Các đường dẫn cần loại trừ khỏi bối cảnh mã nguồn khi đọc code
EXCLUDE_PATHS = [
    LOG_FILE_PATH, # Loại trừ file log tiến hóa
    APP_LOG_FILE_PATH, # Loại trừ file log hoạt động chính của ứng dụng
    PROMPT_FILE_PATH, # Loại trừ file prompt của AI X
    Z_PROMPT_FILE_PATH, # Loại trừ file prompt của AI Z
    "app/prompts/", # Loại trừ thư mục chứa các prompt (phòng trường hợp có file khác)
    USER_REQUEST_FILE # Loại trừ file yêu cầu người dùng
]

# Cấu hình hoạt động của AI Agent, có thể bị ghi đè bởi biến môi trường
MAX_AI_X_RETRIES = _get_env_variable("MAX_AI_X_RETRIES", default=3, var_type=int)
RETRY_SLEEP_SECONDS = _get_env_variable("RETRY_SLEEP_SECONDS", default=5, var_type=int)
SLEEP_BETWEEN_ITERATIONS_SECONDS = _get_env_variable("SLEEP_BETWEEN_ITERATIONS_SECONDS", default=15, var_type=int)
INTERACTIVE_MODE = _get_env_variable("INTERACTIVE_MODE", default=False, var_type=bool)
AI_MODEL_NAME = _get_env_variable("AI_MODEL_NAME", default="gemini-2.5-flash")

# Cấu hình mức độ chi tiết của log (ví dụ: DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = _get_env_variable("LOG_LEVEL", default="INFO") 

# Thông tin phiên bản của AI Agent
VERSION = "0.0.1"

# Các cài đặt khác có thể thêm vào đây trong tương lai
