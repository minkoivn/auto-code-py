import logging
import os
import argparse
from config import DEFAULT_APPLICATION_VERSION

def setup_logging() -> None:
    """Cấu hình cài đặt logging cơ bản cho ứng dụng."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')

def get_application_version(cli_version: int | None = None) -> int:
    """
    Xử lý logic lấy phiên bản ứng dụng từ đối số dòng lệnh, biến môi trường,
    hoặc sử dụng mặc định. Bao gồm kiểm tra, chuyển đổi kiểu và ghi log chi tiết.
    Ưu tiên: Đối số dòng lệnh > Biến môi trường > Mặc định.
    """
    application_version: int = DEFAULT_APPLICATION_VERSION
    source: str = "mặc định"

    if cli_version is not None:
        application_version = cli_version
        source = "đối số dòng lệnh"
        logging.info(f"Phiên bản được chỉ định qua đối số dòng lệnh: {cli_version}")
    else:
        version_str: str | None = os.environ.get('VERSION')
        if version_str:
            logging.info(f"Biến môi trường VERSION được tìm thấy: '{version_str}'")
            try:
                version_int: int = int(version_str)
                application_version = version_int
                source = "biến môi trường"
                logging.info(f"Đã chuyển đổi VERSION từ biến môi trường thành số nguyên: {application_version}")
            except ValueError:
                logging.warning(f"Biến môi trường VERSION '{version_str}' không phải là số nguyên hợp lệ. Sử dụng phiên bản mặc định.")
        else:
            logging.info("Biến môi trường VERSION không được đặt. Sử dụng phiên bản mặc định.")
    
    logging.info(f"Phiên bản được sử dụng: {application_version} (nguồn: {source})")
    return application_version

def parse_cli_arguments() -> argparse.Namespace:
    """Phân tích các đối số dòng lệnh cho ứng dụng, bao gồm tùy chọn phiên bản."""
    parser = argparse.ArgumentParser(description="Chạy Project A với phiên bản được chỉ định.")
    parser.add_argument('--version', type=int, help=f"Chỉ định phiên bản ứng dụng (mặc định: {DEFAULT_APPLICATION_VERSION}).")
    return parser.parse_args()
