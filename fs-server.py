from mcp.server.fastmcp import FastMCP
import os
import sys
import difflib
from typing import Dict

mcp = FastMCP("Moodle Upgrade Assistant")

CURRENT_DIR = "C:/xampp/htdocs/cmsu-lms-moodle"  # main branch, v4.4.5
UAT_BACKUP_DIR = "D:/Work/Manabi/Code/cmsu-lms-moodle-4.4.12-uat-bkp-01-09-26"  # UAT branch backup, v4.4.12

FOLDERS: Dict[str, str] = {
    "custom": CURRENT_DIR,
    "uat": UAT_BACKUP_DIR,
}

print("✅ Moodle Upgrade Assistant is running...", file=sys.stderr)


def _get_folder_path(folder_key: str) -> str:
    """Resolve a logical folder name into an absolute path."""
    normalized = folder_key.strip().lower()
    if normalized not in FOLDERS:
        available = ", ".join(sorted(FOLDERS.keys()))
        raise ValueError(f"Unknown folder '{folder_key}'. Use one of: {available}")
    return FOLDERS[normalized]


def _validate_relative_path(relative_path: str) -> str:
    """Normalize user-provided path separators for cross-platform compatibility."""
    return relative_path.replace("\\", "/").strip("/")


@mcp.tool()
def list_available_folders() -> str:
    """Lists all configured folders that can be queried by other tools."""
    output = ["=== Configured Folders ==="]
    for key in sorted(FOLDERS.keys()):
        output.append(f"{key}: {FOLDERS[key]}")
    return "\n".join(output)

@mcp.tool()
def list_directory_contents(relative_path: str = "", folder: str = "custom") -> str:
    """
    Lists folders and files in the selected folder.
    Defaults to the custom project for backward compatibility.

    folder options: custom, uat
    """
    try:
        base_dir = _get_folder_path(folder)
    except ValueError as e:
        return str(e)

    clean_relative_path = _validate_relative_path(relative_path)
    target_path = os.path.join(base_dir, clean_relative_path)
    
    if not os.path.exists(target_path):
        return f"Path '{clean_relative_path}' does not exist in folder '{folder}'."
        
    try:
        items = os.listdir(target_path)
    except Exception as e:
        return f"Error reading directory: {str(e)}"
        
    header_path = clean_relative_path or "/"
    output = [f"=== Contents of {folder}:/{header_path} ==="]
    
    for item in sorted(items):
        item_target = os.path.join(target_path, item)

        is_dir = os.path.isdir(item_target)
        type_label = "[DIR]" if is_dir else "[FILE]"

        output.append(f"{type_label} {item}")
        
    return "\n".join(output)

@mcp.tool()
def view_file_diff(relative_path: str, from_folder: str = "custom", to_folder: str = "uat") -> str:
    """
    Compares a file between any two configured folders.
    Defaults to: custom -> uat.

    folder options: custom, uat
    """
    try:
        from_base_dir = _get_folder_path(from_folder)
        to_base_dir = _get_folder_path(to_folder)
    except ValueError as e:
        return str(e)

    if from_folder.strip().lower() == to_folder.strip().lower():
        return "from_folder and to_folder must be different."

    clean_relative_path = _validate_relative_path(relative_path)
    path_from = os.path.join(from_base_dir, clean_relative_path)
    path_to = os.path.join(to_base_dir, clean_relative_path)
    
    if not os.path.exists(path_from):
        return f"File '{clean_relative_path}' does not exist in folder '{from_folder}'."
    if not os.path.exists(path_to):
        return f"File '{clean_relative_path}' does not exist in folder '{to_folder}'."
    if os.path.isdir(path_from) or os.path.isdir(path_to):
        return "view_file_diff only supports files, not directories."
        
    try:
        with open(path_from, 'r', encoding='utf-8', errors='ignore') as f_from, \
             open(path_to, 'r', encoding='utf-8', errors='ignore') as f_to:
            diff = difflib.unified_diff(
                f_from.readlines(),
                f_to.readlines(),
                fromfile=f'{from_folder}:/{clean_relative_path}',
                tofile=f'{to_folder}:/{clean_relative_path}',
                n=3 # Lines of context around changes
            )
            diff_text = "".join(diff)
            return diff_text if diff_text else "Success: Files match exactly."
    except Exception as e:
        return f"Error reading files: {str(e)}"

if __name__ == "__main__":
    # Start MCP server over stdio so clients can connect.
    mcp.run(transport="stdio")