import logging
import time
import random
from runtime_config import RuntimeConfig # Nhập module RuntimeConfig

def _process_single_task(
    task_id: int, 
    total_tasks: int, 
    version: int, 
    failure_chance: float, 
    long_task_divisor: int,
    application_name: str # Thêm tham số tên ứng dụng
) -> str:
    """
    Mô phỏng việc xử lý một tác vụ duy nhất và trả về trạng thái của nó.
    Đây là nơi logic nghiệp vụ chi tiết cho từng tác vụ sẽ được đặt.
    Thêm một độ trễ nhỏ để mô phỏng công việc đang được thực hiện.
    Đã được cải tiến để mô phỏng các tình huống khác nhau (thành công/thất bại, thời gian khác nhau).
    Trả về "SUCCESS" hoặc "FAILURE".
    
    Tham số:
        task_id (int): ID của tác vụ hiện tại.
        total_tasks (int): Tổng số tác vụ cần xử lý.
        version (int): Phiên bản ứng dụng.
        failure_chance (float): Xác suất (từ 0.0 đến 1.0) để một tác vụ ngẫu nhiên thất bại.
        long_task_divisor (int): Số nguyên dùng để xác định các tác vụ 'dài' (ví dụ: nếu 5, mỗi tác vụ thứ 5 là dài).
        application_name (str): Tên của ứng dụng.
    """
    logging.debug(f"Đang xử lý tác vụ {task_id}/{total_tasks} cho phiên bản {version} của {application_name}...")

    # Mô phỏng các loại tác vụ hoặc kết quả khác nhau
    sleep_time = 0.01 # Thời gian ngủ mặc định
    status_message = "hoàn thành bình thường."
    result = "SUCCESS" # Mặc định là thành công
    
    # Sử dụng long_task_divisor để xác định tác vụ dài
    if long_task_divisor > 0 and task_id % long_task_divisor == 0: 
        sleep_time = 0.05
        status_message = "là tác vụ quan trọng, có thể mất nhiều thời gian hơn."
    # Sử dụng failure_chance để mô phỏng lỗi
    elif task_id % 3 == 0: # Mỗi tác vụ thứ 3 có thể thất bại
        if random.random() < failure_chance: # 'failure_chance' khả năng thất bại
            logging.error(f"  XXX Tác vụ {task_id} (phiên bản {version}) đã thất bại một cách mô phỏng!")
            result = "FAILURE" # Đánh dấu là thất bại
            # Trong một ứng dụng thực tế, điều này có thể ném ra một ngoại lệ hoặc trả về một trạng thái
            # Chúng ta sẽ không sleep nếu nó thất bại ngay lập tức để tiết kiệm thời gian mô phỏng
            logging.debug(f"  --> Tác vụ {task_id} (phiên bản {version}) đã thất bại mô phỏng, không chờ.")
            return result
        else:
            status_message = "thành công (sau khi có khả năng thất bại)."
    
    logging.debug(f"  --> Tác vụ {task_id} (phiên bản {version}) {status_message}")
    time.sleep(sleep_time) # Mô phỏng công việc
    return result

def run_application_core_logic(runtime_config: RuntimeConfig) -> None:
    """
    Thực thi logic cốt lõi của ứng dụng dựa trên đối tượng RuntimeConfig được cung cấp.
    Đây là nơi công việc chính của ứng dụng sẽ được thực hiện.
    Hiện tại, nó mô phỏng việc xử lý các tác vụ và tổng hợp kết quả.
    Đã được tái cấu trúc để sử dụng RuntimeConfig duy nhất cho tất cả các thông số.
    """
    logging.info("Thực thi logic cốt lõi của ứng dụng...")
    
    # Lấy thông tin từ đối tượng runtime_config
    version = runtime_config.application_version
    application_name = runtime_config.application_name
    failure_chance = runtime_config.failure_chance
    long_task_divisor = runtime_config.long_task_divisor

    # Mô phỏng số lượng tác vụ cần xử lý dựa trên phiên bản
    num_tasks = version * 5 
    logging.info(f"Mô phỏng xử lý {num_tasks} tác vụ cho phiên bản {version} của {application_name}.")
    
    successful_tasks = 0
    failed_tasks = 0

    logging.info(f"Sử dụng cấu hình mô phỏng: Tỉ lệ lỗi = {failure_chance}, Bộ chia tác vụ dài = {long_task_divisor}")

    for i in range(1, num_tasks + 1):
        task_result = _process_single_task(
            i, 
            num_tasks, 
            version, 
            failure_chance, 
            long_task_divisor,
            application_name # Truyền tên ứng dụng
        )
        if task_result == "SUCCESS":
            successful_tasks += 1
        elif task_result == "FAILURE":
            failed_tasks += 1
    
    logging.info("Logic cốt lõi đã hoàn thành.")
    logging.info(f"Tóm tắt kết quả: {successful_tasks} tác vụ thành công, {failed_tasks} tác vụ thất bại trong tổng số {num_tasks}.")
