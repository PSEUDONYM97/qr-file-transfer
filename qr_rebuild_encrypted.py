#!/usr/bin/env python3
"""
QR Encrypted File Reconstruction Tool
Reconstructs files from password-protected encrypted QR chunks with integrity verification
"""

import os
import sys
import re
import hashlib
import getpass
import base64
import argparse
from pathlib import Path

# Encryption support
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

class QRDecryption:
    """Handles AES-256 decryption for QR data"""
    
    def __init__(self):
        if not HAS_CRYPTO:
            raise ImportError("Cryptography library required. Install with: pip install cryptography")
        self.backend = default_backend()
    
    def derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive decryption key from password using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=100000,  # Strong iteration count
            backend=self.backend
        )
        return kdf.derive(password.encode('utf-8'))
    
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
    
    def decode_encrypted_chunk(self, encoded_data: str) -> tuple[bytes, bytes, bytes]:
        """Decode base64 encrypted chunk, returns (encrypted_data, salt, iv)"""
        try:
            combined = base64.b64decode(encoded_data.encode('ascii'))
            if len(combined) < 32:
                raise ValueError("Invalid encrypted chunk format")
            salt = combined[:16]
            iv = combined[16:32]
            encrypted_data = combined[32:]
            return encrypted_data, salt, iv
        except Exception as e:
            raise ValueError(f"Failed to decode encrypted chunk: {e}")

def calculate_chunk_hash(content):
    """Calculate SHA-256 hash of chunk content"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

def calculate_file_hash(content):
    """Calculate SHA-256 hash of entire file content"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def get_decryption_password(confirm_required=False) -> str:
    """Securely prompt for decryption password"""
    if confirm_required:
        print("🔐 Encrypted QR chunks detected - password required for decryption")
    
    while True:
        password = getpass.getpass("Enter decryption password: ")
        if len(password) < 8:
            print("❌ Password must be at least 8 characters long")
            continue
        return password

