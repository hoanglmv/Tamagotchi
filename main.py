"""
Main entry point for myDeskAssistant.
Supports both GUI Desktop Pet (PyQt6) and CLI Terminal mode.
"""

import sys
import os
import argparse
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

from core.persona import get_system_prompt
from core.memory import MemoryManager
from core.llm_client import AssistantBrain
from core.tts_service import TTSService


def run_cli_mode():
    """Run interactive text-based chat directly inside the terminal."""
    print("=" * 60)
    print("✨ myDeskAssistant - Chế độ dòng lệnh (CLI Mode)")
    print("✨ Bạn đang trò chuyện cùng Trợ lý Anime (Frieren / Lumi)")
    print("✨ Gõ 'exit' hoặc 'quit' để thoát.")
    print("=" * 60)

    memory = MemoryManager()
    brain = AssistantBrain(
        memory=memory,
        on_status_change=lambda status, msg: print(f"[{status.upper()}] {msg}" if msg else ""),
        on_tool_call=lambda name, args: print(f"[MCP TOOL] Đang gọi {name}({args})...")
    )
    tts = TTSService()

    async def _chat_loop():
        while True:
            try:
                user_input = input("\nSenpai: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit", "thoat"]:
                    print("\nTạm biệt Senpai! Hẹn gặp lại nha~ (˶ᵔ ᵕ ᵔ˶)")
                    break

                response = await brain.generate_response(user_input)
                print(f"\nLumi: {response}")

                # Optional TTS test in CLI
                audio_file = await tts.generate_speech(response)
                if audio_file:
                    tts.play_audio_file(audio_file)

            except (KeyboardInterrupt, EOFError):
                print("\nĐã dừng ứng dụng.")
                break

    asyncio.run(_chat_loop())


def run_gui_mode():
    """Run full PyQt6 transparent floating desktop pet UI."""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
    from ui.desktop_pet import DesktopPet

    app = QApplication(sys.argv)
    app.setApplicationName("myDeskAssistant")

    # Worker QObject to run async LLM and TTS tasks without freezing Qt main thread
    class AssistantWorker(QObject):
        response_ready = pyqtSignal(str, object)  # response_text, audio_path
        status_changed = pyqtSignal(str, str)    # state ('thinking', 'talking', 'idle'), message

        def __init__(self):
            super().__init__()
            self.memory = MemoryManager()
            self.brain = AssistantBrain(
                memory=self.memory,
                on_status_change=self._on_brain_status,
                on_tool_call=self._on_tool_call
            )
            self.tts = TTSService()
            self._loop = None

        def _on_brain_status(self, status: str, msg: str):
            state = "thinking" if status in ["thinking", "tool"] else "idle"
            self.status_changed.emit(state, msg)

        def _on_tool_call(self, name: str, args: dict):
            self.status_changed.emit("thinking", f"⚡ MCP: {name}")

        @pyqtSlot(str)
        def handle_user_prompt(self, prompt: str):
            """Async processing in thread."""
            async def _process():
                try:
                    self.status_changed.emit("thinking", "Đang suy nghĩ...")
                    response_text = await self.brain.generate_response(prompt)
                    
                    # Generate speech
                    self.status_changed.emit("thinking", "Đang tạo giọng nói...")
                    audio_path = await self.tts.generate_speech(response_text)
                    
                    self.response_ready.emit(response_text, audio_path)
                except Exception as e:
                    err = f"Lỗi: {str(e)}"
                    self.response_ready.emit(err, None)

            asyncio.run(_process())

    # Create Pet UI
    pet = DesktopPet(default_character="frieren")

    # Create Worker and background QThread
    thread = QThread()
    worker = AssistantWorker()
    worker.moveToThread(thread)
    thread.start()

    # Signals connection: UI -> Worker
    pet.user_submitted_message.connect(worker.handle_user_prompt)
    pet.quick_action_requested.connect(worker.handle_user_prompt)

    # Signals connection: Worker -> UI
    worker.status_changed.connect(lambda state, msg: pet.set_state(state, msg))

    def on_response(text: str, audio_path):
        pet.set_speech(text)
        if audio_path:
            pet.set_state("talking", "Đang nói...")
            worker.tts.play_audio_file(
                audio_path,
                on_finish=lambda: pet.set_state("idle", "Sẵn sàng")
            )
        else:
            pet.set_state("idle", "Sẵn sàng")

    worker.response_ready.connect(on_response)

    # Cleanup on exit
    app.aboutToQuit.connect(thread.quit)

    pet.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="myDeskAssistant - Anime Desktop Pet Trợ lý thông minh")
    parser.add_argument("--cli", action="store_true", help="Chạy ở chế độ dòng lệnh Terminal (không mở cửa sổ GUI)")
    args = parser.parse_args()

    if args.cli:
        run_cli_mode()
    else:
        run_gui_mode()
