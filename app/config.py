# app/config.py

# Cấu hình đường dẫn và file
PROMPT_FILE_PATH = "app/prompts/x_prompt.txt"
LOG_FILE_PATH = "app/evolution_log.json"

# Các đường dẫn cần loại trừ khỏi bối cảnh mã nguồn
EXCLUDE_PATHS = [
    LOG_FILE_PATH, # Loại trừ file log
    "app/prompts/" # Loại trừ thư mục chứa các prompt
]

# Cấu hình hoạt động của AI Agent
MAX_AI_X_RETRIES = 3 # Số lần thử lại tối đa khi gọi AI X

# Các cài đặt khác có thể thêm vào đây trong tương lai
# Ví dụ: thời gian chờ giữa các chu kỳ, cấu hình model AI...
