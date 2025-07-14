# app/git_utils.py

import subprocess
from logging_setup import logger # Import the logger

# Custom exception for Git command failures
class GitCommandError(Exception):
    """Exception raised for errors during Git command execution."""
    def __init__(self, message, command=None, returncode=None, stdout=None, stderr=None):
        super().__init__(message)
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

def _execute_git_command(command: list, description: str):
    """
    Execute a Git command and handle errors structurally.
    
    Args:
        command (list): The Git command and its arguments as a list.
        description (str): A description of the operation being performed, for logging.
    
    Raises:
        GitCommandError: If the Git command fails.
    """
    logger.info(f"🚀 [Git] Đang thực thi lệnh: {' '.join(command)} ({description})...")
    try:
        # check=True raises CalledProcessError on non-zero exit code
        # capture_output=True captures stdout and stderr
        # text=True and encoding='utf-8' ensure stdout/stderr are strings
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        logger.info(f"✅ [Git] Lệnh '{' '.join(command)}' thành công.")
        # Log stdout/stderr only if they contain something for successful commands
        if result.stdout.strip():
            logger.debug(f"Stdout: {result.stdout.strip()}")
        if result.stderr.strip():
            logger.debug(f"Stderr: {result.stderr.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        error_msg = f"Lỗi khi thực thi lệnh Git '{' '.join(e.cmd)}' (Mã thoát: {e.returncode})."
        # Always log stdout/stderr for failed commands
        if e.stdout:
            logger.error(f"Stdout:\n{e.stdout.strip()}")
        if e.stderr:
            logger.error(f"Stderr:\n{e.stderr.strip()}")
        logger.error(f"❌ [Git] {error_msg}", exc_info=False) # exc_info=False because we're providing details manually
        raise GitCommandError(
            message=error_msg,
            command=e.cmd,
            returncode=e.returncode,
            stdout=e.stdout,
            stderr=e.stderr
        ) from e
    except FileNotFoundError as e:
        # This handles cases where 'git' command itself is not found (e.g., Git not installed/in PATH)
        error_msg = f"Lỗi: Lệnh 'git' không tìm thấy. Hãy đảm bảo Git đã được cài đặt và có trong PATH."
        logger.critical(f"❌ [Git] {error_msg}", exc_info=True)
        raise GitCommandError(
            message=error_msg,
            command=command
        ) from e
    except Exception as e:
        # Catch any other unexpected errors during subprocess execution
        error_msg = f"Lỗi không xác định khi thực thi lệnh Git '{' '.join(command)}': {e}"
        logger.critical(f"❌ [Git] {error_msg}", exc_info=True)
        raise GitCommandError(
            message=error_msg,
            command=command
        ) from e

def add_and_commit(filepath: str, commit_message: str):
    """
    Thêm file vào staging area của Git và tạo một commit với thông báo đã cho.
    Hàm này sẽ raise GitCommandError nếu bất kỳ lệnh Git nào thất bại.
    """
    try:
        logger.info(f"🚀 [Git] Đang thêm file {filepath} vào staging...")
        _execute_git_command(["git", "add", filepath], f"thêm file {filepath} vào staging")
        
        logger.info(f"🚀 [Git] Đang tạo commit với thông báo: '{commit_message}'")
        _execute_git_command(["git", "commit", "-m", commit_message], f"tạo commit với thông báo: '{commit_message}'")
        logger.info(f"✅ [Git] Đã tạo commit thành công.")
        
    except GitCommandError:
        # Re-raise the specific GitCommandError directly, as _execute_git_command already logs and formats
        raise 
    except Exception as e:
        # Catch any other unexpected errors that might occur outside of _execute_git_command calls
        error_message = f"Lỗi bất ngờ trong quá trình add/commit file '{filepath}': {e}"
        logger.critical(error_message, exc_info=True)
        # Wrap any other unexpected errors into a GitCommandError for consistency
        raise GitCommandError(error_message) from e
