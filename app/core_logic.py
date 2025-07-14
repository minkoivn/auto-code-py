import logging
import time
import random
from config import APPLICATION_NAME

def _process_single_task(task_id: int, total_tasks: int, version: int) -> None:
    """
    Mô phỏng việc xử lý một tác vụ duy nhất.
    Đây là nơi logic nghiệp vụ chi tiết cho từng tác vụ sẽ được đặt.
    Thêm một độ trễ nhỏ để mô phỏng công việc đang được thực hiện.
    Đã được cải tiến để mô phỏng các tình huống khác nhau (thành công/thất bại, thời gian khác nhau).
    """
    logging.debug(f"Đang xử lý tác vụ {task_id}/{total_tasks} cho phiên bản {version} của {APPLICATION_NAME}...")

    # Mô phỏng các loại tác vụ hoặc kết quả khác nhau
    sleep_time = 0.01 # Thời gian ngủ mặc định
    status_message = "hoàn thành bình thường."
    
    if task_id % 5 == 0: # Mỗi tác vụ thứ 5 là "quan trọng" hoặc "dài"
        sleep_time = 0.05
        status_message = "là tác vụ quan trọng, có thể mất nhiều thời gian hơn."
    elif task_id % 3 == 0: # Mỗi tác vụ thứ 3 "thất bại" đôi khi
        if random.random() < 0.2: # 20% khả năng thất bại
            logging.error(f"  XXX Tác vụ {task_id} (phiên bản {version}) đã thất bại một cách mô phỏng!")
            # Trong một ứng dụng thực tế, điều này có thể ném ra một ngoại lệ hoặc trả về một trạng thái
            return 
        else:
            status_message = "thành công (sau khi có khả năng thất bại)."
    
    logging.debug(f"  --> Tác vụ {task_id} (phiên bản {version}) {status_message}")
    time.sleep(sleep_time) # Mô phỏng công việc

def run_application_core_logic(version: int) -> None:
    """
    Thực thi logic cốt lõi của ứng dụng dựa trên phiên bản được cung cấp.
    Đây là nơi công việc chính của ứng dụng sẽ được thực hiện.
    Hiện tại, nó mô phỏng việc xử lý các tác vụ.
    """
    logging.info("Thực thi logic cốt lõi của ứng dụng...")
    
    # Mô phỏng số lượng tác vụ cần xử lý dựa trên phiên bản
    num_tasks = version * 5 
    logging.info(f"Mô phỏng xử lý {num_tasks} tác vụ cho phiên bản {version} của {APPLICATION_NAME}.")
    
    for i in range(1, num_tasks + 1):
        _process_single_task(i, num_tasks, version)
    
    logging.info("Logic cốt lõi đã hoàn thành.")