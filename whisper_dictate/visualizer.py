"""
Google Assistant-style animated dot visualizer.

Displays animated dots that respond to audio input levels.
"""

import math
from typing import List

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QPainter, QRadialGradient
from PyQt6.QtWidgets import QWidget

# Color themes
THEMES = {
    "google": [
        QColor(66, 133, 244),  # Google Blue
        QColor(234, 67, 53),  # Google Red
        QColor(251, 188, 5),  # Google Yellow
        QColor(52, 168, 83),  # Google Green
    ],
    "blue": [
        QColor(30, 136, 229),
        QColor(66, 165, 245),
        QColor(100, 181, 246),
        QColor(144, 202, 249),
    ],
    "purple": [
        QColor(156, 39, 176),
        QColor(171, 71, 188),
        QColor(186, 104, 200),
        QColor(206, 147, 216),
    ],
    "mono": [
        QColor(255, 255, 255),
        QColor(200, 200, 200),
        QColor(255, 255, 255),
        QColor(200, 200, 200),
    ],
}

NUM_DOTS = 4


class DotVisualizer(QWidget):
    """Google Assistant-style animated dots that respond to audio."""

    def __init__(self, theme: str = "google"):
        super().__init__()
        self.dot_heights: List[float] = [0.3] * NUM_DOTS
        self.target_heights: List[float] = [0.3] * NUM_DOTS
        self.phase: float = 0
        self.audio_level: float = 0
        self.colors = THEMES.get(theme, THEMES["google"])

        self.setFixedSize(120, 40)

        # Animation timer
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.animate)
        self.anim_timer.start(30)  # ~33fps

    def set_theme(self, theme: str) -> None:
        """Set the color theme."""
        self.colors = THEMES.get(theme, THEMES["google"])

    def set_audio_level(self, level: float) -> None:
        """
        Set audio level for visualization.

        Args:
            level: Audio level from 0.0 to 1.0
        """
        self.audio_level = min(1.0, level * 2)  # Amplify for visibility

    def animate(self) -> None:
        """Update animation state."""
        self.phase += 0.15

        # Calculate target heights based on audio level and phase
        for i in range(NUM_DOTS):
            # Create wave effect with phase offset per dot
            wave = math.sin(self.phase + i * 0.8) * 0.5 + 0.5
            # Combine with audio level
            self.target_heights[i] = 0.2 + (wave * self.audio_level * 0.8)

        # Smooth interpolation
        for i in range(NUM_DOTS):
            self.dot_heights[i] += (self.target_heights[i] - self.dot_heights[i]) * 0.3

        self.update()

    def paintEvent(self, event) -> None:
        """Paint the animated dots."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        dot_radius = 8
        spacing = (width - NUM_DOTS * dot_radius * 2) / (NUM_DOTS + 1)

        for i in range(NUM_DOTS):
            x = spacing + i * (dot_radius * 2 + spacing) + dot_radius

            # Vertical position based on height
            dot_height = self.dot_heights[i]
            y_offset = (1 - dot_height) * (height * 0.3)
            y = height / 2 - y_offset

            # Scale dot size slightly with audio
            scale = 0.8 + dot_height * 0.4
            r = dot_radius * scale

            # Create gradient for 3D effect
            gradient = QRadialGradient(x - r * 0.3, y - r * 0.3, r * 1.5)
            color = self.colors[i % len(self.colors)]
            gradient.setColorAt(0, color.lighter(130))
            gradient.setColorAt(0.5, color)
            gradient.setColorAt(1, color.darker(120))

            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(x - r), int(y - r), int(r * 2), int(r * 2))

    def stop(self) -> None:
        """Stop the animation timer."""
        self.anim_timer.stop()
