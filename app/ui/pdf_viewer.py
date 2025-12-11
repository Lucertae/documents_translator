"""
LAC Translate - Enterprise PDF Viewer
Premium viewer component with zoom and pan capabilities
© 2026 Design System - Obsidian Glass
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QSlider, QPushButton
)
from PySide6.QtCore import Qt, Signal, QPoint, QTimer
from PySide6.QtGui import QPixmap, QImage, QWheelEvent
import logging


class PDFViewerWidget(QWidget):
    """
    Premium PDF viewer with zoom and pan capabilities.
    Designed for legal and enterprise professionals.
    """

    page_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._zoom_level = 1.0
        self._min_zoom = 0.25
        self._max_zoom = 4.0
        self._current_pixmap = None
        self._is_panning = False
        self._last_pan_point = QPoint()

        self._init_ui()

    def _init_ui(self):
        """Initialize premium interface components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Apply Obsidian Glass styling
        self.setStyleSheet("""
            /* ═══════════════════════════════════════════════════════════════
               OBSIDIAN GLASS - PDF Viewer Component
               ═══════════════════════════════════════════════════════════════ */
            
            QScrollArea {
                background: #0a0a0c;
                border: none;
            }
            
            QLabel#pdf_page {
                background: #fafafa;
                padding: 0;
                border: none;
            }
            
            QLabel#placeholder {
                font-size: 13px;
                font-weight: 500;
                color: #3f3f46;
                background: transparent;
            }
            
            /* Scrollbars */
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #27272a;
                border-radius: 4px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background: #3f3f46;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
            }
            
            QScrollBar:horizontal {
                background: transparent;
                height: 8px;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background: #27272a;
                border-radius: 4px;
                min-width: 40px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #3f3f46;
            }
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0;
            }
        """)

        # Scroll area for PDF content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignCenter)

        # Label to display PDF page
        self.pdf_label = QLabel()
        self.pdf_label.setObjectName("pdf_page")
        self.pdf_label.setAlignment(Qt.AlignCenter)
        self.pdf_label.setScaledContents(False)

        self.scroll_area.setWidget(self.pdf_label)
        layout.addWidget(self.scroll_area, 1)

        # Zoom control bar
        self._create_zoom_bar(layout)

        # Enable mouse tracking for pan
        self.pdf_label.setMouseTracking(True)
        self.scroll_area.setMouseTracking(True)

    def _create_zoom_bar(self, parent_layout):
        """Create premium zoom control bar."""
        bar = QWidget()
        bar.setObjectName("zoom_bar")
        bar.setFixedHeight(44)
        bar.setStyleSheet("""
            QWidget#zoom_bar {
                background: #0f0f12;
                border-top: 1px solid #1f1f23;
            }
            
            QLabel {
                font-size: 11px;
                font-weight: 600;
                
                color: #71717a;
                background: transparent;
                padding: 0;
            }
            
            QPushButton#zoom_btn {
                font-size: 14px;
                font-weight: 500;
                color: #71717a;
                background: transparent;
                border: 1px solid #27272a;
                border-radius: 6px;
                padding: 0;
            }
            QPushButton#zoom_btn:hover {
                color: #e4e4e7;
                background: #18181b;
                border-color: #3f3f46;
            }
            QPushButton#zoom_btn:pressed {
                background: #0f0f12;
            }
            
            QSlider::groove:horizontal {
                height: 4px;
                background: #27272a;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #10b981;
                border: none;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #34d399;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10b981, stop:1 #059669);
                border-radius: 2px;
            }
        """)
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        # Zoom out button
        btn_out = QPushButton("−")
        btn_out.setObjectName("zoom_btn")
        btn_out.setFixedSize(28, 28)
        btn_out.clicked.connect(self.zoom_out)
        layout.addWidget(btn_out)

        # Zoom slider
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(int(self._min_zoom * 100))
        self.zoom_slider.setMaximum(int(self._max_zoom * 100))
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(160)
        self.zoom_slider.valueChanged.connect(self._on_zoom_slider_changed)
        layout.addWidget(self.zoom_slider)

        # Zoom in button
        btn_in = QPushButton("+")
        btn_in.setObjectName("zoom_btn")
        btn_in.setFixedSize(28, 28)
        btn_in.clicked.connect(self.zoom_in)
        layout.addWidget(btn_in)

        layout.addSpacing(8)

        # Zoom percentage label
        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(48)
        self.zoom_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.zoom_label)

        layout.addStretch()

        # Fit button
        btn_fit = QPushButton("Fit")
        btn_fit.setObjectName("zoom_btn")
        btn_fit.setFixedSize(40, 28)
        btn_fit.clicked.connect(self.zoom_fit)
        layout.addWidget(btn_fit)

        parent_layout.addWidget(bar)

    def _on_zoom_slider_changed(self, value):
        """Handle zoom slider value change."""
        zoom = value / 100.0
        self.set_zoom(zoom)

    def display_page(self, image_data: bytes, width: int, height: int):
        """
        Display PDF page from image data.

        Args:
            image_data: PNG image bytes
            width: Original image width
            height: Original image height
        """
        try:
            qimage = QImage.fromData(image_data, "PNG")
            if qimage.isNull():
                logging.error("Failed to load image data")
                return

            self._current_pixmap = QPixmap.fromImage(qimage)
            self._update_display()

        except Exception as e:
            logging.error(f"Failed to display page: {e}")

    def _update_display(self):
        """Update display with current zoom level."""
        if not self._current_pixmap:
            return

        scaled_pixmap = self._current_pixmap.scaled(
            self._current_pixmap.size() * self._zoom_level,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.pdf_label.setPixmap(scaled_pixmap)
        self.pdf_label.adjustSize()

        zoom_percent = int(self._zoom_level * 100)
        self.zoom_label.setText(f"{zoom_percent}%")

    def set_zoom(self, zoom_level: float):
        """
        Set zoom level.

        Args:
            zoom_level: Zoom factor (1.0 = 100%)
        """
        zoom_level = max(self._min_zoom, min(self._max_zoom, zoom_level))

        if abs(zoom_level - self._zoom_level) < 0.01:
            return

        # Store scroll position
        h_scroll = self.scroll_area.horizontalScrollBar()
        v_scroll = self.scroll_area.verticalScrollBar()
        h_ratio = h_scroll.value() / max(h_scroll.maximum(), 1)
        v_ratio = v_scroll.value() / max(v_scroll.maximum(), 1)

        self._zoom_level = zoom_level
        self._update_display()

        # Restore scroll position proportionally
        QTimer.singleShot(0, lambda: self._restore_scroll_position(h_ratio, v_ratio))

        # Update slider without triggering signal
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(int(zoom_level * 100))
        self.zoom_slider.blockSignals(False)

    def _restore_scroll_position(self, h_ratio, v_ratio):
        """Restore scroll position after zoom."""
        h_scroll = self.scroll_area.horizontalScrollBar()
        v_scroll = self.scroll_area.verticalScrollBar()
        h_scroll.setValue(int(h_scroll.maximum() * h_ratio))
        v_scroll.setValue(int(v_scroll.maximum() * v_ratio))

    def zoom_in(self):
        """Increase zoom level by 25%."""
        self.set_zoom(self._zoom_level * 1.25)

    def zoom_out(self):
        """Decrease zoom level by 25%."""
        self.set_zoom(self._zoom_level / 1.25)

    def zoom_fit(self):
        """Fit page to visible area."""
        if not self._current_pixmap:
            return

        viewport_size = self.scroll_area.viewport().size()
        pixmap_size = self._current_pixmap.size()

        width_ratio = viewport_size.width() / pixmap_size.width()
        height_ratio = viewport_size.height() / pixmap_size.height()

        zoom = min(width_ratio, height_ratio) * 0.95
        self.set_zoom(zoom)

    def zoom_reset(self):
        """Reset zoom to 100%."""
        self.set_zoom(1.0)

    def clear(self):
        """Clear displayed content."""
        self.pdf_label.clear()
        self.pdf_label.setObjectName("placeholder")
        self.pdf_label.setText("No document")
        self._current_pixmap = None

    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zoom."""
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

