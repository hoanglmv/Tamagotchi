"""
Desktop Pet UI for myDeskAssistant.
Enhanced with dynamic eye blinking, mouth lip-sync animations,
interactive anime dances (Sway, Hop, Spin), and multiple character expressions.
"""

from typing import Optional, Dict, List
import sys
import math
import random
from pathlib import Path

from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import (
    QPixmap, QPainter, QAction, QColor, QFont, QPen,
    QTransform, QBrush, QPainterPath
)
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QMenu, QApplication, QFrame
)

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
CHARACTERS_DIR = ASSETS_DIR / "characters"

CHARACTER_PROFILES = {
    "frieren": {
        "name": "Frieren",
        "title": "✨ Pháp sư Ngàn năm Frieren",
        "greeting": "Chào bạn... Mình là Frieren. Bạn cần mình tìm kiếm ma pháp, kiểm tra máy tính hay nhảy một điệu không?",
        "idle_file": "frieren.png",
        "special_file": "frieren_mimic.png",
        "special_name": "Kẹt trong rương Mimic 📦",
        "eye_y": 95,
        "mouth_y": 128
    },
    "fern": {
        "name": "Fern",
        "title": "✨ Pháp sư Tập sự Fern",
        "greeting": "Em chào anh... Hôm nay anh làm việc chăm chỉ chứ ạ? Đừng để em phải nhắc nhiều đó nhé! (´・ω・｀)",
        "idle_file": "fern.png",
        "special_file": "fern_pout.png",
        "special_name": "Phồng má giận dỗi (Pout) 😾",
        "eye_y": 90,
        "mouth_y": 120
    },
    "stark": {
        "name": "Stark",
        "title": "⚡ Chiến binh Stark",
        "greeting": "Yo! Tôi là Stark đây! Có việc gì nặng nhọc cần chiến binh ra tay không? Hay là cùng nhảy ăn mừng nào!",
        "idle_file": "stark.png",
        "special_file": "stark_scared.png",
        "special_name": "Hoảng sợ tột độ 😱",
        "eye_y": 90,
        "mouth_y": 122
    },
    "himmel": {
        "name": "Himmel",
        "title": "⚔️ Anh hùng dũng cảm Himmel",
        "greeting": "Chào bạn! Một ngày tuyệt vời đúng không? Hãy nhìn kỹ dáng vẻ đẹp trai và điệu nhảy anh dũng này của tôi nhé!",
        "idle_file": "himmel.png",
        "special_file": "himmel_proud.png",
        "special_name": "Nháy mắt tự luyến ✨",
        "eye_y": 90,
        "mouth_y": 122
    }
}


class FloatingParticle:
    """Cute floating hearts and stars when interacting with the pet."""
    def __init__(self, x: float, y: float, symbol: str = "♥", color: QColor = QColor(244, 63, 94)):
        self.x = x
        self.y = y
        self.symbol = symbol
        self.color = color
        self.alpha = 255
        self.vx = random.uniform(-0.8, 0.8)
        self.vy = random.uniform(-2.5, -1.2)
        self.size = random.randint(14, 20)

    def update(self) -> bool:
        self.x += self.vx
        self.y += self.vy
        self.alpha -= 8
        return self.alpha > 0


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
            .danceBtn {
                background-color: rgba(99, 102, 241, 0.25);
                border: 1px solid rgba(129, 140, 248, 0.4);
                border-radius: 8px;
                color: #C7D2FE;
                font-size: 11px;
                padding: 3px 8px;
            }
            .danceBtn:hover {
                background-color: rgba(99, 102, 241, 0.5);
                color: #FFFFFF;
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
            #sendBtn {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #8B5CF6);
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 7px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            #sendBtn:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4F46E5, stop:1 #7C3AED);
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

        # Quick interaction dance buttons row
        dance_row = QHBoxLayout()
        dance_row.setSpacing(6)
        self.sway_btn = QPushButton("💃 Lắc lư")
        self.sway_btn.setProperty("class", "danceBtn")
        self.sway_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.hop_btn = QPushButton("🦘 Nhảy cẫng")
        self.hop_btn.setProperty("class", "danceBtn")
        self.hop_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.spin_btn = QPushButton("🌀 Xoay tròn")
        self.spin_btn.setProperty("class", "danceBtn")
        self.spin_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        dance_row.addWidget(self.sway_btn)
        dance_row.addWidget(self.hop_btn)
        dance_row.addWidget(self.spin_btn)
        dance_row.addStretch()
        layout.addLayout(dance_row)

        # Input row
        input_layout = QHBoxLayout()
        input_layout.setSpacing(6)
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Gõ tin nhắn gửi Frieren...")
        self.send_btn = QPushButton("Gửi")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)


