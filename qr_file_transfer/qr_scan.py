#!/usr/bin/env python3
"""
QR Batch Scanner - Process multiple QR images for reconstruction
Supports slideshow images, sheets, and individual QR codes
"""

import os
import sys
import argparse
import re
from pathlib import Path
from PIL import Image
import cv2
import numpy as np
from pyzbar import pyzbar
import json

class QRBatchScanner:
    def __init__(self, args):
        self.args = args
        self.found_chunks = []
        self.stats = {
            'images_processed': 0,
            'qr_codes_found': 0,
            'valid_chunks': 0,
            'errors': 0
        }

    def scan_qr_codes_from_image(self, image_path):
        """Extract all QR codes from a single image"""
        try:
            # Load image with OpenCV
            image = cv2.imread(str(image_path))
            if image is None:
                if self.args.verbose:
                    print(f"  ❌ Could not load image: {image_path}")
                self.stats['errors'] += 1
                return []

            # Convert to RGB for pyzbar
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect QR codes
            qr_codes = pyzbar.decode(rgb_image)
            
            if self.args.verbose and qr_codes:
                print(f"  🔍 Found {len(qr_codes)} QR code(s) in {Path(image_path).name}")
            
            results = []
            for qr in qr_codes:
                try:
                    # Decode the QR content
                    content = qr.data.decode('utf-8')
                    results.append(content)
                    self.stats['qr_codes_found'] += 1
                except UnicodeDecodeError:
                    if self.args.verbose:
                        print(f"    ⚠️  Unicode decode error in QR code")
                    self.stats['errors'] += 1
                    
            return results
            
        except Exception as e:
            if self.args.verbose:
                print(f"  ❌ Error processing {image_path}: {e}")
            self.stats['errors'] += 1
            return []

    def parse_chunk_metadata(self, content):
        """Parse QR chunk metadata with checksum support"""
        # Updated regex to handle checksums (backward compatible)
        header_match = re.search(r"--BEGIN part_(\d+)_of_(\d+) file:\s*(.+?)(?:\s+chunk_hash:\s*([a-f0-9]+))?\s*(?:file_hash:\s*([a-f0-9]+))?--", content)
        footer_match = re.search(r"--END part_\d+--", content)

        if not header_match or not footer_match:
            return None

        part_num = int(header_match.group(1))
        total_parts = int(header_match.group(2))
        filename = header_match.group(3).strip()
        chunk_hash = header_match.group(4) if header_match.group(4) else None
        file_hash = header_match.group(5) if header_match.group(5) else None
        
        start = header_match.end()
        end = footer_match.start()
        body = content[start:end].strip('\n\r')
        
        return {
            'part_num': part_num,
            'total_parts': total_parts,
            'filename': filename,
            'body': body,
            'chunk_hash': chunk_hash,
            'file_hash': file_hash,
            'raw_content': content
        }

    def process_image_folder(self, folder_path):
        """Process all images in a folder"""
        if not os.path.isdir(folder_path):
            raise ValueError(f"Not a directory: {folder_path}")
            
        # Find all image files
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
        image_files = []
        
        for file_path in Path(folder_path).iterdir():
            if file_path.suffix.lower() in image_extensions:
                image_files.append(file_path)
                
        if not image_files:
            raise ValueError(f"No image files found in {folder_path}")
            
        image_files.sort()  # Process in alphabetical order
        
        if not self.args.quiet:
            print(f"📁 Found {len(image_files)} image file(s) to process")
            
        # Process each image
        for image_file in image_files:
            if self.args.verbose:
                print(f"📷 Processing: {image_file.name}")
                
            qr_contents = self.scan_qr_codes_from_image(image_file)
            self.stats['images_processed'] += 1
            
            # Parse each QR code content
            for content in qr_contents:
                chunk_data = self.parse_chunk_metadata(content)
                if chunk_data:
                    self.found_chunks.append(chunk_data)
                    self.stats['valid_chunks'] += 1
                    if self.args.verbose:
                        print(f"    ✅ Valid chunk: Part {chunk_data['part_num']:02d} of {chunk_data['total_parts']:02d}")
                else:
                    if self.args.verbose:
                        print(f"    ⚠️  Invalid chunk format (not a file chunk QR)")

    def validate_chunks(self):
        """Validate and organize found chunks"""
        if not self.found_chunks:
            return {}
            
        # Group chunks by filename
        files = {}
        for chunk in self.found_chunks:
            filename = chunk['filename']
            if filename not in files:
                files[filename] = {}
            files[filename][chunk['part_num']] = chunk
            
        # Validate each file's chunks
        validated_files = {}
        for filename, chunks in files.items():
            if not chunks:
                continue
                
            # Check if we have all parts
            expected_total = list(chunks.values())[0]['total_parts']
            expected_parts = set(range(1, expected_total + 1))
            actual_parts = set(chunks.keys())
            
            missing_parts = expected_parts - actual_parts
            extra_parts = actual_parts - expected_parts
            
            if missing_parts:
                print(f"⚠️  {filename}: Missing parts {sorted(missing_parts)}")
            if extra_parts:
                print(f"⚠️  {filename}: Extra parts {sorted(extra_parts)}")
                
            # Only include files with all parts
            if not missing_parts:
                validated_files[filename] = chunks
                if not self.args.quiet:
                    print(f"✅ {filename}: Complete ({len(chunks)} parts)")
            else:
                print(f"❌ {filename}: Incomplete - cannot reconstruct")
                
        return validated_files

    def save_chunks_as_text(self, validated_files, output_dir):
        """Save chunks as individual text files for reconstruction"""
        os.makedirs(output_dir, exist_ok=True)
        
        for filename, chunks in validated_files.items():
            if self.args.verbose:
                print(f"💾 Saving chunks for {filename}")
                
            # Save each chunk as a separate text file
            for part_num, chunk in chunks.items():
                chunk_filename = f"chunk_{part_num:03d}.txt"
                chunk_path = os.path.join(output_dir, chunk_filename)
                
                with open(chunk_path, 'w', encoding='utf-8') as f:
                    f.write(chunk['raw_content'])
                    
                if self.args.verbose:
                    print(f"  📄 Saved: {chunk_filename}")

    def save_summary_report(self, validated_files, output_dir):
        """Save a summary report of the scanning process"""
        report = {
            'scan_summary': self.stats,
            'files_found': {},
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }
        
        for filename, chunks in validated_files.items():
            report['files_found'][filename] = {
                'total_parts': len(chunks),
                'parts': list(chunks.keys()),
                'estimated_size': sum(len(chunk['body'].encode('utf-8')) for chunk in chunks.values())
            }
            
        report_path = os.path.join(output_dir, 'scan_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
            
        if self.args.verbose:
            print(f"📊 Saved scan report: {report_path}")

    def auto_reconstruct(self, validated_files, output_dir):
        """Automatically reconstruct files if requested"""
        if not self.args.auto_reconstruct:
            return
            
        for filename in validated_files.keys():
            if not self.args.quiet:
                print(f"🔄 Auto-reconstructing {filename}")
                
            try:
                # Use the same logic as qr_rebuild.py but with our parsed data
                chunks_data = validated_files[filename]
                
                # Sort chunks by part number
                sorted_chunks = sorted(chunks_data.items())
                
                # Combine just the body content (no headers/footers)
                combined = "".join(chunk_data['body'] for part_num, chunk_data in sorted_chunks)
                
                reconstructed_path = os.path.join(output_dir, filename)
                with open(reconstructed_path, "w", encoding="utf-8") as out:
                    out.write(combined)
                    
                print(f"✅ Reconstructed: {reconstructed_path}")
                
            except Exception as e:
                print(f"❌ Reconstruction failed for {filename}: {e}")

    def print_summary(self, validated_files):
        """Print final summary"""
        if self.args.quiet:
            return
            
        print("\n" + "="*60)
        print("📊 SCAN SUMMARY")
        print("="*60)
        print(f"Images processed: {self.stats['images_processed']}")
        print(f"QR codes found: {self.stats['qr_codes_found']}")
        print(f"Valid chunks: {self.stats['valid_chunks']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Complete files: {len(validated_files)}")
        
        if validated_files:
            print("\n📁 RECONSTRUCTABLE FILES:")
            for filename, chunks in validated_files.items():
                total_bytes = sum(len(chunk['body'].encode('utf-8')) for chunk in chunks.values())
                print(f"  • {filename} ({len(chunks)} parts, ~{total_bytes:,} bytes)")

def main():
    parser = argparse.ArgumentParser(
        description="QR Batch Scanner - Process multiple QR images for file reconstruction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ./qr_images/                    # Scan all images in folder
  %(prog)s ./photos/ --output ./chunks/    # Custom output directory  
  %(prog)s ./scans/ --auto-reconstruct     # Scan and auto-rebuild files
  %(prog)s ./sheets/ --verbose             # Detailed progress output
        """
    )
    
    # Required arguments
    parser.add_argument('input_dir', help='Directory containing QR code images')
    
    # Output options
    parser.add_argument('--output', '-o', default='./scanned_chunks',
                        help='Output directory for chunk files (default: ./scanned_chunks)')
    parser.add_argument('--auto-reconstruct', action='store_true',
                        help='Automatically reconstruct files after scanning')
    
    # Behavior options
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output with detailed progress')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Quiet mode (minimal output)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.quiet and args.verbose:
        parser.error("Cannot use --quiet and --verbose together")
        
    try:
        scanner = QRBatchScanner(args)
        
        # Process images
        scanner.process_image_folder(args.input_dir)
        
        # Validate and organize chunks
        validated_files = scanner.validate_chunks()
        
        if not validated_files:
            print("❌ No complete files found. Check your QR images and try again.")
            sys.exit(1)
            
        # Save chunks and reports
        scanner.save_chunks_as_text(validated_files, args.output)
        scanner.save_summary_report(validated_files, args.output)
        
        # Auto-reconstruct if requested
        scanner.auto_reconstruct(validated_files, args.output)
        
        # Print summary
        scanner.print_summary(validated_files)
        
        if not args.quiet:
            print(f"\n💾 Chunks saved to: {args.output}")
            if not args.auto_reconstruct:
                print(f"🔄 To reconstruct files: python qr_rebuild.py {args.output}")
                
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