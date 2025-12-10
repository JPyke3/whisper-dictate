"""Tests for the visualizer module."""

import os

import pytest

# Skip Qt tests if no display is available
pytestmark = pytest.mark.skipif(
    os.environ.get("DISPLAY") is None and os.environ.get("WAYLAND_DISPLAY") is None,
    reason="No display available for Qt tests",
)


class TestDotVisualizer:
    """Test DotVisualizer widget."""

    def test_init_default_theme(self, qtbot):
        """Test DotVisualizer initialization with default theme."""
        from whisper_dictate.visualizer import DotVisualizer

        widget = DotVisualizer()
        qtbot.addWidget(widget)

        assert widget.colors is not None
        assert len(widget.dot_heights) == 4
        assert widget.audio_level == 0

    def test_init_custom_theme(self, qtbot):
        """Test DotVisualizer initialization with custom theme."""
        from whisper_dictate.visualizer import THEMES, DotVisualizer

        widget = DotVisualizer(theme="blue")
        qtbot.addWidget(widget)

        assert widget.colors == THEMES["blue"]

    def test_init_invalid_theme_falls_back_to_google(self, qtbot):
        """Test invalid theme falls back to google."""
        from whisper_dictate.visualizer import THEMES, DotVisualizer

        widget = DotVisualizer(theme="nonexistent")
        qtbot.addWidget(widget)

        assert widget.colors == THEMES["google"]

    def test_set_theme(self, qtbot):
        """Test changing theme."""
        from whisper_dictate.visualizer import THEMES, DotVisualizer

        widget = DotVisualizer(theme="google")
        qtbot.addWidget(widget)

        widget.set_theme("purple")
        assert widget.colors == THEMES["purple"]

    def test_set_audio_level(self, qtbot):
        """Test setting audio level."""
        from whisper_dictate.visualizer import DotVisualizer

        widget = DotVisualizer()
        qtbot.addWidget(widget)

        widget.set_audio_level(0.5)
        assert widget.audio_level == 1.0  # Amplified by 2x

    def test_set_audio_level_capped_at_one(self, qtbot):
        """Test audio level is capped at 1.0."""
        from whisper_dictate.visualizer import DotVisualizer

        widget = DotVisualizer()
        qtbot.addWidget(widget)

        widget.set_audio_level(2.0)
        assert widget.audio_level == 1.0

    def test_animate_updates_heights(self, qtbot):
        """Test animation updates dot heights."""
        from whisper_dictate.visualizer import DotVisualizer

        widget = DotVisualizer()
        qtbot.addWidget(widget)

        initial_heights = widget.dot_heights.copy()
        widget.audio_level = 1.0

        # Trigger animation
        widget.animate()

        # Heights should have changed
        assert widget.dot_heights != initial_heights

    def test_stop_stops_timer(self, qtbot):
        """Test stop() stops the animation timer."""
        from whisper_dictate.visualizer import DotVisualizer

        widget = DotVisualizer()
        qtbot.addWidget(widget)

        assert widget.anim_timer.isActive()
        widget.stop()
        assert not widget.anim_timer.isActive()

    def test_widget_size(self, qtbot):
        """Test widget has correct fixed size."""
        from whisper_dictate.visualizer import DotVisualizer

        widget = DotVisualizer()
        qtbot.addWidget(widget)

        assert widget.width() == 120
        assert widget.height() == 40

    def test_paint_event_does_not_crash(self, qtbot):
        """Test paintEvent executes without error."""
        from whisper_dictate.visualizer import DotVisualizer

        widget = DotVisualizer()
        qtbot.addWidget(widget)

        # Show widget to trigger paint
        widget.show()
        qtbot.waitExposed(widget)

        # If we get here without crash, test passes


class TestThemes:
    """Test theme definitions."""

    def test_all_themes_have_four_colors(self):
        """Test all themes have exactly 4 colors."""
        from whisper_dictate.visualizer import THEMES

        for name, colors in THEMES.items():
            assert len(colors) == 4, f"Theme '{name}' should have 4 colors"

    def test_google_theme_exists(self):
        """Test google theme is defined."""
        from whisper_dictate.visualizer import THEMES

        assert "google" in THEMES

    def test_all_themes_are_qcolors(self):
        """Test all theme colors are QColor instances."""
        from PyQt6.QtGui import QColor

        from whisper_dictate.visualizer import THEMES

        for name, colors in THEMES.items():
            for color in colors:
                assert isinstance(color, QColor), f"Theme '{name}' has non-QColor"
