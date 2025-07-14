import logging
import sys
from utils import setup_logging, get_application_version, parse_cli_arguments
from config import APPLICATION_NAME


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
        logging.info("Ứng dụng đã bắt đầu chạy")
        logging.info(f"Hello from {APPLICATION_NAME} - Version {self.version}")
        logging.info("Ứng dụng đã chạy xong")


def main() -> None:
    """
    Điểm vào chính của ứng dụng.
    Xử lý phân tích đối số, cấu hình logging, lấy phiên bản và chạy ứng dụng.
    """
    # Phân tích các đối số dòng lệnh để lấy cấu hình ban đầu
    args = parse_cli_arguments()

    # Cấu hình logging với cấp độ từ dòng lệnh
    setup_logging(args.log_level)

    # Lấy phiên bản cuối cùng sau khi xem xét tất cả các nguồn
    final_version = get_application_version(args.version)

    # Khởi tạo và chạy ứng dụng với phiên bản đã xác định
    app = Application(version=final_version)
    app.run()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Ghi log lỗi nghiêm trọng và thoát với mã lỗi
        logging.critical(f"Lỗi nghiêm trọng không mong muốn xảy ra trong quá trình khởi tạo hoặc chạy: {e}", exc_info=True)
        sys.exit(1)
