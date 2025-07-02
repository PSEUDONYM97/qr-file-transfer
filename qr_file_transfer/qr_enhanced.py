#!/usr/bin/env python3
"""
QR File Transfer Tool - Enhanced Version with AES-256 Encryption
Secure, configurable file transfer using QR codes with encryption support
"""

import os
import sys
import argparse
import qrcode
import textwrap
import tempfile
import shutil
import hashlib
import getpass
import base64
import secrets
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from qr_config import QRConfig

# Encryption support
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# Try to import tqdm for progress bars, fall back gracefully
try:
    from tqdm import tqdm as tqdm_lib
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    # Simple fallback progress indicator
    class tqdm_lib:
        def __init__(self, iterable=None, total=None, desc=None, disable=False, **kwargs):
            self.iterable = iterable
            self.total = total or (len(iterable) if iterable else 0)
            self.desc = desc or ""
            self.disable = disable
            self.current = 0
            if not disable and desc:
                print(f"{desc}...")
        
        def __iter__(self):
            if self.iterable:
                for item in self.iterable:
                    yield item
                    self.current += 1
            return self
        
        def __enter__(self):
            return self
        
        def __exit__(self, *args):
            if not self.disable:
                print("✅ Complete!")
        
        def update(self, n=1):
            self.current += n
            if not self.disable and self.total > 0:
                percent = (self.current / self.total) * 100
                if self.current % max(1, self.total // 10) == 0:  # Update every 10%
                    print(f"  Progress: {percent:.0f}% ({self.current}/{self.total})")
        
        def set_postfix(self, **kwargs):
            # Fallback implementation for set_postfix
            if not self.disable:
                items = [f"{k}={v}" for k, v in kwargs.items()]
                if items:
                    print(f"  {', '.join(items)}")

# Use consistent tqdm reference
tqdm = tqdm_lib

# QR Configuration
MAX_QR_BYTES = 2953   # QR code version 40-L holds ~2953 bytes (conservative estimate)
SAFETY_MARGIN = 0.8   # Stay under this % of max to be safe
MAX_CHUNK_SIZE = int(MAX_QR_BYTES * SAFETY_MARGIN)

class QRCrypto:
    """Handles AES-256 encryption/decryption for QR data"""
    
    def __init__(self):
        self.backend = default_backend()
    
    def derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=100000,  # Strong iteration count
            backend=self.backend
        )
        return kdf.derive(password.encode('utf-8'))
    
    def encrypt_data(self, data: str, password: str) -> tuple[bytes, bytes, bytes]:
        """Encrypt data with AES-256-CBC, returns (encrypted_data, salt, iv)"""
        # Generate random salt and IV
        salt = secrets.token_bytes(16)  # 128-bit salt
        iv = secrets.token_bytes(16)    # 128-bit IV
        
        # Derive key from password
        key = self.derive_key(password, salt)
        
        # PKCS7 padding
        data_bytes = data.encode('utf-8')
        padding_length = 16 - (len(data_bytes) % 16)
        padded_data = data_bytes + bytes([padding_length] * padding_length)
        
        # Encrypt
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        return encrypted_data, salt, iv
    
    def decrypt_data(self, encrypted_data: bytes, salt: bytes, iv: bytes, password: str) -> str:
        """Decrypt AES-256-CBC encrypted data"""
        # Derive key from password
        key = self.derive_key(password, salt)
        
        # Decrypt
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=self.backend)
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # Remove PKCS7 padding
        padding_length = padded_data[-1]
        data_bytes = padded_data[:-padding_length]
        
        return data_bytes.decode('utf-8')
    
    def encode_encrypted_chunk(self, encrypted_data: bytes, salt: bytes, iv: bytes) -> str:
        """Encode encrypted chunk as base64 for QR storage"""
        # Format: SALT(16) + IV(16) + ENCRYPTED_DATA
        combined = salt + iv + encrypted_data
        return base64.b64encode(combined).decode('ascii')
    
    def decode_encrypted_chunk(self, encoded_data: str) -> tuple[bytes, bytes, bytes]:
        """Decode base64 encrypted chunk, returns (encrypted_data, salt, iv)"""
        combined = base64.b64decode(encoded_data.encode('ascii'))
        salt = combined[:16]
        iv = combined[16:32]
        encrypted_data = combined[32:]
        return encrypted_data, salt, iv

