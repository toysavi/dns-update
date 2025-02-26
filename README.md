# DNS Updater

This is a desktop application for updating DNS records using a GUI built with PyQt5.

## Requirements
- Python 3.x
- PyQt5
- PyInstaller

## Installation
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`.
3. To create the executable: `pyinstaller --onefile --windowed --icon=img/icon.ico src/dns_updater_gui.py`.

## Usage
- Import a CSV file with DNS records.
- Select the record types (A Record, CNAME, or Both).
- Apply updates to DNS records.
