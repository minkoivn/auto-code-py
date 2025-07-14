# app/settings.py
import os
import logging
from typing import Dict, Any

# Định nghĩa các giá trị mặc định chỉ tồn tại trong settings.py
DEFAULT_FAILURE_CHANCE: float = 0.2
DEFAULT_LONG_TASK_DIVISOR: int = 5

def load_application_settings() -> Dict[str, Any]:
    """
    Tải các cài đặt mô phỏng (tỉ lệ lỗi và bộ chia tác vụ dài) từ biến môi trường
    hoặc sử dụng giá trị mặc định. Phiên bản và tên ứng dụng được quản lý riêng.
    Trả về một từ điển chứa các cài đặt mô phỏng.
    """
    settings = {
        "failure_chance": DEFAULT_FAILURE_CHANCE,
        "long_task_divisor": DEFAULT_LONG_TASK_DIVISOR,
    }

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

    logging.info(f"Tất cả cài đặt mô phỏng đã tải: {settings}")
    return settings
