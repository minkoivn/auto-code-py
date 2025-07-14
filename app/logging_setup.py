# app/logging_setup.py

import logging
import os
from config import APP_LOG_FILE_PATH # Import từ config.py

def setup_logging():
    """
    Cấu hình hệ thống logging cho ứng dụng AI Agent X.
    Thiết lập một logger với console handler để ghi log ra màn hình
    và một file handler để ghi log vào tệp.
    """
    logger = logging.getLogger('ai_agent_x')
    logger.setLevel(logging.INFO) # Đặt mức log mặc định là INFO

    # Kiểm tra nếu đã có handler để tránh thêm nhiều lần khi module được import lại
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO) # Mức log cho console handler
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler
        # Đảm bảo thư mục cho file log tồn tại trước khi tạo FileHandler
        log_dir = os.path.dirname(APP_LOG_FILE_PATH)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        fh = logging.FileHandler(APP_LOG_FILE_PATH, encoding='utf-8')
        fh.setLevel(logging.INFO) # Mức log cho file handler
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

# Gọi hàm setup_logging ngay lập tức để cấu hình logger khi module này được import.
# Các module khác có thể import `logger` trực tiếp từ đây để sử dụng.
logger = setup_logging()

if __name__ == '__main__':
    # Ví dụ sử dụng logger khi chạy file này trực tiếp
    logger.debug("Đây là một thông báo DEBUG (sẽ không hiển thị với INFO level).")
    logger.info("Đây là một thông báo INFO.")
    logger.warning("Đây là một cảnh báo.")
    logger.error("Đây là một lỗi.")
    logger.critical("Đây là một lỗi nghiêm trọng.")
