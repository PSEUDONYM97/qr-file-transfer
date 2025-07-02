@echo off
REM QR File Transfer Tool v2.0 - Windows Batch Launcher
REM Usage: qr generate file.txt --verbose
REM        qr read ./photos/ --verbose

python "%~dp0qr.py" %* 