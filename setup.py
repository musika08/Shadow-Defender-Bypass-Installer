import os
import sys
import subprocess
import ctypes
import shutil
import winreg
import traceback
import tempfile
import time
from pathlib import Path

# --- VERSION CONTROL ---
APP_VERSION = "1.00"
# -----------------------

# --- IMPORTS ---
try:
    import requests
    import urllib3
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
        QMainWindow, QMessageBox, QProgressBar, QFrame, QGraphicsDropShadowEffect
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QThread, QUrl
    from PyQt6.QtGui import QFont, QColor, QIcon, QPixmap, QPainter, QBrush, QDesktopServices
except ImportError as e:
    ctypes.windll.user32.MessageBoxW(0, f"Error: Missing Libraries.\n\n{e}\n\nPlease run 'requirements.bat' first!", "Dependency Error", 0x10)
    sys.exit(1)

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    EXE_PATH = sys.executable
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_PATH = os.path.abspath(__file__)

DOWNLOAD_URLS = [
    "http://www.shadowdefender.com/download/SD1.5.0.726_Setup.exe",
    "https://www.shadowdefender.com/download/Setup.exe",
    "http://www.shadowdefender.com/download/Setup.exe"
]

PORTABLE_7Z_URL = "https://www.7-zip.org/a/7zr.exe"

TARGET_INSTALL_PATH = r"C:\Program Files\Shadow Defender\ShadowDefender.exe"
TARGET_INSTALL_PATH_X86 = r"C:\Program Files (x86)\Shadow Defender\ShadowDefender.exe"