class DesktopPet(QWidget):
    """
    Transparent, frameless Desktop Pet with eye blinking, mouth lip-sync,
    special expressions, and multiple anime dances.
    """

    user_submitted_message = pyqtSignal(str)
    quick_action_requested = pyqtSignal(str)
    character_changed = pyqtSignal(str)

    def __init__(self, default_character: str = "frieren"):
        super().__init__()

        self.current_character = default_character
        self.current_state = "idle"       # 'idle', 'thinking', 'talking'
        self.active_expression = "idle"   # 'idle' or 'special'
        self.dance_mode = None            # None, 'sway', 'hop', 'spin'
        self.dance_duration_ticks = 0

        self.drag_position = QPoint()
        self.animation_tick = 0
        self.is_blinking = False
        self.particles: List[FloatingParticle] = []

        # Load pixmaps
        self.pixmaps_idle: Dict[str, QPixmap] = {}
        self.pixmaps_special: Dict[str, QPixmap] = {}
        self._load_character_pixmaps()

        self._init_window()
        self._init_ui()
        self._init_animation_timer()
        self._init_blink_timer()

    def _load_character_pixmaps(self):
        """Pre-load idle and special expression images from disk."""
        for char_key, info in CHARACTER_PROFILES.items():
            idle_path = CHARACTERS_DIR / info["idle_file"]
            if idle_path.exists():
                pix = QPixmap(str(idle_path)).scaled(
                    210, 240,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.pixmaps_idle[char_key] = pix

            special_path = CHARACTERS_DIR / info["special_file"]
            if special_path.exists():
                pix_sp = QPixmap(str(special_path)).scaled(
                    210, 240,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.pixmaps_special[char_key] = pix_sp

    def _init_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(540, 320)

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
        self.mascot_label.setFixedSize(220, 260)
        self.mascot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mascot_label.setCursor(Qt.CursorShape.OpenHandCursor)
        self.mascot_label.setToolTip("Click chuột trái để xoa đầu • Kéo thả chuột • Click đúp để ẩn/hiện chat • Chuột phải để mở menu")

        # Glass Chat Bubble
        self.bubble = GlassBubble(self)
        self.bubble.send_btn.clicked.connect(self._on_send_clicked)
        self.bubble.input_field.returnPressed.connect(self._on_send_clicked)

        # Connect dance buttons
        self.bubble.sway_btn.clicked.connect(lambda: self.start_dance("sway"))
        self.bubble.hop_btn.clicked.connect(lambda: self.start_dance("hop"))
        self.bubble.spin_btn.clicked.connect(lambda: self.start_dance("spin"))

        main_layout.addWidget(self.mascot_label)
        main_layout.addWidget(self.bubble)

        self._render_mascot()

    def _init_animation_timer(self):
        """Frame update timer (approx 20 FPS)."""
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._on_animation_frame)
        self.anim_timer.start(50)

    def _init_blink_timer(self):
        """Natural eye blinking timer every 3-5 seconds."""
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self._trigger_blink)
        self.blink_timer.start(random.randint(3000, 4800))

    def _trigger_blink(self):
        if self.active_expression == "idle" and self.current_state != "talking":
            self.is_blinking = True
            QTimer.singleShot(160, self._stop_blink)
        self.blink_timer.start(random.randint(3200, 5200))

    def _stop_blink(self):
        self.is_blinking = False

    def start_dance(self, dance_type: str, duration_seconds: float = 6.0):
        """Trigger an animated dance move (sway, hop, spin)."""
        self.dance_mode = dance_type
        self.dance_duration_ticks = int(duration_seconds * 20)
        # Spawn celebration particles
        for _ in range(5):
            self.particles.append(FloatingParticle(
                x=random.randint(80, 140),
                y=random.randint(40, 90),
                symbol=random.choice(["♪", "♫", "✨", "♥"]),
                color=QColor(random.choice(["#F43F5E", "#8B5CF6", "#38BDF8", "#FBBF24"]))
            ))
        dance_names = {"sway": "Đang lắc lư 💃", "hop": "Nhảy chân sáo 🦘", "spin": "Xoay tròn 🌀"}
        self.bubble.status_badge.setText(dance_names.get(dance_type, "Đang nhảy"))

    def set_expression(self, expression_type: str):
        """Switch between 'idle' (normal) and 'special' (mimic, pout, scared, proud)."""
        self.active_expression = expression_type
        self._render_mascot()

    def set_character(self, char_key: str):
        """Switch current character."""
        if char_key in CHARACTER_PROFILES:
            self.current_character = char_key
            self.active_expression = "idle"
            self.dance_mode = None
            profile = CHARACTER_PROFILES[char_key]
            self.bubble.name_label.setText(profile["title"])
            self.bubble.input_field.setPlaceholderText(f"Gõ tin nhắn gửi {profile['name']}...")
            self.set_speech(profile["greeting"])
            self._render_mascot()
            self.character_changed.emit(char_key)

    def _on_animation_frame(self):
        self.animation_tick += 1

        # Check dance duration countdown
        if self.dance_mode:
            self.dance_duration_ticks -= 1
            if self.dance_duration_ticks <= 0:
                self.dance_mode = None
                self.bubble.status_badge.setText("Sẵn sàng")

        # Update particles
        self.particles = [p for p in self.particles if p.update()]

        self._render_mascot()

    def _render_mascot(self):
        """Render character with breathing, dance transforms, blinking eyes, and mouth lip-sync."""
        # Choose base pixmap
        if self.active_expression == "special" and self.current_character in self.pixmaps_special:
            base_pixmap = self.pixmaps_special[self.current_character]
        else:
            base_pixmap = self.pixmaps_idle.get(self.current_character)

        if not base_pixmap or base_pixmap.isNull():
            return

        canvas = QPixmap(220, 260)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Transform calculations
        angle = 0.0
        scale_x = 1.0
        scale_y = 1.0
        offset_y = 0

        if self.dance_mode == "sway":
            # Sway left and right with rotation and soft vertical dip
            angle = math.sin(self.animation_tick * 0.22) * 11.0
            offset_y = int(-abs(math.sin(self.animation_tick * 0.22)) * 8)
            # Add rhythmic notes occasionally
            if self.animation_tick % 15 == 0:
                self.particles.append(FloatingParticle(110, 50, random.choice(["♪", "♫"]), QColor("#818CF8")))

        elif self.dance_mode == "hop":
            # Happy jumping with squash and stretch
            jump_phase = math.sin(self.animation_tick * 0.35)
            if jump_phase > 0:
                # In air: stretched tall
                offset_y = int(-jump_phase * 22)
                scale_y = 1.0 + (jump_phase * 0.08)
                scale_x = 1.0 - (jump_phase * 0.05)
            else:
                # Landed: squished wide
                offset_y = 0
                scale_y = 1.0 + (jump_phase * 0.06)
                scale_x = 1.0 - (jump_phase * 0.06)

        elif self.dance_mode == "spin":
            # 3D Pirouette spin flip
            scale_x = math.cos(self.animation_tick * 0.3)
            offset_y = int(math.sin(self.animation_tick * 0.3) * 4)

        else:
            # Normal idle / talking floating breathing
            if self.current_state == "idle":
                offset_y = int(math.sin(self.animation_tick * 0.12) * 4)
                scale_y = 1.0 + (math.sin(self.animation_tick * 0.12) * 0.012)
            elif self.current_state == "thinking":
                offset_y = int(math.sin(self.animation_tick * 0.25) * 3)
            elif self.current_state == "talking":
                # Lively talk bounce
                offset_y = int(abs(math.sin(self.animation_tick * 0.35)) * -5)
                scale_y = 1.0 + (abs(math.sin(self.animation_tick * 0.35)) * 0.02)

        # Draw transformed character
        center_x = canvas.width() / 2.0
        center_y = canvas.height() / 2.0 + 10 + offset_y

        transform = QTransform()
        transform.translate(center_x, center_y)
        transform.rotate(angle)
        transform.scale(scale_x, scale_y)
        transform.translate(-base_pixmap.width() / 2.0, -base_pixmap.height() / 2.0)

        painter.setTransform(transform)
        painter.drawPixmap(0, 0, base_pixmap)

        # Reset transform for drawing facial overlays on top
        painter.resetTransform()

        # Facial Overlays (Blinking & Mouth movement)
        if self.active_expression == "idle":
            # 1. Eye Blinking
            if self.is_blinking:
                self._draw_blinking_eyes(painter, center_x, center_y + offset_y)

            # 2. Talking Mouth Lip-sync
            if self.current_state == "talking":
                self._draw_talking_mouth(painter, center_x, center_y + offset_y)

        # Draw floating particles
        for p in self.particles:
            painter.setPen(QColor(p.color.red(), p.color.green(), p.color.blue(), p.alpha))
            font = QFont("Segoe UI Emoji, Arial", p.size, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(int(p.x), int(p.y), p.symbol)

        painter.end()
        self.mascot_label.setPixmap(canvas)

    def _draw_blinking_eyes(self, painter: QPainter, cx: float, cy: float):
        """Draw cute smiling closed eye arcs (^^) during blink."""
        pen = QPen(QColor(49, 46, 129), 3.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Left and right eye arcs
        eye_y = int(cy - 20)
        # Left eye arc
        painter.drawArc(int(cx - 32), eye_y, 18, 12, 30 * 16, 120 * 16)
        # Right eye arc
        painter.drawArc(int(cx + 14), eye_y, 18, 12, 30 * 16, 120 * 16)

    def _draw_talking_mouth(self, painter: QPainter, cx: float, cy: float):
        """Animate mouth opening/closing with speech rhythm."""
        # 4-stage mouth animation
        cycle = (self.animation_tick // 2) % 4
        if cycle in [1, 2]:
            mouth_y = int(cy + 6)
            mouth_h = 7 if cycle == 1 else 10
            
            # Mouth opening
            painter.setPen(QPen(QColor(190, 18, 60), 1.5))
            painter.setBrush(QColor(225, 29, 72))
            painter.drawEllipse(int(cx - 5), mouth_y, 10, mouth_h)
            
            # Cute tongue inside
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(253, 164, 175))
            painter.drawEllipse(int(cx - 3), mouth_y + 4, 6, 4)

    def set_state(self, state: str, status_text: Optional[str] = None):
        """Update mascot visual state: 'idle' | 'thinking' | 'talking'."""
        self.current_state = state

        if status_text is not None and not self.dance_mode:
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

    # --- Mouse Interactions: Petting, Dragging, Context Menu ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.mascot_label.setCursor(Qt.CursorShape.ClosedHandCursor)
            
            # Interactive petting reaction: spawn hearts!
            self.particles.append(FloatingParticle(
                x=event.position().x(),
                y=event.position().y(),
                symbol="♥",
                color=QColor("#F43F5E")
            ))
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.mascot_label.setCursor(Qt.CursorShape.OpenHandCursor)

    def mouseDoubleClickEvent(self, event):
        """Toggle bubble visibility or trigger jump."""
        if self.bubble.isVisible():
            self.bubble.hide()
            self.resize(240, 280)
        else:
            self.resize(540, 320)
            self.bubble.show()
        event.accept()

    def contextMenuEvent(self, event):
        """Right-click menu with character selection, dance moves, and special expressions."""
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

        # Character switch submenu
        char_menu = menu.addMenu("🌸 Chọn nhân vật đồng hành")
        for key, info in CHARACTER_PROFILES.items():
            action = QAction(f"{info['title']} {'✓' if key == self.current_character else ''}", self)
            action.triggered.connect(lambda checked, k=key: self.set_character(k))
            char_menu.addAction(action)

        # Expressions submenu
        expr_menu = menu.addMenu("🎭 Biểu cảm nhân vật")
        normal_act = QAction(f"Bình thường (Idle) {'✓' if self.active_expression == 'idle' else ''}", self)
        normal_act.triggered.connect(lambda: self.set_expression("idle"))
        expr_menu.addAction(normal_act)

        current_info = CHARACTER_PROFILES[self.current_character]
        special_act = QAction(f"{current_info['special_name']} {'✓' if self.active_expression == 'special' else ''}", self)
        special_act.triggered.connect(lambda: self.set_expression("special"))
        expr_menu.addAction(special_act)

        # Dance submenu
        dance_menu = menu.addMenu("💃 Điệu nhảy & Chuyển động")
        sway_act = QAction("Lắc lư sang hai bên (Sway)", self)
        sway_act.triggered.connect(lambda: self.start_dance("sway"))
        dance_menu.addAction(sway_act)

        hop_act = QAction("Nhảy chân sáo ăn mừng (Happy Hop)", self)
        hop_act.triggered.connect(lambda: self.start_dance("hop"))
        dance_menu.addAction(hop_act)

        spin_act = QAction("Xoay tròn 3D (Pirouette Spin)", self)
        spin_act.triggered.connect(lambda: self.start_dance("spin"))
        dance_menu.addAction(spin_act)

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
