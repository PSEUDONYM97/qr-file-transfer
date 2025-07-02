# 🚀 QR File Transfer Tool

**Transfer files securely using QR codes - Perfect for air-gapped systems and mobile workflows**

Convert any file into QR code sheets, scan them with your phone, and reconstruct the original file perfectly. Built for security professionals, developers, and anyone needing reliable offline file transfer.

## ✨ Key Features

- **📱 Single Image Support**: Process individual QR images or entire folders
- **🛡️ Air-Gap Security**: Complete offline operation with optional AES-256 encryption  
- **📄 Sheet Generation**: Multiple QR codes per image for efficient scanning
- **🔧 Format Preservation**: Exact file reconstruction with tabs, encoding, and structure intact
- **⚡ Smart Detection**: Auto-detects file types and processing methods
- **🖥️ Cross-Platform**: Works on Windows, macOS, and Linux

---

## 🚀 Quick Start

### Installation

#### Option 1: Install from PyPI (Recommended)
```bash
# Install directly from PyPI
pip install qr-file-transfer

# Test the installation
qr --version
```

#### Option 2: Install from Source
```bash
# Clone the repository
git clone https://github.com/PSEUDONYM97/qr-file-transfer.git
cd qr-file-transfer

# Install with pip (creates `qr` command)
pip install -e .

# Or install dependencies manually
pip install -r requirements.txt

# Test the installation
python qr.py --version  # Manual install
qr --version             # Pip install
```

#### Requirements
- Python 3.8 or higher
- See `requirements.txt` for Python package dependencies

### Basic Usage

```bash
# Generate QR code sheets (recommended)
python qr.py generate myfile.txt --sheet

# Process single QR image (auto-detects and rebuilds)
python qr.py read my_photo_of_qr.png

# Process folder of QR images  
python qr.py read ./qr_photos/

# Generate with encryption
python qr.py generate sensitive.txt --encrypt --sheet
```

---

## 🎯 Use Cases

### 📱 **Mobile File Transfer**
Take photos of QR sheets with your phone, transfer to any device, and reconstruct files instantly.

### 🛡️ **Air-Gapped Security**  
Securely transfer files between isolated systems using only visual QR codes.

### 🏢 **Enterprise Workflows**
Bridge secure networks, transfer configurations, and maintain audit trails.

### 🎓 **Educational/Research**
Share code, data, and documents in environments with network restrictions.

---

## 📖 Complete Command Reference

### Generate QR Codes

```bash
# Basic generation
python qr.py generate myfile.txt

# Generate QR sheets (9 codes per image - recommended)
python qr.py generate myfile.txt --sheet

# With encryption (prompts for password)
python qr.py generate myfile.txt --encrypt --sheet

# Verbose output with progress tracking
python qr.py generate myfile.txt --sheet --verbose

# Skip automatic cleanup for debugging
python qr.py generate myfile.txt --sheet --no-cleanup
```

### Read QR Codes

```bash
# Process single QR image (auto-detects and rebuilds)
python qr.py read qr_photo.png

# Process folder of QR images
python qr.py read ./qr_photos/

# Process with verbose output
python qr.py read ./qr_photos/ --verbose

# Handle encrypted content
python qr.py read ./encrypted_qrs/ --encrypted
```

### Legacy Commands (Still Supported)

```bash
# Traditional workflow (v1.x style)
python qr.py scan ./qr_photos/           # Scan QR images
python qr.py rebuild ./scanned_chunks/   # Rebuild from chunks
```

### Configuration

```bash
# View current settings
python qr.py config show

# Reset to defaults
python qr.py config reset

# Get help for any command
python qr.py --help
python qr.py generate --help
python qr.py read --help
```

---

## 🔄 Complete Workflow Examples

### **Standard Workflow**
```bash
# 1. Generate QR sheets with verification
python qr.py generate important_file.txt --sheet --verbose

# 2. Take photos of QR sheets with mobile device
#    - Use any QR scanner app or camera
#    - Save images to a folder

# 3. Process scanned images and reconstruct file
python qr.py read ./qr_photos/
# Output: important_file.txt (exactly as original)
```