def parse_chunk_file(file_path, password=None, decryption=None, verbose=False):
    """Parse a chunk file and extract metadata and content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Check for encrypted chunk format
        encrypted_match = re.search(
            r'--BEGIN ENCRYPTED part_(\d+)_of_(\d+) file: (.+?) chunk_hash: (\w+) file_hash: (\w+)--\n(.+?)\n--END ENCRYPTED part_(\d+)--',
            content, re.DOTALL
        )
        
        if encrypted_match:
            if not HAS_CRYPTO:
                raise RuntimeError("Encrypted chunk found but cryptography library not available")
            if not password or not decryption:
                raise ValueError("Encrypted chunk requires password and decryption handler")
                
            part_num = int(encrypted_match.group(1))
            total_parts = int(encrypted_match.group(2))
            filename = encrypted_match.group(3)
            chunk_hash = encrypted_match.group(4)
            file_hash = encrypted_match.group(5)
            encrypted_data_b64 = encrypted_match.group(6)
            end_part = int(encrypted_match.group(7))
            
            if part_num != end_part:
                raise ValueError(f"Part number mismatch in encrypted chunk: {part_num} vs {end_part}")
            
            if verbose:
                print(f"🔐 Decrypting chunk {part_num:02d}...")
            
            # Decrypt the chunk content
            try:
                encrypted_data, salt, iv = decryption.decode_encrypted_chunk(encrypted_data_b64)
                chunk_content = decryption.decrypt_data(encrypted_data, salt, iv, password)
            except Exception as e:
                raise ValueError(f"Failed to decrypt chunk {part_num}: {e}")
            
            # Verify chunk integrity
            calculated_hash = calculate_chunk_hash(chunk_content)
            if calculated_hash != chunk_hash:
                raise ValueError(f"Chunk {part_num} integrity verification failed: hash mismatch")
            
            return {
                'part_num': part_num,
                'total_parts': total_parts,
                'filename': filename,
                'chunk_hash': chunk_hash,
                'file_hash': file_hash,
                'content': chunk_content,
                'encrypted': True
            }
        
        # Standard unencrypted chunk format
        match = re.search(
            r'--BEGIN part_(\d+)_of_(\d+) file: (.+?) chunk_hash: (\w+) file_hash: (\w+)--\n(.+?)\n--END part_(\d+)--',
            content, re.DOTALL
        )
        
        if not match:
            raise ValueError("Invalid chunk format - missing required headers")
            
        part_num = int(match.group(1))
        total_parts = int(match.group(2))
        filename = match.group(3)
        chunk_hash = match.group(4)
        file_hash = match.group(5)
        chunk_content = match.group(6)
        end_part = int(match.group(7))
        
        if part_num != end_part:
            raise ValueError(f"Part number mismatch: {part_num} vs {end_part}")
        
        # Verify chunk integrity
        calculated_hash = calculate_chunk_hash(chunk_content)
        if calculated_hash != chunk_hash:
            raise ValueError(f"Chunk {part_num} integrity verification failed: hash mismatch")
        
        return {
            'part_num': part_num,
            'total_parts': total_parts,
            'filename': filename,
            'chunk_hash': chunk_hash,
            'file_hash': file_hash,
            'content': chunk_content,
            'encrypted': False
        }
        
    except Exception as e:
        raise ValueError(f"Error parsing {file_path}: {e}")

def find_chunk_files(chunk_dir="scanned_chunks"):
    """Find all chunk files in the specified directory"""
    if not os.path.isdir(chunk_dir):
        raise FileNotFoundError(f"Chunk directory not found: {chunk_dir}")
    
    chunk_files = []
    for file in os.listdir(chunk_dir):
        if file.endswith('.txt'):
            chunk_files.append(os.path.join(chunk_dir, file))
    
    if not chunk_files:
        raise FileNotFoundError(f"No chunk files found in {chunk_dir}")
    
    return sorted(chunk_files)

def reconstruct_file(chunk_dir="scanned_chunks", output_file=None, password=None, verify_only=False, verbose=False):
    """Reconstruct file from encrypted or unencrypted chunks with integrity verification"""
    
    if not HAS_CRYPTO and password:
        raise RuntimeError("Cryptography library required for encrypted chunks. Install with: pip install cryptography")
    
    print(f"🔍 Scanning for chunks in: {chunk_dir}")
    chunk_files = find_chunk_files(chunk_dir)
    print(f"📁 Found {len(chunk_files)} chunk file(s)")
    
    # Parse all chunks to determine if encryption is used
    chunks = {}
    filename = None
    total_parts = None
    file_hash = None
    is_encrypted = False
    decryption = None
    
    # First pass: check for encryption and get password if needed
    for chunk_file in chunk_files:
        try:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if 'BEGIN ENCRYPTED' in content:
                is_encrypted = True
                break
        except Exception as e:
            print(f"⚠️  Warning: Could not read {chunk_file}: {e}")
    
    # Initialize decryption if needed
    if is_encrypted:
        if not password:
            password = get_decryption_password(confirm_required=True)
        decryption = QRDecryption()
        print("🔐 Encrypted chunks detected - using AES-256 decryption")
    
    print("📋 Parsing chunks...")
    # Parse all chunks
    for chunk_file in chunk_files:
        try:
            chunk_info = parse_chunk_file(chunk_file, password, decryption, verbose)
            
            # Validate consistency
            if filename is None:
                filename = chunk_info['filename']
                total_parts = chunk_info['total_parts']
                file_hash = chunk_info['file_hash']
            else:
                if chunk_info['filename'] != filename:
                    print(f"⚠️  Warning: Filename mismatch in {chunk_file}")
                if chunk_info['total_parts'] != total_parts:
                    print(f"⚠️  Warning: Total parts mismatch in {chunk_file}")
                if chunk_info['file_hash'] != file_hash:
                    print(f"⚠️  Warning: File hash mismatch in {chunk_file}")
            
            chunks[chunk_info['part_num']] = chunk_info['content']
            
            encryption_note = " (encrypted)" if chunk_info['encrypted'] else ""
            if verbose:
                print(f"  ✅ Part {chunk_info['part_num']:02d}: {len(chunk_info['content']):,} chars{encryption_note}")
                
        except ValueError as e:
            print(f"❌ Error parsing {chunk_file}: {e}")
            return False
    
    # Check for missing chunks
    expected_parts = set(range(1, total_parts + 1))
    found_parts = set(chunks.keys())
    missing_parts = expected_parts - found_parts
    
    if missing_parts:
        print(f"❌ Missing chunks: {sorted(missing_parts)}")
        return False
    
    extra_parts = found_parts - expected_parts
    if extra_parts:
        print(f"⚠️  Extra chunks found: {sorted(extra_parts)}")
    
    print(f"✅ All {total_parts} chunks parsed successfully")
    
    if verify_only:
        print("🔍 Verification mode - file integrity check only")
        # Reconstruct content for hash verification
        content_parts = [chunks[i] for i in range(1, total_parts + 1)]
        reconstructed_content = ''.join(content_parts)
        
        # Verify file hash
        calculated_file_hash = calculate_file_hash(reconstructed_content)
        if calculated_file_hash == file_hash:
            encryption_msg = " (encrypted)" if is_encrypted else ""
            print(f"✅ File integrity verified{encryption_msg}: {filename}")
            print(f"📊 Content size: {len(reconstructed_content):,} characters")
            print(f"🔒 File hash: {file_hash}")
            return True
        else:
            print(f"❌ File integrity verification failed!")
            print(f"   Expected: {file_hash}")
            print(f"   Calculated: {calculated_file_hash}")
            return False
    
    # Reconstruct the file
    print(f"🔄 Reconstructing file: {filename}")
    content_parts = [chunks[i] for i in range(1, total_parts + 1)]
    reconstructed_content = ''.join(content_parts)
    
    # Verify file integrity
    calculated_file_hash = calculate_file_hash(reconstructed_content)
    if calculated_file_hash != file_hash:
        print(f"❌ File integrity verification failed!")
        print(f"   Expected: {file_hash}")
        print(f"   Calculated: {calculated_file_hash}")
        return False
    
    # Determine output file
    if not output_file:
        output_file = filename
        if is_encrypted and output_file.endswith('_encrypted'):
            # Remove encryption suffix for output
            output_file = output_file[:-10]  # Remove '_encrypted'
    
    # Check if output file exists
    if os.path.exists(output_file):
        response = input(f"⚠️  File '{output_file}' exists. Overwrite? [y/N]: ")
        if response.lower() != 'y':
            print("Operation cancelled.")
            return False
    
    # Write reconstructed file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(reconstructed_content)
        
        file_size = len(reconstructed_content.encode('utf-8'))
        encryption_msg = " (decrypted)" if is_encrypted else ""
        print(f"✅ File reconstructed successfully{encryption_msg}: {output_file}")
        print(f"📊 File size: {file_size:,} bytes")
        print(f"🔒 Verified hash: {file_hash}")
        
        # Clear password from memory (best effort)
        if password:
            password = "X" * len(password)
        
        return True
        
    except Exception as e:
        print(f"❌ Error writing file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="QR Encrypted File Reconstruction Tool - Rebuild files from encrypted QR chunks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Reconstruct from scanned_chunks/
  %(prog)s --chunk-dir my_chunks/             # Use custom chunk directory
  %(prog)s --output decrypted_file.txt        # Specify output filename
  %(prog)s --verify-only                      # Only verify integrity, don't write file
  %(prog)s --chunk-dir encrypted_chunks/ -v   # Verbose reconstruction with custom dir
        """
    )
    
    parser.add_argument('--chunk-dir', default='scanned_chunks',
                        help='Directory containing chunk files (default: scanned_chunks)')
    parser.add_argument('--output', '-o',
                        help='Output filename (default: derived from chunks)')
    parser.add_argument('--verify-only', action='store_true',
                        help='Only verify file integrity, do not write output file')
    parser.add_argument('--password', '-p',
                        help='Decryption password (will prompt if not provided)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    
    args = parser.parse_args()
    
    if args.password and not HAS_CRYPTO:
        print("❌ Password provided but cryptography library not available")
        print("   Install with: pip install cryptography")
        sys.exit(1)
    
    try:
        success = reconstruct_file(
            chunk_dir=args.chunk_dir,
            output_file=args.output,
            password=args.password,
            verify_only=args.verify_only,
            verbose=args.verbose
        )
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 