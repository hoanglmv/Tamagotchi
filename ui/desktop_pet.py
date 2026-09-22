"""
Desktop Pet UI for myDeskAssistant.
Frameless, translucent, draggable PyQt6 window featuring characters from Sousou no Frieren
(Frieren, Fern, Stark, Himmel) with glassmorphic chat bubble.
"""

from typing import Optional, Dict
import sys
import math
from pathlib import Path

from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QPainter, QAction, QColor, QFont, QIcon, QTransform
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QMenu, QApplication, QFrame
)

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
CHARACTERS_DIR = ASSETS_DIR / "characters"

CHARACTER_PROFILES = {
    "frieren": {
        "name": "Frieren-sama",
        "title": "✨ Pháp sư Ngàn năm Frieren",
        "greeting": "Chào bạn... Mình là Frieren. Bạn cần mình tìm kiếm ma pháp hay kiểm tra máy tính không?",
        "file": "frieren.png"
    },
    "fern": {
        "name": "Fern",
        "title": "✨ Pháp sư Tập sự Fern",
        "greeting": "Em chào anh... Hôm nay anh làm việc chăm chỉ chứ ạ? Em có thể giúp anh kiểm tra máy tính hoặc sắp xếp file.",
        "file": "fern.png"
    },
    "stark": {
        "name": "Stark",
        "title": "⚡ Chiến binh Stark",
        "greeting": "Yo! Tôi là Stark đây! Có việc gì nặng nhọc trên máy tính cần giải quyết không?",
        "file": "stark.png"
    },
    "himmel": {
        "name": "Himmel",
        "title": "⚔️ Anh hùng dũng cảm Himmel",
        "greeting": "Chào bạn! Một ngày tuyệt vời đúng không? Là một dũng sĩ, tôi luôn sẵn sàng hỗ trợ bạn!",
        "file": "himmel.png"
    }
}


class GlassBubble(QFrame):
    """Glassmorphic speech bubble and interactive input frame."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("glassBubble")
        self.setStyleSheet("""
            #glassBubble {
                background-color: rgba(15, 23, 42, 0.92);
                border: 1px solid rgba(148, 163, 184, 0.35);
                border-radius: 18px;
            }
            QLabel {
                color: #F8FAFC;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            #speechLabel {
                font-size: 13px;
                line-height: 1.45;
                color: #F1F5F9;
                padding: 4px;
            }
            #statusBadge {
                font-size: 11px;
                font-weight: bold;
                color: #38BDF8;
                padding: 2px 8px;
                border-radius: 6px;
                background-color: rgba(56, 189, 248, 0.18);
            }
            QLineEdit {
                background-color: rgba(30, 41, 59, 0.85);
                border: 1px solid rgba(148, 163, 184, 0.3);
                border-radius: 10px;
                color: #FFFFFF;
                padding: 7px 12px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #818CF8;
                background-color: rgba(30, 41, 59, 0.98);
            }
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #8B5CF6);
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 7px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4F46E5, stop:1 #7C3AED);
            }
            QPushButton:pressed {
                background-color: #4338CA;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # Header with status badge
        header_layout = QHBoxLayout()
        self.name_label = QLabel(CHARACTER_PROFILES["frieren"]["title"])
        self.name_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #A5B4FC;")
        self.status_badge = QLabel("Sẵn sàng")
        self.status_badge.setObjectName("statusBadge")
        header_layout.addWidget(self.name_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_badge)
        layout.addLayout(header_layout)

        # Speech text label
        self.speech_label = QLabel(CHARACTER_PROFILES["frieren"]["greeting"])
        self.speech_label.setObjectName("speechLabel")
        self.speech_label.setWordWrap(True)
        self.speech_label.setMaximumWidth(290)
        layout.addWidget(self.speech_label)

        # Input row
        input_layout = QHBoxLayout()
        input_layout.setSpacing(6)
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Gõ tin nhắn gửi Frieren...")
        self.send_btn = QPushButton("Gửi")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)


