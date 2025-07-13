# app/main.py
"""Đây là module chính của Project A."""
import logging
import os

# Define constants
DEFAULT_APPLICATION_VERSION = 1

def _setup_logging():
    """Cấu hình cài đặt logging cơ bản cho ứng dụng."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')

# Call the setup function immediately
_setup_logging()

def _get_application_version():
    """
    Xử lý logic lấy phiên bản ứng dụng từ biến môi trường hoặc sử dụng mặc định.
    Bao gồm kiểm tra, chuyển đổi kiểu và ghi log chi tiết.
    """
    version_str = os.environ.get('VERSION')
    application_version = DEFAULT_APPLICATION_VERSION # Khởi tạo với phiên bản mặc định
    source = "mặc định"

    if version_str:
        logging.info(f"Biến môi trường VERSION được tìm thấy: '{version_str}'")
        try:
            version_int = int(version_str) # Kiểm tra xem VERSION có phải là số nguyên
            application_version = version_int
            source = "biến môi trường"
            logging.info(f"Đã chuyển đổi VERSION thành số nguyên: {application_version}")
        except ValueError:
            logging.warning(f"Biến môi trường VERSION '{version_str}' không phải là số nguyên hợp lệ. Sử dụng phiên bản mặc định.")
    else:
        logging.info("Biến môi trường VERSION không được đặt. Sử dụng phiên bản mặc định.")
    
    logging.info(f"Phiên bản được sử dụng: {application_version} (nguồn: {source})")
    return application_version

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
