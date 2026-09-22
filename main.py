"""
Main entry point for myDeskAssistant.
Supports both GUI Desktop Pet (PyQt6) with Frieren characters,
animations, dances, and CLI Terminal mode.
"""

import sys
import os
import re
import argparse
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

from core.persona import get_character_prompt, CHARACTER_PERSONAS
from core.memory import MemoryManager
from core.llm_client import AssistantBrain
from core.tts_service import TTSService


def detect_interactive_intent(prompt: str) -> dict:
    """Detect if user asks for a dance or specific expression."""
    p_lower = prompt.lower()
    result = {"dance": None, "expression": None}

    # Dances
    if any(k in p_lower for k in ["lắc lư", "sway"]):
        result["dance"] = "sway"
    elif any(k in p_lower for k in ["nhảy cẫng", "nhảy chân sáo", "hop"]):
        result["dance"] = "hop"
    elif any(k in p_lower for k in ["xoay", "spin"]):
        result["dance"] = "spin"
    elif any(k in p_lower for k in ["nhảy", "khiêu vũ", "dance", "múa", "ăn mừng"]):
        result["dance"] = "hop"

    # Expressions
    if any(k in p_lower for k in ["mimic", "rương", "kẹt trong rương"]):
        result["expression"] = "special"
    elif any(k in p_lower for k in ["phồng má", "dỗi", "giận"]):
        result["expression"] = "special"
    elif any(k in p_lower for k in ["sợ", "hoảng", "cứu tôi"]):
        result["expression"] = "special"
    elif any(k in p_lower for k in ["đẹp trai", "tự luyến", "tỏa sáng"]):
        result["expression"] = "special"
    elif any(k in p_lower for k in ["bình thường", "đứng yên", "thôi"]):
        result["expression"] = "idle"

    return result


def run_cli_mode():
    """Run interactive text-based chat directly inside the terminal."""
    print("=" * 65)
    print("✨ myDeskAssistant - Chế độ dòng lệnh (CLI Mode)")
    print("✨ Bạn đang trò chuyện cùng các nhân vật Frieren (Frieren, Fern, Stark, Himmel)")
    print("✨ Gõ 'switch [frieren|fern|stark|himmel]' để đổi nhân vật.")
    print("✨ Gõ 'exit' hoặc 'quit' để thoát.")
    print("=" * 65)

    memory = MemoryManager()
    brain = AssistantBrain(
        memory=memory,
        active_character="frieren",
        on_status_change=lambda status, msg: print(f"[{status.upper()}] {msg}" if msg else ""),
        on_tool_call=lambda name, args: print(f"[MCP TOOL] Đang kích hoạt {name}({args})...")
    )
    tts = TTSService()

    async def _chat_loop():
        while True:
            try:
                char_name = CHARACTER_PERSONAS[brain.active_character]["name"]
                user_input = input(f"\nBạn (đang nói với {char_name}): ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit", "thoat"]:
                    print("\nTạm biệt bạn! Hẹn gặp lại trong chuyến hành trình tiếp theo.")
                    break

                if user_input.lower().startswith("switch "):
                    target = user_input.split()[1].lower()
                    if target in CHARACTER_PERSONAS:
                        brain.set_character(target)
                        print(f"✨ Đã đổi nhân vật đồng hành sang: {CHARACTER_PERSONAS[target]['name']}")
                        continue
                    else:
                        print(f"Nhân vật không hợp lệ. Chọn một trong: {list(CHARACTER_PERSONAS.keys())}")
                        continue

                response = await brain.generate_response(user_input)
                print(f"\n{char_name}: {response}")

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

    class AssistantWorker(QObject):
        response_ready = pyqtSignal(str, object)  # response_text, audio_path
        status_changed = pyqtSignal(str, str)    # state ('thinking', 'talking', 'idle'), message

        def __init__(self, character: str = "frieren"):
            super().__init__()
            self.memory = MemoryManager()
            self.brain = AssistantBrain(
                memory=self.memory,
                active_character=character,
                on_status_change=self._on_brain_status,
                on_tool_call=self._on_tool_call
            )
            self.tts = TTSService()

        def set_character(self, char_key: str):
            self.brain.set_character(char_key)

        def _on_brain_status(self, status: str, msg: str):
            state = "thinking" if status in ["thinking", "tool"] else "idle"
            self.status_changed.emit(state, msg)

        def _on_tool_call(self, name: str, args: dict):
            self.status_changed.emit("thinking", f"⚡ MCP: {name}")

        @pyqtSlot(str)
        def handle_user_prompt(self, prompt: str):
            async def _process():
                try:
                    self.status_changed.emit("thinking", "Đang suy nghĩ...")
                    response_text = await self.brain.generate_response(prompt)
                    
                    self.status_changed.emit("thinking", "Đang tạo giọng nói...")
                    audio_path = await self.tts.generate_speech(response_text)
                    
                    self.response_ready.emit(response_text, audio_path)
                except Exception as e:
                    err = f"Lỗi: {str(e)}"
                    self.response_ready.emit(err, None)

            asyncio.run(_process())

    # Create Pet UI
    pet = DesktopPet(default_character="frieren")

    # Background worker thread
    thread = QThread()
    worker = AssistantWorker(character="frieren")
    worker.moveToThread(thread)
    thread.start()

    def on_user_message(prompt: str):
        # Check interactive intent (dance or expression)
        intent = detect_interactive_intent(prompt)
        if intent["dance"]:
            pet.start_dance(intent["dance"], duration_seconds=8.0)
        if intent["expression"]:
            pet.set_expression(intent["expression"])

        worker.handle_user_prompt(prompt)

    # Signals
    pet.user_submitted_message.connect(on_user_message)
    pet.quick_action_requested.connect(on_user_message)
    pet.character_changed.connect(worker.set_character)

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

    app.aboutToQuit.connect(thread.quit)

    pet.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="myDeskAssistant - Frieren Desktop Pet Trợ lý thông minh")
    parser.add_argument("--cli", action="store_true", help="Chạy ở chế độ dòng lệnh Terminal")
    args = parser.parse_args()

    if args.cli:
        run_cli_mode()
    else:
        run_gui_mode()
