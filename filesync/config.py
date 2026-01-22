"""
Configuration settings for the file synchronization tool.
"""
import os

# === CONFIGURATION VARIABLES ===
try:
    from .local_config import DEFAULT_SRC_DIR, IGNORED_DIRS
except ImportError:
    # If the local_config.py file is not found, the default source directory is not set
    # and must be provided by the user via the command line.
    DEFAULT_SRC_DIR = None
    IGNORED_DIRS = []

HASH_CHUNK_SIZE = 8192
"""
Size of the chunks (in bytes) to read from files when computing a hash.
A larger chunk size can speed up hashing for large files.
"""

HASH_DB_FILENAME = ".syncdb.json"
"""
Name of the local hash database file. This file is created in both the
source and destination directories to store file hashes and timestamps,
enabling faster future scans.
"""


# === COLOR CODES FOR CONSOLE OUTPUT ===
class Colors:
    """
    A class to store ANSI escape codes for colored console output.
    """
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
