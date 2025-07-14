# git_exceptions.py

class GitError(Exception):
    """Base exception for Git operations."""
    pass

class GitCommandError(GitError):
    """Raised when a Git command fails."""
    def __init__(self, command_args, stdout, stderr, returncode, message="Git command failed"):
        self.command_args = command_args
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        super().__init__(f"{message}: '{' '.join(command_args)}' exited with code {returncode}.\nSTDOUT: {stdout}\nSTDERR: {stderr}")

class GitCommandNotFoundError(GitCommandError):
    """Raised when a Git command (e.g., 'git' itself) is not found."""
    def __init__(self, command, message="Git command not found"):
        # For command not found, usually return code is 127
        super().__init__([command], "", f"Command '{command}' not found. Please ensure Git is installed and in your PATH.", 127, message)
        self.command_name = command

class NotAGitRepositoryError(GitError):
    """Raised when an operation is performed outside a Git repository."""
    def __init__(self, path, message="Not a Git repository"): 
        self.path = path
        super().__init__(f"{message}: {path}")
