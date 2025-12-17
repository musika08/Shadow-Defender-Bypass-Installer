# 🛡️ Shadow Defender Tool (v1.00)

![Version](https://img.shields.io/badge/version-v1.00-blue?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-blue?style=flat-square)
![Python](https://img.shields.io/badge/built%20with-Python%203%20%2B%20PyQt6-yellow?style=flat-square)

A specialized utility designed to install **Shadow Defender** on modern Windows systems (Windows 10/11) by automatically handling compatibility conflicts with **Core Isolation (Memory Integrity)**.

## 🚧 The Problem
On Windows 11 and newer builds of Windows 10, **Core Isolation (Memory Integrity)** prevents the Shadow Defender driver from loading, causing installation failures or Blue Screens (BSOD).

## 💡 The Solution
This tool automates the bypass process:
1.  **Detects** if Core Isolation is active in the Registry.
2.  **Disables** the conflict automatically (with user permission).
3.  **Installs** the software safely after the necessary reboot.

---

## ✨ Features

### 🖥️ Modern GUI Dashboard
- Clean, dark-mode interface built with **PyQt6**.
- Real-time progress bars for downloading and extraction.
- **Light Blue** status indicators and custom iconography.

### ⚡ Smart Installation
- **Auto-Download:** Automatically fetches the official `setup.exe` from Shadow Defender servers if missing.
- **Deep Extraction:** Uses internal logic to extract the core installer from the downloaded wrapper (supports auto-detection of 7-Zip/WinRAR).
- **Core Isolation Bypass:** Modifies `HypervisorEnforcedCodeIntegrity` registry keys to ensure driver compatibility.

### 🗑️ One-Click Uninstaller
- Includes a dedicated **Red "UNINSTALL" button**.
- Automatically locates the installation path and executes the clean removal process.

---

## 📥 Installation & Usage

### Option 1: The Easy Way (Recommended)
_Best for users who just want to use the tool._

1.  Go to the [**Releases**](https://github.com/YOUR_USERNAME/YOUR_REPO/releases) page.
2.  Download **`ShadowDefenderTool.exe`**.
3.  Right-click and select **Run as Administrator**.
4.  Click **INSTALL**.
    * *If Core Isolation is detected, accept the prompt to disable it and reboot your PC.*

### Option 2: The Developer Way (Source Code)
_Best for developers who want to modify the script._

1.  Clone this repository or download the Source Code zip.
2.  Run the dependency manager:
    ```cmd
    requirements.bat
    ```
    *(This will install Python libraries like PyQt6, requests, and urllib3 via a custom CLI dashboard)*.
3.  Run the tool:
    ```cmd
    python setup.py
    ```

### ⚙️ How to Compile (Build .exe)
If you want to build your own executable from the source:
1.  Ensure you have run `requirements.bat`.
2.  Double-click **`build.bat`**.
3.  The script will automatically detect your environment, generate the icon, and produce a standalone file in the `dist/` folder.

---

## 📸 Screenshots

| Installer Dashboard | Uninstall Mode |
|:---:|:---:|
| *(Add a screenshot of your Green/Blue GUI here)* | *(Add a screenshot of the Uninstall confirmation here)* |

---

## ⚠️ Disclaimer
This tool modifies Windows Registry keys related to Virtualization-based Security (VBS) to allow legacy drivers to load.
* **Use at your own risk.**
* Disabling Core Isolation lowers security slightly to allow the Shadow Defender driver to function.
* Always ensure you are using valid software licenses.

## ☕ Credits
**Created by Musika**
* Built with Python & PyQt6.
* Uninstaller & Auto-Repair logic added in v1.00.
