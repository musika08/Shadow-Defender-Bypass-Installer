# 🛡️ Shadow Defender Bypass Installer (v1.00)

![Version](https://img.shields.io/badge/version-v1.00-blue?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-blue?style=flat-square)
[![Support](https://img.shields.io/badge/ko--fi-Support%20Creator-ff5f5f?style=flat-square&logo=ko-fi)](https://ko-fi.com/musika)

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

## 📥 Installation

### Method 1: PowerShell One-Liner (Fastest)
Run this command in **PowerShell** to download and launch the tool automatically:

```powershell
iwr -useb [https://raw.githubusercontent.com/musika08/Shadow-Defender-Bypass-Installer/main/install.ps1](https://raw.githubusercontent.com/musika08/Shadow-Defender-Bypass-Installer/main/install.ps1) | iex
