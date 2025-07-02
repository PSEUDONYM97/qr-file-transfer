# 🚀 QR File Transfer Tool v2.0 - Usage Guide

## ✨ **New in v2.0: Smart Unified Interface**

### **📤 Generate QR Codes**
```bash
# Basic generation (auto-cleanup with 30-second viewing window)
python qr.py generate document.txt --verbose

# Generate organized QR sheets
python qr.py generate important.pdf --sheet --verbose

# Secure encrypted transfer
python qr.py generate secret.txt --encrypt --sheet
```

### **📥 Read QR Codes (Auto-Detection)**
```bash
# Smart auto-detection: scan images and auto-rebuild files
python qr.py read ./phone_photos/ --verbose

# Process chunk files directly
python qr.py read ./scanned_chunks/ --verbose

# Handle mixed content intelligently  
python qr.py read ./mixed_folder/ --verbose
```

## 🎯 **Complete Workflow Example**
```bash
# 1. Generate QR codes with 30-second preview
python qr.py generate myfile.txt --verbose
# 📱 QR codes available for viewing...
# 🕐 Auto-cleanup in 30 seconds (Ctrl+C to keep files)

# 2. Scan QR photos from phone and auto-rebuild
python qr.py read ./phone_photos/ --verbose
# ✨ Detected: QR images directory (8 images found)
# 📸 Processing QR images with auto-rebuild...
# ✅ Original file automatically reconstructed!
```

## 🔧 **User Experience Features**

### **30-Second Viewing Window**
- QR codes stay visible for 30 seconds before cleanup
- Press `Ctrl+C` to cancel cleanup and preserve files
- User-friendly countdown timer
- Perfect for quick phone scanning

### **Smart Auto-Detection** 
- Automatically identifies QR images vs chunk files
- Handles mixed directories intelligently
- Clear feedback on detected content type
- No need to remember different commands

### **Professional Output Structure**
```
qr_output/
  └── filename_20250701_152751/
      ├── qr_codes/        # Individual PNG files
      ├── sheets/          # Combined QR sheets  
      └── reports/         # Processing reports
```

## 🎨 **Control Options**

### **Cleanup Control**
```bash
# Default: 30-second viewing window + auto-cleanup
python qr.py generate file.txt

# Disable cleanup (files preserved permanently)
python qr.py generate file.txt --no-cleanup

# Force immediate cleanup
python qr.py generate file.txt --cleanup
```

### **Processing Modes**
```bash
# Force specific detection
python qr.py read ./folder/ --as-images     # Treat as QR images
python qr.py read ./folder/ --as-chunks     # Treat as chunk files

# Processing control
python qr.py read ./folder/ --mode scan-only      # Only scan
python qr.py read ./folder/ --mode rebuild-only   # Only rebuild
```

## 🚀 **Windows Convenience**
```bash
# Use the batch file for easier access
qr.bat generate myfile.txt --verbose
qr.bat read ./photos/ --verbose
```

---

**v2.0 delivers a professional, unified CLI experience with smart automation and user-friendly defaults.** 🎯 