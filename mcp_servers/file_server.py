"""
File MCP Server for myDeskAssistant
Provides file cleanup, organization, reading, and writing tools.
"""

from typing import Dict, Any, List, Optional
import os
import sys
import glob
import shutil
from pathlib import Path
from fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP(
    name="FileServer",
    instructions="Provides tools to organize downloads, inspect directories, and read or write local files."
)

CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".ico"],
    "Documents": [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".txt", ".md", ".csv"],
    "Installers": [".exe", ".msi", ".deb", ".dmg", ".pkg", ".appimage", ".rpm"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Code": [".py", ".js", ".ts", ".html", ".css", ".json", ".cpp", ".c", ".rs", ".java", ".go"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".flv", ".webm"],
    "Audio": [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"]
}


def _get_default_downloads_dir() -> Path:
    """Find the standard user Downloads directory across Windows, WSL, and Linux."""
    # Check WSL Windows user downloads first if in WSL
    if sys.platform.startswith("linux") and os.path.exists("/mnt/c/Users"):
        for user_folder in sorted(os.listdir("/mnt/c/Users")):
            candidate = Path(f"/mnt/c/Users/{user_folder}/Downloads")
            if candidate.is_dir() and user_folder not in ["Default", "Public", "All Users"]:
                return candidate

    return Path.home() / "Downloads"


@mcp.tool
def organize_downloads(folder_path: Optional[str] = None, dry_run: bool = True) -> Dict[str, Any]:
    """
    Scan and organize files in the Downloads folder (or custom directory) into categories:
    Images, Documents, Installers, Archives, Code, Videos, Audio.
    
    Args:
        folder_path: Target directory path (defaults to User's Downloads folder if None).
        dry_run: If True, only simulate and return what will be moved without making changes.
                 If False, actually create folders and move the files.
                 
    Returns:
        dict: Summary of actions, affected files, and total categorized count.
    """
    target_dir = Path(folder_path).resolve() if folder_path else _get_default_downloads_dir()

    if not target_dir.exists() or not target_dir.is_dir():
        return {
            "status": "error",
            "message": f"Thư mục không tồn tại: {str(target_dir)}",
            "dry_run": dry_run,
            "moved_count": 0,
            "plan": {}
        }

    # Map extension to category
    ext_to_cat = {}
    for cat, exts in CATEGORIES.items():
        for ext in exts:
            ext_to_cat[ext.lower()] = cat

    move_plan: Dict[str, List[str]] = {cat: [] for cat in CATEGORIES.keys()}
    move_plan["Others"] = []

    total_files = 0
    for item in target_dir.iterdir():
        if item.is_file() and not item.name.startswith("."):
            ext = item.suffix.lower()
            cat = ext_to_cat.get(ext)
            if cat:
                move_plan[cat].append(item.name)
                total_files += 1

    # Filter empty categories
    filtered_plan = {cat: files for cat, files in move_plan.items() if files}

    if dry_run:
        return {
            "status": "success",
            "message": f"Đã quét thư mục '{target_dir}'. Phát hiện {total_files} file có thể phân loại (chế độ xem trước dry_run=True).",
            "target_dir": str(target_dir),
            "dry_run": True,
            "total_files": total_files,
            "plan": filtered_plan
        }

    # Execute move
    moved_count = 0
    errors = []
    for cat, files in filtered_plan.items():
        dest_folder = target_dir / cat
        dest_folder.mkdir(exist_ok=True)
        for fname in files:
            src = target_dir / fname
            dst = dest_folder / fname
            try:
                # If destination already exists, resolve collision
                if dst.exists():
                    stem = src.stem
                    suffix = src.suffix
                    dst = dest_folder / f"{stem}_{int(src.stat().st_mtime)}{suffix}"
                shutil.move(str(src), str(dst))
                moved_count += 1
            except Exception as e:
                errors.append(f"{fname}: {str(e)}")

    return {
        "status": "success" if not errors else "partial",
        "message": f"Đã phân loại thành công {moved_count}/{total_files} files trong thư mục '{target_dir}'.",
        "target_dir": str(target_dir),
        "dry_run": False,
        "moved_count": moved_count,
        "errors": errors,
        "plan": filtered_plan
    }


@mcp.tool
def read_file(file_path: str, max_chars: int = 4000) -> str:
    """
    Read text content from a specified file.
    
    Args:
        file_path: Path to the target file.
        max_chars: Maximum characters to return to avoid token overflow.
        
    Returns:
        str: File content or error message.
    """
    p = Path(file_path).resolve()
    if not p.exists():
        return f"Lỗi: File '{file_path}' không tồn tại."
    if not p.is_file():
        return f"Lỗi: '{file_path}' là thư mục, không phải file."

    try:
        content = p.read_text(encoding="utf-8", errors="replace")
        if len(content) > max_chars:
            return content[:max_chars] + f"\n... [Nội dung đã được cắt bớt vì vượt quá {max_chars} ký tự]"
        return content
    except Exception as e:
        return f"Lỗi khi đọc file: {str(e)}"


@mcp.tool
def write_file(file_path: str, content: str) -> str:
    """
    Write or overwrite text content to a specified file.
    
    Args:
        file_path: Target file path.
        content: Text content to write into the file.
        
    Returns:
        str: Success or failure confirmation.
    """
    try:
        p = Path(file_path).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Đã ghi thành công {len(content)} ký tự vào file '{file_path}'."
    except Exception as e:
        return f"Lỗi khi ghi file '{file_path}': {str(e)}"


@mcp.tool
def list_directory(path: Optional[str] = None) -> Dict[str, Any]:
    """
    List contents of a directory (files and folders).
    
    Args:
        path: Path to list (defaults to current project directory if None).
        
    Returns:
        dict: List of files and folders with size and type info.
    """
    target = Path(path).resolve() if path else Path.cwd()
    if not target.exists():
        return {"status": "error", "message": f"Thư mục '{target}' không tồn tại."}

    files = []
    folders = []
    try:
        for item in sorted(target.iterdir()):
            if item.name.startswith("."):
                continue
            if item.is_dir():
                folders.append(item.name)
            else:
                files.append({
                    "name": item.name,
                    "size_bytes": item.stat().st_size
                })
        return {
            "status": "success",
            "path": str(target),
            "folders": folders,
            "files": files,
            "total_items": len(folders) + len(files)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    # Runs the MCP server with STDIO transport
    mcp.run()
