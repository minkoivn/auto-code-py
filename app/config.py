import os
from dotenv import load_dotenv

# Load environment variables from .env file
# This should be called early to ensure all subsequent os.getenv calls can utilize .env values.
load_dotenv()

# Application configuration
APP_LOG_FILE_PATH = os.getenv('APP_LOG_FILE_PATH', 'app.log')
EVOLUTION_LOG_FILE_PATH = os.getenv('EVOLUTION_LOG_FILE_PATH', 'evolution.log')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

# Exclude these files from AI context. These are typically sensitive or generated files
# that the AI should not modify or read directly for context.
AI_CONTEXT_EXCLUSIONS = [
    APP_LOG_FILE_PATH,
    EVOLUTION_LOG_FILE_PATH,
    'config.py', # config.py itself to prevent AI from modifying core config too freely
    '.env'       # .env should definitely be excluded for security and to prevent accidental modification
]

# Other configurations (placeholder for future additions)
# Example: GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')