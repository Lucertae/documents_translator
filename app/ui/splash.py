"""
Splash screen con barra di caricamento per LAC Translate.
Mostra un feedback visivo durante il caricamento dei moduli pesanti
(torch, transformers, modello OPUS-MT, motore OCR, ecc.).
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QPainter, QLinearGradient


class SplashScreen(QWidget):
    """Splash screen con barra di progresso e messaggi di stato."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(520, 300)

        # Centra sullo schermo
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                (geo.width() - self.width()) // 2,
                (geo.height() - self.height()) // 2,
            )

        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 32)
        layout.setSpacing(0)

        # Titolo
        title = QLabel("LAC Translate")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont("Segoe UI", 26, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #e8e8e8; background: transparent;")
        layout.addWidget(title)

        layout.addSpacing(4)

        # Sottotitolo
        subtitle = QLabel("Professional PDF Translation")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_font = QFont("Segoe UI", 11)
        subtitle.setFont(sub_font)
        subtitle.setStyleSheet("color: #9a9a9a; background: transparent;")
        layout.addWidget(subtitle)

        layout.addStretch()

        # Messaggio di stato
        self._status = QLabel("Avvio in corso…")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = QFont("Segoe UI", 10)
        self._status.setFont(status_font)
        self._status.setStyleSheet("color: #bbbbbb; background: transparent;")
        layout.addWidget(self._status)

        layout.addSpacing(12)

        # Barra di progresso
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(6)
        self._bar.setStyleSheet("""
            QProgressBar {
                background: #2a2a2a;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a9eff, stop:1 #7b68ee
                );
                border-radius: 3px;
            }
        """)
        layout.addWidget(self._bar)

        layout.addSpacing(16)

        # Versione
        from app.__version__ import __version__
        ver = QLabel(f"v{__version__}")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver_font = QFont("Segoe UI", 8)
        ver.setFont(ver_font)
        ver.setStyleSheet("color: #666666; background: transparent;")
        layout.addWidget(ver)

    # ------------------------------------------------------------------
    def paintEvent(self, event):
        """Sfondo scuro con gradiente sottile."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor("#1e1e2e"))
        grad.setColorAt(1.0, QColor("#161622"))
        p.setBrush(grad)
        p.setPen(QColor("#333344"))
        p.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 12, 12)
        p.end()

    # ------------------------------------------------------------------
    def set_progress(self, value: int, message: str):
        """Aggiorna barra e messaggio di stato."""
        self._bar.setValue(min(value, 100))
        self._status.setText(message)
        # Forza il ridisegno immediato
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
