import logging
import argparse
from config import DEFAULT_APPLICATION_VERSION
from app.utils import setup_logging, get_application_version


class Application:
    """
    Lớp đại diện cho ứng dụng Project A.
    Xử lý logic lấy phiên bản và chạy ứng dụng.
    """

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
        self.version: int = get_application_version(cli_version)

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
    setup_logging()

    # Phân tích các đối số dòng lệnh bằng phương thức mới
    args = Application._parse_cli_arguments()

    # Chuyển phiên bản đã phân tích vào hàm tạo của Application
    app = Application(cli_version=args.version)
    app.run()
