import logging
import os
import argparse
from config import DEFAULT_APPLICATION_VERSION

def setup_logging(level_str: str = 'INFO') -> None:
    """
    Cấu hình cài đặt logging cơ bản cho ứng dụng với cấp độ có thể tùy chỉnh.
    Cấp độ có thể được truyền vào dưới dạng chuỗi (ví dụ: 'DEBUG', 'INFO', 'WARNING').
    """
    # Ánh xạ chuỗi cấp độ thành các hằng số logging, mặc định là INFO nếu không hợp lệ
    log_level = getattr(logging, level_str.upper(), logging.INFO)
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')
    logging.info(f"Cấu hình logging hoàn tất. Cấp độ: {logging.getLevelName(log_level)}")

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
    """
    Phân tích các đối số dòng lệnh cho ứng dụng, bao gồm tùy chọn phiên bản
    và cấp độ logging.
    """
    parser = argparse.ArgumentParser(description="Chạy Project A với phiên bản được chỉ định.")
    parser.add_argument('--version', type=int, help=f"Chỉ định phiên bản ứng dụng (mặc định: {DEFAULT_APPLICATION_VERSION}).")
    parser.add_argument('--log-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Chỉ định cấp độ logging (mặc định: INFO).")
    return parser.parse_args()
