import logging
import sys
from utils import prepare_application_startup
from config import APPLICATION_NAME
from core_logic import run_application_core_logic


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
        
        # Gọi hàm logic cốt lõi đã được tách riêng
        run_application_core_logic(self.version)
        
        logging.info("Ứng dụng đã chạy xong")


def main() -> None:
    """
    Điểm vào chính của ứng dụng.
    Xử lý phân tích đối số, cấu hình logging, lấy phiên bản và chạy ứng dụng.
    """
    # Hàm prepare_application_startup đã được di chuyển sang utils.py
    # và tập trung hóa logic khởi tạo.
    final_version = prepare_application_startup()

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
