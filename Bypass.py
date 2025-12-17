import os
import sys
import requests
import subprocess
import ctypes
import shutil
import winreg
import urllib3
import traceback

# --- VERSION CONTROL ---
APP_VERSION = "1.01"
# -----------------------

# --- CRASH PROTECTION & IMPORTS ---
try:
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
        QMainWindow, QMessageBox, QProgressBar, QFrame, QGraphicsDropShadowEffect
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QThread, QUrl
    from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap, QPainter, QBrush, QDesktopServices
except ImportError as e:
    ctypes.windll.user32.MessageBoxW(0, f"Error: Missing Libraries.\n\n{e}\n\nPlease run 'requirements.bat' first!", "Dependency Error", 0x10)
    sys.exit(1)

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "_SD_Temp_Install")
SETUP_FILENAME = "ShadowDefenderSetup.exe"
SETUP_PATH = os.path.join(BASE_DIR, SETUP_FILENAME)
TARGET_INSTALL_PATH = r"C:\Program Files\Shadow Defender\ShadowDefender.exe"
TARGET_INSTALL_PATH_X86 = r"C:\Program Files (x86)\Shadow Defender\ShadowDefender.exe"
UNINSTALLER_PATH = r"C:\Program Files\Shadow Defender\Uninstall.exe"
UNINSTALLER_PATH_X86 = r"C:\Program Files (x86)\Shadow Defender\Uninstall.exe"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

DOWNLOAD_URLS = [
    "https://www.shadowdefender.com/download/Setup.exe",
    "http://www.shadowdefender.com/download/Setup.exe"
]

class Archiver:
    def __init__(self):
        self.exe_path, self.type = self._detect_archiver()

    def _detect_archiver(self):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\7-Zip") as key:
                path, _ = winreg.QueryValueEx(key, "Path")
                exe = os.path.join(path, "7z.exe")
                if os.path.exists(exe): return exe, "7z"
        except: pass
        
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WinRAR") as key:
                path, _ = winreg.QueryValueEx(key, "exe64")
                if os.path.exists(path): return path, "rar"
        except: pass

        candidates = [
            (r"C:\Program Files\7-Zip\7z.exe", "7z"),
            (r"C:\Program Files (x86)\7-Zip\7z.exe", "7z"),
            (r"C:\Program Files\WinRAR\WinRAR.exe", "rar"),
            (r"C:\Program Files (x86)\WinRAR\WinRAR.exe", "rar")
        ]
        for p, t in candidates:
            if os.path.exists(p): return p, t
        return None, None

    def extract(self, source, dest):
        if not self.exe_path: raise FileNotFoundError("Archiver not found. Please install 7-Zip or WinRAR.")
        os.makedirs(dest, exist_ok=True)
        if self.type == "7z":
            cmd = [self.exe_path, "x", "-y", f"-o{dest}", source]
        else:
            cmd = [self.exe_path, "x", "-y", source, dest]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)

