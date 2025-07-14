import logging
import os
from dotenv import load_dotenv

# Gọi load_dotenv() sớm nhất có thể để đảm bảo tất cả các biến môi trường
# được tải trước khi bất kỳ module nào khác phụ thuộc vào chúng được khởi tạo.
load_dotenv()

# Giả định config.py tồn tại và định nghĩa APP_LOG_FILE_PATH và LOG_LEVEL
# dựa trên lịch sử commit gần đây.
from config import APP_LOG_FILE_PATH, LOG_LEVEL
from orchestrator import Orchestrator # Giả định orchestrator là một thành phần cốt lõi

# Định cấu hình logging sử dụng các cài đặt từ config hoặc biến môi trường
log_level = os.getenv('LOG_LEVEL', LOG_LEVEL).upper()

# Đảm bảo thư mục cho tệp log tồn tại
log_dir = os.path.dirname(APP_LOG_FILE_PATH)
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(level=log_level,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(APP_LOG_FILE_PATH),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Ứng dụng đang khởi động...")
    try:
        # Khởi tạo Orchestrator (thành phần chính của AI Z)
        # Orchestrator này sẽ xử lý các tương tác,
        # gọi AI Z và có khả năng gọi AI X.
        orchestrator = Orchestrator()

        # Đây là nơi logic để khởi động máy chủ web hoặc vòng lặp chính sẽ được đặt.
        # Mô tả dự án đề cập đến "trang web tương tác với người dùng ở localhost:3000"
        # và "chạy liên tục như web".
        # Trong một ứng dụng thực tế, điều này có thể là 'app.run()' nếu sử dụng Flask,
        # hoặc một lời gọi tương tự cho framework web được sử dụng.
        logger.info("Hệ thống AI đã được khởi tạo. Sẵn sàng tương tác với giao diện web tại localhost:3000.")
        
        # Ví dụ: nếu đây là ứng dụng Flask, bạn có thể có:
        # from app import app
        # app.run(debug=True, port=3000)
        
        # Để đơn giản trong ví dụ này, chúng ta chỉ ghi log và đợi.
        # Trong thực tế, sẽ có một vòng lặp sự kiện hoặc server chạy ở đây.
        pass

    except Exception as e:
        logger.error(f"Một lỗi không mong muốn đã xảy ra trong quá trình khởi động ứng dụng: {e}", exc_info=True)
        # Có thể tùy chọn re-raise hoặc thoát với mã lỗi
        # import sys
        # sys.exit(1)
