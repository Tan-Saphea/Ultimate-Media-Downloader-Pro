import sys
import os
import threading
import re
import json
import urllib.request
import subprocess
import logging
import traceback
from datetime import timedelta
import webbrowser

def get_app_data_dir():
    app_dir = os.path.join(os.path.expanduser('~'), '.ultimate_media_downloader')
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Setup logging
LOG_FILE = os.path.join(get_app_data_dir(), 'downloader.log')
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def global_exception_handler(exctype, value, tb):
    logging.error("Uncaught exception", exc_info=(exctype, value, tb))
    sys.__excepthook__(exctype, value, tb)
sys.excepthook = global_exception_handler

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                 QHBoxLayout, QLineEdit, QPushButton, QComboBox, 
                                 QLabel, QProgressBar, QMessageBox, QFileDialog, 
                                 QGraphicsDropShadowEffect, QDialog, QCheckBox, 
                                 QFrame, QGridLayout, QScrollArea, QListWidget)
    from PyQt5.QtCore import pyqtSignal, QObject, Qt, QThread, QPropertyAnimation, QEasingCurve, QTimer
    from PyQt5.QtGui import QColor, QPixmap, QPainter, QPainterPath, QPen, QCursor
    import yt_dlp
    import webbrowser
except ImportError:
    venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv', 'bin', 'python')
    if os.path.exists(venv_python) and sys.executable != venv_python:
        print(f"Relaunching in Virtual Environment: {venv_python}")
        os.execv(venv_python, [venv_python] + sys.argv)
    else:
        print("Required packages are missing. Run: python -m pip install PyQt5 yt-dlp")
        sys.exit(1)

SETTINGS_FILE = os.path.join(get_app_data_dir(), "settings.json")
HISTORY_FILE = os.path.join(get_app_data_dir(), "history.json")

DARK_THEME = """
QMainWindow, QDialog, QScrollArea, QWidget#scrollAreaWidgetContents { background-color: #1e1e2e; }
QLabel { color: #f8fafc; font-family: 'Inter', '-apple-system', 'Segoe UI', sans-serif; font-size: 16px; font-weight: 500; letter-spacing: 0.3px; line-height: 1.5; }
QLabel#appTitle { font-size: 28px; font-weight: 800; color: #89b4fa; letter-spacing: 0.5px; }
QLabel#sectionLabel { font-size: 16px; font-weight: 600; color: #cbd5e1; letter-spacing: 0.3px; }
QLabel#secondaryText { font-size: 14px; font-weight: 400; color: #94a3b8; }
QLineEdit { background-color: #313244; color: #f8fafc; border: 1.5px solid #45475a; border-radius: 8px; padding: 12px; font-size: 16px; font-weight: 500; letter-spacing: 0.3px; }
QLineEdit::placeholder { color: #94a3b8; font-weight: 400; }
QLineEdit:focus { border: 1.5px solid #89b4fa; }
QPushButton { background-color: #89b4fa; color: #111827; border: none; border-radius: 8px; padding: 12px 18px; font-weight: 700; font-size: 16px; letter-spacing: 0.5px; }
QPushButton:hover { background-color: #b4befe; }
QPushButton:pressed { background-color: #74c7ec; }
QPushButton:disabled { background-color: #45475a; color: #94a3b8; }
QPushButton#cancelBtn { background-color: #f38ba8; color: #111827; }
QPushButton#cancelBtn:hover { background-color: #fca3a1; }
QPushButton#pauseBtn { background-color: #f9e2af; color: #111827; }
QPushButton#pauseBtn:hover { background-color: #f5e0a5; }
QPushButton#themeBtn { background-color: transparent; font-size: 18px; border: 1.5px solid #45475a; color: #f8fafc; }
QPushButton#themeBtn:hover { background-color: #313244; }
QComboBox { background-color: #313244; color: #f8fafc; border: 1.5px solid #45475a; border-radius: 8px; padding: 10px 14px; font-size: 16px; font-weight: 500; letter-spacing: 0.3px; }
QComboBox::drop-down { border: none; }
QProgressBar { border: 1.5px solid #45475a; border-radius: 8px; text-align: center; color: #f8fafc; background-color: #313244; font-weight: 700; font-size: 14px; letter-spacing: 0.5px; }
QProgressBar::chunk { background-color: #a6e3a1; border-radius: 7px; }
QCheckBox { color: #f8fafc; font-size: 16px; font-weight: 500; }
QFrame#previewCard { background-color: #313244; border-radius: 12px; border: 1px solid #45475a; }
QListWidget { background-color: #313244; color: #f8fafc; border: 1px solid #45475a; border-radius: 8px; font-size: 16px; font-weight: 500; }
"""

