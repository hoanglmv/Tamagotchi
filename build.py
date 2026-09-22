"""
Build script to package myDeskAssistant into standalone executable binaries
for Windows (.exe) and Linux using PyInstaller.
"""

import sys
import os
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"
ASSETS_DIR = BASE_DIR / "ui" / "assets"
ICON_PATH = BASE_DIR / "ui" / "assets" / "characters" / "frieren.ico"


def build():
    print("=" * 60)
    print("🚀 Bắt đầu đóng gói myDeskAssistant...")
    print(f"Hệ điều hành: {sys.platform}")
    print("=" * 60)

    # Ensure pyinstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Đang cài đặt PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Path separator for PyInstaller --add-data
    sep = ";" if sys.platform == "win32" else ":"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=myDeskAssistant",
        "--noconfirm",
        "--clean",
        "--onedir",  # Folder distribution is fastest and most reliable for PyQt6 + assets
        f"--add-data=ui/assets{sep}ui/assets",
        f"--add-data=.env.example{sep}.",
        "--hidden-import=PyQt6",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=PyQt6.QtSvg",
        "--hidden-import=fastmcp",
        "--hidden-import=openai",
        "--hidden-import=edge_tts",
        "--hidden-import=psutil",
        "--hidden-import=pyperclip",
        "--hidden-import=pygame",
        "--hidden-import=PIL",
    ]

    if ICON_PATH.exists() and sys.platform == "win32":
        cmd.append(f"--icon={ICON_PATH}")

    # For Windows GUI app without dark console popping up
    if sys.platform == "win32":
        cmd.append("--noconsole")

    cmd.append("main.py")

    print("Đang thực thi lệnh:", " ".join(cmd))
    subprocess.check_call(cmd, cwd=str(BASE_DIR))

    # Copy .env.example into dist output folder
    target_output = DIST_DIR / "myDeskAssistant"
    if target_output.exists():
        shutil.copy(BASE_DIR / ".env.example", target_output / ".env.example")
        if not (target_output / ".env").exists() and (BASE_DIR / ".env").exists():
            shutil.copy(BASE_DIR / ".env.example", target_output / ".env")

        readme_text = (
            "myDeskAssistant - Frieren Anime Desktop Pet\n"
            "===========================================\n"
            "HƯỚNG DẪN SỬ DỤNG:\n"
            "1. Mở file '.env' và điền OPENROUTER_API_KEY của bạn.\n"
            "2. Chạy file thực thi 'myDeskAssistant' (hoặc myDeskAssistant.exe trên Windows).\n"
            "3. Click chuột phải lên nhân vật để đổi giữa Frieren, Fern, Stark, Himmel!\n"
        )
        (target_output / "README.txt").write_text(readme_text, encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"🎉 Đóng gói hoàn tất! Thư mục ứng dụng sẵn sàng tại: {target_output}")
    print("=" * 60)


if __name__ == "__main__":
    build()
