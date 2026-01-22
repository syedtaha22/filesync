"""
Core logic for the file synchronization tool.
This module contains the FileSync class which handles scanning directories,
comparing files, and performing synchronization actions.
"""

import os
import shutil
import hashlib
import json
from .config import Colors, HASH_CHUNK_SIZE, HASH_DB_FILENAME, IGNORED_DIRS

# === FileSync Class ===
class FileSync:
    """
    Synchronizes files between a source and destination directory using a hash-based approach.

    The tool maintains a small JSON database (`.syncdb.json`) in each directory to
    store file hashes. This allows for quick detection of new, modified, or
    deleted files without re-hashing everything on subsequent runs.

    Parameters
    ----------
    src_dir : str
        The path to the source directory.
    dest_dir : str
        The path to the destination directory.
    verbosity : int, optional
        The level of detail for console output.
        - 0: Silent, only critical errors.
        - 1: Normal (default), show key actions and summary.
        - 2: Detailed, show each file being scanned.
    restore : bool, optional
        If True, the tool runs in RESTORE mode, treating the destination as
        the source of truth and copying files back to the original source.
        Defaults to False.
    scan_only : bool, optional
        If True, the tool will only perform a scan and print a summary of
        changes without performing any file operations (copying, deleting).
        Defaults to False.

    Attributes
    ----------
    src_dir : str
        The absolute path to the source directory.
    dest_dir : str
        The absolute path to the destination directory.
    verbosity : int
        The configured verbosity level.
    restore : bool
        Flag for RESTORE mode.
    scan_only : bool
        Flag for scan-only mode.
    src_db_path : str
        Full path to the source's hash database file.
    dest_db_path : str
        Full path to the destination's hash database file.
    src_hash_db : dict
        A dictionary loaded from the source's hash database.
    dest_hash_db : dict
        A dictionary loaded from the destination's hash database.
    """
    def __init__(self, src_dir, dest_dir, verbosity=1, restore=False, scan_only=False):
        self.src_dir = src_dir
        self.dest_dir = dest_dir
        self.verbosity = verbosity
        self.restore = restore
        self.scan_only = scan_only

        # Each dir has its own hash DB
        self.src_db_path = os.path.join(self.src_dir, HASH_DB_FILENAME)
        self.dest_db_path = os.path.join(self.dest_dir, HASH_DB_FILENAME)

        self.src_hash_db = self.load_hash_db(self.src_db_path)
        self.dest_hash_db = self.load_hash_db(self.dest_db_path)

    def log(self, msg, level=1, color=Colors.RESET):
        """
        Prints messages to the console based on the configured verbosity level.

        Parameters
        ----------
        msg : str
            The message to print.
        level : int, optional
            The minimum verbosity level required to display the message.
            Defaults to 1.
        color : str, optional
            The ANSI color code to apply to the message. Defaults to `Colors.RESET`.
        """
        if self.verbosity >= level:
            print(f"{color}{msg}{Colors.RESET}")

    def get_file_hash(self, path):
        """
        Calculates the SHA-256 hash of a file.

        The file is read in chunks to handle large files efficiently without
        loading the entire file into memory.

        Parameters
        ----------
        path : str
            The full path to the file.

        Returns
        -------
        str or None
            The hexadecimal representation of the file's hash, or None if an
            error occurred (e.g., file not found or permission denied).
        """
        sha256 = hashlib.sha256()
        try:
            with open(path, 'rb') as f:
                while chunk := f.read(HASH_CHUNK_SIZE):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            self.log(f"[!] Error hashing {path}: {e}", 0, Colors.RED)
            return None

    def load_hash_db(self, db_path):
        """
        Loads the hash database from a JSON file.

        Parameters
        ----------
        db_path : str
            The full path to the hash database file.

        Returns
        -------
        dict
            A dictionary containing file paths and their hashes. Returns an
            empty dictionary if the file does not exist or is invalid.
        """
        if os.path.exists(db_path):
            try:
                with open(db_path, 'r') as f:
                    return json.load(f)
            except (IOError, json.JSONDecodeError):
                self.log(f"[!] Invalid or corrupted DB file: {db_path}. Creating new one.",
                         1, Colors.YELLOW)
                return {}
        return {}

    def save_hash_db(self, db_path, db):
        """
        Saves the hash database dictionary to a JSON file.

        Parameters
        ----------
        db_path : str
            The full path where the hash database should be saved.
        db : dict
            The dictionary containing file paths and their hashes.
        """
        with open(db_path, 'w') as f:
            json.dump(db, f, indent=2)

    def scan_folder(self, folder, hash_db, tag):
        """
        Scans a directory to build a dictionary of files and their hashes.

        This method checks the provided `hash_db` first to see if a hash for
        a file is already known. If the file is unchanged, the cached hash is
        reused, speeding up the scan process.

        Parameters
        ----------
        folder : str
            The path to the directory to scan.
        hash_db : dict
            The hash database for the folder being scanned.
        tag : str
            A descriptive tag (e.g., 'src' or 'dest') for logging purposes.

        Returns
        -------
        dict
            A dictionary where keys are relative file paths and values are
            dictionaries containing the file's full path and hash.
        """
        files = {}
        for root, dirs, filenames in os.walk(folder):
            # Filter out ignored directories in-place to prevent os.walk from descending into them
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            
            for filename in filenames:
                if filename == HASH_DB_FILENAME:
                    continue  # Skip our own db file
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, folder)

                # Reuse cached hash if it exists
                file_hash = hash_db.get(rel_path)
                if not file_hash:
                    file_hash = self.get_file_hash(full_path)

                files[rel_path] = {
                    'full_path': full_path,
                    'hash': file_hash
                }
                self.log(f"[scan {tag}] {rel_path}", 2, Colors.CYAN)
        return files

    def copy_file(self, src_path, dest_path):
        """
        Copies a file from the source to the destination, creating necessary
        directories.

        Parameters
        ----------
        src_path : str
            The full path of the file to copy.
        dest_path : str
            The full path where the file should be copied.
        """
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(src_path, dest_path)
        self.log(f"[+] Copied: {src_path} -> {dest_path}", 1, Colors.GREEN)

    def prompt_delete(self, path):
        """
        Prompts the user to confirm the deletion of a file.

        This method is used in BACKUP mode for files that exist in the
        destination but not in the source.

        Parameters
        ----------
        path : str
            The full path of the file to be deleted.
        """
        while True:
            answer = input(f"[?] File only in destination: {path}. Delete it? [y/n]: ").lower()
            if answer == 'y':
                os.remove(path)
                self.log(f"[-] Deleted: {path}", 0, Colors.RED)
                break
            elif answer == 'n':
                self.log("[=] Kept", 0, Colors.YELLOW)
                break

    def scan_changes(self):
        """
        Performs a full scan of both the source and destination directories to
        detect differences.

        The behavior (which directory is treated as source/destination) depends
        on the `self.restore` flag.

        Returns
        -------
        tuple
            A tuple containing:
            - A dictionary summarizing the counts of new, modified, and deleted files.
            - A dictionary representing the scanned files from the primary source.
            - A dictionary representing the scanned files from the destination.
        """
        if self.restore:
            self.log("[*] Running in RESTORE mode", 0, Colors.YELLOW)
            src_root, dest_root = self.dest_dir, self.src_dir
            src_db, dest_db = self.dest_hash_db, self.src_hash_db
        else:
            src_root, dest_root = self.src_dir, self.dest_dir
            src_db, dest_db = self.src_hash_db, self.dest_hash_db

        self.log("[*] Scanning source...", 0, Colors.BLUE)
        src_files = self.scan_folder(src_root, src_db, 'src')

        self.log("[*] Scanning destination...", 0, Colors.BLUE)
        dest_files = self.scan_folder(dest_root, dest_db, 'dest')

        new_files, modified_files, deleted_files = [], [], []

        for rel_path, src_info in src_files.items():
            src_hash = src_info['hash']
            if rel_path not in dest_files:
                new_files.append(rel_path)
            else:
                dest_hash = dest_files[rel_path]['hash']
                if src_hash != dest_hash:
                    modified_files.append(rel_path)

        if not self.restore:
            for rel_path in dest_files:
                if rel_path not in src_files:
                    deleted_files.append(rel_path)

        summary = {
            "src_count": len(src_files),
            "dest_count": len(dest_files),
            "new": new_files,
            "modified": modified_files,
            "deleted": deleted_files,
        }
        return summary, src_files, dest_files

    def sync(self):
        """
        Executes the synchronization process.

        This method first calls `scan_changes` to identify all differences,
        then prints a summary. If `scan_only` is False and the user confirms,
        it performs the necessary file copies and deletions (in BACKUP mode).
        Finally, it updates the local hash databases.
        """
        summary, src_files, dest_files = self.scan_changes()

        # Print summary
        self.log("\n=== SCAN SUMMARY ===", 0, Colors.BOLD)
        self.log(f"Source files:      {summary['src_count']}", 0, Colors.CYAN)
        self.log(f"Destination files: {summary['dest_count']}", 0, Colors.CYAN)
        self.log(f"New files:         {len(summary['new'])}", 0, Colors.GREEN)
        self.log(f"Modified files:    {len(summary['modified'])}", 0, Colors.YELLOW)
        self.log(f"Deleted files:     {len(summary['deleted'])}", 0, Colors.RED)
        self.log("=====================\n", 0, Colors.BOLD)

        if self.scan_only:
            self.log("[=] Scan-only mode: no changes applied.", 0, Colors.YELLOW)
            return

        choice = input("[?] Proceed with sync? [y/n]: ").lower()
        if choice != 'y':
            self.log("[=] Sync cancelled.", 0, Colors.YELLOW)
            return

        if self.restore:
            src_root, dest_root = self.dest_dir, self.src_dir
            src_db_path, dest_db_path = self.dest_db_path, self.src_db_path
        else:
            src_root, dest_root = self.src_dir, self.dest_dir
            src_db_path, dest_db_path = self.src_db_path, self.dest_db_path

        updated_src_db, updated_dest_db = {}, {}

        for rel_path, src_info in src_files.items():
            src_path = src_info['full_path']
            src_hash = src_info['hash']
            dest_path = os.path.join(dest_root, rel_path)

            # Update the databases with current hashes
            updated_src_db[rel_path] = src_hash
            updated_dest_db[rel_path] = src_hash

            if rel_path in summary["new"] or rel_path in summary["modified"]:
                self.copy_file(src_path, dest_path)

        if not self.restore:
            for rel_path in summary["deleted"]:
                if rel_path in dest_files:
                    dest_path = dest_files[rel_path]['full_path']
                    self.prompt_delete(dest_path)

        # Save the updated databases
        self.save_hash_db(src_db_path, updated_src_db)
        self.save_hash_db(dest_db_path, updated_dest_db)

        self.log("\n[✓] Sync complete. Hash DBs updated.", 0, Colors.GREEN)