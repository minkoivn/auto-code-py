import subprocess
import logging
import os

logger = logging.getLogger(__name__)

def _run_git_command(command_args, cwd=None):
    """
    Thực thi một lệnh Git và xử lý đầu ra cũng như lỗi một cách duyên dáng.

    Args:
        command_args (list): Một danh sách các chuỗi đại diện cho lệnh Git và các đối số của nó.
                             Ví dụ: ['add', '.']
        cwd (str, optional): Thư mục làm việc hiện tại cho lệnh. Mặc định là None (thư mục làm việc của tiến trình hiện tại).

    Returns:
        tuple: (success (bool), stdout (str), stderr (str))
    """
    full_command = ['git'] + command_args
    command_str = ' '.join(full_command)
    cwd_info = f" trong thư mục '{cwd}'" if cwd else ""

    logger.debug(f"Đang thực thi lệnh Git: {command_str}{cwd_info}")

    try:
        process = subprocess.run(
            full_command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False, # Chúng ta xử lý mã trả về thủ công
            encoding='utf-8', # Đảm bảo mã hóa đúng cho đầu ra
            errors='replace' # Thay thế các ký tự không thể giải mã
        )

        stdout = process.stdout.strip()
        stderr = process.stderr.strip()

        if process.returncode != 0:
            log_message = f"Lệnh Git THẤT BẠI (Mã trả về: {process.returncode}): {command_str}{cwd_info}"
            logger.error(log_message)
            if stdout:
                logger.error(f"STDOUT:\n{stdout}")
            if stderr:
                logger.error(f"STDERR:\n{stderr}")
            return False, stdout, stderr
        else:
            logger.info(f"Lệnh Git THÀNH CÔNG: {command_str}{cwd_info}")
            if stdout:
                logger.debug(f"STDOUT:\n{stdout}")
            if stderr: # Thường trống khi thành công, nhưng tốt cho việc gỡ lỗi
                logger.debug(f"STDERR:\n{stderr}")
            return True, stdout, stderr

    except FileNotFoundError:
        logger.error(f"Không tìm thấy tệp thực thi Git. Vui lòng đảm bảo Git đã được cài đặt và có trong PATH của hệ thống.")
        return False, "", "Không tìm thấy tệp thực thi Git."
    except subprocess.CalledProcessError as e:
        # Điều này không nên xảy ra nếu check=False, nhưng là một phương án dự phòng
        logger.error(f"Lệnh Git thất bại với CalledProcessError: {command_str}{cwd_info}")
        logger.error(f"Mã trả về: {e.returncode}, Đầu ra: {e.output}, Lỗi chuẩn: {e.stderr}")
        return False, e.stdout, e.stderr
    except Exception as e:
        logger.error(f"Đã xảy ra lỗi không mong muốn khi thực thi lệnh Git '{command_str}': {e}", exc_info=True)
        return False, "", str(e)


# --- Các hàm tiện ích Git đã được tái cấu trúc ---

def git_add(filepath, repo_path=None):
    """Thêm tệp vào khu vực dàn dựng Git."""
    success, stdout, stderr = _run_git_command(['add', filepath], cwd=repo_path)
    if not success:
        logger.error(f"Không thể thêm '{filepath}'. Lỗi: {stderr}")
    return success

def git_commit(message, repo_path=None):
    """Cam kết các thay đổi vào kho lưu trữ Git."""
    success, stdout, stderr = _run_git_command(['commit', '-m', message], cwd=repo_path)
    if not success:
        logger.error(f"Không thể cam kết với thông báo: '{message}'. Lỗi: {stderr}")
    return success

def git_checkout(branch_name, create_new=False, repo_path=None):
    """
    Kiểm tra một nhánh Git.
    Nếu create_new là True, tạo một nhánh mới.
    """
    command = ['checkout']
    if create_new:
        command.append('-b')
    command.append(branch_name)

    success, stdout, stderr = _run_git_command(command, cwd=repo_path)
    if not success:
        logger.error(f"Không thể kiểm tra nhánh '{branch_name}'. Lỗi: {stderr}")
    return success

