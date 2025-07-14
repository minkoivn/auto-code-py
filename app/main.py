# app/main.py (Đã nâng cấp để tự sửa lỗi)
import os
import subprocess
import time
import hashlib
import shutil
import logging
from pathlib import Path

# --- Cấu hình ---
APP_FILE = Path("app/application.py")
VERSIONS_DIR = Path("app/versions")
LOGS_DIR = Path("app/logs")
LOG_FILE = LOGS_DIR / "supervisor.log"
PYTHON_EXECUTABLE = "python"  # Hoặc "python3"
MAX_FIX_ATTEMPTS = 3 # Giới hạn số lần thử sửa lỗi liên tiếp

# --- Thiết lập Logging ---
LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# --- Import orchestrator để có thể gọi AI sửa lỗi ---
# Chúng ta import ở đây vì main là cấp cao nhất, sẽ không gây lỗi circular import
from orchestrator import trigger_self_correction

def get_file_hash(filepath: Path) -> str:
    """Tính toán hash SHA-256 của một tệp."""
    if not filepath.exists():
        return ""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def backup_working_version(source: Path):
    """Sao lưu phiên bản đang hoạt động vào thư mục versions."""
    VERSIONS_DIR.mkdir(exist_ok=True)
    backup_path = VERSIONS_DIR / f"{source.name}.{int(time.time())}.bak"
    try:
        shutil.copy(source, backup_path)
        logging.info(f"Đã sao lưu phiên bản hoạt động tới: {backup_path}")
        return backup_path
    except Exception as e:
        logging.error(f"Sao lưu thất bại: {e}")
        return None

def restore_last_working_version(target: Path) -> bool:
    """Phục hồi phiên bản hoạt động cuối cùng từ thư mục versions."""
    try:
        backups = sorted(VERSIONS_DIR.glob(f"{target.name}.*.bak"), key=os.path.getmtime, reverse=True)
        if not backups:
            logging.error("Không tìm thấy phiên bản sao lưu nào để phục hồi.")
            return False
        
        latest_backup = backups[0]
        shutil.copy(latest_backup, target)
        logging.warning(f"Đã phục hồi tệp '{target}' từ bản sao lưu '{latest_backup}'.")
        return True
    except Exception as e:
        logging.error(f"Phục hồi thất bại: {e}")
        return False

def main():
    """Hàm chính giám sát và chạy ứng dụng với khả năng tự sửa lỗi."""
    process = None
    last_hash = get_file_hash(APP_FILE)
    fix_attempts = 0
    
    if last_hash:
        backup_working_version(APP_FILE)

    while True:
        try:
            # Khởi chạy hoặc khởi động lại tiến trình
            if process is None or process.poll() is not None:
                # Nếu tiến trình đã từng chạy và bị lỗi
                if process and process.poll() is not None and process.poll() != 0:
                    error_output = process.stderr.read() if process.stderr else "Không thể đọc lỗi từ stderr."
                    logging.error(f"'{APP_FILE}' đã thoát với mã lỗi {process.poll()}. Lỗi: {error_output}")

                    if fix_attempts < MAX_FIX_ATTEMPTS:
                        fix_attempts += 1
                        logging.warning(f"Bắt đầu quá trình tự sửa lỗi (Lần {fix_attempts}/{MAX_FIX_ATTEMPTS})...")
                        # Gọi AI để sửa lỗi
                        trigger_self_correction(error_output)
                        # Hash sẽ thay đổi và vòng lặp tiếp theo sẽ xử lý khởi động lại
                        time.sleep(1) # Chờ một chút để file được ghi
                        last_hash = get_file_hash(APP_FILE)
                    else:
                        logging.critical(f"Đã đạt giới hạn {MAX_FIX_ATTEMPTS} lần sửa lỗi. Đang phục hồi phiên bản ổn định cuối cùng.")
                        if restore_last_working_version(APP_FILE):
                            last_hash = get_file_hash(APP_FILE)
                            fix_attempts = 0 # Reset bộ đếm
                        else:
                            logging.critical("Không thể phục hồi. Hệ thống tạm dừng.")
                            break
                
                logging.info(f"Đang khởi chạy '{APP_FILE}'...")
                # Mở tiến trình với stderr=subprocess.PIPE để bắt lỗi
                process = subprocess.Popen([PYTHON_EXECUTABLE, str(APP_FILE)], stderr=subprocess.PIPE, text=True, encoding='utf-8')
                logging.info(f"'{APP_FILE}' đã được khởi chạy với PID: {process.pid}.")
                time.sleep(2)

                # Nếu sau khi khởi động mà nó vẫn chạy tốt, reset bộ đếm lỗi
                if process.poll() is None:
                    fix_attempts = 0

            # Giám sát thay đổi tệp
            current_hash = get_file_hash(APP_FILE)
            if current_hash != last_hash:
                logging.warning(f"Phát hiện thay đổi trong '{APP_FILE}'. Đang khởi động lại...")
                
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                logging.info("Tiến trình cũ đã được dừng.")

                backup_working_version(APP_FILE)
                last_hash = current_hash
                process = None
                continue

            time.sleep(3)

        except KeyboardInterrupt:
            logging.info("Phát hiện Ctrl+C. Đang tắt hệ thống...")
            if process and process.poll() is None:
                process.terminate()
            break
        except Exception as e:
            logging.critical(f"Lỗi nghiêm trọng trong vòng lặp giám sát: {e}", exc_info=True)
            break

if __name__ == "__main__":
    main()