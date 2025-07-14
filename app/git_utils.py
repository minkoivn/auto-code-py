import subprocess
import logging
import os
from git_exceptions import GitCommandError, GitCommandNotFoundError, NotAGitRepositoryError

logger = logging.getLogger(__name__)

def _run_git_command(command_args, cwd=None):
    """Thực thi một lệnh Git và trả về (success, stdout, stderr)."""
    try:
        process = subprocess.run(
            ['git'] + command_args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            encoding='utf-8',
            errors='replace'
        )
        if process.returncode != 0:
            return False, process.stdout.strip(), process.stderr.strip()
        return True, process.stdout.strip(), process.stderr.strip()
    except FileNotFoundError:
        return False, "", "Lệnh 'git' không tìm thấy."
    except Exception as e:
        return False, "", str(e)

class GitAgent:
    """Một lớp để đóng gói các thao tác Git."""
    def __init__(self, repo_path="."):
        self.repo_path = repo_path
        if not os.path.isdir(os.path.join(repo_path, '.git')):
            raise NotAGitRepositoryError(path=repo_path)

    def add_and_commit(self, filepath, message):
        """Thêm một file và commit thay đổi."""
        # Add file
        success, _, stderr = _run_git_command(['add', filepath], cwd=self.repo_path)
        if not success:
            raise GitCommandError(['add', filepath], "", stderr, 1, f"Thêm file thất bại: {filepath}")

        # Commit
        success, _, stderr = _run_git_command(['commit', '-m', message], cwd=self.repo_path)
        if not success:
            # Nếu commit thất bại (ví dụ: không có gì để commit), có thể không phải lỗi nghiêm trọng
            if "nothing to commit" in stderr:
                logger.warning(f"Không có gì để commit cho file: {filepath}")
                return # Coi như thành công nếu không có gì thay đổi
            raise GitCommandError(['commit', '-m', message], "", stderr, 1, f"Commit thất bại: {message}")
        
        logger.info(f"Đã commit thành công file '{filepath}' với thông điệp: '{message}'")


def git_log_last_n_commits(n=10, repo_path=None):
    """Truy xuất N thông báo commit cuối cùng."""
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

# Các hàm git khác có thể giữ nguyên hoặc chuyển vào lớp GitAgent nếu cần