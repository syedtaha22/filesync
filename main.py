import os
import sys
import argparse
from filesync.filesync_core import FileSync
from filesync.config import Colors, DEFAULT_SRC_DIR, HASH_DB_FILENAME

def main():
    """
    Parses command-line arguments and initiates the FileSync process.

    This function sets up the argument parser to handle various options
    like source/destination directories, restore mode, scan-only mode,
    and verbosity. It then validates the provided paths and starts the
    synchronization.
    """
    parser = argparse.ArgumentParser(
        prog="main.py",
        description=(
            "Backup & Restore Tool with local hash DBs.\n\n"
            "This program maintains SHA-256 hashes of files inside a small JSON file "
            f"({HASH_DB_FILENAME}) stored at the root of each directory (source and destination). "
            "It uses these hashes to detect new, modified, and deleted files.\n\n"
            "Workflow:\n"
            "   • In BACKUP mode (default):\n"
            "       - Source (--src) is scanned.\n"
            "       - Destination (--dest) is scanned.\n"
            "       - Files missing or modified in destination are copied from source.\n"
            "       - Files only in destination can be deleted (you will be prompted).\n\n"
            "   • In RESTORE mode (--restore):\n"
            "       - Destination (--dest) is treated as the source of truth (backup).\n"
            "       - Source (--src) is overwritten/restored from backup.\n"
            "       - No deletions are performed in restore mode.\n\n"
            "Hash DBs:\n"
            f"   • Each directory keeps its own {HASH_DB_FILENAME}.\n"
            "   • These DBs speed up scans and reduce unnecessary hashing.\n"
            "   • They are updated after every sync.\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )

    src_required = DEFAULT_SRC_DIR is None

    parser.add_argument(
        "--src", type=str, default=DEFAULT_SRC_DIR, required=src_required,
        help=(
            "Source directory to scan.\n"
            "In BACKUP mode: treated as the original data.\n"
            "In RESTORE mode: treated as the target to restore into.\n"
            "This argument is mandatory if local_config.py is not present."
        )
    )
    parser.add_argument(
        "--dest", type=str, required=True,
        help=(
            "Destination (backup) directory.\n"
            "In BACKUP mode: files are written/copied here.\n"
            "In RESTORE mode: files are read/restored from here."
        )
    )
    parser.add_argument(
        "--restore", action="store_true",
        help=(
            "Switch to RESTORE mode.\n"
            "Treat destination (--dest) as the source of truth and copy files "
            "into the source (--src)."
        )
    )
    parser.add_argument(
        "--scan", action="store_true",
        help=(
            "Scan only: detect and list new/modified/deleted files, "
            "but do not copy or delete anything."
        )
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=0,
        help=(
            "Control logging verbosity:\n"
            "   -v   show copied files\n"
            "   -vv  detailed (show each scanned/copied file)\n"
        )
    )

    args = parser.parse_args()

    # Validate directory paths before starting
    if not os.path.isdir(args.src):
        print(f"{Colors.RED}[!] Source folder does not exist: {args.src}{Colors.RESET}")
        sys.exit(1)

    if not os.path.isdir(args.dest):
        print(f"{Colors.RED}[!] Backup folder does not exist: {args.dest}{Colors.RESET}")
        sys.exit(1)

    # Print a status header
    if args.restore:
        print(f"{Colors.BOLD}[=] Restoring from backup: {args.dest}\n  -> to source: {args.src}{Colors.RESET}\n")
    else:
        print(f"{Colors.BOLD}[=] Backing up from source: {args.src}\n  -> to backup: {args.dest}{Colors.RESET}\n")

    syncer = FileSync(
        args.src, args.dest,
        verbosity=args.verbose,
        restore=args.restore,
        scan_only=args.scan
    )
    syncer.sync()

if __name__ == "__main__":
    main()