class QRTransferTool:
    def __init__(self, args):
        self.args = args
        self.temp_dir = None
        self.qr_files = []
        self.file_hash = None
        self.crypto = QRCrypto() if HAS_CRYPTO else None
        self.encryption_password = None
    
    def _safe_print(self, text):
        """Print text with fallback for Unicode issues on Windows"""
        try:
            print(text)
        except UnicodeEncodeError:
            # Fallback: remove Unicode characters for Windows compatibility
            safe_text = text.encode('ascii', 'ignore').decode('ascii')
            print(safe_text)
        
    def __enter__(self):
        if self.args.cleanup:
            self.temp_dir = tempfile.mkdtemp(prefix="qr_transfer_")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Secure cleanup - clear sensitive data
        if self.encryption_password:
            # Overwrite password in memory (best effort)
            self.encryption_password = "X" * len(self.encryption_password)
            self.encryption_password = None
            
        if self.args.cleanup and self.temp_dir:
            # Cleanup handled by unified CLI - skip countdown for individual tools
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            if self.args.verbose:
                print(f"🧹 Cleaned up temporary directory: {self.temp_dir}")

    def get_encryption_password(self) -> str:
        """Securely prompt for encryption password"""
        if not HAS_CRYPTO:
            raise RuntimeError("Cryptography library not available. Install with: pip install cryptography")
        
        self._safe_print("🔐 Encryption enabled - password required")
        while True:
            password = getpass.getpass("Enter encryption password: ")
            if len(password) < 8:
                self._safe_print("❌ Password must be at least 8 characters long")
                continue
            
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                self._safe_print("❌ Passwords do not match")
                continue
                
            return password

    def calculate_file_hash(self, content):
        """Calculate SHA-256 hash of entire file content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def calculate_chunk_hash(self, chunk_content):
        """Calculate SHA-256 hash of chunk content"""
        return hashlib.sha256(chunk_content.encode('utf-8')).hexdigest()[:16]  # First 16 chars for space

    def sanitize_file(self, filepath):
        """Read and sanitize file content, preserving formatting with memory optimization"""
        file_size = os.path.getsize(filepath)
        
        # For very large files (>50MB), use streaming approach
        if file_size > 50 * 1024 * 1024:  # 50MB threshold
            if self.args.verbose:
                print(f"🧠 Large file detected ({file_size:,} bytes), using memory-optimized streaming...")
            return self._stream_large_file(filepath, file_size)
        
        # Show progress for large files
        with tqdm(total=file_size, desc="📖 Reading file", unit="B", unit_scale=True, 
                 disable=self.args.quiet or file_size < 1024*1024) as pbar:
            
            with open(filepath, "rb") as f:
                chunks = []
                while True:
                    chunk = f.read(8192)  # Read in 8KB chunks
                    if not chunk:
                        break
                    chunks.append(chunk)
                    pbar.update(len(chunk))
                
                raw = b''.join(chunks)
        
        # Strip UTF-8 BOM if present
        if raw.startswith(b'\xef\xbb\xbf'):
            raw = raw[3:]
        return raw.decode("utf-8", errors="replace")

    def _stream_large_file(self, filepath, file_size):
        """Stream large files in chunks to optimize memory usage"""
        buffer_size = 1024 * 1024  # 1MB buffer
        decoded_parts = []
        
        with tqdm(total=file_size, desc="📖 Streaming large file", unit="B", unit_scale=True, 
                 disable=self.args.quiet) as pbar:
            
            with open(filepath, "rb") as f:
                # Handle UTF-8 BOM if present
                first_chunk = f.read(3)
                if first_chunk.startswith(b'\xef\xbb\xbf'):
                    first_chunk = first_chunk[3:]
                    pbar.update(3)
                
                # Process first chunk
                if first_chunk:
                    remaining_bytes = first_chunk
                else:
                    remaining_bytes = b''
                
                while True:
                    chunk = f.read(buffer_size)
                    if not chunk:
                        # Process any remaining bytes
                        if remaining_bytes:
                            try:
                                decoded_parts.append(remaining_bytes.decode("utf-8", errors="replace"))
                            except UnicodeDecodeError:
                                decoded_parts.append(remaining_bytes.decode("utf-8", errors="replace"))
                        break
                    
                    pbar.update(len(chunk))
                    
                    # Combine with remaining bytes from previous iteration
                    full_chunk = remaining_bytes + chunk
                    
                    # Find the last complete UTF-8 character boundary
                    # to avoid splitting multi-byte characters
                    decode_end = len(full_chunk)
                    remaining_bytes = b''
                    
                    # Look for incomplete UTF-8 sequences at the end
                    for i in range(min(4, len(full_chunk))):
                        try:
                            test_chunk = full_chunk[:decode_end-i]
                            decoded = test_chunk.decode("utf-8")
                            # If successful, save any remaining bytes
                            if i > 0:
                                remaining_bytes = full_chunk[decode_end-i:]
                            decoded_parts.append(decoded)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # If we can't decode, use error handling
                        decoded_parts.append(full_chunk.decode("utf-8", errors="replace"))
                        remaining_bytes = b''
        
        return ''.join(decoded_parts)

    def split_at_line_boundaries(self, data, max_chunk_size):
        """Split data into chunks at line boundaries with memory optimization"""
        # For very large content, use streaming approach
        if len(data) > 100 * 1024 * 1024:  # 100MB threshold
            if self.args.verbose:
                print("🧠 Using streaming chunking for very large content...")
            return self._stream_chunk_large_content(data, max_chunk_size)
        
        lines = data.splitlines(keepends=True)
        chunks = []
        current = ''
        
        # Progress bar for chunking large files
        with tqdm(lines, desc="🔄 Analyzing content", disable=self.args.quiet or len(lines) < 1000) as pbar:
            for line in pbar:
                line_bytes = len(line.encode("utf-8"))
                current_bytes = len(current.encode("utf-8"))
                
                if current_bytes + line_bytes > max_chunk_size and current:
                    chunks.append(current)
                    current = ''
                current += line
                
        if current:
            chunks.append(current)
        return chunks

    def _stream_chunk_large_content(self, data, max_chunk_size):
        """Stream-based chunking for very large content to minimize memory usage"""
        chunks = []
        current = ''
        line_start = 0
        
        # Estimate total lines for progress bar
        estimated_lines = data.count('\n') + 1
        processed_lines = 0
        
        with tqdm(total=estimated_lines, desc="🔄 Streaming chunk analysis", 
                 disable=self.args.quiet, unit="lines") as pbar:
            
            while line_start < len(data):
                # Find next line ending
                line_end = data.find('\n', line_start)
                if line_end == -1:
                    # Last line without newline
                    line = data[line_start:]
                    line_start = len(data)
                else:
                    # Include the newline character
                    line = data[line_start:line_end + 1]
                    line_start = line_end + 1
                
                line_bytes = len(line.encode("utf-8"))
                current_bytes = len(current.encode("utf-8"))
                
                if current_bytes + line_bytes > max_chunk_size and current:
                    chunks.append(current)
                    current = ''
                
                current += line
                processed_lines += 1
                
                # Update progress every 1000 lines
                if processed_lines % 1000 == 0:
                    pbar.update(1000)
        
        if current:
            chunks.append(current)
        
        return chunks

    def generate_qr_image(self, data, error_correction=qrcode.ERROR_CORRECT_L):
        """Generate a single QR code image"""
        qr = qrcode.QRCode(
            version=None,  # Auto-determine version
            error_correction=error_correction,
            box_size=self.args.box_size,
            border=self.args.border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white")

    def generate_single_qr_chunk(self, chunk_data):
        """Generate a single QR code chunk (for parallel processing)"""
        i, chunk, filename, total_parts = chunk_data
        
        # Handle encryption if enabled
        if self.args.encrypt and self.encryption_password and self.crypto:
            if self.args.verbose:
                self._safe_print(f"  🔐 Encrypting chunk {i:02d}...")
            
            # Encrypt the chunk content
            encrypted_data, salt, iv = self.crypto.encrypt_data(chunk, self.encryption_password)
            encoded_chunk = self.crypto.encode_encrypted_chunk(encrypted_data, salt, iv)
            
            # Calculate hash of original content for integrity
            chunk_hash = self.calculate_chunk_hash(chunk)
            
            # Create encrypted payload with metadata
            header = f"--BEGIN ENCRYPTED part_{i:02}_of_{total_parts:02} file: {filename} chunk_hash: {chunk_hash} file_hash: {self.file_hash}--\n"
            footer = f"--END ENCRYPTED part_{i:02}--"
            payload = header + encoded_chunk + footer
            
        else:
            # Standard unencrypted processing
            chunk_hash = self.calculate_chunk_hash(chunk)
            header = f"--BEGIN part_{i:02}_of_{total_parts:02} file: {filename} chunk_hash: {chunk_hash} file_hash: {self.file_hash}--\n"
            footer = f"--END part_{i:02}--"
            payload = header + chunk + footer
        
        # Generate QR image
        qr_img = self.generate_qr_image(payload)
        
        return (i, qr_img, chunk_hash, len(chunk.encode('utf-8')))

    def create_qr_sheet(self, qr_images, cols=3):
        """Combine multiple QR codes into a single sheet"""
        if not qr_images:
            return None
            
        # Calculate sheet dimensions
        qr_size = qr_images[0].size[0]
        rows = (len(qr_images) + cols - 1) // cols
        
        # Add padding between QRs
        padding = 20
        sheet_width = cols * qr_size + (cols + 1) * padding
        sheet_height = rows * qr_size + (rows + 1) * padding + 60  # Extra for labels
        
        # Create sheet image with progress tracking
        sheet = Image.new('RGB', (sheet_width, sheet_height), 'white')
        draw = ImageDraw.Draw(sheet)
        
        # Try to load a font
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        # Place QR codes with labels
        with tqdm(qr_images, desc="📋 Creating sheet", disable=self.args.quiet) as pbar:
            for i, qr_img in enumerate(pbar):
                row = i // cols
                col = i % cols
                
                x = padding + col * (qr_size + padding)
                y = padding + row * (qr_size + padding + 30)
                
                # Paste QR code (convert to RGB if needed)
                if qr_img.mode != 'RGB':
                    qr_img = qr_img.convert('RGB')
                sheet.paste(qr_img, (x, y))
                
                # Add label with encryption indicator
                label = f"Part {i+1:02d}"
                if self.args.encrypt:
                    label += " 🔐"
                    
                text_bbox = draw.textbbox((0, 0), label, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                label_x = x + (qr_size - text_width) // 2
                label_y = y + qr_size + 5
                draw.text((label_x, label_y), label, fill='black', font=font)
        
        return sheet

    def process_file(self, filepath):
        """Main processing function"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
            
        if self.args.verbose:
            print(f"📁 Processing file: {filepath}")
            
        # Handle encryption password if needed
        if self.args.encrypt:
            self.encryption_password = self.get_encryption_password()
            if self.args.verbose:
                self._safe_print("🔐 Encryption enabled - content will be secured")
            
        # Read and prepare content
        content = self.sanitize_file(filepath)
        content_bytes = len(content.encode('utf-8'))
        
        # Calculate file hash for integrity verification
        if not self.args.quiet:
            self._safe_print("🔒 Calculating file hash...")
        self.file_hash = self.calculate_file_hash(content)
        
        if self.args.verbose:
            self._safe_print(f"📊 File size: {content_bytes:,} bytes")
            self._safe_print(f"🔒 File hash: {self.file_hash[:16]}...")
            
        # Split into chunks
        chunks = self.split_at_line_boundaries(content, MAX_CHUNK_SIZE)
        total_parts = len(chunks)
        
        if self.args.verbose:
            print(f"🔄 Split into {total_parts} chunk(s)")
            
        if total_parts > 100 and not self.args.force:
            response = input(f"⚠️  Warning: {total_parts} QR codes will be generated. Continue? [y/N]: ")
            if response.lower() != 'y':
                print("Operation cancelled.")
                return
                
        # Generate QR codes with checksums and parallel processing
        filename = os.path.basename(filepath)
        qr_images = []
        
        encryption_status = " with AES-256 encryption" if self.args.encrypt else " with integrity verification"
        if not self.args.quiet:
            self._safe_print(f"🎯 Generating {total_parts} QR codes{encryption_status}...")
            
        # Use parallel processing for better performance (if more than 3 chunks)
        if total_parts > 3 and not self.args.no_parallel:
            if self.args.verbose:
                max_workers = min(8, (os.cpu_count() or 2) + 2)  # Reasonable default
                print(f"🚀 Using parallel processing with {max_workers} workers...")
            
            # Prepare chunk data for parallel processing
            chunk_data_list = [
                (i+1, chunk, filename, total_parts) 
                for i, chunk in enumerate(chunks)
            ]
            
            # Results storage
            results = {}
            
            # Use ThreadPoolExecutor for parallel QR generation
            max_workers = min(8, (os.cpu_count() or 2) + 2)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_index = {
                    executor.submit(self.generate_single_qr_chunk, chunk_data): chunk_data[0] 
                    for chunk_data in chunk_data_list
                }
                
                # Process completed tasks with progress bar
                progress_iter = as_completed(future_to_index)
                if not self.args.quiet:
                    progress_iter = tqdm(progress_iter, total=total_parts, desc="🎯 Generating QR codes", unit="QR")
                
                for future in progress_iter:
                    index = future_to_index[future]
                    try:
                        i, qr_img, chunk_hash, chunk_bytes = future.result()
                        results[i] = (qr_img, chunk_hash, chunk_bytes)
                        
                        if self.args.verbose:
                            encryption_note = " (encrypted)" if self.args.encrypt else ""
                            print(f"  📄 Part {i:02d}: {chunk_bytes:,} bytes, hash: {chunk_hash}{encryption_note}")
                            
                    except Exception as exc:
                        self._safe_print(f"  ❌ Part {index} generated an exception: {exc}")
                        
            # Sort results by part number
            qr_images = [results[i][0] for i in sorted(results.keys())]
            
        else:
            # Sequential processing for small files
            chunk_iter = enumerate(chunks, 1)
            if not self.args.quiet:
                chunk_iter = tqdm(chunk_iter, total=total_parts, desc="🎯 Generating QR codes", unit="QR")
                
            for i, chunk in chunk_iter:
                # Handle encryption if enabled
                if self.args.encrypt and self.encryption_password and self.crypto:
                    if self.args.verbose:
                        self._safe_print(f"  🔐 Encrypting chunk {i:02d}...")
                    
                    # Encrypt the chunk content
                    encrypted_data, salt, iv = self.crypto.encrypt_data(chunk, self.encryption_password)
                    encoded_chunk = self.crypto.encode_encrypted_chunk(encrypted_data, salt, iv)
                    
                    # Calculate hash of original content for integrity
                    chunk_hash = self.calculate_chunk_hash(chunk)
                    
                    # Create encrypted payload with metadata
                    header = f"--BEGIN ENCRYPTED part_{i:02}_of_{total_parts:02} file: {filename} chunk_hash: {chunk_hash} file_hash: {self.file_hash}--\n"
                    footer = f"--END ENCRYPTED part_{i:02}--"
                    payload = header + encoded_chunk + footer
                    
                else:
                    # Standard unencrypted processing
                    chunk_hash = self.calculate_chunk_hash(chunk)
                    header = f"--BEGIN part_{i:02}_of_{total_parts:02} file: {filename} chunk_hash: {chunk_hash} file_hash: {self.file_hash}--\n"
                    footer = f"--END part_{i:02}--"
                    payload = header + chunk + footer
                
                # Generate QR image
                qr_img = self.generate_qr_image(payload)
                qr_images.append(qr_img)
                
                if self.args.verbose:
                    chunk_bytes = len(chunk.encode('utf-8'))
                    encryption_note = " (encrypted)" if self.args.encrypt else ""
                    print(f"  📄 Part {i:02d}: {chunk_bytes:,} bytes, hash: {chunk_hash}{encryption_note}")
                
        # Save QR codes
        self.save_qr_codes(qr_images, filename, total_parts)
        
        encryption_msg = f" with AES-256 encryption" if self.args.encrypt else " with checksums"
        if not self.args.quiet:
            self._safe_print(f"✅ Generated {total_parts} QR codes{encryption_msg} for {filename}")

    def save_qr_codes(self, qr_images, filename, total_parts):
        """Save QR codes as individual files or sheets"""
        output_dir = self.temp_dir if (self.args.cleanup and self.temp_dir) else "."
        base_name = Path(filename).stem
        
        # Add encryption suffix to filename
        if self.args.encrypt:
            base_name += "_encrypted"
        
        if self.args.sheet:
            # Generate sheet(s)
            qrs_per_sheet = self.args.sheet_size
            sheets = []
            
            if not self.args.quiet:
                print(f"📋 Creating {(len(qr_images) + qrs_per_sheet - 1) // qrs_per_sheet} sheet(s)...")
            
            for i in range(0, len(qr_images), qrs_per_sheet):
                sheet_qrs = qr_images[i:i + qrs_per_sheet]
                sheet_img = self.create_qr_sheet(sheet_qrs, cols=self.args.sheet_cols)
                if sheet_img:
                    sheets.append(sheet_img)
                    
            # Save sheets with progress
            save_iter = enumerate(sheets, 1)
            if not self.args.quiet and len(sheets) > 1:
                save_iter = tqdm(save_iter, total=len(sheets), desc="💾 Saving sheets")
                
            for i, sheet in save_iter:
                sheet_file = os.path.join(output_dir, f"{base_name}_sheet_{i:02d}.png")
                sheet.save(sheet_file)
                self.qr_files.append(sheet_file)
                if self.args.verbose:
                    print(f"  💾 Saved sheet: {sheet_file}")
                    
        else:
            # Save individual QR codes
            save_iter = enumerate(qr_images, 1)
            if not self.args.quiet and len(qr_images) > 5:
                save_iter = tqdm(save_iter, total=len(qr_images), desc="💾 Saving QR codes")
                
            for i, qr_img in save_iter:
                qr_file = os.path.join(output_dir, f"{base_name}_part_{i:02d}_of_{total_parts:02d}.png")
                qr_img.save(qr_file)
                self.qr_files.append(qr_file)
                
        # Display or open files
        if self.args.display and not self.args.quiet:
            self.display_qr_codes()

    def display_qr_codes(self):
        """Display QR codes based on display mode"""
        if self.args.display == "viewer":
            # Open in system viewer
            for qr_file in self.qr_files:
                if sys.platform.startswith('darwin'):  # macOS
                    os.system(f"open '{qr_file}'")
                elif sys.platform.startswith('win'):  # Windows
                    os.system(f"start '{qr_file}'")
                else:  # Linux
                    os.system(f"xdg-open '{qr_file}'")
        elif self.args.display == "cli":
            # ASCII art display (basic implementation)
            print("📱 QR codes generated. Use a QR scanner to capture them.")