def git_pull(branch_name=None, repo_path=None):
    """Kéo các thay đổi từ kho lưu trữ từ xa."""
    command = ['pull']
    if branch_name:
        # Giả sử remote là origin
        command.extend(['origin', branch_name])
    success, stdout, stderr = _run_git_command(command, cwd=repo_path)
    if not success:
        logger.error(f"Không thể kéo các thay đổi. Lỗi: {stderr}")
    return success

def git_push(branch_name=None, repo_path=None, force=False):
    """Đẩy các thay đổi lên kho lưu trữ từ xa."""
    command = ['push']
    if force:
        command.append('--force')
    if branch_name:
        command.extend(['origin', branch_name]) # Giả sử remote là origin
    success, stdout, stderr = _run_git_command(command, cwd=repo_path)
    if not success:
        logger.error(f"Không thể đẩy các thay đổi. Lỗi: {stderr}")
    return success

def git_stash_push(message=None, repo_path=None):
    """Lưu trữ các thay đổi hiện tại."""
    command = ['stash', 'push']
    if message:
        command.extend(['-m', message])
    success, stdout, stderr = _run_git_command(command, cwd=repo_path)
    if not success:
        logger.error(f"Không thể lưu trữ các thay đổi. Lỗi: {stderr}")
    return success

def git_stash_pop(repo_path=None):
    """Áp dụng các thay đổi được lưu trữ gần đây nhất và xóa nó khỏi danh sách lưu trữ."""
    success, stdout, stderr = _run_git_command(['stash', 'pop'], cwd=repo_path)
    if not success:
        logger.error(f"Không thể khôi phục stash. Lỗi: {stderr}")
    return success

def get_current_branch(repo_path=None):
    """Lấy tên của nhánh Git hiện tại."""
    success, stdout, stderr = _run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'], cwd=repo_path)
    if success:
        return stdout.strip()
    else:
        logger.error(f"Không thể lấy nhánh hiện tại. Lỗi: {stderr}")
        return None

def git_reset_hard(commit_hash, repo_path=None):
    """Đặt lại kho lưu trữ về một commit cụ thể, loại bỏ tất cả các thay đổi chưa được commit."""
    success, stdout, stderr = _run_git_command(['reset', '--hard', commit_hash], cwd=repo_path)
    if not success:
        logger.error(f"Không thể hard reset về {commit_hash}. Lỗi: {stderr}")
    return success

def git_status(repo_path=None):
    """Lấy trạng thái hiện tại của kho lưu trữ Git."""
    success, stdout, stderr = _run_git_command(['status', '--porcelain'], cwd=repo_path)
    if success:
        return stdout.strip()
    else:
        logger.error(f"Không thể lấy trạng thái git. Lỗi: {stderr}")
        return None

def git_log_last_n_commits(n=10, repo_path=None):
    """Truy xuất N thông báo commit cuối cùng."""
    # Sử dụng --pretty=format:%s cho chỉ chủ đề, hoặc %B cho toàn bộ nội dung. %H cho hash.
    # Hiện tại, hãy lấy hash và chủ đề
    command = ['log', f'-n{n}', '--pretty=format:%H %s']
    success, stdout, stderr = _run_git_command(command, cwd=repo_path)
    if success:
        commits = []
        for line in stdout.strip().split('\n'):
            if line:
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    commits.append({"hash": parts[0], "message": parts[1]})
        return commits
    else:
        logger.error(f"Không thể lấy {n} commit cuối cùng. Lỗi: {stderr}")
        return []

def git_diff(repo_path=None):
    """Lấy sự khác biệt của các thay đổi chưa được commit."""
    success, stdout, stderr = _run_git_command(['diff'], cwd=repo_path)
    if success:
        return stdout.strip()
    else:
        logger.error(f"Không thể lấy git diff. Lỗi: {stderr}")
        return None
