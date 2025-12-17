"""
LAC Translate - Enterprise PDF Translation Suite
Premium interface for legal professionals and enterprises
© 2026 Design System - Obsidian Glass
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QFileDialog,
    QMessageBox, QProgressBar, QSplitter, QFrame,
    QStatusBar, QGraphicsDropShadowEffect, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QPropertyAnimation, QEasingCurve, Property, QSize
from PySide6.QtGui import QAction, QKeySequence, QFont, QColor, QPainter, QLinearGradient, QPainterPath, QIcon, QPen
import qtawesome as qta
import logging
from pathlib import Path

from .pdf_viewer import PDFViewerWidget
from ..core import TranslationEngine, PDFProcessor


class TranslationWorker(QThread):
    """Background worker for translation operations."""
    
    progress = Signal(int, int)
    finished = Signal(object)
    error = Signal(str)
    
    def __init__(self, pdf_processor, translator, page_num):
        super().__init__()
        self.pdf_processor = pdf_processor
        self.translator = translator
        self.page_num = page_num
        
    def run(self):
        try:
            translated_doc = self.pdf_processor.translate_page(
                self.page_num,
                self.translator
            )
            self.finished.emit(translated_doc)
        except Exception as e:
            self.error.emit(str(e))


class GlowButton(QPushButton):
    """Premium button with animated glow effect and FontAwesome icons."""
    
    def __init__(self, text="", icon_name=None, accent=False, parent=None):
        super().__init__(text, parent)
        self.accent = accent
        self._glow_opacity = 0.0
        self.setMouseTracking(True)
        
        # Set FontAwesome icon if provided
        if icon_name:
            icon_color = '#ffffff' if accent else '#e4e4e7'
            self.setIcon(qta.icon(icon_name, color=icon_color))
            self.setIconSize(QSize(18, 18))
        
        # Glow animation
        self._glow_anim = QPropertyAnimation(self, b"glow_opacity")
        self._glow_anim.setDuration(200)
        self._glow_anim.setEasingCurve(QEasingCurve.OutCubic)
    
    def get_glow_opacity(self):
        return self._glow_opacity
    
    def set_glow_opacity(self, value):
        self._glow_opacity = value
        self.update()
    
    glow_opacity = Property(float, get_glow_opacity, set_glow_opacity)
    
    def enterEvent(self, event):
        self._glow_anim.stop()
        self._glow_anim.setStartValue(self._glow_opacity)
        self._glow_anim.setEndValue(1.0)
        self._glow_anim.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._glow_anim.stop()
        self._glow_anim.setStartValue(self._glow_opacity)
        self._glow_anim.setEndValue(0.0)
        self._glow_anim.start()
        super().leaveEvent(event)


class DocumentPanel(QFrame):
    """Floating document panel with premium styling."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.setObjectName("document_panel")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setObjectName("panel_header")
        header.setFixedHeight(44)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        # Status indicator dot
        self.status_dot = QLabel("●")
        self.status_dot.setObjectName("status_dot")
        header_layout.addWidget(self.status_dot)
        
        title_label = QLabel(title)
        title_label.setObjectName("panel_title")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # Content area
        self.content_area = QWidget()
        self.content_area.setObjectName("panel_content")
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(1, 0, 1, 1)
        
        self.viewer = PDFViewerWidget()
        content_layout.addWidget(self.viewer)
        
        layout.addWidget(self.content_area, 1)
    
    def set_active(self, active: bool):
        """Set panel active state."""
        color = "#10b981" if active else "#475569"
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 8px;")


