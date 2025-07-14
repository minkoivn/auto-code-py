import subprocess
import logging

logger = logging.getLogger(__name__)

class GitCommandError(Exception):
    """Custom exception for Git command errors."""
    def __init__(self, message, returncode, stdout, stderr):
        super().__init__(message)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

class Git:
    def __init__(self, repo_path="."):
        self.repo_path = repo_path

    def _run_git_command(self, command_args):
        """
        Runs a git command with robust error handling and logging.
        Returns stdout if successful.
        Raises GitCommandError on non-zero exit code or other issues.
        """
        full_command = ["git"] + command_args
        logger.debug(f"Executing Git command: {' '.join(full_command)}")
        try:
            process = subprocess.run(
                full_command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False # Do not raise CalledProcessError automatically
            )
            stdout = process.stdout.strip()
            stderr = process.stderr.strip()
            returncode = process.returncode

            if returncode != 0:
                error_message = (
                    f"Git command failed: {' '.join(full_command)}\n"
                    f"Return Code: {returncode}\n"
                    f"STDOUT:\n{stdout}\n"
                    f"STDERR:\n{stderr}"
                )
                logger.error(error_message)
                raise GitCommandError(error_message, returncode, stdout, stderr)
            else:
                logger.info(f"Git command successful: {' '.join(full_command)}")
                if stdout:
                    logger.debug(f"Git command stdout:\n{stdout}")
                if stderr: # stderr might contain warnings even on success
                    logger.warning(f"Git command stderr (if any):\n{stderr}")
            return stdout
        except FileNotFoundError:
            error_message = "Git executable not found. Please ensure Git is installed and in your PATH."
            logger.critical(error_message)
            raise GitCommandError(error_message, -1, "", "Git not found")
        except Exception as e:
            error_message = f"An unexpected error occurred while running git command: {e}"
            logger.critical(error_message)
            raise GitCommandError(error_message, -1, "", str(e))

    def get_status(self):
        """
        Executes 'git status' and returns the status output.
        """
        logger.info("Getting current Git repository status...")
        try:
            status_output = self._run_git_command(["status"])
            logger.debug(f"Git status output:\n{status_output}")
            return status_output
        except GitCommandError as e:
            logger.error(f"Failed to get Git status: {e.stderr}")
            raise # Re-raise the specific GitCommandError
        except Exception as e:
            logger.error(f"An unexpected error occurred while getting Git status: {e}")
            raise # Re-raise other unexpected exceptions