### **Encrypted Workflow**
```bash
# 1. Generate encrypted QR codes
python qr.py generate sensitive_data.json --encrypt --sheet --verbose
# → Prompts for password, generates encrypted QR sheets

# 2. Transfer QR sheets (print, photo, etc.)

# 3. Scan and decrypt on target system  
python qr.py read ./received_qr_images/ --encrypted
# → Prompts for password, verifies integrity, reconstructs file
```

### **Single Image Processing** ✨ New in v2.0
```bash
# Process individual QR images directly
python qr.py read single_qr_photo.png      # ✅ Auto-detects and rebuilds
python qr.py read screenshot_qr.jpg        # ✅ Works with any image format
python qr.py read phone_camera_qr.png      # ✅ Handles phone photos
```

---

## 📊 Capacity & Performance

### File Size Guidelines

- **Small files** (< 1KB): Single QR code
- **Medium files** (1-10KB): 2-5 QR codes  
- **Large files** (10KB+): Multiple sheets recommended

### QR Code Specifications

- **Version**: Auto-determined (up to 40)
- **Error Correction**: Level L (maximum capacity)
- **Capacity**: ~2,300 bytes per QR code (with safety margin)

### Performance Tips

- Use `--sheet` for files requiring multiple QR codes
- Enable `--verbose` for detailed progress on large operations
- Use `--no-cleanup` for debugging and inspection

---

## 🛠️ Technical Details

### Format Preservation

- **Tabs**: Preserved as literal `\t` characters
- **Encoding**: UTF-8 with BOM handling
- **Line Endings**: Platform-appropriate preservation  
- **Special Characters**: Complete Unicode support

### Security Features

- **AES-256 Encryption**: PBKDF2 key derivation with 100,000 iterations
- **Integrity Verification**: SHA-256 checksums for all content
- **Air-Gap Safe**: Complete offline operation
- **Memory Protection**: Automatic password clearing

### Smart Detection

The tool automatically detects input types and chooses optimal processing:

- **QR Images**: Scans codes and rebuilds files automatically
- **Text Chunks**: Rebuilds files from previously scanned data
- **Mixed Content**: Handles combinations intelligently

---

## 🔧 Troubleshooting

### Common Issues

**"Invalid version" Error**
```bash
# File too large for single QR - use chunking
python qr.py generate largefile.txt --sheet
```

**Missing Tab Characters**
```bash
# Check reconstruction method
python qr.py read ./qr_photos/ --verbose
# Use qr_rebuild.py directly if needed for tab preservation
```

**Import Errors**
```bash
pip install -r requirements.txt
# Ensure qrcode[pil] and Pillow are installed
```

### Debug Mode

```bash
python qr.py generate myfile.txt --verbose --no-cleanup
python qr.py read ./qr_photos/ --verbose
# Shows detailed processing information and preserves temporary files
```

### Getting Help

```bash
python qr.py --help              # General help
python qr.py generate --help     # Command-specific help
python qr.py read --help         # Command-specific help
```

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-username/qr-file-transfer.git
cd qr-file-transfer

# Install in development mode
pip install -e .

# Test the installation
python qr.py --version
```

### Types of Contributions Welcome

- 🐛 **Bug Reports**: Found an issue? Please report it!
- 💡 **Feature Requests**: Ideas for new functionality
- 📖 **Documentation**: Improve docs, examples, or tutorials
- 🔧 **Code Contributions**: Bug fixes, optimizations, new features

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

- **Documentation**: See [USAGE_GUIDE.md](USAGE_GUIDE.md) for detailed examples
- **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/PSEUDONYM97/qr-file-transfer/issues)
- **Discussions**: Join the conversation in [GitHub Discussions](https://github.com/PSEUDONYM97/qr-file-transfer/discussions)

---

**🎯 Mission**: Making secure, air-gapped file transfer accessible and reliable through professional-grade QR code technology.

**Status**: ✅ Production Ready - Enterprise-grade security with intuitive CLI interface 