class MainWindow(QMainWindow):
    """
    LAC Translate Enterprise Edition
    Premium interface for professional document translation
    """
    
    def __init__(self):
        super().__init__()
        
        self.pdf_processor = None
        self.translator = None
        self.current_page = 0
        self.translated_pages = {}
        self.translation_worker = None
        
        self._init_ui()
        self._create_actions()
        self._create_menus()
        self._apply_premium_stylesheet()
        
        source_code = TranslationEngine.get_language_code("English")
        target_code = TranslationEngine.get_language_code("Italiano")
        self.translator = TranslationEngine(source_code, target_code)
        
        logging.info("LAC Translate Enterprise initialized")
    
    def _init_ui(self):
        """Initialize premium enterprise interface."""
        self.setWindowTitle("LAC Translate")
        self.setGeometry(50, 50, 1800, 1000)
        self.setMinimumSize(1400, 800)
        
        # Central widget
        central = QWidget()
        central.setObjectName("central_widget")
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top bar with branding
        top_bar = self._create_top_bar()
        main_layout.addWidget(top_bar)
        
        # Main content area
        content = QWidget()
        content.setObjectName("main_content")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 24)
        content_layout.setSpacing(20)
        
        # Left sidebar - Controls
        sidebar = self._create_sidebar()
        content_layout.addWidget(sidebar)
        
        # Document panels
        panels_container = QWidget()
        panels_layout = QHBoxLayout(panels_container)
        panels_layout.setContentsMargins(0, 0, 0, 0)
        panels_layout.setSpacing(16)
        
        # Original document panel
        self.original_panel = DocumentPanel("SOURCE DOCUMENT")
        self.original_panel.set_active(False)
        panels_layout.addWidget(self.original_panel)
        
        # Translated document panel
        self.translated_panel = DocumentPanel("TRANSLATION OUTPUT")
        self.translated_panel.set_active(False)
        panels_layout.addWidget(self.translated_panel)
        
        # Shortcuts
        self.original_viewer = self.original_panel.viewer
        self.translated_viewer = self.translated_panel.viewer
        
        content_layout.addWidget(panels_container, 1)
        
        main_layout.addWidget(content, 1)
        
        # Bottom status bar
        self._create_statusbar()
    
    def _create_top_bar(self) -> QWidget:
        """Create premium top bar with branding."""
        bar = QWidget()
        bar.setObjectName("top_bar")
        bar.setFixedHeight(64)
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(28, 0, 28, 0)
        layout.setSpacing(16)
        
        # Logo / Brand
        brand = QLabel("LAC")
        brand.setObjectName("brand_logo")
        layout.addWidget(brand)
        
        brand_sub = QLabel("TRANSLATE")
        brand_sub.setObjectName("brand_sub")
        layout.addWidget(brand_sub)
        
        # Spacer with subtle line
        layout.addSpacing(32)
        
        # Document info - con icona FontAwesome
        self.file_icon = QLabel()
        self.file_icon.setPixmap(qta.icon('fa5s.file-pdf', color='#71717a').pixmap(QSize(16, 16)))
        layout.addWidget(self.file_icon)
        layout.addSpacing(8)
        
        self.file_label = QLabel("Nessun documento caricato")
        self.file_label.setObjectName("file_label")
        layout.addWidget(self.file_label, 1)
        
        # Page navigation - clear and intuitive
        nav_container = QWidget()
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(8)
        
        self.btn_prev = QPushButton("Indietro")
        self.btn_prev.setIcon(qta.icon('fa5s.chevron-left', color='#ffffff'))
        self.btn_prev.setObjectName("nav_btn")
        self.btn_prev.setFixedSize(100, 38)
        self.btn_prev.setToolTip("Vai alla pagina precedente")
        self.btn_prev.clicked.connect(self.previous_page)
        self.btn_prev.setEnabled(False)
        nav_layout.addWidget(self.btn_prev)
        
        self.page_label = QLabel("—")
        self.page_label.setObjectName("page_indicator")
        self.page_label.setFixedWidth(100)
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setToolTip("Pagina corrente / Totale pagine")
        nav_layout.addWidget(self.page_label)
        
        self.btn_next = QPushButton("Avanti")
        self.btn_next.setIcon(qta.icon('fa5s.chevron-right', color='#ffffff'))
        self.btn_next.setLayoutDirection(Qt.RightToLeft)  # Icon on right
        self.btn_next.setObjectName("nav_btn")
        self.btn_next.setFixedSize(100, 38)
        self.btn_next.setToolTip("Vai alla pagina successiva")
        self.btn_next.clicked.connect(self.next_page)
        self.btn_next.setEnabled(False)
        nav_layout.addWidget(self.btn_next)
        
        layout.addWidget(nav_container)
        
        return bar
    
    def _create_sidebar(self) -> QWidget:
        """Create premium sidebar with controls."""
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(320)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)
        
        # Section: Document - con icona FontAwesome
        section_doc_layout = QHBoxLayout()
        section_doc_layout.setContentsMargins(0, 0, 0, 0)
        section_doc_layout.setSpacing(8)
        section_doc_icon = QLabel()
        section_doc_icon.setPixmap(qta.icon('fa5s.file-alt', color='#a1a1aa').pixmap(QSize(14, 14)))
        section_doc_layout.addWidget(section_doc_icon)
        section_doc = QLabel("DOCUMENTO")
        section_doc.setObjectName("section_label")
        section_doc_layout.addWidget(section_doc)
        section_doc_layout.addStretch()
        layout.addLayout(section_doc_layout)
        layout.addSpacing(10)
        
        self.btn_open = GlowButton("Apri PDF...", icon_name='fa5s.folder-open')
        self.btn_open.setObjectName("btn_primary")
        self.btn_open.setFixedHeight(48)
        self.btn_open.setToolTip("Clicca per selezionare un file PDF da tradurre")
        self.btn_open.clicked.connect(self.open_pdf)
        layout.addWidget(self.btn_open)
        
        # Hint per utenti
        hint_open = QLabel("Seleziona il documento PDF da tradurre")
        hint_open.setObjectName("hint_label")
        layout.addWidget(hint_open)
        
        layout.addSpacing(24)
        
        # Section: Languages - con icona FontAwesome
        section_lang_layout = QHBoxLayout()
        section_lang_layout.setContentsMargins(0, 0, 0, 0)
        section_lang_layout.setSpacing(8)
        section_lang_icon = QLabel()
        section_lang_icon.setPixmap(qta.icon('fa5s.language', color='#a1a1aa').pixmap(QSize(14, 14)))
        section_lang_layout.addWidget(section_lang_icon)
        section_lang = QLabel("TRADUZIONE")
        section_lang.setObjectName("section_label")
        section_lang_layout.addWidget(section_lang)
        section_lang_layout.addStretch()
        layout.addLayout(section_lang_layout)
        layout.addSpacing(10)
        
        # Source language
        source_row = QWidget()
        source_layout = QVBoxLayout(source_row)
        source_layout.setContentsMargins(0, 0, 0, 0)
        source_layout.setSpacing(4)
        
        source_label_layout = QHBoxLayout()
        source_label_layout.setContentsMargins(0, 0, 0, 0)
        source_label_layout.setSpacing(6)
        source_icon = QLabel()
        source_icon.setPixmap(qta.icon('fa5s.book', color='#e4e4e7').pixmap(QSize(12, 12)))
        source_label_layout.addWidget(source_icon)
        source_label = QLabel("Lingua originale:")
        source_label.setObjectName("field_label")
        source_label_layout.addWidget(source_label)
        source_label_layout.addStretch()
        source_layout.addLayout(source_label_layout)
        
        self.combo_source = QComboBox()
        self.combo_source.setObjectName("lang_select")
        self.combo_source.addItems(["Auto-Detect"] + TranslationEngine.get_supported_languages())
        self.combo_source.setCurrentText("English")
        self.combo_source.setFixedHeight(40)
        self.combo_source.currentTextChanged.connect(self.update_translator)
        source_layout.addWidget(self.combo_source)
        
        layout.addWidget(source_row)
        layout.addSpacing(8)
        
        # Arrow indicator
        arrow = QLabel("↓")
        arrow.setObjectName("lang_arrow")
        arrow.setAlignment(Qt.AlignCenter)
        layout.addWidget(arrow)
        layout.addSpacing(8)
        
        # Target language
        target_row = QWidget()
        target_layout = QVBoxLayout(target_row)
        target_layout.setContentsMargins(0, 0, 0, 0)
        target_layout.setSpacing(4)
        
        target_label_layout = QHBoxLayout()
        target_label_layout.setContentsMargins(0, 0, 0, 0)
        target_label_layout.setSpacing(6)
        target_icon = QLabel()
        target_icon.setPixmap(qta.icon('fa5s.bullseye', color='#e4e4e7').pixmap(QSize(12, 12)))
        target_label_layout.addWidget(target_icon)
        target_label = QLabel("Traduci in:")
        target_label.setObjectName("field_label")
        target_label_layout.addWidget(target_label)
        target_label_layout.addStretch()
        target_layout.addLayout(target_label_layout)
        
        self.combo_target = QComboBox()
        self.combo_target.setObjectName("lang_select")
        self.combo_target.addItems(TranslationEngine.get_supported_languages())
        self.combo_target.setCurrentText("Italiano")
        self.combo_target.setFixedHeight(40)
        self.combo_target.currentTextChanged.connect(self.update_translator)
        target_layout.addWidget(self.combo_target)
        
        layout.addWidget(target_row)
        
        layout.addSpacing(24)
        
        # Translate button - Hero action
        self.btn_translate = GlowButton("TRADUCI PAGINA", icon_name='fa5s.play', accent=True)
        self.btn_translate.setObjectName("btn_accent")
        self.btn_translate.setFixedHeight(50)
        self.btn_translate.setToolTip("Traduce solo la pagina attualmente visualizzata")
        self.btn_translate.clicked.connect(self.translate_current_page)
        self.btn_translate.setEnabled(False)
        layout.addWidget(self.btn_translate)
        
        layout.addSpacing(10)
        
        # Translate all
        self.btn_translate_all = GlowButton("Traduci tutto", icon_name='fa5s.copy')
        self.btn_translate_all.setObjectName("btn_secondary")
        self.btn_translate_all.setFixedHeight(44)
        self.btn_translate_all.setToolTip("Traduce tutte le pagine del documento (può richiedere tempo)")
        self.btn_translate_all.clicked.connect(self.translate_all_pages)
        self.btn_translate_all.setEnabled(False)
        layout.addWidget(self.btn_translate_all)
        
        layout.addSpacing(24)
        
        # Section: View Controls (Zoom) - con icona FontAwesome
        section_view_layout = QHBoxLayout()
        section_view_layout.setContentsMargins(0, 0, 0, 0)
        section_view_layout.setSpacing(8)
        section_view_icon = QLabel()
        section_view_icon.setPixmap(qta.icon('fa5s.search', color='#a1a1aa').pixmap(QSize(14, 14)))
        section_view_layout.addWidget(section_view_icon)
        section_view = QLabel("VISUALIZZA")
        section_view.setObjectName("section_label")
        section_view_layout.addWidget(section_view)
        section_view_layout.addStretch()
        layout.addLayout(section_view_layout)
        layout.addSpacing(10)
        
        # Zoom controls row
        zoom_row = QWidget()
        zoom_layout = QHBoxLayout(zoom_row)
        zoom_layout.setContentsMargins(0, 0, 0, 0)
        zoom_layout.setSpacing(6)
        
        self.btn_zoom_out = GlowButton("", icon_name='fa5s.minus')
        self.btn_zoom_out.setObjectName("btn_small")
        self.btn_zoom_out.setFixedSize(40, 40)
        self.btn_zoom_out.setToolTip("Riduci zoom")
        self.btn_zoom_out.clicked.connect(lambda: self.original_viewer.zoom_out())
        zoom_layout.addWidget(self.btn_zoom_out)
        
        self.btn_zoom_fit = GlowButton("Adatta", icon_name='fa5s.expand')
        self.btn_zoom_fit.setObjectName("btn_small")
        self.btn_zoom_fit.setFixedHeight(40)
        self.btn_zoom_fit.setToolTip("Adatta alla finestra")
        self.btn_zoom_fit.clicked.connect(lambda: self.original_viewer.zoom_fit())
        zoom_layout.addWidget(self.btn_zoom_fit, 1)
        
        self.btn_zoom_in = GlowButton("", icon_name='fa5s.plus')
        self.btn_zoom_in.setObjectName("btn_small")
        self.btn_zoom_in.setFixedSize(40, 40)
        self.btn_zoom_in.setToolTip("Aumenta zoom")
        self.btn_zoom_in.clicked.connect(lambda: self.original_viewer.zoom_in())
        zoom_layout.addWidget(self.btn_zoom_in)
        
        layout.addWidget(zoom_row)
        
        layout.addStretch()
        
        # Progress indicator (hidden by default)
        self.progress_container = QWidget()
        self.progress_container.setVisible(False)
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(8)
        
        self.progress_label = QLabel("Traduzione in corso...")
        self.progress_label.setObjectName("progress_label")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progress_bar")
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(self.progress_container)
        layout.addSpacing(20)
        
        # Export section - con icona FontAwesome
        section_export_layout = QHBoxLayout()
        section_export_layout.setContentsMargins(0, 0, 0, 0)
        section_export_layout.setSpacing(8)
        section_export_icon = QLabel()
        section_export_icon.setPixmap(qta.icon('fa5s.save', color='#a1a1aa').pixmap(QSize(14, 14)))
        section_export_layout.addWidget(section_export_icon)
        section_export = QLabel("SALVA")
        section_export.setObjectName("section_label")
        section_export_layout.addWidget(section_export)
        section_export_layout.addStretch()
        layout.addLayout(section_export_layout)
        layout.addSpacing(10)
        
        self.btn_save = GlowButton("Salva PDF tradotto...", icon_name='fa5s.file-download')
        self.btn_save.setObjectName("btn_primary")
        self.btn_save.setFixedHeight(44)
        self.btn_save.setToolTip("Salva il documento tradotto come nuovo file PDF")
        self.btn_save.clicked.connect(self.save_pdf)
        self.btn_save.setEnabled(False)
        layout.addWidget(self.btn_save)
        
        # Hint
        hint_save = QLabel("Esporta il documento tradotto")
        hint_save.setObjectName("hint_label")
        layout.addWidget(hint_save)
        
        layout.addSpacing(10)
        
        return sidebar
    
    def _create_actions(self):
        """Create keyboard shortcuts."""
        self.action_open = QAction("&Open PDF...", self)
        self.action_open.setShortcut(QKeySequence.Open)
        self.action_open.triggered.connect(self.open_pdf)
        
        self.action_save = QAction("&Save PDF...", self)
        self.action_save.setShortcut(QKeySequence.Save)
        self.action_save.triggered.connect(self.save_pdf)
        
        self.action_quit = QAction("&Quit", self)
        self.action_quit.setShortcut(QKeySequence.Quit)
        self.action_quit.triggered.connect(self.close)
        
        self.action_zoom_in = QAction("Zoom &In", self)
        self.action_zoom_in.setShortcut(QKeySequence.ZoomIn)
        self.action_zoom_in.triggered.connect(lambda: self.original_viewer.zoom_in())
        
        self.action_zoom_out = QAction("Zoom &Out", self)
        self.action_zoom_out.setShortcut(QKeySequence.ZoomOut)
        self.action_zoom_out.triggered.connect(lambda: self.original_viewer.zoom_out())
        
        self.action_zoom_fit = QAction("&Fit to Window", self)
        self.action_zoom_fit.triggered.connect(lambda: self.original_viewer.zoom_fit())
        
        self.action_zoom_reset = QAction("&Reset Zoom", self)
        self.action_zoom_reset.setShortcut("Ctrl+0")
        self.action_zoom_reset.triggered.connect(lambda: self.original_viewer.zoom_reset())
    
    def _create_menus(self):
        """Create minimal menu bar."""
        menubar = self.menuBar()
        menubar.setObjectName("menu_bar")
        
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.action_open)
        file_menu.addAction(self.action_save)
        file_menu.addSeparator()
        file_menu.addAction(self.action_quit)
        
        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self.action_zoom_in)
        view_menu.addAction(self.action_zoom_out)
        view_menu.addAction(self.action_zoom_fit)
        view_menu.addAction(self.action_zoom_reset)
    
    def _create_statusbar(self):
        """Create minimal status bar."""
        self.status_bar = QStatusBar()
        self.status_bar.setObjectName("status_bar")
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def _apply_premium_stylesheet(self):
        """
        OBSIDIAN GLASS Design System
        Premium enterprise aesthetic for 2026
        """
        self.setStyleSheet("""
            /* ═══════════════════════════════════════════════════════════════
               OBSIDIAN GLASS - Premium Design System
               Enterprise-grade aesthetic for legal professionals
               ═══════════════════════════════════════════════════════════════ */
            
            /* ─── Foundation ─────────────────────────────────────────────── */
            * {
                font-family: 'SF Pro Display', 'Inter', 'Segoe UI Variable', system-ui;
            }
            
            QMainWindow {
                background: #09090b;
            }
            
            QWidget#central_widget {
                background: #09090b;
            }
            
            /* ─── Top Bar ────────────────────────────────────────────────── */
            QWidget#top_bar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #18181b, stop:1 #09090b);
                border-bottom: 1px solid #27272a;
            }
            
            QLabel#brand_logo {
                font-size: 22px;
                font-weight: 800;
                letter-spacing: 3px;
                color: #fafafa;
                background: transparent;
            }
            
            QLabel#brand_sub {
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 4px;
                color: #71717a;
                background: transparent;
                padding-top: 4px;
            }
            
            QLabel#file_label {
                font-size: 13px;
                font-weight: 500;
                color: #a1a1aa;
                background: transparent;
                padding-left: 24px;
                border-left: 1px solid #27272a;
            }
            
            QLabel#page_indicator {
                font-size: 14px;
                font-weight: 700;
                color: #ffffff;
                background: #18181b;
                border: 1px solid #3f3f46;
                border-radius: 10px;
                padding: 0 16px;
            }
            
            QPushButton#nav_btn {
                font-size: 13px;
                font-weight: 600;
                color: #ffffff;
                background: #27272a;
                border: 1px solid #3f3f46;
                border-radius: 10px;
            }
            QPushButton#nav_btn:hover {
                color: #ffffff;
                background: #3f3f46;
                border-color: #52525b;
            }
            QPushButton#nav_btn:pressed {
                background: #18181b;
            }
            QPushButton#nav_btn:disabled {
                color: #52525b;
                background: #1f1f23;
                border-color: #27272a;
            }
            
            /* ─── Main Content ───────────────────────────────────────────── */
            QWidget#main_content {
                background: #09090b;
            }
            
            /* ─── Sidebar ────────────────────────────────────────────────── */
            QWidget#sidebar {
                background: #0f0f12;
                border: 1px solid #1f1f23;
                border-radius: 16px;
            }
            
            QLabel#section_label {
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 1px;
                color: #a1a1aa;
                background: transparent;
                padding-bottom: 6px;
            }
            
            QLabel#field_label {
                font-size: 13px;
                font-weight: 600;
                color: #e4e4e7;
                background: transparent;
            }
            
            QLabel#lang_arrow {
                font-size: 16px;
                color: #3f3f46;
                background: transparent;
            }
            
            /* ─── Language Selectors ─────────────────────────────────────── */
            QComboBox#lang_select {
                font-size: 14px;
                font-weight: 500;
                color: #e4e4e7;
                background: #18181b;
                border: 1px solid #27272a;
                border-radius: 10px;
                padding: 0 16px;
                padding-right: 36px;
            }
            QComboBox#lang_select:hover {
                border-color: #3f3f46;
                background: #1f1f23;
            }
            QComboBox#lang_select:focus {
                border-color: #10b981;
            }
            QComboBox#lang_select::drop-down {
                border: none;
                width: 32px;
            }
            QComboBox#lang_select::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #71717a;
            }
            QComboBox QAbstractItemView {
                font-size: 13px;
                color: #e4e4e7;
                background: #18181b;
                border: 1px solid #27272a;
                border-radius: 12px;
                padding: 8px;
                selection-background-color: #27272a;
                selection-color: #fafafa;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 10px 16px;
                border-radius: 8px;
            }
            QComboBox QAbstractItemView::item:hover {
                background: #27272a;
            }
            
            /* ─── Buttons ────────────────────────────────────────────────── */
            QPushButton#btn_primary {
                font-size: 14px;
                font-weight: 600;
                color: #ffffff;
                background: #27272a;
                border: 1px solid #3f3f46;
                border-radius: 12px;
                padding: 8px 16px;
                text-align: left;
            }
            QPushButton#btn_primary:hover {
                background: #3f3f46;
                border-color: #52525b;
                color: #ffffff;
            }
            QPushButton#btn_primary:pressed {
                background: #18181b;
            }
            QPushButton#btn_primary:disabled {
                color: #71717a;
                background: #18181b;
                border-color: #27272a;
            }
            
            QPushButton#btn_accent {
                font-size: 15px;
                font-weight: 700;
                color: #ffffff;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #059669, stop:1 #10b981);
                border: none;
                border-radius: 14px;
                padding: 10px 20px;
            }
            QPushButton#btn_accent:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #10b981, stop:1 #34d399);
                color: #ffffff;
            }
            QPushButton#btn_accent:pressed {
                background: #047857;
            }
            QPushButton#btn_accent:disabled {
                color: #9ca3af;
                background: #1f2937;
                border: 1px solid #374151;
            }
            
            QPushButton#btn_secondary {
                font-size: 14px;
                font-weight: 600;
                color: #ffffff;
                background: #1f1f23;
                border: 1px solid #3f3f46;
                border-radius: 12px;
                padding: 8px 16px;
                text-align: left;
            }
            QPushButton#btn_secondary:hover {
                color: #ffffff;
                background: #27272a;
                border-color: #52525b;
            }
            QPushButton#btn_secondary:pressed {
                background: #18181b;
            }
            QPushButton#btn_secondary:disabled {
                color: #71717a;
                background: #18181b;
                border-color: #27272a;
            }
            
            /* ─── Hint Labels ─────────────────────────────────────────────── */
            QLabel#hint_label {
                font-size: 11px;
                font-weight: 400;
                color: #71717a;
                background: transparent;
                padding: 4px 0 0 4px;
            }
            
            /* ─── Small Buttons (Zoom, etc) ─────────────────────────────── */
            QPushButton#btn_small {
                font-size: 14px;
                font-weight: 600;
                color: #ffffff;
                background: #1f1f23;
                border: 1px solid #3f3f46;
                border-radius: 10px;
            }
            QPushButton#btn_small:hover {
                background: #27272a;
                border-color: #52525b;
                color: #ffffff;
            }
            QPushButton#btn_small:pressed {
                background: #18181b;
            }
            QPushButton#btn_small:disabled {
                color: #52525b;
                background: #18181b;
                border-color: #27272a;
            }
            
            /* ─── Progress ───────────────────────────────────────────────── */
            QLabel#progress_label {
                font-size: 13px;
                font-weight: 600;
                color: #10b981;
                background: transparent;
            }
            
            QProgressBar#progress_bar {
                background: #18181b;
                border: none;
                border-radius: 3px;
            }
            QProgressBar#progress_bar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10b981, stop:1 #34d399);
                border-radius: 2px;
            }
            
            /* ─── Document Panels ────────────────────────────────────────── */
            QFrame#document_panel {
                background: #0f0f12;
                border: 1px solid #1f1f23;
                border-radius: 16px;
            }
            
            QWidget#panel_header {
                background: transparent;
                border-bottom: 1px solid #1f1f23;
            }
            
            QLabel#status_dot {
                font-size: 8px;
                color: #475569;
                background: transparent;
                padding-right: 8px;
            }
            
            QLabel#panel_title {
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 2px;
                color: #52525b;
                background: transparent;
            }
            
            QWidget#panel_content {
                background: #0a0a0c;
                border-bottom-left-radius: 15px;
                border-bottom-right-radius: 15px;
            }
            
            /* ─── Menu Bar ───────────────────────────────────────────────── */
            QMenuBar#menu_bar {
                font-size: 13px;
                color: #a1a1aa;
                background: transparent;
                border: none;
                padding: 4px 8px;
            }
            QMenuBar#menu_bar::item {
                padding: 8px 16px;
                background: transparent;
                border-radius: 6px;
            }
            QMenuBar#menu_bar::item:selected {
                background: #27272a;
                color: #fafafa;
            }
            
            QMenu {
                font-size: 13px;
                color: #e4e4e7;
                background: #18181b;
                border: 1px solid #27272a;
                border-radius: 12px;
                padding: 8px;
            }
            QMenu::item {
                padding: 10px 24px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background: #27272a;
            }
            QMenu::separator {
                height: 1px;
                background: #27272a;
                margin: 8px 12px;
            }
            
            /* ─── Status Bar ─────────────────────────────────────────────── */
            QStatusBar#status_bar {
                font-size: 11px;
                font-weight: 500;
                color: #52525b;
                background: #09090b;
                border-top: 1px solid #1f1f23;
                padding: 8px 24px;
            }
            
            /* ─── Scrollbars ─────────────────────────────────────────────── */
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
            
            /* ─── Splitter ───────────────────────────────────────────────── */
            QSplitter::handle {
                background: transparent;
                width: 16px;
            }
            
            /* ─── Message Boxes ──────────────────────────────────────────── */
            QMessageBox {
                background: #18181b;
            }
            QMessageBox QLabel {
                color: #e4e4e7;
                font-size: 14px;
            }
            QMessageBox QPushButton {
                font-size: 13px;
                font-weight: 500;
                color: #fafafa;
                background: #27272a;
                border: 1px solid #3f3f46;
                border-radius: 8px;
                padding: 8px 24px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background: #3f3f46;
            }
            
            /* ─── File Dialog ────────────────────────────────────────────── */
            QFileDialog {
                background: #18181b;
            }
            QFileDialog QLabel {
                color: #e4e4e7;
            }
            QFileDialog QLineEdit {
                background: #27272a;
                border: 1px solid #3f3f46;
                border-radius: 6px;
                padding: 8px;
                color: #fafafa;
            }
            QFileDialog QListView,
            QFileDialog QTreeView {
                background: #0f0f12;
                border: 1px solid #27272a;
                border-radius: 8px;
                color: #e4e4e7;
            }
            QFileDialog QListView::item:selected,
            QFileDialog QTreeView::item:selected {
                background: #27272a;
            }
        """)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Business Logic (unchanged functionality)
    # ═══════════════════════════════════════════════════════════════════════
    
    @Slot()
    def open_pdf(self):
        """Open PDF file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open PDF Document",
            "",
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            if self.pdf_processor:
                self.pdf_processor.close()
            
            self.pdf_processor = PDFProcessor(file_path)
            self.current_page = 0
            self.translated_pages.clear()
            
            # Update UI
            filename = Path(file_path).name
            if len(filename) > 40:
                filename = filename[:37] + "..."
            self.file_label.setText(filename)
            self.original_panel.set_active(True)
            self.update_page_display()
            
            # Enable controls
            self.btn_prev.setEnabled(True)
            self.btn_next.setEnabled(True)
            self.btn_translate.setEnabled(True)
            self.btn_translate_all.setEnabled(True)
            
            self.status_bar.showMessage(
                f"Loaded document • {self.pdf_processor.page_count} pages"
            )
            
            logging.info(f"Opened PDF: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open PDF:\n{str(e)}"
            )
            logging.error(f"Failed to open PDF: {e}")
    
    def update_page_display(self):
        """Update display for current page."""
        if not self.pdf_processor:
            return
        
        self.page_label.setText(
            f"{self.current_page + 1} / {self.pdf_processor.page_count}"
        )
        
        try:
            img_data, width, height = self.pdf_processor.render_page(
                self.current_page, zoom=1.5
            )
            self.original_viewer.display_page(img_data, width, height)
            self.original_viewer.zoom_fit()
        except Exception as e:
            logging.error(f"Failed to render page: {e}")
        
        if self.current_page in self.translated_pages:
            self.display_translated_page(self.current_page)
            self.translated_panel.set_active(True)
        else:
            self.translated_viewer.clear()
            self.translated_panel.set_active(False)
    
    def display_translated_page(self, page_num):
        """Display translated version of page."""
        translated_doc = self.translated_pages[page_num]
        page = translated_doc[0]
        pix = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5))
        img_data = pix.tobytes("png")
        self.translated_viewer.display_page(img_data, pix.width, pix.height)
        self.translated_viewer.zoom_fit()
    
    @Slot()
    def previous_page(self):
        """Navigate to previous page."""
        if self.pdf_processor and self.current_page > 0:
            self.current_page -= 1
            self.update_page_display()
    
    @Slot()
    def next_page(self):
        """Navigate to next page."""
        if self.pdf_processor and self.current_page < self.pdf_processor.page_count - 1:
            self.current_page += 1
            self.update_page_display()
    
    @Slot()
    def update_translator(self):
        """Update translator with selected languages."""
        source_lang = self.combo_source.currentText()
        target_lang = self.combo_target.currentText()
        
        # Get language codes
        source_code = "en" if source_lang == "Auto-Detect" else TranslationEngine.get_language_code(source_lang)
        target_code = TranslationEngine.get_language_code(target_lang)
        
        # Prevent same language translation (en -> en, etc)
        if source_code == target_code:
            self.status_bar.showMessage("⚠️ Seleziona lingue diverse per sorgente e destinazione")
            self.btn_translate.setEnabled(False)
            self.btn_translate_all.setEnabled(False)
            return
        
        # Re-enable translate buttons if a PDF is loaded
        if self.pdf_processor:
            self.btn_translate.setEnabled(True)
            self.btn_translate_all.setEnabled(True)
        
        try:
            if self.translator:
                self.translator.set_languages(source_code, target_code)
                self.status_bar.showMessage(f"✓ Pronto: {source_lang} → {target_lang}")
        except ValueError as e:
            self.status_bar.showMessage(f"⚠️ Coppia linguistica non supportata")
            logging.warning(f"Language pair not supported: {e}")
    
    @Slot()
    def translate_current_page(self):
        """Translate current page."""
        if not self.pdf_processor or not self.translator:
            return
        
        if self.translation_worker and self.translation_worker.isRunning():
            QMessageBox.information(self, "In Progress", "Translation already in progress")
            return
        
        self.progress_container.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.progress_label.setText(f"Translating page {self.current_page + 1}...")
        self.status_bar.showMessage("Processing...")
        
        self.translation_worker = TranslationWorker(
            self.pdf_processor,
            self.translator,
            self.current_page
        )
        self.translation_worker.finished.connect(self.on_translation_finished)
        self.translation_worker.error.connect(self.on_translation_error)
        self.translation_worker.start()
    
    @Slot(object)
    def on_translation_finished(self, translated_doc):
        """Handle translation completion."""
        self.translated_pages[self.current_page] = translated_doc
        self.display_translated_page(self.current_page)
        self.translated_panel.set_active(True)
        
        self.progress_container.setVisible(False)
        self.status_bar.showMessage(
            f"Page {self.current_page + 1} translated successfully", 5000
        )
        self.btn_save.setEnabled(True)
        
        logging.info(f"Page {self.current_page + 1} translated successfully")
    
    @Slot(str)
    def on_translation_error(self, error_msg):
        """Handle translation error."""
        self.progress_container.setVisible(False)
        self.status_bar.showMessage("Translation failed")
        
        QMessageBox.critical(
            self,
            "Translation Error",
            f"Failed to translate page:\n{error_msg}"
        )
        logging.error(f"Translation error: {error_msg}")
    
    @Slot()
    def translate_all_pages(self):
        """Translate all pages."""
        QMessageBox.information(
            self,
            "Coming Soon",
            "Batch translation will be available in the next update."
        )
    
    @Slot()
    def save_pdf(self):
        """Save translated PDF."""
        if not self.translated_pages:
            QMessageBox.warning(
                self,
                "No Content",
                "No translated pages to save."
            )
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Translated PDF",
            "",
            "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return
        
        try:
            import pymupdf
            output_doc = pymupdf.open()
            
            for page_num in sorted(self.translated_pages.keys()):
                translated_doc = self.translated_pages[page_num]
                output_doc.insert_pdf(translated_doc)
            
            output_doc.save(
                file_path,
                garbage=4,
                deflate=True,
                clean=True
            )
            output_doc.close()
            
            self.status_bar.showMessage(f"Saved: {Path(file_path).name}", 5000)
            QMessageBox.information(
                self,
                "Export Complete",
                f"PDF saved successfully:\n{file_path}"
            )
            
            logging.info(f"Saved translated PDF: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to save PDF:\n{str(e)}"
            )
            logging.error(f"Failed to save PDF: {e}")


import pymupdf
