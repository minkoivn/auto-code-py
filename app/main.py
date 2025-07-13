# app/main.py
"""Đây là module chính của Project A."""
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')

def _get_application_version():
    """
    Xử lý logic lấy phiên bản ứng dụng từ biến môi trường hoặc sử dụng mặc định.
    Bao gồm kiểm tra, chuyển đổi kiểu và ghi log chi tiết.
    """
    version = os.environ.get('VERSION')
    if version:
        logging.info(f"Biến môi trường VERSION được tìm thấy: '{version}'")
        try:
            version_int = int(version) # Kiểm tra xem VERSION có phải là số nguyên
            logging.info(f"Đã chuyển đổi VERSION thành số nguyên: {version_int}")
            return version_int
        except ValueError:
            logging.warning("Biến môi trường VERSION không phải là số nguyên hợp lệ. Sử dụng phiên bản mặc định.")
            logging.info("Sử dụng phiên bản mặc định: 1")
            return 1
    else:
        logging.info("Biến môi trường VERSION không được đặt. Sử dụng phiên bản mặc định.")
        logging.info("Sử dụng phiên bản mặc định: 1")
        return 1

def run_application():
    """
    Đây là hàm chính của ứng dụng.
    Hiện tại nó chỉ in ra một thông điệp.
    """
    try:
        logging.info("Ứng dụng đã bắt đầu chạy")
        version = _get_application_version()
        logging.info(f"Phiên bản cuối cùng đang sử dụng: {version}")
        print(f"Hello from Project A - Version {version}")
        logging.info("Ứng dụng đã chạy xong")
    except Exception as e:
        logging.exception(f"Lỗi trong quá trình chạy ứng dụng: {e}")
    finally:
        logging.info("Ứng dụng đã kết thúc")

if __name__ == "__main__":
    run_application()
