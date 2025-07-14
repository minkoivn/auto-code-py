# app/git_utils.py

import subprocess
from logging_setup import logger # Import the logger

def add_and_commit(filepath: str, commit_message: str):
    """
    Thêm file vào staging area của Git và tạo một commit với thông báo đã cho.
    Hàm này sẽ raise lỗi nếu bất kỳ lệnh Git nào thất bại.
    """
    try:
        logger.info(f"🚀 [Git] Đang thêm file {filepath} vào staging...")
        subprocess.run(["git", "add", filepath], check=True)
        
        logger.info(f"🚀 [Git] Đang tạo commit với thông báo: '{commit_message}'")
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        logger.info(f"✅ [Git] Đã tạo commit thành công.")
        
    except subprocess.CalledProcessError as e:
        # Bắt các lỗi cụ thể từ lệnh Git và cung cấp thông báo chi tiết hơn
        if e.cmd[1] == "add":
            error_message = f"Lỗi khi thêm file '{filepath}' vào Git: {e}"
            logger.error(error_message, exc_info=True)
            raise RuntimeError(error_message) from e
        elif e.cmd[1] == "commit":
            error_message = f"Lỗi khi tạo commit: {e}"
            logger.error(error_message, exc_info=True)
            raise RuntimeError(error_message) from e
        else:
            error_message = f"Lỗi không xác định khi thực thi lệnh Git: {e}"
            logger.error(error_message, exc_info=True)
            raise RuntimeError(error_message) from e
    except Exception as e:
        error_message = f"Lỗi bất ngờ khi thực thi thao tác Git: {e}"
        logger.critical(error_message, exc_info=True)
        raise RuntimeError(error_message) from e
