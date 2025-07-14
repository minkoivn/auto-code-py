# app/git_utils.py

import subprocess
import os
from logging_setup import logger

# Custom exception for Git command failures
class GitCommandError(Exception):
    """Exception raised for errors during Git command execution."""
    def __init__(self, message, command=None, returncode=None, stdout=None, stderr=None):
        super().__init__(message)
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

class GitAgent:
    """
    A class to encapsulate Git operations for the AI Agent.
    """
    def __init__(self, repo_path: str = "."):
        """
        Initializes the GitAgent with the path to the Git repository.
        
        Args:
            repo_path (str): The path to the Git repository. Defaults to current directory.
        """
        self.repo_path = os.path.abspath(repo_path) # Normalize path
        
        # Verify if the provided path is a Git repository
        try:
            # Check if .git directory exists for the root of the repo
            # Or if the path is inside a Git work tree
            if not os.path.exists(os.path.join(self.repo_path, '.git')) and \
               not self._is_inside_git_work_tree(self.repo_path):
                raise ValueError(f"'{self.repo_path}' is not a valid Git repository ('.git' folder not found or not inside a work tree).")

            logger.info(f"Initialized GitAgent for repository: {self.repo_path}")
        except GitCommandError as e:
            logger.critical(f"Directory {self.repo_path} is not a valid Git repository or git is not installed. Error: {e.message}", exc_info=True)
            raise ValueError(f"'{self.repo_path}' is not a valid Git repository.") from e
        except Exception as e:
            logger.critical(f"An unexpected error occurred during GitAgent initialization for path {self.repo_path}: {e}", exc_info=True)
            raise ValueError(f"Failed to initialize GitAgent for '{self.repo_path}'.") from e
            
    def _is_inside_git_work_tree(self, path: str) -> bool:
        """Checks if the given path is inside a Git work tree using `git rev-parse --is-inside-work-tree`."""
        try:
            result = self._execute_command(["git", "rev-parse", "--is-inside-work-tree"],
                                           "checking if inside git work tree",
                                           cwd=path, suppress_logging=True)
            return result.stdout.strip() == "true"
        except GitCommandError:
            return False # Command failed, so not inside a git work tree

    def _execute_command(self, command: list, description: str, cwd: str = None, suppress_logging: bool = False):
        """
        Execute a Git command and handle errors structurally.
        
        Args:
            command (list): The Git command and its arguments as a list.
            description (str): A description of the operation being performed, for logging.
            cwd (str, optional): The current working directory for the command. Defaults to None (current process's cwd).
            suppress_logging (bool): If True, suppresses info/debug logging for this command.
        
        Raises:
            GitCommandError: If the Git command fails.
        """
        process_kwargs = {}
        if cwd:
            process_kwargs['cwd'] = cwd
            
        if not suppress_logging:
            logger.info(f"🚀 [Git] Đang thực thi lệnh: {' '.join(command)} ({description})...")
        
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8', **process_kwargs)
            
            if not suppress_logging:
                logger.info(f"✅ [Git] Lệnh '{' '.join(command)}' thành công.")
                if result.stdout.strip():
                    logger.debug(f"Stdout: {result.stdout.strip()}")
                if result.stderr.strip():
                    logger.debug(f"Stderr: {result.stderr.strip()}")
            return result
        except subprocess.CalledProcessError as e:
            error_msg = f"Lỗi khi thực thi lệnh Git '{' '.join(e.cmd)}' (Mã thoát: {e.returncode})."
            if e.stdout:
                logger.error(f"Stdout:\n{e.stdout.strip()}")
            if e.stderr:
                logger.error(f"Stderr:\n{e.stderr.strip()}")
            logger.error(f"❌ [Git] {error_msg}", exc_info=False)
            raise GitCommandError(
                message=error_msg,
                command=e.cmd,
                returncode=e.returncode,
                stdout=e.stdout,
                stderr=e.stderr
            ) from e
        except FileNotFoundError as e:
            error_msg = f"Lỗi: Lệnh 'git' không tìm thấy. Hãy đảm bảo Git đã được cài đặt và có trong PATH."
            logger.critical(f"❌ [Git] {error_msg}", exc_info=True)
            raise GitCommandError(
                message=error_msg,
                command=command
            ) from e
        except Exception as e:
            error_msg = f"Lỗi không xác định khi thực thi lệnh Git '{' '.join(command)}': {e}"
            logger.critical(f"❌ [Git] {error_msg}", exc_info=True)
            raise GitCommandError(
                message=error_msg,
                command=command
            ) from e

    def add_and_commit(self, filepath: str, commit_message: str):
        """
        Thêm file vào staging area của Git và tạo một commit với thông báo đã cho.
        """
        try:
            logger.info(f"🚀 [Git] Đang thêm file {filepath} vào staging...")
            self._execute_command(["git", "add", filepath], f"thêm file {filepath} vào staging", cwd=self.repo_path)
            
            logger.info(f"🚀 [Git] Đang tạo commit với thông báo: '{commit_message}'")
            self._execute_command(["git", "commit", "-m", commit_message], f"tạo commit với thông báo: '{commit_message}'", cwd=self.repo_path)
            logger.info(f"✅ [Git] Đã tạo commit thành công.")
            
        except GitCommandError:
            raise 
        except Exception as e:
            error_message = f"Lỗi bất ngờ trong quá trình add/commit file '{filepath}': {e}"
            logger.critical(error_message, exc_info=True)
            raise GitCommandError(error_message) from e

    def get_status(self) -> dict:
        """
        Báo cáo các thay đổi đang chờ xử lý, tệp chưa được theo dõi và trạng thái kho lưu trữ chung.
        
        Returns:
            dict: A dictionary containing lists of 'staged', 'unstaged', and 'untracked' files.
        """
        logger.info("🚀 [Git] Đang kiểm tra trạng thái kho lưu trữ...")
        try:
            result = self._execute_command(["git", "status", "--porcelain"], "lấy trạng thái Git", cwd=self.repo_path)
            output_lines = result.stdout.strip().split('\n')
            
            staged_files = []
            unstaged_files = []
            untracked_files = []

            # Check if output is empty after stripping, or just contains empty lines
            if not output_lines or (len(output_lines) == 1 and not output_lines[0]):
                logger.info("✅ [Git] Kho lưu trữ sạch, không có thay đổi nào.")
                return {
                    "staged": [],
                    "unstaged": [],
                    "untracked": [],
                    "is_clean": True,
                    "summary": "Kho lưu trữ sạch."
                }

            for line in output_lines:
                if not line:
                    continue

                status_code = line[0:2]
                filepath = line[3:].strip() # Path might contain spaces, need to handle quoted paths

                # Handle quoted paths (e.g., "path with spaces.txt")
                if filepath.startswith('"') and filepath.endswith('"'):
                    filepath = filepath[1:-1]
                
                # Staged (index status) - X in XY
                if status_code[0] in ['A', 'M', 'D', 'R', 'C']:
                    staged_files.append(filepath)
                
                # Unstaged (work tree status) - Y in XY
                # This covers modifications, deletions, etc. that are not yet staged.
                # '??' indicates untracked, handled separately.
                if status_code[1] in ['M', 'D', 'A', 'R', 'C', 'T']:
                    # Only add if there's an actual unstaged change (Y is not space)
                    if status_code[1] != ' ':
                        unstaged_files.append(filepath)

                # Untracked
                if status_code == '??':
                    untracked_files.append(filepath)
            
            # Remove duplicates using set to ensure unique file paths, then convert back to list
            staged_files = list(set(staged_files))
            unstaged_files = list(set(unstaged_files))
            untracked_files = list(set(untracked_files))

            # Generate summary string
            summary_parts = []
            if staged_files:
                summary_parts.append(f"{len(staged_files)} tệp đã được đưa vào staging.")
            if unstaged_files:
                summary_parts.append(f"{len(unstaged_files)} tệp đã thay đổi nhưng chưa được đưa vào staging.")
            if untracked_files:
                summary_parts.append(f"{len(untracked_files)} tệp chưa được theo dõi.")
            
            summary = ", ".join(summary_parts) if summary_parts else "Kho lưu trữ sạch."

            logger.info(f"✅ [Git] Trạng thái kho lưu trữ: {summary}")

            return {
                "staged": staged_files,
                "unstaged": unstaged_files,
                "untracked": untracked_files,
                "is_clean": not (staged_files or unstaged_files or untracked_files),
                "summary": summary
            }

        except GitCommandError:
            raise
        except Exception as e:
            error_message = f"Lỗi không xác định khi lấy trạng thái Git: {e}"
            logger.critical(error_message, exc_info=True)
            raise GitCommandError(error_message) from e

    def _get_diff_summary(self) -> str:
        """
        Generates a summary of pending Git changes (staged and unstaged diffs) using `git diff --stat`.
        This method is private and could be used by other public methods to enrich their output.
        """
        logger.info("🚀 [Git] Đang tạo bản tóm tắt các thay đổi Git đang chờ xử lý...")
        diff_summary_parts = []
        
        # Get unstaged changes (changes in working directory not yet staged)
        unstaged_result = self._execute_command(
            ["git", "diff", "--stat"], 
            "lấy tóm tắt diff của các thay đổi chưa được đưa vào staging", 
            cwd=self.repo_path, 
            suppress_logging=True
        )
        if unstaged_result.stdout.strip():
            diff_summary_parts.append("\n--- Thay đổi CHƯA được đưa vào staging ---\n" + unstaged_result.stdout.strip())

        # Get staged changes (changes in index, ready to be committed)
        staged_result = self._execute_command(
            ["git", "diff", "--cached", "--stat"], 
            "lấy tóm tắt diff của các thay đổi đã được đưa vào staging", 
            cwd=self.repo_path, 
            suppress_logging=True
        )
        if staged_result.stdout.strip():
            diff_summary_parts.append("\n--- Thay đổi ĐÃ được đưa vào staging ---\n" + staged_result.stdout.strip())

        if not diff_summary_parts:
            logger.info("✅ [Git] Không có thay đổi nào đang chờ xử lý để tạo tóm tắt diff.")
            return "Không có thay đổi nào đang chờ xử lý (work tree sạch)."
        
        full_summary = "\n".join(diff_summary_parts)
        logger.info("✅ [Git] Đã tạo tóm tắt diff thành công.")
        return full_summary