LIGHT_THEME = """
QMainWindow, QDialog, QScrollArea, QWidget#scrollAreaWidgetContents { background-color: #f8fafc; }
QLabel { color: #111827; font-family: 'Inter', '-apple-system', 'Segoe UI', sans-serif; font-size: 16px; font-weight: 500; letter-spacing: 0.3px; line-height: 1.5; }
QLabel#appTitle { font-size: 28px; font-weight: 800; color: #2563eb; letter-spacing: 0.5px; }
QLabel#sectionLabel { font-size: 16px; font-weight: 600; color: #4b5563; letter-spacing: 0.3px; }
QLabel#secondaryText { font-size: 14px; font-weight: 400; color: #64748b; }
QLineEdit { background-color: #ffffff; color: #111827; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 12px; font-size: 16px; font-weight: 500; letter-spacing: 0.3px; }
QLineEdit::placeholder { color: #64748b; font-weight: 400; }
QLineEdit:focus { border: 1.5px solid #3b82f6; }
QPushButton { background-color: #3b82f6; color: #ffffff; border: none; border-radius: 8px; padding: 12px 18px; font-weight: 700; font-size: 16px; letter-spacing: 0.5px; }
QPushButton:hover { background-color: #60a5fa; }
QPushButton:pressed { background-color: #2563eb; }
QPushButton:disabled { background-color: #e2e8f0; color: #94a3b8; }
QPushButton#cancelBtn { background-color: #ef4444; color: #ffffff; }
QPushButton#cancelBtn:hover { background-color: #f87171; }
QPushButton#pauseBtn { background-color: #f59e0b; color: #ffffff; }
QPushButton#pauseBtn:hover { background-color: #fbbf24; }
QPushButton#themeBtn { background-color: transparent; font-size: 18px; border: 1.5px solid #cbd5e1; color: #111827; }
QPushButton#themeBtn:hover { background-color: #e2e8f0; }
QComboBox { background-color: #ffffff; color: #111827; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 10px 14px; font-size: 16px; font-weight: 500; letter-spacing: 0.3px; }
QComboBox::drop-down { border: none; }
QProgressBar { border: 1.5px solid #cbd5e1; border-radius: 8px; text-align: center; color: #111827; background-color: #e2e8f0; font-weight: 700; font-size: 14px; letter-spacing: 0.5px; }
QProgressBar::chunk { background-color: #10b981; border-radius: 7px; }
QCheckBox { color: #111827; font-size: 16px; font-weight: 500; }
QFrame#previewCard { background-color: #ffffff; border-radius: 12px; border: 1px solid #cbd5e1; }
QListWidget { background-color: #ffffff; color: #111827; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 16px; font-weight: 500; }
"""

class DroppableLineEdit(QLineEdit):
    dropped = pyqtSignal(str)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    def dropEvent(self, event):
        text = event.mimeData().text()
        self.setText(text)
        self.dropped.emit(text)
        event.acceptProposedAction()

class CancelException(Exception):
    pass

class ThumbnailWorker(QThread):
    finished = pyqtSignal(bytes)
    def __init__(self, url):
        super().__init__()
        self.url = url
    def run(self):
        try:
            req = urllib.request.Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})
            data = urllib.request.urlopen(req, timeout=10).read()
            self.finished.emit(data)
        except Exception as e:
            logging.error(f"Error fetching thumbnail: {e}")

