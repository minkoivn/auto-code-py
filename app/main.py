import logging
import sys
from utils import prepare_application_startup
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

    def _execute_core_logic(self) -> None:
        """
        Phương thức giữ chỗ cho logic cốt lõi thực tế của ứng dụng.
        Đây là nơi công việc chính của ứng dụng sẽ được thực hiện.
        Hiện tại, nó mô phỏng việc xử lý các tác vụ.
        """
        logging.info("Thực thi logic cốt lõi của ứng dụng...")
        
        # Mô phỏng số lượng tác vụ cần xử lý dựa trên phiên bản
        num_tasks = self.version * 5 
        logging.info(f"Mô phỏng xử lý {num_tasks} tác vụ cho phiên bản {self.version} của {APPLICATION_NAME}.")
        
        for i in range(1, num_tasks + 1):
            logging.debug(f"Đang xử lý tác vụ {i}/{num_tasks}...")
            # Trong một ứng dụng thực tế, đây sẽ là nơi thực hiện công việc cụ thể
            # Ví dụ: gọi API, xử lý dữ liệu, ghi vào cơ sở dữ liệu, v.v.
        
        logging.info("Logic cốt lõi đã hoàn thành.")

    def run(self) -> None:
        """
        Đây là hàm chính của ứng dụng.
        Hiện tại nó chỉ in ra một thông điệp.
        """
        logging.info("Ứng dụng đã bắt đầu chạy")
        logging.info(f"Hello from {APPLICATION_NAME} - Version {self.version}")
        
        # Gọi phương thức giữ chỗ cho logic cốt lõi
        self._execute_core_logic()
        
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
