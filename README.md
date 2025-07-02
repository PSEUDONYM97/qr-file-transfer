# 🚀 QR File Transfer Tool v3.0

**Transfer files securely using QR codes - Perfect for air-gapped systems and mobile workflows**

Convert any file into QR code sheets, scan them with your phone, and reconstruct the original file perfectly. Built for security professionals, developers, and anyone needing reliable offline file transfer.

## ✨ Key Features

- **📱 Single Image Support**: Process individual QR images or entire folders
- **🛡️ Air-Gap Security**: Complete offline operation with optional AES-256 encryption  
- **📄 Sheet Generation**: Multiple QR codes per image for efficient scanning
- **🔧 Format Preservation**: Exact file reconstruction with tabs, encoding, and structure intact
- **⚡ Smart Detection**: Auto-detects file types and processing methods
- **🖥️ Cross-Platform**: Works on Windows, macOS, and Linux
- **🌍 Global Command**: Run `qr` from anywhere after installation

---

## 🚀 Quick Start

### Installation

#### Option 1: Install from Source (Recommended)
```bash
# Clone the repository
git clone https://github.com/PSEUDONYM97/qr-file-transfer.git
cd qr-file-transfer

# Install with pip (creates `qr` command)
pip install -e .

# Add Python Scripts to PATH (see instructions below)
```

#### Option 2: Direct Usage (No Installation)
```bash
# Clone the repository
git clone https://github.com/PSEUDONYM97/qr-file-transfer.git
cd qr-file-transfer

# Install dependencies
pip install -r requirements.txt

# Use directly
python qr.py generate myfile.txt --sheet
```

#### Requirements
- Python 3.8 or higher
- See `requirements.txt` for Python package dependencies

### 🌍 Making `qr` Command Global

After running `pip install -e .`, you need to add the Python Scripts directory to your system PATH:

#### Windows
1. **Find your Python Scripts directory**:
   ```powershell
   python -c "import site; print(site.USER_BASE + '\\Scripts')"
   ```
   This will show something like: `C:\Users\YourName\AppData\Roaming\Python\Python3XX\Scripts`

2. **Add to PATH permanently**:
   - Press `Win + R`, type `sysdm.cpl`, press Enter
   - Click "Environment Variables"
   - Under "User variables", select "Path" and click "Edit"
   - Click "New" and add your Scripts directory path
   - Click "OK" on all dialogs
   - **Restart your command prompt/PowerShell**

3. **Test the global command**:
   ```bash
   qr --version  # Should show: qr 3.0.0
   ```

#### macOS/Linux
1. **Find your Python Scripts directory**:
   ```bash
   python3 -c "import site; print(site.USER_BASE + '/bin')"
   ```

2. **Add to PATH permanently**:
   ```bash
   # Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

3. **Test the global command**:
   ```bash
   qr --version  # Should show: qr 3.0.0
   ```

### Basic Usage

```bash
# Generate QR code sheets (recommended)
qr generate myfile.txt --sheet

# Process single QR image (auto-detects and rebuilds)
qr read my_photo_of_qr.png

# Process folder of QR images  
qr read ./qr_photos/

# Generate with encryption
qr generate sensitive.txt --encrypt --sheet
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
qr generate myfile.txt

# Generate QR sheets (9 codes per image - recommended)
qr generate myfile.txt --sheet

# With encryption (prompts for password)
qr generate myfile.txt --encrypt --sheet

# Verbose output with progress tracking
qr generate myfile.txt --sheet --verbose

# Skip automatic cleanup for debugging
qr generate myfile.txt --sheet --no-cleanup
```

### Read QR Codes

```bash
# Process single QR image (auto-detects and rebuilds)
qr read qr_photo.png

# Process folder of QR images
qr read ./qr_photos/

# Process with verbose output
qr read ./qr_photos/ --verbose

# Handle encrypted content
qr read ./encrypted_qrs/ --encrypted
```

### Legacy Commands (Still Supported)

```bash
# Traditional workflow (v1.x style)
qr scan ./qr_photos/           # Scan QR images
qr rebuild ./scanned_chunks/   # Rebuild from chunks

# Or use the Python script directly if global command isn't working
python qr.py generate myfile.txt --sheet
python qr.py read ./qr_photos/
```

### Configuration

```bash
# View current settings
qr config show

# Reset to defaults
qr config reset

# Get help for any command
qr --help
qr generate --help
qr read --help
```

---

## 🔄 Complete Workflow Examples

### **Standard Workflow**
```bash
# 1. Generate QR sheets with verification
qr generate important_file.txt --sheet --verbose

# 2. Take photos of QR sheets with mobile device
#    - Use any QR scanner app or camera
#    - Save images to a folder

# 3. Process scanned images and reconstruct file
qr read ./qr_photos/
# Output: important_file.txt (exactly as original)
```

### **Encrypted Workflow**
```bash
# 1. Generate encrypted QR codes
qr generate sensitive_data.json --encrypt --sheet --verbose
# → Prompts for password, generates encrypted QR sheets

# 2. Transfer QR sheets (print, photo, etc.)

# 3. Scan and decrypt on target system  
qr read ./received_qr_images/ --encrypted
# → Prompts for password, verifies integrity, reconstructs file
```

### **Single Image Processing** ✨ New in v2.0+
```bash
# Process individual QR images directly
qr read single_qr_photo.png      # ✅ Auto-detects and rebuilds
qr read screenshot_qr.jpg        # ✅ Works with any image format
qr read phone_camera_qr.png      # ✅ Handles phone photos
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

**"qr command not found" Error**
```bash
# Check if Python Scripts is in PATH
echo $PATH  # Linux/macOS
echo $env:PATH  # Windows PowerShell

# Use the direct Python method if PATH isn't set up
python qr.py --version
python qr.py generate myfile.txt --sheet
```

**"Invalid version" Error**
```bash
# File too large for single QR - use chunking
qr generate largefile.txt --sheet
```

**Missing Tab Characters**
```bash
# Check reconstruction method
qr read ./qr_photos/ --verbose
# Use qr_rebuild.py directly if needed for tab preservation
```

**Import Errors**
```bash
pip install -r requirements.txt
# Ensure qrcode[pil] and Pillow are installed
```

### Debug Mode

```bash
qr generate myfile.txt --verbose --no-cleanup
qr read ./qr_photos/ --verbose
# Shows detailed processing information and preserves temporary files
```

### Getting Help

```bash
qr --help              # General help
qr generate --help     # Command-specific help
qr read --help         # Command-specific help
```

---

## 🎯 Version 3.0 Global Command Features

### ✨ **What's New in v3.0**

- **🌍 Global Installation**: Run `qr` from anywhere after proper PATH setup
- **📦 Package Structure**: Proper Python package for pip installation
- **🛠️ Improved Setup**: Clear instructions for cross-platform installation
- **🔧 Fallback Support**: Direct Python usage if global command isn't working
- **📚 Enhanced Documentation**: Step-by-step installation guide

### 🚀 **Quick Test After Installation**

```bash
# Test the global command
qr --version                     # Should show: qr 3.0.0

# Create a quick test
echo "Hello World" > test.txt
qr generate test.txt --sheet     # Generate QR sheet
qr read qr_output/*/qr_codes/*.png  # Read it back

# If global command doesn't work, use Python directly
python qr.py --version
python qr.py generate test.txt --sheet
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
qr --version  # or python qr.py --version
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

**v3.0**: 🌍 Now with global command support - use `qr` from anywhere! 