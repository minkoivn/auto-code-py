import logging
import sys
from utils import prepare_application_startup
from config import APPLICATION_NAME
from core_logic import run_application_core_logic


def main() -> None:
    """
    Điểm vào chính của ứng dụng.
    Xử lý phân tích đối số, cấu hình logging, lấy phiên bản và chạy ứng dụng.
    """
    # Thực hiện các bước khởi tạo ứng dụng và lấy phiên bản cuối cùng
    final_version = prepare_application_startup()

    logging.info("Ứng dụng đã bắt đầu chạy")
    logging.info(f"Hello from {APPLICATION_NAME} - Version {final_version}")
    
    # Trực tiếp gọi hàm logic cốt lõi sau khi khởi tạo
    run_application_core_logic(final_version)
    
    logging.info("Ứng dụng đã chạy xong")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Ghi log lỗi nghiêm trọng và thoát với mã lỗi
        logging.critical(f"Lỗi nghiêm trọng không mong muốn xảy ra trong quá trình khởi tạo hoặc chạy: {e}", exc_info=True)
        sys.exit(1)
