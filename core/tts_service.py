"""
TTS (Text-to-Speech) Service for myDeskAssistant.
Converts LLM responses to natural speech using edge-tts and plays audio safely.
"""

from typing import Optional, Callable
import os
import re
import sys
import hashlib
import asyncio
import threading
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "audio_cache"


def clean_text_for_tts(text: str) -> str:
    """Clean markdown, emojis, symbols and URLs so TTS speaks naturally."""
    if not text:
        return ""
    # Remove code blocks
    cleaned = re.sub(r"```[\s\S]*?```", "", text)
    # Remove inline code
    cleaned = re.sub(r"`[^`]+`", "", cleaned)
    # Remove markdown bold/italics
    cleaned = re.sub(r"[*_~#]+", "", cleaned)
    # Remove links
    cleaned = re.sub(r"https?://\S+", "", cleaned)
    # Remove anime faces / Kaomoji: (˶ᵔ ᵕ ᵔ˶), (｡♥‿♥｡), etc.
    cleaned = re.sub(r"\([^\)]*[\u2500-\u2BFF\u3000-\u303F\uFF00-\uFFEF\u0250-\u02AF][^\)]*\)", "", cleaned)
    # Remove excessive whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


class TTSService:
    """Manages Edge-TTS voice generation, caching, and safe audio playback."""

    def __init__(
        self,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        pitch: Optional[str] = None
    ):
        self.voice = voice or os.getenv("TTS_VOICE", "vi-VN-HoaiMyNeural")
        self.rate = rate or os.getenv("TTS_RATE", "+0%")
        self.pitch = pitch or os.getenv("TTS_PITCH", "+0Hz")
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.is_playing = False
        self._mixer_initialized = False

    def _init_audio_device(self) -> bool:
        """Attempt to initialize pygame audio mixer safely."""
        if self._mixer_initialized:
            return True
        try:
            import pygame
            # Don't print pygame welcome message
            os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
            pygame.mixer.init()
            self._mixer_initialized = True
            return True
        except Exception:
            return False

    async def generate_speech(self, text: str) -> Optional[Path]:
        """
        Convert text to MP3 audio file.
        Returns Path to the generated MP3 file, or None on failure.
        """
        cleaned = clean_text_for_tts(text)
        if not cleaned:
            return None

        # Generate hash for caching
        text_hash = hashlib.md5(f"{self.voice}_{self.rate}_{self.pitch}_{cleaned}".encode("utf-8")).hexdigest()
        output_file = CACHE_DIR / f"{text_hash}.mp3"

        if output_file.exists() and output_file.stat().st_size > 0:
            return output_file

        try:
            import edge_tts
            communicate = edge_tts.Communicate(
                text=cleaned,
                voice=self.voice,
                rate=self.rate,
                pitch=self.pitch
            )
            await communicate.save(str(output_file))
            return output_file
        except Exception as e:
            print(f"[TTSService] Cảnh báo tạo âm thanh edge-tts: {e}")
            return None

    def play_audio_file(self, audio_path: Path, on_finish: Optional[Callable[[], None]] = None) -> None:
        """
        Play audio file asynchronously in a separate thread.
        Calls on_finish callback when playback completes or fails.
        """
        def _worker():
            try:
                if self._init_audio_device():
                    import pygame
                    pygame.mixer.music.load(str(audio_path))
                    pygame.mixer.music.play()
                    self.is_playing = True
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
                else:
                    # If no physical audio device is attached (e.g. headless WSL),
                    # simulate short speech duration so talking animation runs briefly
                    file_size = audio_path.stat().st_size
                    # Approx 3-4 seconds per 30KB
                    duration = max(2.0, min(8.0, file_size / 8000.0))
                    import time
                    time.sleep(duration)
            except Exception as e:
                print(f"[TTSService] Lỗi khi phát âm thanh: {e}")
            finally:
                self.is_playing = False
                if on_finish:
                    on_finish()

        threading.Thread(target=_worker, daemon=True).start()
