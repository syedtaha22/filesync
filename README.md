# File Synchronization Tool

## Overview

This tool provides a simple and efficient way to back up and restore files between directories.  It uses SHA-256 hashing to efficiently detect new, modified, and deleted files, minimizing redundant operations and speeding up sync times.

### Usage

```bash
main.py [--src SRC] --dest DEST [--restore] [--scan] [-v]
```

### Workflow

  * **In BACKUP mode (default):**

      * Source (`--src`) is scanned.
      * Destination (`--dest`) is scanned.
      * Files missing or modified in the destination are copied from the source.
      * Files that exist only in the destination can be deleted (you will be prompted).

  * **In RESTORE mode (`--restore`):**

      * The destination (`--dest`) is treated as the source of truth (the backup).
      * The source (`--src`) is overwritten/restored from the backup.
      * No deletions are performed in restore mode.

### Hash Databases

  * Each directory keeps its own `.syncdb.json` file.
  * These databases speed up scans and reduce unnecessary hashing.
  * They are updated after every sync.

## File Structure

The project is organized into a modular structure for better maintainability.

```
.
├── filesync/
│   ├── __init__.py 
│   ├── config.py           # Stores shared configuration variables
│   ├── filesync_core.py    # Contains the core synchronization logic
│   └── local_config.py     # Local Configuration (optional, must be defined)
├── .gitignore 
├── clean_pyc.sh  
├── README.md
└── main.py                 # The main entry point for the application
```

## Command-line Arguments

| Option            | Description                                                                                                       |
|-------------------|-------------------------------------------------------------------------------------------------------------------|
| `-h`, `--help`    | Shows the help message and exits.                                                                                 |
| `--src SRC`       | Source directory to scan. **This argument is mandatory if `local_config.py` is not present.**                     |
| `--dest DEST`     | Destination (backup) directory. **Required.**                                                                     |
| `--restore`       | Switches to RESTORE mode, treating the destination as the source of truth.                                        |
| `--scan`          | Runs in scan-only mode to detect changes without performing any file operations.                                  |
| `-v`, `--verbose` | Controls logging verbosity. Use `-v` to show copied files, `-vv` for detailed output of all scanned/copied files. |

## Usage Examples

### Setting a Default Source Directory

To avoid having to specify the source every time, you can create a `local_config.py` file inside `filesync/` and define the `DEFAULT_SRC_DIR` variable.

```python
DEFAULT_SRC_DIR = r"/path/to/your/source/folder"
```

**Note: If `filesync/local_configs.py` does not define `DEFAULT_SRC_DIR` the `--src` argument is mandatory.**

### Basic Backup


```bash
python main.py --src /path/to/your/source/folder --dest /path/to/your/backup/location
```

### Restore Mode

```bash
python main.py --restore --src /path/to/restore/to --dest /path/to/backup/from
```

### Scan Only

To see what changes would be made without performing any actions, use the `--scan` flag.

```bash
python main.py --scan --src /path/to/your/source/folder --dest /path/to/your/backup/location
```
