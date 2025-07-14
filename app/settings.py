# app/settings.py
import os
import logging
from typing import Dict, Any

# Định nghĩa các giá trị mặc định.
# (Lưu ý: APPLICATION_NAME và DEFAULT_APPLICATION_VERSION hiện cũng có trong config.py.
#  Việc này sẽ được giải quyết trong các lần thay đổi sau.)
APPLICATION_NAME: str = "Project A"
DEFAULT_APPLICATION_VERSION: int = 1
DEFAULT_FAILURE_CHANCE: float = 0.2
DEFAULT_LONG_TASK_DIVISOR: int = 5

def load_application_settings() -> Dict[str, Any]:
    """
    Tải tất cả các cài đặt ứng dụng từ biến môi trường hoặc sử dụng giá trị mặc định.
    Trả về một từ điển chứa các cài đặt.
    """
    settings = {
        "application_name": APPLICATION_NAME,
        "version": DEFAULT_APPLICATION_VERSION,
        "failure_chance": DEFAULT_FAILURE_CHANCE,
        "long_task_divisor": DEFAULT_LONG_TASK_DIVISOR,
    }

    # Tải phiên bản ứng dụng
    version_str: str | None = os.environ.get('VERSION')
    if version_str:
        try:
            version_int: int = int(version_str)
            settings["version"] = version_int
            logging.info(f"Đã tải phiên bản ứng dụng từ biến môi trường: {version_int}")
        except ValueError:
            logging.warning(f"Biến môi trường VERSION '{version_str}' không phải là số nguyên hợp lệ. Sử dụng mặc định ({DEFAULT_APPLICATION_VERSION}).")
    else:
        logging.info(f"Biến môi trường VERSION không được đặt. Sử dụng mặc định ({DEFAULT_APPLICATION_VERSION}).")

    # Tải tỉ lệ lỗi
    failure_chance_str = os.getenv('FAILURE_CHANCE')
    if failure_chance_str:
        try:
            chance = float(failure_chance_str)
            if not (0.0 <= chance <= 1.0):
                raise ValueError("Giá trị phải nằm trong khoảng [0.0, 1.0]")
            settings["failure_chance"] = chance
            logging.info(f"Đã tải tỉ lệ lỗi từ biến môi trường: {chance}")
        except ValueError as e:
            logging.warning(f"Biến môi trường FAILURE_CHANCE '{failure_chance_str}' không hợp lệ ({e}). Sử dụng mặc định ({DEFAULT_FAILURE_CHANCE}).")
    else:
        logging.info(f"Biến môi trường FAILURE_CHANCE không được đặt. Sử dụng mặc định ({DEFAULT_FAILURE_CHANCE}).")

    # Tải bộ chia tác vụ dài
    long_task_divisor_str = os.getenv('LONG_TASK_DIVISOR')
    if long_task_divisor_str:
        try:
            divisor = int(long_task_divisor_str)
            if divisor <= 0:
                raise ValueError("Giá trị phải là số nguyên dương.")
            settings["long_task_divisor"] = divisor
            logging.info(f"Đã tải bộ chia tác vụ dài từ biến môi trường: {divisor}")
        except ValueError as e:
            logging.warning(f"Biến môi trường LONG_TASK_DIVISOR '{long_task_divisor_str}' không hợp lệ ({e}). Sử dụng mặc định ({DEFAULT_LONG_TASK_DIVISOR}).")
    else:
        logging.info(f"Biến môi trường LONG_TASK_DIVISOR không được đặt. Sử dụng mặc định ({DEFAULT_LONG_TASK_DIVISOR}).")

    logging.info(f"Tất cả cài đặt đã tải: {settings}")
    return settings
