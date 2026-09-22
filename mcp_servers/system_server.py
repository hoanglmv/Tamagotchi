"""
System MCP Server for myDeskAssistant
Provides hardware metrics, application launcher, and clipboard management tools.
"""

from typing import Dict, Any, Optional
import os
import sys
import platform
import subprocess
import shutil
import psutil
from fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP(
    name="SystemServer",
    instructions="Provides tools to inspect hardware stats, launch applications, and manage clipboard."
)


def _is_wsl() -> bool:
    """Check if running inside Windows Subsystem for Linux (WSL)."""
    return "microsoft" in platform.release().lower() or "wsl" in platform.uname().release.lower()


@mcp.tool
def get_pc_stats() -> Dict[str, Any]:
    """
    Get current hardware and system performance metrics:
    CPU usage, RAM memory usage, Disk storage, and Battery status.
    
    Returns:
        dict: A dictionary containing CPU, RAM, Disk, and Battery information.
    """
    cpu_usage = psutil.cpu_percent(interval=0.3)
    cpu_count = psutil.cpu_count(logical=True)
    
    # Virtual Memory
    vm = psutil.virtual_memory()
    total_ram_gb = round(vm.total / (1024 ** 3), 2)
    available_ram_gb = round(vm.available / (1024 ** 3), 2)
    used_ram_gb = round((vm.total - vm.available) / (1024 ** 3), 2)
    ram_usage_percent = vm.percent

    # Disk usage (Root or system drive)
    root_path = "C:\\" if sys.platform == "win32" else "/"
    try:
        disk = psutil.disk_usage(root_path)
        disk_total_gb = round(disk.total / (1024 ** 3), 2)
        disk_used_gb = round(disk.used / (1024 ** 3), 2)
        disk_free_gb = round(disk.free / (1024 ** 3), 2)
        disk_percent = disk.percent
    except Exception:
        disk_total_gb = disk_used_gb = disk_free_gb = disk_percent = 0.0

    # Battery
    battery_info = {"has_battery": False, "percent": 0, "power_plugged": True}
    try:
        battery = psutil.sensors_battery()
        if battery:
            battery_info = {
                "has_battery": True,
                "percent": battery.percent,
                "power_plugged": bool(battery.power_plugged),
            }
    except Exception:
        pass

    return {
        "os": platform.system(),
        "platform_release": platform.release(),
        "is_wsl": _is_wsl(),
        "cpu": {
            "usage_percent": cpu_usage,
            "core_count": cpu_count
        },
        "ram": {
            "total_gb": total_ram_gb,
            "used_gb": used_ram_gb,
            "available_gb": available_ram_gb,
            "usage_percent": ram_usage_percent
        },
        "disk": {
            "drive": root_path,
            "total_gb": disk_total_gb,
            "used_gb": disk_used_gb,
            "free_gb": disk_free_gb,
            "usage_percent": disk_percent
        },
        "battery": battery_info
    }


@mcp.tool
def launch_app(app_name: str) -> str:
    """
    Launch a local desktop application or open a file/URL.
    Examples of app_name: 'chrome', 'vscode', 'notepad', 'calculator', 'terminal', or website URL.
    
    Args:
        app_name: The name or alias of the application to open.
        
    Returns:
        str: Success or failure message describing the action taken.
    """
    app_lower = app_name.strip().lower()
    is_windows = sys.platform == "win32"
    in_wsl = _is_wsl()

    # Dictionary of standard app mappings
    app_aliases = {
        "chrome": {"win": "chrome", "linux": "google-chrome", "wsl": "cmd.exe /c start chrome"},
        "google chrome": {"win": "chrome", "linux": "google-chrome", "wsl": "cmd.exe /c start chrome"},
        "browser": {"win": "start", "linux": "xdg-open", "wsl": "cmd.exe /c start"},
        "vscode": {"win": "code", "linux": "code", "wsl": "code"},
        "code": {"win": "code", "linux": "code", "wsl": "code"},
        "notepad": {"win": "notepad", "linux": "gedit", "wsl": "cmd.exe /c start notepad"},
        "calculator": {"win": "calc", "linux": "gnome-calculator", "wsl": "cmd.exe /c start calc"},
        "calc": {"win": "calc", "linux": "gnome-calculator", "wsl": "cmd.exe /c start calc"},
        "terminal": {"win": "wt", "linux": "x-terminal-emulator", "wsl": "cmd.exe /c start wt"},
        "explorer": {"win": "explorer", "linux": "nautilus", "wsl": "explorer.exe ."},
    }

    try:
        # Check if app_name is an explicit URL
        if app_lower.startswith(("http://", "https://")):
            if in_wsl:
                subprocess.Popen(["cmd.exe", "/c", "start", app_name])
            elif is_windows:
                os.startfile(app_name)
            else:
                subprocess.Popen(["xdg-open", app_name])
            return f"Đã mở liên kết URL: {app_name}"

        # Match alias
        target_command = None
        if app_lower in app_aliases:
            mapping = app_aliases[app_lower]
            if in_wsl:
                target_command = mapping["wsl"]
            elif is_windows:
                target_command = mapping["win"]
            else:
                target_command = mapping["linux"]
        else:
            # Fallback to app_name directly
            if in_wsl:
                target_command = f"cmd.exe /c start {app_name}"
            else:
                target_command = app_name

        # Execute
        if in_wsl:
            subprocess.Popen(target_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Đã kích hoạt khởi chạy '{app_name}' thông qua WSL/Windows host."
        elif is_windows:
            try:
                os.startfile(target_command)
            except Exception:
                subprocess.Popen(target_command, shell=True)
            return f"Đã mở ứng dụng '{app_name}' thành công trên Windows."
        else:
            # Linux
            if shutil.which(target_command):
                subprocess.Popen([target_command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Đã mở ứng dụng '{app_name}' thành công trên Linux."
            else:
                # Try xdg-open
                subprocess.Popen(["xdg-open", app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Đã gửi lệnh mở '{app_name}' qua xdg-open."

    except Exception as e:
        return f"Không thể mở ứng dụng '{app_name}'. Lỗi: {str(e)}"


@mcp.tool
def get_clipboard() -> str:
    """
    Read the current text content from the system clipboard.
    
    Returns:
        str: The copied text currently inside the clipboard.
    """
    try:
        import pyperclip
        content = pyperclip.paste()
        if not content:
            return "Clipboard hiện đang trống."
        # Truncate if extremely long to protect token context
        if len(content) > 2000:
            return content[:2000] + "... [nội dung đã được rút gọn]"
        return content
    except Exception as e:
        return f"Không thể đọc clipboard: {str(e)}"


@mcp.tool
def set_clipboard(text: str) -> str:
    """
    Write text content to the system clipboard.
    
    Args:
        text: The text string to copy into clipboard.
        
    Returns:
        str: Confirmation message.
    """
    try:
        import pyperclip
        pyperclip.copy(text)
        return "Đã sao chép nội dung vào clipboard thành công!"
    except Exception as e:
        return f"Không thể ghi vào clipboard: {str(e)}"


if __name__ == "__main__":
    # Runs the MCP server with STDIO transport
    mcp.run()
