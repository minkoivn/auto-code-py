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
        version = os.environ.get('VERSION')
        if version:
            try:
                version = int(version) # Kiểm tra xem VERSION có phải là số nguyên
                logging.info(f"Đã lấy phiên bản từ biến môi trường: {version}")
            except ValueError:
                logging.warning("Biến môi trường VERSION không phải là số nguyên. Sử dụng phiên bản mặc định.")
                version = 1
        else:
            version = 1
        logging.info(f"Phiên bản đang sử dụng: {version}")
        print(f"Hello from Project A - Version {version}")
        logging.info("Ứng dụng đã chạy xong")
    except Exception as e:
        logging.exception(f"Lỗi trong quá trình chạy ứng dụng: {e}")

if __name__ == "__main__":
    run_application()