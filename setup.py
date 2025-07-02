#!/usr/bin/env python3
"""
Setup script for QR File Transfer Tool
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="qr-file-transfer",
    version="3.0.0",
    author="QR File Transfer Team",
    author_email="",
    description="Professional-grade file transfer using QR codes with AES-256 encryption - Now globally installable!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PSEUDONYM97/qr-file-transfer",
    project_urls={
        "Bug Reports": "https://github.com/PSEUDONYM97/qr-file-transfer/issues",
        "Source": "https://github.com/PSEUDONYM97/qr-file-transfer",
        "Documentation": "https://github.com/PSEUDONYM97/qr-file-transfer#readme",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security :: Cryptography",
        "Topic :: System :: Archiving",
        "Topic :: Utilities",
    ],
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "qr=qr_file_transfer.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="qr-code file-transfer encryption air-gap security cli global-command",
) 