# app/git_utils.py

import subprocess

def add_and_commit(filepath: str, commit_message: str):
    """
    Thêm file vào staging area của Git và tạo một commit với thông báo đã cho.
    Hàm này sẽ raise lỗi nếu bất kỳ lệnh Git nào thất bại.
    """
    try:
        print(f"🚀 [Git] Đang thêm file {filepath} vào staging...")
        subprocess.run(["git", "add", filepath], check=True)
        
        print(f"🚀 [Git] Đang tạo commit với thông báo: '{commit_message}'")
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        print(f"✅ [Git] Đã tạo commit thành công.")
        
    except subprocess.CalledProcessError as e:
        # Bắt các lỗi cụ thể từ lệnh Git và cung cấp thông báo chi tiết hơn
        if e.cmd[1] == "add":
            raise RuntimeError(f"Lỗi khi thêm file '{filepath}' vào Git: {e}") from e
        elif e.cmd[1] == "commit":
            raise RuntimeError(f"Lỗi khi tạo commit: {e}") from e
        else:
            raise RuntimeError(f"Lỗi không xác định khi thực thi lệnh Git: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Lỗi bất ngờ khi thực thi thao tác Git: {e}") from e
