Shadow Defender Universal Installer

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6)
![Version](https://img.shields.io/badge/Version-1.00-green)
[![Support](https://img.shields.io/badge/Support-Ko--fi-FF5E5B)](https://ko-fi.com/musika)


A smart, automated tool designed to make Shadow Defender compatible with modern Windows 10 and 11 systems.
🛑 The Problem

Shadow Defender is a powerful security tool, but its core driver (diskpt.sys) is incompatible with a modern Windows 11 security feature called Core Isolation (Memory Integrity).

    If you try to install the standard version on Windows 11, it often fails or causes a Blue Screen of Death (BSOD).

    Manually fixing this requires editing the Registry and complex reboot sequences.

✅ The Solution

This tool automates the entire process. It acts as a "wrapper" that detects system conflicts, prepares your PC, and installs the software safely without you needing to touch technical settings.
⚙️ What It Does (Step-by-Step)

    System Check: It scans your computer to see if Core Isolation is enabled.

    Auto-Fix: If a conflict is found, it automatically disables the specific registry keys preventing the driver from loading.

    Smart Resume: If your PC needs to reboot to apply the fix, the tool sets itself to auto-start. Once you log back in, it pops back up and continues exactly where it left off.

    Dependency-Free: You don't need to install WinRAR or 7-Zip. The tool includes a "Self-Healing" engine that automatically fetches a portable extraction tool if your system is missing one.

    Deep Extraction: It handles the complex unpacking of the installer (removing compatibility wrappers) to ensure the clean driver setup is run.

    Clean Up: Once the installation is finished, the tool deletes itself to keep your Downloads/Temp folder clean.

🛡️ Safety & Restoration

This tool is designed to respect your system security. When you use this tool to Uninstall Shadow Defender:

    It removes the software completely.

    It offers to Re-Enable Core Isolation, restoring your Windows 11 security settings to their original, safe state.

🚀 How to Use

Option 1: The One-Line Command (Fastest) Open PowerShell as Administrator and paste:
PowerShell

irm https://raw.githubusercontent.com/musika08/Shadow-Defender-Bypass-Installer/main/install.ps1 | iex

Option 2: Manual Download

    Download ShadowDefenderTool.exe.

    Right-click and Run as Administrator.

    Click Install. The tool handles the rest.
