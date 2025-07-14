# config.py
import os
from dotenv import load_dotenv

# Paths
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
# Assuming the repo root is one level up from app/
REPO_DIR = os.path.dirname(APP_ROOT)

# Control files
CONTROL_DIR = os.path.join(REPO_DIR, ".control")
TRIGGER_NEXT_STEP_FLAG = os.path.join(CONTROL_DIR, "trigger_next_step")
USER_REQUEST_FILE = os.path.join(CONTROL_DIR, "user_request.txt")

# Environment variables and configurable settings
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
# Validate GEMINI_API_KEY immediately upon loading config.py
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set. Please set it in the .env file or system environment.")

# Specific log file paths
APP_LOG_FILE_PATH = os.getenv('APP_LOG_FILE_PATH', 'app.log') # For general application logs
EVOLUTION_LOG_FILE_PATH = os.getenv('EVOLUTION_LOG_FILE_PATH', 'evolution_log.json') # For evolution history log

# LOG_FILE_PATH is imported by orchestrator.py for history. 
# It should map to EVOLUTION_LOG_FILE_PATH for consistency with L71.
LOG_FILE_PATH = EVOLUTION_LOG_FILE_PATH

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

# Core AI parameters
MAX_AI_X_RETRIES = int(os.getenv('MAX_AI_X_RETRIES', 3))
RETRY_SLEEP_SECONDS = int(os.getenv('RETRY_SLEEP_SECONDS', 5))
SLEEP_BETWEEN_ITERATIONS_SECONDS = int(os.getenv('SLEEP_BETWEEN_ITERATIONS_SECONDS', 10))

# Other settings
VERSION = "0.74.0" # Hardcoded version, ideally read from git tags or dynamic
INTERACTIVE_MODE = os.getenv('INTERACTIVE_MODE', 'False').lower() == 'true'

# Paths to exclude from source code context (for get_source_code_context)
EXCLUDE_PATHS = [
    ".git",
    "__pycache__",
    ".idea",
    ".vscode",
    "*.pyc",
    "node_modules",
    "venv",
    ".env",
    CONTROL_DIR, # Exclude control directory content
    APP_LOG_FILE_PATH, # Exclude general app log file from context
    EVOLUTION_LOG_FILE_PATH, # Exclude evolution history log file from context
]