class Worker(QThread):
    status_update = pyqtSignal(str, str)
    progress_update = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    finished_result = pyqtSignal(bool)
    ask_download = pyqtSignal()

    def __init__(self, mode="auto"):
        super().__init__()
        self.mode = mode
        self.archiver = Archiver()

    def run(self):
        try:
            if self.mode == "download": 
                self.download_setup()
            elif self.mode == "uninstall":
                self.run_uninstall()
                return

            self.process_pipeline()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def run_uninstall(self):
        target_uninstaller = None
        if os.path.exists(UNINSTALLER_PATH):
            target_uninstaller = UNINSTALLER_PATH
        elif os.path.exists(UNINSTALLER_PATH_X86):
            target_uninstaller = UNINSTALLER_PATH_X86
        
        if not target_uninstaller:
            raise Exception("Uninstaller not found. Is Shadow Defender installed?")

        self.status_update.emit("Uninstalling...", "#ff4444")
        self.progress_update.emit(50)
        
        # Run the uninstaller
        subprocess.run([target_uninstaller], check=True)
        
        self.status_update.emit("Uninstalled", "#aaaaaa")
        self.progress_update.emit(100)
        self.finished_result.emit(True)

    def download_setup(self):
        self.status_update.emit("Downloading Setup...", "#00ffff")
        downloaded = False
        for url in DOWNLOAD_URLS:
            try:
                with requests.get(url, headers=HEADERS, stream=True, verify=False, timeout=20) as r:
                    r.raise_for_status()
                    total = int(r.headers.get('content-length', 0))
                    with open(SETUP_PATH, 'wb') as f:
                        if total == 0:
                            f.write(r.content)
                        else:
                            dl = 0
                            for data in r.iter_content(chunk_size=8192):
                                dl += len(data)
                                f.write(data)
                                self.progress_update.emit(int((dl / total) * 100))
                downloaded = True
                break
            except: continue
        if not downloaded: raise Exception("Download failed from all mirrors.")

    def process_pipeline(self):
        usage = shutil.disk_usage(BASE_DIR)
        if usage.free < (100 * 1024 * 1024):
            raise Exception("Insufficient disk space. Please free up 100MB.")

        if not self.archiver.exe_path: raise Exception("WinRAR or 7-Zip is required.")
        if not os.path.exists(SETUP_PATH):
            self.ask_download.emit()
            return
        
        subprocess.run("taskkill /f /im ShadowDefenderSetup.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        self.status_update.emit("Extracting Core Files...", "#00ffff")
        self.progress_update.emit(10)
        
        if os.path.exists(TEMP_DIR):
            try: shutil.rmtree(TEMP_DIR)
            except: pass

        ext1 = os.path.join(TEMP_DIR, "Stage1")
        self.archiver.extract(SETUP_PATH, ext1)
        
        setup_x64 = self._find_file(ext1, "setup_x64.exe")
        if not setup_x64: raise Exception("Installer corrupt (Stage 1).")
        
        self.status_update.emit("Preparing Installer...", "#00ffff")
        self.progress_update.emit(40)
        ext2 = os.path.join(TEMP_DIR, "Stage2")
        self.archiver.extract(setup_x64, ext2)
        
        final_setup = self._find_file(ext2, "setup.exe")
        if not final_setup: raise Exception("Installer corrupt (Stage 2).")
        
        target = os.path.join(ext2, "Install_SD.exe")
        if os.path.exists(target): os.remove(target)
        os.rename(final_setup, target)
        
        self.status_update.emit("Installing...", "#00ff7f")
        self.progress_update.emit(100)
        
        subprocess.run([target], check=True)
        
        installed = os.path.exists(TARGET_INSTALL_PATH) or os.path.exists(TARGET_INSTALL_PATH_X86)
        self.finished_result.emit(installed)

    def _find_file(self, folder, name):
        for r, _, f in os.walk(folder):
            for i in f:
                if i.lower() == name.lower(): return os.path.join(r, i)
        return None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def generate_icon(self):
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor("#00ff7f"))) 
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
        painter.setBrush(QBrush(QColor("#1a1a1a"))) 
        painter.drawRect(20, 15, 24, 34)
        painter.end()
        return QIcon(pixmap)

    def open_kofi(self):
        QDesktopServices.openUrl(QUrl("https://ko-fi.com/musika"))

    def setup_ui(self):
        self.setWindowTitle(f"Shadow Defender Tool v{APP_VERSION}")
        self.setFixedSize(420, 420) # Slightly taller for dual buttons
        
        self.setStyleSheet("""
            QMainWindow { background-color: #1a1a1a; }
            QLabel { font-family: 'Segoe UI'; }
            QProgressBar {
                border: 1px solid #333333;
                background-color: #121212;
                height: 8px;
                border-radius: 4px;
            }
            QProgressBar::chunk { background-color: #00ff7f; border-radius: 4px; }
        """)

        self.setWindowIcon(self.generate_icon())

        central = QWidget()
        self.setCentralWidget(central)
        lay = QVBoxLayout(central)
        lay.setSpacing(20)
        lay.setContentsMargins(40, 35, 40, 20)

        # Title Layout
        self.title = QLabel("SHADOW DEFENDER")
        self.title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("color: #ffffff; letter-spacing: 1px;")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 255, 127, 80))
        shadow.setOffset(0, 0)
        self.title.setGraphicsEffect(shadow)
        
        lay.addWidget(self.title)

        self.sub = QLabel("Windows 11 Bypass Installer")
        self.sub.setFont(QFont("Segoe UI", 10))
        self.sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub.setStyleSheet("color: #666666; font-weight: 500;")
        lay.addWidget(self.sub)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #333333;")
        lay.addWidget(line)

        lay.addStretch()

        self.status = QLabel("Ready to Start")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setFont(QFont("Segoe UI", 11))
        self.status.setStyleSheet("color: #888888;")
        lay.addWidget(self.status)

        self.pbar = QProgressBar()
        self.pbar.setTextVisible(False)
        self.pbar.setValue(0)
        lay.addWidget(self.pbar)

        lay.addStretch()

        # --- BUTTONS LAYOUT (Install & Uninstall) ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        # INSTALL BUTTON
        self.btn_install = QPushButton("INSTALL")
        self.btn_install.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_install.setMinimumHeight(50)
        self.btn_install.clicked.connect(lambda: self.start_process_flow("install"))
        self.btn_install.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #444;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #383838;
                border-color: #00ff7f;
                color: #00ff7f;
            }
            QPushButton:pressed { background-color: #222; }
            QPushButton:disabled { color: #555; border-color: #222; }
        """)
        btn_layout.addWidget(self.btn_install)

        # UNINSTALL BUTTON
        self.btn_uninstall = QPushButton("UNINSTALL")
        self.btn_uninstall.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_uninstall.setMinimumHeight(50)
        self.btn_uninstall.clicked.connect(lambda: self.start_process_flow("uninstall"))
        self.btn_uninstall.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #ffaaaa;
                border: 1px solid #552222;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3d2222;
                border-color: #ff4444;
                color: #ff4444;
            }
            QPushButton:pressed { background-color: #221111; }
            QPushButton:disabled { color: #555; border-color: #222; }
        """)
        btn_layout.addWidget(self.btn_uninstall)

        lay.addLayout(btn_layout)

        # --- FOOTER LAYOUT ---
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 5, 0, 0)
        
        # Support
        self.btn_kofi = QPushButton("☕ Support")
        self.btn_kofi.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_kofi.clicked.connect(self.open_kofi)
        self.btn_kofi.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #aaaaaa;
                border: 1px solid #444444;
                border-radius: 12px;
                padding: 4px 10px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #29abe0;
                color: white;
                border-color: #29abe0;
            }
        """)
        footer_layout.addWidget(self.btn_kofi)
        
        footer_layout.addStretch()

        # Version
        self.version_lab = QLabel(f"v{APP_VERSION}")
        self.version_lab.setStyleSheet("color: #444444; font-size: 10px; font-weight: bold;")
        footer_layout.addWidget(self.version_lab)

        footer_layout.addStretch()

        # Signature
        self.sig = QLabel("by Musika")
        self.sig.setFont(QFont("Segoe UI", 9))
        self.sig.setStyleSheet("color: #444444; font-style: italic;")
        footer_layout.addWidget(self.sig)

        lay.addLayout(footer_layout)

    def is_core_isolation_on(self):
        try:
            path = r"SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                val, _ = winreg.QueryValueEx(key, "Enabled")
                return val == 1
        except:
            return False

    def disable_core_isolation(self):
        try:
            path = r"SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity"
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                winreg.SetValueEx(key, "Enabled", 0, winreg.REG_DWORD, 0)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Registry Error", f"Could not disable Core Isolation:\n{e}")
            return False

    def start_process_flow(self, action_type):
        # UNINSTALL FLOW
        if action_type == "uninstall":
            confirm = QMessageBox.question(self, "Confirm Uninstall", 
                "Are you sure you want to remove Shadow Defender?", 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirm == QMessageBox.StandardButton.Yes:
                self.start_worker("uninstall")
            return

        # INSTALL FLOW (Check Core Isolation First)
        if self.is_core_isolation_on():
            msg = QMessageBox()
            msg.setWindowTitle("Conflict Detected")
            msg.setText("Windows Core Isolation (Memory Integrity) is ENABLED.")
            msg.setInformativeText("This feature prevents Shadow Defender from working.\n\nDo you want to turn it OFF automatically?")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setStyleSheet("background-color: #2d2d2d; color: white;")
            
            if msg.exec() == QMessageBox.StandardButton.Yes:
                if self.disable_core_isolation():
                    reboot = QMessageBox.question(self, "Reboot Required", 
                        "Core Isolation disabled successfully.\n\nYou must REBOOT your PC for this to take effect.\n\nReboot now?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if reboot == QMessageBox.StandardButton.Yes:
                        subprocess.run("shutdown /r /t 0", shell=True)
                        sys.exit()
                    else:
                        self.update_status("Pending Reboot", "#ffcc00")
                        return 
                else: return 
            else:
                QMessageBox.warning(self, "Warning", "Installation may fail or BSOD if Core Isolation remains on.")

        self.start_worker("auto")

    def start_worker(self, mode):
        self.btn_install.setEnabled(False)
        self.btn_uninstall.setEnabled(False)
        
        if mode == "uninstall":
            self.btn_uninstall.setText("...")
        else:
            self.btn_install.setText("PROCESSING...")
            
        self.pbar.setValue(0)
        self.worker = Worker(mode)
        self.worker.status_update.connect(self.update_status) 
        self.worker.progress_update.connect(self.pbar.setValue)
        self.worker.error_occurred.connect(self.err)
        self.worker.ask_download.connect(self.ask_dl)
        self.worker.finished_result.connect(self.fin)
        self.worker.start()

    def update_status(self, text, color_hex):
        self.status.setText(text)
        self.status.setStyleSheet(f"color: {color_hex}; font-weight: bold;")

    def ask_dl(self):
        if QMessageBox.question(self, "Download Required", "Installer missing. Download now?", 
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.start_worker("download")
        else: self.reset("Cancelled", "#ff6666") 

    def fin(self, success):
        if os.path.exists(TEMP_DIR):
            try: shutil.rmtree(TEMP_DIR)
            except: pass

        # Check if it was an uninstall or install based on worker mode
        if self.worker.mode == "uninstall":
             QMessageBox.information(self, "Uninstall", "Uninstaller process finished.")
             self.reset("Uninstalled", "#aaaaaa")
        else:
            if success:
                QMessageBox.information(self, "Success", "Installation Verified Successfully.")
                self.reset("Installed Successfully", "#00ff7f") 
            else: self.reset("Setup Not Completed", "#ffcc00")

    def err(self, m):
        QMessageBox.critical(self, "Error", m)
        self.reset("Error Occurred", "#ff4444") 

    def reset(self, txt, color="#888888"):
        self.status.setText(txt)
        self.status.setStyleSheet(f"color: {color};")
        self.btn_install.setEnabled(True)
        self.btn_uninstall.setEnabled(True)
        self.btn_install.setText("INSTALL")
        self.btn_uninstall.setText("UNINSTALL")
        self.pbar.setValue(0)

if __name__ == "__main__":
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            script_path = os.path.abspath(__file__)
            params = f'"{script_path}"'
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
            sys.exit()

        app = QApplication(sys.argv)
        w = MainWindow()
        w.show()
        sys.exit(app.exec())
    
    except Exception as e:
        with open("crash_log.txt", "w") as f:
            traceback.print_exc(file=f)
        ctypes.windll.user32.MessageBoxW(0, f"Critical Error:\n{str(e)}", "Crash", 0x10)
