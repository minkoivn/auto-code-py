import logging
from app.utils import setup_logging, get_application_version, parse_cli_arguments


class Application:
    """
    Lớp đại diện cho ứng dụng Project A.
    Xử lý logic lấy phiên bản và chạy ứng dụng.
    """

    def __init__(self, version: int) -> None:
        """
        Khởi tạo đối tượng Application với phiên bản đã được xác định.
        """
        self.version: int = version

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

    # Phân tích các đối số dòng lệnh
    args = parse_cli_arguments()

    # Lấy phiên bản cuối cùng sau khi xem xét tất cả các nguồn
    final_version = get_application_version(args.version)

    # Khởi tạo và chạy ứng dụng với phiên bản đã xác định
    app = Application(version=final_version)
    app.run()
