#!/usr/bin/env python3
"""
QR Rebuild Tool with Checksum Verification
Reconstruct files from QR chunks with integrity validation
"""

import re
import os
import sys
import hashlib

def calculate_chunk_hash(chunk_content):
    """Calculate SHA-256 hash of chunk content"""
    return hashlib.sha256(chunk_content.encode('utf-8')).hexdigest()[:16]

def calculate_file_hash(content):
    """Calculate SHA-256 hash of entire file content"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def parse_chunk_metadata(chunk_text):
    """Parse QR chunk metadata with checksum validation"""
    # Updated regex to handle checksums
    header_match = re.search(r"--BEGIN part_(\d+)_of_(\d+) file:\s*(.+?)(?:\s+chunk_hash:\s*([a-f0-9]+))?\s*(?:file_hash:\s*([a-f0-9]+))?--", chunk_text)
    footer_match = re.search(r"--END part_\d+--", chunk_text)

    if not header_match or not footer_match:
        return None

    part_num = int(header_match.group(1))
    total_parts = int(header_match.group(2))
    filename = header_match.group(3).strip()
    chunk_hash = header_match.group(4) if header_match.group(4) else None
    file_hash = header_match.group(5) if header_match.group(5) else None
    
    start = header_match.end()
    end = footer_match.start()
    body = chunk_text[start:end]
    # Only remove leading/trailing newlines, preserve tabs and spaces
    body = body.strip('\n\r')
    
    return {
        'part_num': part_num,
        'total_parts': total_parts,
        'filename': filename,
        'body': body,
        'chunk_hash': chunk_hash,
        'file_hash': file_hash,
        'raw_content': chunk_text
    }

def collect_chunks_from_folder(folder_path, verify_checksums=True):
    """Collect and validate chunks from folder"""
    chunks = []
    integrity_errors = []
    
    for fname in sorted(os.listdir(folder_path)):
        if fname.lower().endswith(".txt"):
            path = os.path.join(folder_path, fname)
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
                chunk_data = parse_chunk_metadata(text)
                if chunk_data:
                    # Validate chunk checksum if present
                    if verify_checksums and chunk_data['chunk_hash']:
                        expected_hash = chunk_data['chunk_hash']
                        actual_hash = calculate_chunk_hash(chunk_data['body'])
                        
                        if expected_hash != actual_hash:
                            error_msg = f"Chunk {chunk_data['part_num']:02d}: Hash mismatch! Expected {expected_hash}, got {actual_hash}"
                            integrity_errors.append(error_msg)
                            print(f"❌ {error_msg}")
                        else:
                            print(f"✅ Chunk {chunk_data['part_num']:02d}: Hash verified")
                    
                    chunks.append(chunk_data)
                else:
                    print(f"Warning: Skipped invalid chunk in {fname}")
    
    return chunks, integrity_errors

def validate_file_integrity(chunks, reconstructed_content):
    """Validate overall file integrity"""
    if not chunks:
        return True, []
        
    # Check if all chunks have the same file hash
    file_hashes = set(chunk.get('file_hash') for chunk in chunks if chunk.get('file_hash'))
    
    if len(file_hashes) > 1:
        return False, [f"Inconsistent file hashes found: {file_hashes}"]
    
    if not file_hashes:
        return True, ["No file hash available for verification"]
    
    expected_file_hash = file_hashes.pop()
    actual_file_hash = calculate_file_hash(reconstructed_content)
    
    if expected_file_hash != actual_file_hash:
        return False, [f"File hash mismatch! Expected {expected_file_hash}, got {actual_file_hash}"]
    
    return True, ["File hash verified successfully"]

def check_chunk_completeness(chunks):
    """Check if all required chunks are present"""
    if not chunks:
        return {}
    
    # Group by filename
    files = {}
    for chunk in chunks:
        filename = chunk['filename']
        if filename not in files:
            files[filename] = {}
        files[filename][chunk['part_num']] = chunk
    
    results = {}
    for filename, file_chunks in files.items():
        expected_total = list(file_chunks.values())[0]['total_parts']
        expected_parts = set(range(1, expected_total + 1))
        actual_parts = set(file_chunks.keys())
        
        missing_parts = expected_parts - actual_parts
        extra_parts = actual_parts - expected_parts
        
        results[filename] = {
            'complete': len(missing_parts) == 0,
            'missing_parts': missing_parts,
            'extra_parts': extra_parts,
            'chunks': file_chunks
        }
    
    return results

def main():
    if len(sys.argv) not in [2, 3]:
        print("Usage: python qr_rebuild_verified.py <folder_path> [--no-verify]")
        print("  --no-verify: Skip checksum validation")
        sys.exit(1)

    folder = sys.argv[1]
    verify_checksums = "--no-verify" not in sys.argv
    
    if not os.path.isdir(folder):
        print(f"Error: {folder} is not a valid folder.")
        sys.exit(1)

    print(f"🔍 Reading QR chunks from: {folder}")
    print(f"🔒 Checksum verification: {'Enabled' if verify_checksums else 'Disabled'}")
    
    # Collect chunks with validation
    chunks, integrity_errors = collect_chunks_from_folder(folder, verify_checksums)
    
    if not chunks:
        print("❌ No valid chunks found.")
        sys.exit(1)

    # Check completeness
    file_results = check_chunk_completeness(chunks)
    
    for filename, result in file_results.items():
        print(f"\n📁 File: {filename}")
        
        if result['missing_parts']:
            print(f"❌ Missing parts: {sorted(result['missing_parts'])}")
            continue
            
        if result['extra_parts']:
            print(f"⚠️  Extra parts found: {sorted(result['extra_parts'])}")
        
        if not result['complete']:
            print(f"❌ Cannot reconstruct {filename} - incomplete chunks")
            continue
            
        print(f"✅ All {len(result['chunks'])} parts present")
        
        # Reconstruct file
        sorted_chunks = sorted(result['chunks'].items())
        combined = "".join(chunk_data['body'] for part_num, chunk_data in sorted_chunks)
        
        # Validate file integrity
        file_valid, messages = validate_file_integrity(list(result['chunks'].values()), combined)
        
        for message in messages:
            print(f"🔒 {message}")
        
        if not file_valid and verify_checksums:
            print(f"❌ File integrity validation failed for {filename}")
            continue
        
        # Write reconstructed file
        output_path = os.path.join(folder, filename)
        with open(output_path, "w", encoding="utf-8") as out:
            out.write(combined)
        
        print(f"✅ Successfully rebuilt: {output_path}")
        
        # Summary
        if integrity_errors:
            print(f"\n⚠️  {len(integrity_errors)} integrity error(s) detected during reconstruction")
        else:
            print(f"🎉 File reconstructed with full integrity verification!")

if __name__ == "__main__":
    main() 