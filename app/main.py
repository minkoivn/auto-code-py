import logging
import os
import argparse
from config import DEFAULT_APPLICATION_VERSION

class Application:
    """
    Lớp đại diện cho ứng dụng Project A.
    Xử lý logic lấy phiên bản và chạy ứng dụng.
    """

    @staticmethod
    def setup_logging() -> None:
        """Cấu hình cài đặt logging cơ bản cho ứng dụng."""
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')

    @staticmethod
    def _parse_cli_arguments() -> argparse.Namespace:
        """Phân tích các đối số dòng lệnh cho ứng dụng, bao gồm tùy chọn phiên bản."""
        parser = argparse.ArgumentParser(description="Chạy Project A với phiên bản được chỉ định.")
        parser.add_argument('--version', type=int, help=f"Chỉ định phiên bản ứng dụng (mặc định: {DEFAULT_APPLICATION_VERSION}).")
        return parser.parse_args()

    def __init__(self, cli_version: int | None = None) -> None:
        """
        Khởi tạo đối tượng Application, bao gồm việc lấy phiên bản ứng dụng
        từ biến môi trường, đối số dòng lệnh, hoặc sử dụng mặc định.
        """
        self.version: int = self._get_application_version(cli_version)

    def _get_application_version(self, cli_version: int | None = None) -> int:
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

    def run(self) -> None:
        """
        Đây là hàm chính của ứng dụng.
        Hiện tại nó chỉ in ra một thông điệp.
        """
        try:
            logging.info("Ứng dụng đã bắt đầu chạy")
            logging.info(f"Hello from Project A - Version {self.version}")
            logging.info("Ứng dụng đã chạy xong")
        except Exception as e:
            logging.exception(f"Lỗi trong quá trình chạy ứng dụng: {e}")
        finally:
            logging.info("Ứng dụng đã kết thúc")


if __name__ == "__main__":
    Application.setup_logging()

    # Phân tích các đối số dòng lệnh bằng phương thức mới
    args = Application._parse_cli_arguments()

    # Chuyển phiên bản đã phân tích vào hàm tạo của Application
    app = Application(cli_version=args.version)
    app.run()
