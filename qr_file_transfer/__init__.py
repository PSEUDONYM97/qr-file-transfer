"""
QR File Transfer Tool - Package Initialization

Professional-grade file transfer using QR codes with AES-256 encryption.
Converts files to QR codes for secure air-gapped transfer.
"""

__version__ = "3.0.0"
__author__ = "QR File Transfer Team"

# Import main CLI function for console script entry point
from .cli import main

__all__ = ["main"] 