class DesktopPet(QWidget):
    """Transparent, frameless, draggable Desktop Pet mascot with Frieren characters."""

    user_submitted_message = pyqtSignal(str)
    quick_action_requested = pyqtSignal(str)
    character_changed = pyqtSignal(str)

    def __init__(self, default_character: str = "frieren"):
        super().__init__()

        self.current_character = default_character
        self.current_state = "idle"  # 'idle', 'thinking', 'talking'
        self.drag_position = QPoint()
        self.animation_tick = 0

        # Load character pixmaps
        self.character_pixmaps: Dict[str, QPixmap] = {}
        self._load_character_pixmaps()

        self._init_window()
        self._init_ui()
        self._init_animation_timer()

    def _load_character_pixmaps(self):
        """Pre-load character images from disk."""
        for char_key, info in CHARACTER_PROFILES.items():
            png_path = CHARACTERS_DIR / info["file"]
            if png_path.exists():
                pix = QPixmap(str(png_path))
                # Scale smoothly to pet display size (approx 210x240)
                scaled = pix.scaled(210, 240, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.character_pixmaps[char_key] = scaled
            else:
                # Fallback empty pixmap
                p = QPixmap(210, 240)
                p.fill(Qt.GlobalColor.transparent)
                self.character_pixmaps[char_key] = p

    def _init_window(self):
        """Configure frameless, translucent, always-on-top window attributes."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(540, 320)

        # Position at bottom-right corner of screen
        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.availableGeometry()
            x = screen_geo.width() - self.width() - 40
            y = screen_geo.height() - self.height() - 40
            self.move(x, y)

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(12)

        # Mascot Label
        self.mascot_label = QLabel()
        self.mascot_label.setFixedSize(220, 250)
        self.mascot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mascot_label.setCursor(Qt.CursorShape.OpenHandCursor)
        self.mascot_label.setToolTip("Kéo thả bằng chuột trái • Click đúp để ẩn/hiện chat • Chuột phải để đổi nhân vật & menu")

        # Glass Chat Bubble
        self.bubble = GlassBubble(self)
        self.bubble.send_btn.clicked.connect(self._on_send_clicked)
        self.bubble.input_field.returnPressed.connect(self._on_send_clicked)

        main_layout.addWidget(self.mascot_label)
        main_layout.addWidget(self.bubble)

        self._render_mascot()

    def _init_animation_timer(self):
        """Subtle floating / breathing animation loop (12 FPS)."""
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._on_animation_frame)
        self.anim_timer.start(80)

    def _on_animation_frame(self):
        self.animation_tick += 1
        self._render_mascot()

    def set_character(self, char_key: str):
        """Switch current Frieren character."""
        if char_key in CHARACTER_PROFILES:
            self.current_character = char_key
            profile = CHARACTER_PROFILES[char_key]
            self.bubble.name_label.setText(profile["title"])
            self.bubble.input_field.setPlaceholderText(f"Gõ tin nhắn gửi {profile['name']}...")
            self.set_speech(profile["greeting"])
            self._render_mascot()
            self.character_changed.emit(char_key)

    def _render_mascot(self):
        """Render mascot with dynamic floating/breathing displacement and expression cues."""
        base_pixmap = self.character_pixmaps.get(self.current_character)
        if not base_pixmap or base_pixmap.isNull():
            return

        canvas = QPixmap(220, 250)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Floating calculation
        if self.current_state == "idle":
            offset_y = int(math.sin(self.animation_tick * 0.14) * 4)
            scale_pulse = 1.0 + (math.sin(self.animation_tick * 0.14) * 0.015)
        elif self.current_state == "thinking":
            offset_y = int(math.sin(self.animation_tick * 0.28) * 3)
            scale_pulse = 1.0
        elif self.current_state == "talking":
            offset_y = int(abs(math.sin(self.animation_tick * 0.38)) * -6)
            scale_pulse = 1.0 + (abs(math.sin(self.animation_tick * 0.38)) * 0.02)
        else:
            offset_y = 0
            scale_pulse = 1.0

        # Draw character centered with scale and offset
        w = int(base_pixmap.width() * scale_pulse)
        h = int(base_pixmap.height() * scale_pulse)
        x = (canvas.width() - w) // 2
        y = (canvas.height() - h) // 2 + offset_y

        painter.drawPixmap(x, y, w, h, base_pixmap)

        # Micro-icons based on state
        if self.current_state == "thinking":
            # Pondering sparkles/gear icon above head
            painter.setBrush(QColor(245, 158, 11, 220))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(canvas.width() - 35, 20 + offset_y, 14, 14)
            painter.drawEllipse(canvas.width() - 45, 38 + offset_y, 7, 7)
        elif self.current_state == "talking":
            # Musical note / speech bubble cue
            painter.setBrush(QColor(56, 189, 248, 220))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(canvas.width() - 32, 24 + offset_y, 10, 10)

        painter.end()
        self.mascot_label.setPixmap(canvas)

    def set_state(self, state: str, status_text: Optional[str] = None):
        """Update mascot visual state: 'idle' | 'thinking' | 'talking'."""
        self.current_state = state

        if status_text is not None:
            self.bubble.status_badge.setText(status_text)
            if state == "thinking":
                self.bubble.status_badge.setStyleSheet("font-size: 11px; font-weight: bold; color: #F59E0B; background-color: rgba(245, 158, 11, 0.2); padding: 2px 8px; border-radius: 6px;")
            elif state == "talking":
                self.bubble.status_badge.setStyleSheet("font-size: 11px; font-weight: bold; color: #34D399; background-color: rgba(52, 211, 153, 0.2); padding: 2px 8px; border-radius: 6px;")
            else:
                self.bubble.status_badge.setStyleSheet("font-size: 11px; font-weight: bold; color: #38BDF8; background-color: rgba(56, 189, 248, 0.18); padding: 2px 8px; border-radius: 6px;")

        self._render_mascot()

    def set_speech(self, text: str):
        """Update speech text in the bubble."""
        self.bubble.speech_label.setText(text)
        if not self.bubble.isVisible():
            self.bubble.show()

    def _on_send_clicked(self):
        text = self.bubble.input_field.text().strip()
        if text:
            self.bubble.input_field.clear()
            self.user_submitted_message.emit(text)

    # --- Mouse Event Handlers for Dragging ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.mascot_label.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.mascot_label.setCursor(Qt.CursorShape.OpenHandCursor)

    def mouseDoubleClickEvent(self, event):
        """Toggle bubble visibility on double click."""
        if self.bubble.isVisible():
            self.bubble.hide()
            self.resize(240, 270)
        else:
            self.resize(540, 320)
            self.bubble.show()
        event.accept()

    def contextMenuEvent(self, event):
        """Right-click context menu with character switcher and quick tools."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1E293B;
                color: #F8FAFC;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #4F46E5;
            }
        """)

        # Character switcher submenu
        char_menu = menu.addMenu("🌸 Chọn nhân vật đồng hành")
        for key, info in CHARACTER_PROFILES.items():
            action = QAction(f"{info['title']} {'✓' if key == self.current_character else ''}", self)
            action.triggered.connect(lambda checked, k=key: self.set_character(k))
            char_menu.addAction(action)

        menu.addSeparator()

        chat_action = QAction("💬 Ẩn/Hiện khung chat", self)
        chat_action.triggered.connect(lambda: self.mouseDoubleClickEvent(event))
        menu.addAction(chat_action)

        pc_action = QAction("⚡ Kiểm tra PC (CPU/RAM/Pin)", self)
        pc_action.triggered.connect(lambda: self.quick_action_requested.emit("Kiểm tra tình trạng máy tính giúp em nha!"))
        menu.addAction(pc_action)

        downloads_action = QAction("📂 Quét dọn Downloads", self)
        downloads_action.triggered.connect(lambda: self.quick_action_requested.emit("Quét dọn phân loại thư mục Downloads giúp em nhé!"))
        menu.addAction(downloads_action)

        menu.addSeparator()

        exit_action = QAction("🚪 Tạm biệt (Thoát ứng dụng)", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(exit_action)

        menu.exec(event.globalPos())