def main():
    parser = argparse.ArgumentParser(
        description="QR File Transfer Tool - Secure file transfer using QR codes with encryption support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s myfile.txt                    # Basic QR generation with checksums
  %(prog)s myfile.txt --sheet            # Generate QR sheets with verification
  %(prog)s myfile.txt --encrypt          # Generate encrypted QR codes (AES-256)
  %(prog)s secret.txt --encrypt --sheet  # Encrypted QR sheets for sensitive data
  %(prog)s large_file.txt --no-parallel  # Disable parallel processing
        """
    )
    
    # Required arguments
    parser.add_argument('file', nargs='?', help='File to convert to QR codes')
    
    # Configuration options
    parser.add_argument('--config', help='Specify configuration file path')
    parser.add_argument('--save-config', action='store_true',
                        help='Save current settings as default configuration')
    parser.add_argument('--show-config', action='store_true',
                        help='Show current configuration and exit')
    parser.add_argument('--reset-config', action='store_true',
                        help='Reset configuration to defaults')
    
    # Security options
    parser.add_argument('--encrypt', action='store_true',
                        help='Encrypt file content with AES-256 before QR generation')
    
    # Output options
    parser.add_argument('--sheet', action='store_true',
                        help='Generate QR code sheets instead of individual files')
    parser.add_argument('--sheet-size', type=int,
                        help='QR codes per sheet (default from config)')
    parser.add_argument('--sheet-cols', type=int,
                        help='Columns per sheet (default from config)')
    
    # Display options
    parser.add_argument('--display', choices=['viewer', 'cli', 'none'],
                        help='How to display generated QR codes (default from config)')
    
    # QR code options
    parser.add_argument('--box-size', type=int,
                        help='QR code box size (default from config)')
    parser.add_argument('--border', type=int,
                        help='QR code border size (default from config)')
    
    # Performance options
    parser.add_argument('--no-parallel', action='store_true',
                        help='Disable parallel QR generation (use sequential)')
    parser.add_argument('--no-progress', action='store_true',
                        help='Disable progress bars')
    
    # Behavior options
    parser.add_argument('--cleanup', action='store_true',
                        help='Auto-cleanup temporary files')
    parser.add_argument('--force', action='store_true',
                        help='Skip confirmation for large numbers of QR codes')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Quiet mode (minimal output)')
    
    args = parser.parse_args()
    
    # Override progress bars if requested
    if args.no_progress:
        args.quiet = True
    
    # Check encryption dependencies
    if args.encrypt and not HAS_CRYPTO:
        print("Error: Encryption requires 'cryptography' library")
        print("   Install with: pip install cryptography")
        sys.exit(1)
    
    # Load configuration (skip for now due to integration issues)
    # config = QRConfig(args.config)
    
    # Handle configuration commands
    if args.show_config:
        print("📋 Configuration management temporarily disabled")
        # config.print_config()
        sys.exit(0)
    
    if args.reset_config:
        print("📋 Configuration management temporarily disabled")
        # config.reset_to_defaults()
        sys.exit(0)
    
    # Apply defaults manually for now
    if not hasattr(args, 'box_size') or args.box_size is None:
        args.box_size = 10
    if not hasattr(args, 'border') or args.border is None:
        args.border = 4
    if not hasattr(args, 'sheet_size') or args.sheet_size is None:
        args.sheet_size = 9
    if not hasattr(args, 'sheet_cols') or args.sheet_cols is None:
        args.sheet_cols = 3
    if not hasattr(args, 'display') or args.display is None:
        args.display = 'none'
    
    # Validate arguments
    if args.quiet and args.verbose:
        parser.error("Cannot use --quiet and --verbose together")
    
    if not args.file:
        parser.error("File argument is required")
        
    if args.verbose and not HAS_TQDM:
        print("📊 Note: Install 'tqdm' for enhanced progress bars: pip install tqdm")
        
    if args.verbose and not HAS_CRYPTO:
        print("🔐 Note: Install 'cryptography' for encryption support: pip install cryptography")
        
    try:
        with QRTransferTool(args) as tool:
            tool.process_file(args.file)
            
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 