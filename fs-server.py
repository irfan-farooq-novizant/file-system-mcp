from mcp.server.fastmcp import FastMCP
import os
import sys
import difflib

mcp = FastMCP("Moodle Upgrade Assistant")

CURRENT_DIR = "C:/xampp/htdocs/cmsu-lms-moodle"  # Your v4.4.5
STABLE_DIR = "D:/Work/Projects/cmsu-moodle-projects/moodle-4.4.12" # Clean v4.4.12

print("✅ Moodle Upgrade Assistant is running...", file=sys.stderr)

@mcp.tool()
def list_directory_contents(relative_path: str = "") -> str:
    """
    Lists folders and files in the custom project and checks if they exist in vanilla 4.4.12.
    Use this to scan for entirely custom plugins, themes, or missing core folders.
    """
    target_path = os.path.join(CURRENT_DIR, relative_path)
    stable_path = os.path.join(STABLE_DIR, relative_path)
    
    if not os.path.exists(target_path):
        return f"Path '{relative_path}' does not exist in your custom project."
        
    try:
        items = os.listdir(target_path)
    except Exception as e:
        return f"Error reading directory: {str(e)}"
        
    output = [f"=== Contents of /{relative_path} ==="]
    
    for item in sorted(items):
        item_rel_path = os.path.join(relative_path, item).replace("\\", "/")
        item_target = os.path.join(target_path, item)
        item_stable = os.path.join(stable_path, item)
        
        is_dir = os.path.isdir(item_target)
        type_label = "[DIR]" if is_dir else "[FILE]"
        
        # Check if this exists in vanilla Moodle
        status = ""
        if not os.path.exists(item_stable):
            status = " <-- 🚨 ENTIRELY CUSTOM (Not in vanilla 4.4.12)"
            
        output.append(f"{type_label} {item}{status}")
        
    return "\n".join(output)

@mcp.tool()
def view_file_diff(relative_path: str) -> str:
    """
    Compares a file in the custom 4.4.5 project against the clean 4.4.12 file.
    Shows exactly what code modifications you made.
    """
    path_a = os.path.join(CURRENT_DIR, relative_path)
    path_b = os.path.join(STABLE_DIR, relative_path)
    
    if not os.path.exists(path_a):
        return f"File '{relative_path}' does not exist in your custom project."
    if not os.path.exists(path_b):
        return f"File '{relative_path}' is entirely custom (does not exist in vanilla core)."
        
    try:
        with open(path_a, 'r', encoding='utf-8', errors='ignore') as f_a, \
             open(path_b, 'r', encoding='utf-8', errors='ignore') as f_b:
            diff = difflib.unified_diff(
                f_b.readlines(), # Vanilla 4.4.12 core lines
                f_a.readlines(), # Your custom 4.4.5 modifications
                fromfile=f'Vanilla_4.4.12:/{relative_path}',
                tofile=f'Your_Custom:/{relative_path}',
                n=3 # Lines of context around changes
            )
            diff_text = "".join(diff)
            return diff_text if diff_text else "Success: Core files match exactly. No custom changes here."
    except Exception as e:
        return f"Error reading files: {str(e)}"

if __name__ == "__main__":
    # Start MCP server over stdio so clients can connect.
    mcp.run(transport="stdio")