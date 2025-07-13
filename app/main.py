# app/main.py
"""Đây là module chính của Project A."""
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')

def run_application():
    """
    Đây là hàm chính của ứng dụng.
    Hiện tại nó chỉ in ra một thông điệp.
    """
    try:
        logging.info("Ứng dụng đã bắt đầu chạy")
        version = os.environ.get('VERSION', '1') # Lấy version từ biến môi trường, mặc định là 1 nếu không có
        print(f"Hello from Project A - Version {version}")
        logging.info("Ứng dụng đã chạy xong")
    except Exception as e:
        logging.exception(f"Lỗi trong quá trình chạy ứng dụng: {e}")

if __name__ == "__main__":
    run_application()