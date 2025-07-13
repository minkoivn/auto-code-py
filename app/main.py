# app/main.py
"""Đây là module chính của Project A."""
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_application():
    """
    Đây là hàm chính của ứng dụng.
    Hiện tại nó chỉ in ra một thông điệp.
    """
    try:
        logging.info("Ứng dụng đã bắt đầu chạy")
        # TODO: Cân nhắc đưa phiên bản ra biến cấu hình
        print("Hello from Project A - Version 1")
        logging.info("Ứng dụng đã chạy xong")
    except Exception as e:
        logging.error(f"Lỗi trong quá trình chạy ứng dụng: {e}")

if __name__ == "__main__":
    run_application()