class DependencyManager:
    """Handles external tools with Offline Support."""
    def __init__(self, temp_dir):
        self.temp_dir = temp_dir
        self.local_tool = os.path.join(temp_dir, "7zr.exe")
        self.system_tool, self.tool_type = self._detect_system_archiver()

    def _detect_system_archiver(self):
        # 1. Registry Check
        for key_path, exe_name, type_ in [
            (r"SOFTWARE\7-Zip", "7z.exe", "7z"),
            (r"SOFTWARE\WinRAR", "WinRAR.exe", "rar")
        ]:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                    path, _ = winreg.QueryValueEx(key, "Path" if "7-Zip" in key_path else "exe64")
                    exe = os.path.join(path, exe_name) if "7-Zip" in key_path else path
                    if os.path.exists(exe): return exe, type_
            except: pass

        # 2. Manual Locations
        candidates = [
            (r"C:\Program Files\7-Zip\7z.exe", "7z"),
            (r"C:\Program Files (x86)\7-Zip\7z.exe", "7z"),
            (r"C:\Program Files\WinRAR\WinRAR.exe", "rar"),
            (r"C:\Program Files (x86)\WinRAR\WinRAR.exe", "rar")
        ]
        for p, t in candidates:
            if os.path.exists(p): return p, t
        return None, None

    def get_extractor_cmd(self):
        if self.system_tool: return self.system_tool, self.tool_type
        if os.path.exists(self.local_tool): return self.local_tool, "7z"
        return None, None

    def download_portable_tool(self):
        if self.system_tool: return
        
        # Check Local Cache First (Offline Mode)
        cached_tool = os.path.join(BASE_DIR, "7zr.exe")
        if os.path.exists(cached_tool):
            shutil.copy(cached_tool, self.local_tool)
            return

        try:
            r = requests.get(PORTABLE_7Z_URL, stream=True, timeout=15)
            with open(self.local_tool, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        except:
            raise Exception("Failed to download 7-Zip. Please place '7zr.exe' in the script folder.")

class Worker(QThread):
    status_update = pyqtSignal(str, str)
    progress_update = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    finished_result = pyqtSignal(bool)

    def __init__(self, mode="auto"):
        super().__init__()
        self.mode = mode
        self.temp_dir = None

    def run(self):
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                self.temp_dir = temp_dir
                self.deps = DependencyManager(temp_dir)

                if self.mode == "uninstall":
                    self.run_uninstall()
                else:
                    self.run_install_pipeline()
        except Exception as e:
            traceback.print_exc()
            self.error_occurred.emit(str(e))

    def run_uninstall(self):
        target_uninstaller = None
        if os.path.exists(r"C:\Program Files\Shadow Defender\Uninstall.exe"):
            target_uninstaller = r"C:\Program Files\Shadow Defender\Uninstall.exe"
        elif os.path.exists(r"C:\Program Files (x86)\Shadow Defender\Uninstall.exe"):
            target_uninstaller = r"C:\Program Files (x86)\Shadow Defender\Uninstall.exe"
        
        if not target_uninstaller:
            raise Exception("Uninstaller not found.")

        self.status_update.emit("Uninstalling...", "#ff4444")
        self.progress_update.emit(50)
        subprocess.run([target_uninstaller], check=True)
        self.status_update.emit("Uninstalled", "#aaaaaa")
        self.progress_update.emit(100)
        self.finished_result.emit(True)

    def run_install_pipeline(self):
        # 1. Dependency Check
        tool_path, _ = self.deps.get_extractor_cmd()
        if not tool_path:
            self.status_update.emit("Fetching Tools...", "#00ffff")
            self.deps.download_portable_tool()
            tool_path, _ = self.deps.get_extractor_cmd()
            if not tool_path: raise Exception("Could not initialize extraction tools.")

        setup_path = os.path.join(self.temp_dir, "ShadowDefenderSetup.exe")

        # 2. Download Setup (With Offline Cache Check)
        self.status_update.emit("Downloading Setup...", "#00ffff")
        download_success = False
        
        cached_setup = os.path.join(BASE_DIR, "ShadowDefenderSetup.exe")
        if not os.path.exists(cached_setup):
             cached_setup = os.path.join(BASE_DIR, "Setup.exe")
        
        if os.path.exists(cached_setup):
            shutil.copy(cached_setup, setup_path)
            download_success = True
            self.progress_update.emit(30)
        else:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            for url in DOWNLOAD_URLS:
                try:
                    with requests.get(url, headers=headers, stream=True, verify=False, timeout=30) as r:
                        if r.status_code != 200: continue
                        if 'text/html' in r.headers.get('Content-Type', '').lower(): continue
                        total = int(r.headers.get('content-length', 0))
                        dl = 0
                        with open(setup_path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                dl += len(chunk)
                                f.write(chunk)
                                if total > 0: self.progress_update.emit(int((dl / total) * 30))
                    if os.path.getsize(setup_path) > 2 * 1024 * 1024:
                        download_success = True
                        break
                except: continue
        
        if not download_success: raise Exception("Download failed. No internet or cached 'Setup.exe'.")

        # 3. Extraction (Bypass Logic)
        self.status_update.emit("Extracting Core...", "#00ffff")
        ext1 = os.path.join(self.temp_dir, "Stage1")
        self._extract(setup_path, ext1)
        
        setup_x64 = self._find_file(ext1, "setup_x64.exe")
        if not setup_x64: setup_x64 = self._find_file(ext1, "setup.exe")
        if not setup_x64: raise Exception("Installer corrupt (Extraction failed).")
        
        self.progress_update.emit(60)
        ext2 = os.path.join(self.temp_dir, "Stage2")
        self._extract(setup_x64, ext2)
        
        final_setup = self._find_file(ext2, "setup.exe")
        if not final_setup: final_setup = setup_x64

        target = os.path.join(ext2, "Install_SD.exe") if final_setup != setup_x64 else os.path.join(ext1, "Install_SD.exe")
        try: shutil.move(final_setup, target)
        except: shutil.copy(final_setup, target)

        # 4. Install
        self.status_update.emit("Installing...", "#00ff7f")
        self.progress_update.emit(100)
        subprocess.run([target], check=True)
        
        installed = os.path.exists(TARGET_INSTALL_PATH) or os.path.exists(TARGET_INSTALL_PATH_X86)
        self.finished_result.emit(installed)

    def _extract(self, source, dest):
        exe, type_ = self.deps.get_extractor_cmd()
        os.makedirs(dest, exist_ok=True)
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        cmd = [exe, "x", "-y", f"-o{dest}", source] if type_ == "7z" else [exe, "x", "-y", source, dest]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=si)

    def _find_file(self, folder, name):
        for r, _, f in os.walk(folder):
            for i in f:
                if i.lower() == name.lower(): return os.path.join(r, i)
        return None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.remove_resume_key()

    def generate_icon(self):
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor("#00CCFF"))) 
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
        painter.end()
        return QIcon(pixmap)

    def open_kofi(self):
        QDesktopServices.openUrl(QUrl("https://ko-fi.com/musika"))

    def setup_ui(self):
        self.setWindowTitle("Shadow Defender Tool")
        self.setFixedSize(420, 420)
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

        icon_file = os.path.join(BASE_DIR, "icon.ico")
        if os.path.exists(icon_file): self.setWindowIcon(QIcon(icon_file))
        else: self.setWindowIcon(self.generate_icon())

        central = QWidget()
        self.setCentralWidget(central)
        lay = QVBoxLayout(central)
        lay.setSpacing(20)
        lay.setContentsMargins(40, 35, 40, 20)

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

        self.sub = QLabel("Universal Bypass Installer")
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

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

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

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 5, 0, 0)
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

        self.version_lab = QLabel(f"v{APP_VERSION}")
        self.version_lab.setStyleSheet("color: #444444; font-size: 10px; font-weight: bold;")
        footer_layout.addWidget(self.version_lab)
        footer_layout.addStretch()

        self.sig = QLabel("by Musika")
        self.sig.setFont(QFont("Segoe UI", 9))
        self.sig.setStyleSheet("color: #444444; font-style: italic;")
        footer_layout.addWidget(self.sig)
        lay.addLayout(footer_layout)

    # --- CORE ISOLATION & REGISTRY LOGIC ---
    def is_core_isolation_on(self):
        try:
            path = r"SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                val, _ = winreg.QueryValueEx(key, "Enabled")
                return val == 1
        except: return False

    def disable_core_isolation(self):
        try:
            path = r"SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity"
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                winreg.SetValueEx(key, "Enabled", 0, winreg.REG_DWORD, 0)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not disable Core Isolation:\n{e}")
            return False

    def register_program(self):
        key_serial = "8XKHG-HXTW7-QWNX4-5MDX7-4R7CZ"
        organization = "Shadow Defender User"
        try:
            path = r"SOFTWARE\Shadow Defender"
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, path) as reg_key:
                winreg.SetValueEx(reg_key, "Name", 0, winreg.REG_SZ, organization)
                winreg.SetValueEx(reg_key, "Code", 0, winreg.REG_SZ, key_serial)
            return True
        except: return False

    def offer_security_restore(self):
        msg = QMessageBox()
        msg.setWindowTitle("Security Check")
        msg.setText("Shadow Defender has been removed.")
        msg.setInformativeText("Do you want to re-enable Windows Core Isolation?")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setStyleSheet("background-color: #2d2d2d; color: white;")
        if msg.exec() == QMessageBox.StandardButton.Yes:
            try:
                path = r"SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity"
                with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                    winreg.SetValueEx(key, "Enabled", 0, winreg.REG_DWORD, 1)
                QMessageBox.information(self, "Secure", "Core Isolation Enabled.\nPlease reboot.")
            except: pass

    def set_resume_key(self):
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\RunOnce"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValueEx(key, "ShadowDefenderInstaller", 0, winreg.REG_SZ, f'"{EXE_PATH}"')
        except Exception as e:
            print(f"Failed to set resume key: {e}")

    def remove_resume_key(self):
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\RunOnce"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, "ShadowDefenderInstaller")
        except: pass
    
    # --- SELF DESTRUCT LOGIC ---
    def self_destruct(self):
        if getattr(sys, 'frozen', False):
            cmd = f'ping 127.0.0.1 -n 3 > nul & del /f /q "{sys.executable}"'
            subprocess.Popen(f'cmd /c "{cmd}"', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Cleanup', "Do you want to delete this installer file now?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.self_destruct()
        event.accept()

    def start_process_flow(self, action_type):
        if action_type == "uninstall":
            if QMessageBox.question(self, "Confirm Uninstall", "Remove Shadow Defender?", 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                self.start_worker("uninstall")
            return

        if self.is_core_isolation_on():
            msg = QMessageBox()
            msg.setWindowTitle("Conflict Detected")
            msg.setText("Windows Core Isolation is ENABLED.")
            msg.setInformativeText("This prevents Shadow Defender from working.\n\nTurn it OFF automatically?")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setStyleSheet("background-color: #2d2d2d; color: white;")
            
            if msg.exec() == QMessageBox.StandardButton.Yes:
                if self.disable_core_isolation():
                    self.set_resume_key()
                    if QMessageBox.question(self, "Reboot Required", 
                        "Core Isolation disabled.\n\nReboot now? (Installer will resume automatically)",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                        subprocess.run("shutdown /r /t 0", shell=True)
                        sys.exit()
                    else:
                        self.update_status("Pending Reboot", "#ffcc00")
                        return 
            else:
                QMessageBox.warning(self, "Warning", "Installation may fail or BSOD if Core Isolation remains on.")

        self.start_worker("auto")

    def start_worker(self, mode):
        self.btn_install.setEnabled(False)
        self.btn_uninstall.setEnabled(False)
        self.status.setText("PROCESSING...")
        self.pbar.setValue(0)
        self.worker = Worker(mode)
        self.worker.status_update.connect(self.update_status) 
        self.worker.progress_update.connect(self.pbar.setValue)
        self.worker.error_occurred.connect(self.err)
        self.worker.finished_result.connect(self.fin)
        self.worker.start()

    def update_status(self, text, color_hex):
        self.status.setText(text)
        self.status.setStyleSheet(f"color: {color_hex}; font-weight: bold;")

    def fin(self, success):
        if self.worker.mode == "uninstall":
             self.offer_security_restore()
             QMessageBox.information(self, "Uninstall", "Uninstaller process finished.\n\nThis tool will now self-destruct.")
             self.self_destruct()
             sys.exit(0)
        else:
            if success:
                self.register_program()
                QMessageBox.information(self, "Success", "Shadow Defender Installed & Registered.\n\nThis tool will now self-destruct.")
                self.self_destruct()
                sys.exit(0)
            else: 
                self.reset("Setup Cancelled", "#ffcc00")

    def err(self, m):
        QMessageBox.critical(self, "Error", m)
        self.reset("Error Occurred", "#ff4444") 

    def reset(self, txt, color="#888888"):
        self.status.setText(txt)
        self.status.setStyleSheet(f"color: {color};")
        self.btn_install.setEnabled(True)
        self.btn_uninstall.setEnabled(True)
        self.pbar.setValue(0)

if __name__ == "__main__":
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            if getattr(sys, 'frozen', False):
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, None, None, 1)
            else:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{__file__}"', None, 1)
            sys.exit()
        app = QApplication(sys.argv)
        w = MainWindow()
        w.show()
        sys.exit(app.exec())
    except Exception as e:
        with open("crash_log.txt", "w") as f: traceback.print_exc(file=f)
        ctypes.windll.user32.MessageBoxW(0, f"Critical Error:\n{str(e)}", "Crash", 0x10)