class InfoWorker(QThread):
    info_ready = pyqtSignal(dict)
    error = pyqtSignal(str)
    def __init__(self, url):
        super().__init__()
        self.url = url
    def run(self):
        opts = {'quiet': True, 'no_warnings': True, 'extract_flat': False, 'noplaylist': True}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                self.info_ready.emit(info)
        except Exception as e:
            logging.error(f"Info extraction error: {e}")
            self.error.emit(str(e))

class DownloadWorker(QThread):
    progress = pyqtSignal(dict)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    status = pyqtSignal(str)
    warning = pyqtSignal(str)

    def __init__(self, urls, options, out_path):
        super().__init__()
        self.urls = urls
        self.options = options
        self.out_path = out_path
        self.is_cancelled = False

    def run(self):
        try:
            opts = {
                'outtmpl': os.path.join(self.out_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self.hook],
                'quiet': True,
                'no_warnings': True,
                'noplaylist': not self.options.get('playlist', False),
            }
            
            # Setup bundled ffmpeg location if available
            if sys.platform == "win32":
                bundled_ffmpeg = resource_path('ffmpeg.exe')
                if os.path.exists(bundled_ffmpeg):
                    opts['ffmpeg_location'] = bundled_ffmpeg

            m_type = self.options.get('type', 'Video')
            fmt = self.options.get('format', 'MP4').lower()
            q = self.options.get('quality', 'Best')

            if m_type == 'Audio Only':
                opts['format'] = 'bestaudio/best'
                opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': fmt, 'preferredquality': '192'}]
            else:
                q_str = ''
                if q not in ['Best', 'Auto']:
                    h = "".join(filter(str.isdigit, q))
                    if h: q_str = f'[height<={h}]'
                opts['format'] = f'bestvideo{q_str}+bestaudio/best{q_str}/best'
                opts['merge_output_format'] = fmt

            if self.options.get('subtitles', False):
                opts['writesubtitles'] = True
                opts['subtitleslangs'] = ['en', 'all']
                if 'postprocessors' not in opts: opts['postprocessors'] = []
                opts['postprocessors'].append({'key': 'FFmpegEmbedSubtitle'})

            self.status.emit("Starting downloads...")
            for url in self.urls:
                if self.is_cancelled:
                    raise CancelException("Cancelled")
                try:
                    logging.info(f"Downloading URL: {url}")
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        ydl.download([url])
                except CancelException:
                    raise
                except Exception as e:
                    logging.error(f"Error downloading {url}: {e}")
                    self.warning.emit(f"Failed to download {url}: {e}")
                    continue

            if not self.is_cancelled:
                self.finished.emit("Download completed successfully!")

        except CancelException:
            logging.info("Download cancelled.")
            self.error.emit("Download Cancelled or Paused")
        except Exception as e:
            if not self.is_cancelled:
                logging.error(f"Fatal download error: {e}")
                self.error.emit(str(e))

    def hook(self, d):
        if self.is_cancelled:
            raise CancelException("Cancelled")
        if d['status'] == 'downloading':
            try:
                p_raw = d.get('_percent_str', '0.0%').replace('%', '').strip()
                p = float(re.sub(r'\x1b[^m]*m', '', p_raw))
                sp = re.sub(r'\x1b[^m]*m', '', d.get('_speed_str', 'N/A'))
                eta = re.sub(r'\x1b[^m]*m', '', d.get('_eta_str', 'N/A'))
                dl = re.sub(r'\x1b[^m]*m', '', d.get('_downloaded_bytes_str', 'N/A'))
                tl = re.sub(r'\x1b[^m]*m', '', d.get('_total_bytes_str', d.get('_estimate_bytes_str', 'N/A')))
                self.progress.emit({'p': int(p), 'sp': sp, 'eta': eta, 'dl': dl, 'tl': tl})
            except: pass
        elif d['status'] == 'finished':
            self.progress.emit({'p': 100, 'sp': 'Done', 'eta': '00:00', 'dl': 'All', 'tl': 'All'})
            self.status.emit("Processing media... (this may take a minute)")

class SuccessDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Complete")
        self.setFixedSize(450, 480)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main background frame for drop shadow
        container = QVBoxLayout(self)
        container.setContentsMargins(20, 20, 20, 20)
        
        self.bg_frame = QFrame()
        self.bg_frame.setObjectName("popupBg")
        self.bg_frame.setStyleSheet("QFrame#popupBg { background-color: #313244; border-radius: 16px; border: 1px solid #45475a; }")
        container.addWidget(self.bg_frame)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 10)
        self.bg_frame.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.bg_frame)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        layout.setContentsMargins(35, 40, 35, 40)
        layout.setSpacing(18)
        
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(130, 130)
        self.set_circular_avatar(resource_path("me.jpg"))
        
        avatar_layout = QHBoxLayout()
        avatar_layout.setAlignment(Qt.AlignCenter)
        avatar_layout.addWidget(self.avatar_label)
        layout.addLayout(avatar_layout)
        
        name_label = QLabel("Tan Saphea")
        name_label.setObjectName("appTitle")
        name_label.setStyleSheet("font-size: 26px; font-weight: 800; color: #89b4fa; letter-spacing: 0.5px;")
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)
        
        job_label = QLabel("Software Engineering Enthusiast")
        job_label.setObjectName("sectionLabel")
        job_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #a6e3a1; letter-spacing: 0.3px;")
        job_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(job_label)
        
        desc_label = QLabel("I am passionate about software engineering and modern technology. I enjoy building applications, learning new programming languages, and developing tools that improve productivity and digital learning.")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 15px; font-weight: 400; color: #bac2de; line-height: 1.6;")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setContentsMargins(10, 0, 10, 0)
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.portfolio_btn = QPushButton("🌐 Visit Portfolio")
        self.portfolio_btn.setStyleSheet("QPushButton { background-color: #89b4fa; color: #111827; border-radius: 8px; padding: 12px; font-weight: 700; font-size: 14px; } QPushButton:hover { background-color: #b4befe; }")
        self.portfolio_btn.clicked.connect(self.open_portfolio)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.setStyleSheet("QPushButton { background-color: #45475a; color: #f8fafc; border-radius: 8px; padding: 12px; font-weight: 700; font-size: 14px; } QPushButton:hover { background-color: #585b70; }")
        self.close_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.portfolio_btn)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)

        # Apply smooth animation when appearing
        self.setWindowOpacity(0.0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(400)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        QTimer.singleShot(50, self.anim.start)

    def open_portfolio(self):
        webbrowser.open("https://github.com/tansaphea")

    def set_circular_avatar(self, path):
        sz = 140
        tgt = QPixmap(sz, sz)
        tgt.fill(Qt.transparent)
        if not os.path.exists(path):
            self.avatar_label.setText("Success!")
            self.avatar_label.setStyleSheet("border: 2px solid #cbd5e1; border-radius: 70px; background-color: #313244; font-size: 20px; font-weight: 700; color: #10b981;")
            self.avatar_label.setAlignment(Qt.AlignCenter)
            return
        src = QPixmap(path)
        if src.isNull(): return
        ratio = max(sz / src.width(), sz / src.height())
        s_w, s_h = int(src.width() * ratio), int(src.height() * ratio)
        src = src.scaled(s_w, s_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        ptr = QPainter(tgt)
        ptr.setRenderHint(QPainter.Antialiasing, True)
        ptr.setRenderHint(QPainter.SmoothPixmapTransform, True)
        clip = QPainterPath()
        clip.addEllipse(0, 0, sz, sz)
        ptr.setClipPath(clip)
        ptr.drawPixmap(int((sz - s_w) / 2), int((sz - s_h) / 2), src)
        ptr.setClipping(False)
        ptr.setPen(QPen(QColor("white"), 2))
        ptr.drawEllipse(1, 1, sz - 2, sz - 2)
        ptr.end()
        self.avatar_label.setPixmap(tgt)

class HistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download History")
        self.setFixedSize(400, 300)
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        l = QLabel("Recent Downloads:")
        l.setObjectName("sectionLabel")
        layout.addWidget(l)
        layout.addWidget(self.list_widget)
        self.load_history()

    def load_history(self):
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r') as f:
                    data = json.load(f)
                    for item in reversed(data):
                        self.list_widget.addItem(item)
        except: pass

class DownloaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ultimate Media Downloader - Pro Edition")
        self.setMinimumSize(850, 680)
        self.settings = {"path": os.path.expanduser('~/Downloads'), "dark": True}
        self.load_settings()
        
        self.dl_worker = None
        self.info_worker = None
        self.last_clip = ""
        
        self.setup_ui()
        self.apply_theme()
        
        QApplication.clipboard().dataChanged.connect(self.check_clipboard)

    def load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    self.settings.update(json.load(f))
        except: pass

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f)
        except: pass

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(30, 25, 30, 25)
        main_layout.setSpacing(18)

        # Header
        header = QHBoxLayout()
        title = QLabel("Ultimate Media Downloader Pro")
        title.setObjectName("appTitle")
        header.addWidget(title)
        header.addStretch()
        self.theme_btn = QPushButton("🌙" if self.settings.get('dark', True) else "☀️")
        self.theme_btn.setObjectName("themeBtn")
        self.theme_btn.setFixedSize(45, 45)
        self.theme_btn.clicked.connect(self.toggle_theme)
        header.addWidget(self.theme_btn)
        main_layout.addLayout(header)

        # URL Input
        url_layout = QHBoxLayout()
        self.url_input = DroppableLineEdit()
        self.url_input.setPlaceholderText("🔗 Paste or drop video links here (comma separate for bulk)...")
        self.url_input.textChanged.connect(self.on_url_change)
        
        self.clear_btn = QPushButton("✖")
        self.clear_btn.setFixedSize(48, 48)
        self.clear_btn.clicked.connect(self.url_input.clear)
        self.clear_btn.setStyleSheet("background-color: transparent; border: 1.5px solid #cbd5e1;")
        
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.clear_btn)
        main_layout.addLayout(url_layout)

        # Preview Card
        self.preview_card = QFrame()
        self.preview_card.setObjectName("previewCard")
        self.preview_card.hide()
        p_layout = QHBoxLayout(self.preview_card)
        
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(160, 90)
        self.thumb_label.setScaledContents(True)
        self.thumb_label.setStyleSheet("border-radius: 8px;")
        
        info_layout = QVBoxLayout()
        self.p_title = QLabel("Fetching info...")
        self.p_title.setObjectName("sectionLabel")
        self.p_title.setWordWrap(True)
        
        self.p_dur = QLabel("Duration: --:--")
        self.p_dur.setObjectName("secondaryText")
        
        self.p_plat = QLabel("Platform: Unknown")
        self.p_plat.setObjectName("secondaryText")
        
        info_layout.addWidget(self.p_title)
        info_layout.addWidget(self.p_dur)
        info_layout.addWidget(self.p_plat)
        info_layout.addStretch()
        
        p_layout.addWidget(self.thumb_label)
        p_layout.addLayout(info_layout)
        p_layout.addStretch()
        main_layout.addWidget(self.preview_card)

        # Settings
        opt_layout = QGridLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Video", "Audio Only"])
        self.type_combo.currentTextChanged.connect(self.update_options)
        
        self.format_combo = QComboBox()
        self.quality_combo = QComboBox()
        
        lb_type = QLabel("Type:")
        lb_type.setObjectName("sectionLabel")
        lb_fmt = QLabel("Format:")
        lb_fmt.setObjectName("sectionLabel")
        lb_ql = QLabel("Quality:")
        lb_ql.setObjectName("sectionLabel")
        
        opt_layout.addWidget(lb_type, 0, 0)
        opt_layout.addWidget(self.type_combo, 0, 1)
        opt_layout.addWidget(lb_fmt, 0, 2)
        opt_layout.addWidget(self.format_combo, 0, 3)
        opt_layout.addWidget(lb_ql, 0, 4)
        opt_layout.addWidget(self.quality_combo, 0, 5)
        
        main_layout.addLayout(opt_layout)

        # Toggles
        tog_layout = QHBoxLayout()
        self.sub_chk = QCheckBox("Embed Subtitles")
        self.pl_chk = QCheckBox("Download Playlist")
        tog_layout.addWidget(self.sub_chk)
        tog_layout.addWidget(self.pl_chk)
        tog_layout.addStretch()
        main_layout.addLayout(tog_layout)

        # Path
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setText(self.settings.get('path', os.path.expanduser('~/Downloads')))
        self.path_input.setReadOnly(True)
        
        browse_btn = QPushButton("📁 Browse")
        browse_btn.clicked.connect(self.browse)
        open_btn = QPushButton("📂 Open Folder")
        open_btn.clicked.connect(self.open_folder)
        open_btn.setStyleSheet("background-color: transparent; border: 1.5px solid #cbd5e1; color: inherit;")
        
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_btn)
        path_layout.addWidget(open_btn)
        main_layout.addLayout(path_layout)

        # Progress info
        self.status = QLabel("✨ Ready to download")
        self.status.setObjectName("sectionLabel")
        self.status.setStyleSheet("color: #3b82f6;") # Will override dynamically later
        main_layout.addWidget(self.status)

        stat_layout = QHBoxLayout()
        self.speed_lbl = QLabel("Speed: 0 B/s")
        self.speed_lbl.setObjectName("secondaryText")
        self.eta_lbl = QLabel("ETA: 00:00")
        self.eta_lbl.setObjectName("secondaryText")
        self.size_lbl = QLabel("Progress: 0 / 0 MB")
        self.size_lbl.setObjectName("secondaryText")
        for lbl in [self.speed_lbl, self.eta_lbl, self.size_lbl]:
            stat_layout.addWidget(lbl)
        main_layout.addLayout(stat_layout)

        self.bar = QProgressBar()
        self.bar.setValue(0)
        self.bar.setFixedHeight(26)
        self.bar.setTextVisible(True)
        self.bar.setFormat("%p% Complete")
        main_layout.addWidget(self.bar)

        # Actions
        btn_layout = QHBoxLayout()
        self.hist_btn = QPushButton("📜 History")
        self.hist_btn.setStyleSheet("background-color: transparent; border: 1.5px solid #cbd5e1; color: inherit;")
        self.hist_btn.clicked.connect(self.show_history)
        
        self.pause_btn = QPushButton("⏸️ Pause")
        self.pause_btn.setObjectName("pauseBtn")
        self.pause_btn.clicked.connect(self.pause_download)
        self.pause_btn.hide()

        self.cancel_btn = QPushButton("✖ Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.cancel_download)
        self.cancel_btn.hide()
        
        self.dl_btn = QPushButton("🚀 Start Download")
        self.dl_btn.setFixedHeight(54)
        self.dl_btn.clicked.connect(self.start)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(59, 130, 246, 100))
        shadow.setOffset(0, 4)
        self.dl_btn.setGraphicsEffect(shadow)

        btn_layout.addWidget(self.hist_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.dl_btn, 2)
        main_layout.addLayout(btn_layout)

        self.update_options(self.type_combo.currentText())

    def update_options(self, m_type):
        self.format_combo.clear()
        self.quality_combo.clear()
        if m_type == 'Video':
            self.format_combo.addItems(["MP4", "MKV", "WEBM"])
            self.quality_combo.addItems(["Auto (Best)", "4K", "2K", "1080p", "720p", "480p", "360p", "144p"])
            self.quality_combo.setEnabled(True)
            self.sub_chk.setEnabled(True)
        else:
            self.format_combo.addItems(["MP3", "M4A", "WAV"])
            self.quality_combo.addItem("Best Audio")
            self.quality_combo.setEnabled(False)
            self.sub_chk.setEnabled(False)

    def apply_theme(self):
        is_dark = self.settings.get('dark', True)
        self.setStyleSheet(DARK_THEME if is_dark else LIGHT_THEME)
        self.theme_btn.setText("🌙" if is_dark else "☀️")
        
        # Override dynamic elements style fixes based on theme
        btn_border = "#45475a" if is_dark else "#cbd5e1"
        btn_color = "#f8fafc" if is_dark else "#111827"
        
        style = f"background-color: transparent; border: 1.5px solid {btn_border}; color: {btn_color};"
        self.clear_btn.setStyleSheet(style)
        self.hist_btn.setStyleSheet(style)
        
        self.status.setStyleSheet(f"color: {'#89b4fa' if is_dark else '#3b82f6'}; font-weight: 700;")

    def toggle_theme(self):
        self.settings['dark'] = not self.settings.get('dark', True)
        self.save_settings()
        self.apply_theme()

    def browse(self):
        f = QFileDialog.getExistingDirectory(self, "Select Folder", self.path_input.text())
        if f:
            self.path_input.setText(f)
            self.settings['path'] = f
            self.save_settings()

    def open_folder(self):
        path = self.path_input.text()
        if sys.platform == "darwin": subprocess.call(["open", path])
        elif sys.platform == "win32": os.startfile(path)
        else: subprocess.call(["xdg-open", path])

    def check_clipboard(self):
        txt = QApplication.clipboard().text().strip()
        if txt and txt != self.last_clip:
            valid = any(x in txt for x in ['youtube.com', 'youtu.be', 'tiktok.com', 'facebook.com', 'instagram.com', 'x.com', 'twitter.com', 'vimeo.com'])
            if valid:
                self.last_clip = txt
                self.url_input.setText(txt)

    def on_url_change(self):
        txt = self.url_input.text().strip().split(',')[0] # preview first logic
        if txt.startswith("http"):
            self.preview_card.show()
            self.p_title.setText("Fetching video info...")
            self.thumb_label.clear()
            if self.info_worker: self.info_worker.terminate()
            self.info_worker = InfoWorker(txt)
            self.info_worker.info_ready.connect(self.show_preview)
            self.info_worker.start()
        else:
            self.preview_card.hide()

    def show_preview(self, info):
        self.p_title.setText(info.get('title', 'Unknown Title'))
        sec = info.get('duration', 0)
        self.p_dur.setText(f"Duration: {str(timedelta(seconds=int(sec))) if sec else 'Unknown'}")
        self.p_plat.setText(f"Platform: {info.get('extractor', 'Unknown')}")
        
        url = info.get('thumbnail')
        if url:
            if hasattr(self, 'thumb_worker') and self.thumb_worker:
                self.thumb_worker.terminate()
            self.thumb_worker = ThumbnailWorker(url)
            self.thumb_worker.finished.connect(self.load_thumbnail_data)
            self.thumb_worker.start()

    def load_thumbnail_data(self, data):
        try:
            pm = QPixmap()
            pm.loadFromData(data)
            pm = pm.scaled(160, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.thumb_label.setPixmap(pm)
        except Exception as e:
            logging.error(f"Error drawing thumbnail pixmap: {e}")

    def show_history(self):
        HistoryDialog(self).exec_()

    def record_history(self, title):
        hist = []
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r') as f:
                    hist = json.load(f)
        except: pass
        if title not in hist:
            hist.append(title)
        if len(hist) > 20: hist.pop(0)
        with open(HISTORY_FILE, 'w') as f: json.dump(hist, f)

    def start(self):
        out_path = self.path_input.text()
        if not os.path.exists(out_path) or not os.path.isdir(out_path):
            QMessageBox.warning(self, "Error", "Download path does not exist.")
            return
        if not os.access(out_path, os.W_OK):
            QMessageBox.warning(self, "Error", "Download path is not writable. Please check permissions.")
            return

        raw_urls = [u.strip() for u in self.url_input.text().split(',') if u.strip()]
        valid_urls = []
        for u in raw_urls:
            if re.match(r'^https?://', u):
                valid_urls.append(u)
            else:
                logging.warning(f"Skipped invalid URL: {u}")
                
        if not valid_urls:
            QMessageBox.warning(self, "Error", "Please paste at least one valid HTTP/HTTPS link.")
            return

        urls = valid_urls
        self.dl_btn.hide()
        self.cancel_btn.show()
        self.pause_btn.show()
        self.bar.setValue(0)
        self.status.setText("Initializing...")
        
        is_dark = self.settings.get('dark', True)
        self.status.setStyleSheet(f"color: {'#f9e2af' if is_dark else '#f59e0b'}; font-weight: 700;") # Yellow processing

        opts = {
            'type': self.type_combo.currentText(),
            'format': self.format_combo.currentText(),
            'quality': self.quality_combo.currentText(),
            'playlist': self.pl_chk.isChecked(),
            'subtitles': self.sub_chk.isChecked()
        }

        self.dl_worker = DownloadWorker(urls, opts, self.path_input.text())
        self.dl_worker.progress.connect(self.update_progress)
        self.dl_worker.status.connect(self.status.setText)
        self.dl_worker.finished.connect(self.on_success)
        self.dl_worker.error.connect(self.on_error)
        self.dl_worker.warning.connect(self.on_warning)
        self.dl_worker.start()

    def cancel_download(self):
        if self.dl_worker:
            self.dl_worker.is_cancelled = True
            self.status.setText("Cancelling...")
            self.reset_ui(err=True)

    def pause_download(self):
        if self.dl_worker:
            self.dl_worker.is_cancelled = True
            self.status.setText("Paused. Click Start to resume.")
            is_dark = self.settings.get('dark', True)
            self.status.setStyleSheet(f"color: {'#fab005' if is_dark else '#d97706'}; font-weight: 700;")
            self.reset_ui(err=False)

    def update_progress(self, d):
        self.bar.setValue(d['p'])
        self.speed_lbl.setText(f"Speed: {d['sp']}")
        self.eta_lbl.setText(f"ETA: {d['eta']}")
        self.size_lbl.setText(f"Progress: {d['dl']} / {d['tl']}")

    def reset_ui(self, err=False):
        self.cancel_btn.hide()
        self.pause_btn.hide()
        self.dl_btn.show()
        is_dark = self.settings.get('dark', True)
        if err: self.status.setStyleSheet(f"color: {'#f38ba8' if is_dark else '#ef4444'}; font-weight: 700;") # red

    def on_success(self, msg):
        self.reset_ui()
        self.bar.setValue(100)
        self.status.setText("✅ Download Complete")
        
        is_dark = self.settings.get('dark', True)
        self.status.setStyleSheet(f"color: {'#a6e3a1' if is_dark else '#10b981'}; font-weight: 700;") # green
        
        self.record_history(self.p_title.text())
        self.url_input.clear()
        
        SuccessDialog(self).exec_()

    def on_error(self, err):
        self.reset_ui(err=True)
        self.status.setText(f"❌ Error: {err}")
        if "Cancelled" not in err:
            QMessageBox.critical(self, "Error", str(err))

    def on_warning(self, msg):
        logging.warning(msg)
        is_dark = self.settings.get('dark', True)
        self.status.setStyleSheet(f"color: {'#fab005' if is_dark else '#d97706'}; font-weight: 700;")
        self.status.setText(f"⚠️ {msg}")


def check_ffmpeg():
    if sys.platform == "win32":
        if os.path.exists(resource_path('ffmpeg.exe')):
            return True, ""
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return True, ""
    except FileNotFoundError:
        return False, "ffmpeg was not found on your system.\n\nPlease install ffmpeg (e.g., 'brew install ffmpeg' on macOS or bundle it on Windows) or some formats may fail to merge."

if __name__ == '__main__':
    logging.info("Starting up Ultimate Media Downloader...")
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    ffmpeg_ok, ffmpeg_msg = check_ffmpeg()
    if not ffmpeg_ok:
        logging.warning("ffmpeg is missing!")
        QMessageBox.warning(None, "Missing Tool", ffmpeg_msg)
    
    font = app.font()
    font.setFamily("Inter")
    font.setPixelSize(16)
    app.setFont(font)
    
    window = DownloaderApp()
    window.show()
    sys.exit(app.exec_())
