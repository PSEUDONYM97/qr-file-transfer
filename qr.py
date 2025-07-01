#!/usr/bin/env python3
"""
QR File Transfer Tool - Unified Command Line Interface
Professional-grade file transfer using QR codes with encryption support

Usage:
    qr generate <file> [options]    # Generate QR codes from file
    qr scan <images> [options]       # Scan QR images to chunks
    qr rebuild <chunks> [options]    # Rebuild files from chunks
    qr config [show|reset]           # Manage configuration
    qr --help                        # Show this help
"""

import sys
import os
import argparse
from pathlib import Path

# Import our existing modules
try:
    from qr_enhanced import QRTransferTool, QRCrypto, HAS_CRYPTO, HAS_TQDM
    from qr_scan import QRBatchScanner
    from qr_config import QRConfig
    import qr_rebuild
    import qr_rebuild_encrypted
    import qr_rebuild_verified
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("   Make sure all QR tool files are in the same directory")
    sys.exit(1)

class QRUnifiedCLI:
    """Unified CLI for QR File Transfer Tool"""
    
    def __init__(self):
        self.version = "2.0.0-dev"
        self.description = """
QR File Transfer Tool v2 - Simplified CLI for secure file transfer via QR codes
═════════════════════════════════════════════════════════════════════════════

Convert files and folders to QR codes with AES-256 encryption, organized output,
and comprehensive integrity verification. Perfect for air-gapped environments
and secure file transfer workflows.

🚀 v2 Simplified Commands:
  • qr generate - Create QR codes from files or folders  
  • qr read     - Process QR images or chunks back to files

✨ Key Features:
  • Folder batch processing with organized output structure
  • AES-256 encryption with PBKDF2 key derivation
  • SHA-256 integrity verification for chunks and files  
  • Parallel QR generation with progress tracking
  • Professional sheet layouts for easy scanning
  • Automated cleanup and workflow management
  • Cross-platform compatibility (Windows/macOS/Linux)

🎯 Professional Workflows:
  • Batch process entire directories: qr generate ./docs/ --sheet
  • Secure encrypted transfer: qr generate secret.txt --encrypt
  • Organized output structure: qr generate ./files/ -o ./qr_backup/
  • Complete read workflow: qr read ./photos/ --auto-rebuild
        """
    
    def _safe_print(self, text):
        """Print text with fallback for Unicode issues on Windows"""
        try:
            print(text)
        except UnicodeEncodeError:
            # Fallback: remove Unicode characters for Windows compatibility
            safe_text = text.encode('ascii', 'ignore').decode('ascii')
            print(safe_text)
    
    def create_parser(self):
        """Create the main argument parser with subcommands"""
        parser = argparse.ArgumentParser(
            prog='qr',
            description=self.description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Common workflows:
  qr generate file.txt --sheet              # Create QR sheets for easy scanning
  qr generate ./documents/ --sheet          # Batch process entire folder  
  qr generate secret.txt --encrypt          # AES-256 encrypted QR codes
  qr generate ./folder/ -o ./qr_backup/     # Organized output structure
  
🚀 v2.0 Simplified Interface:
  qr read ./photos/                         # Auto-scan QR images + rebuild files
  qr read ./scanned_chunks/                 # Auto-rebuild from chunk files
  qr read ./mixed_folder/                   # Handle both images and chunks

Legacy workflows (v1.x style):
  qr scan ./photos/ --auto-rebuild          # Still supported
  qr rebuild ./scanned_chunks/ --verify     # Still supported

Folder workflows:
  qr generate ./docs/ --pattern "*.txt"     # Process only text files
  qr generate ./src/ --recursive            # Include subdirectories  
  qr generate ./files/ --preserve-structure # Maintain folder hierarchy

For detailed help on any command:
  qr <command> --help

Project: https://github.com/username/qr-file-transfer
Issues: https://github.com/username/qr-file-transfer/issues
Version: """ + self.version
        )
        
        parser.add_argument('--version', action='version', version=f'qr {self.version}')
        
        # Create subparsers for commands
        subparsers = parser.add_subparsers(
            dest='command',
            title='Commands',
            description='Available operations (v2.0 simplified interface)',
            help='Use "qr <command> --help" for detailed help'
        )
        
        # Generate command
        self.create_generate_parser(subparsers)
        
        # Read command (v2.0 unified)
        self.create_read_parser(subparsers)
        
        # Legacy commands (v1.x compatibility)
        self.create_scan_parser(subparsers)
        self.create_rebuild_parser(subparsers)
        
        # Config command
        self.create_config_parser(subparsers)
        
        return parser
    
    def create_generate_parser(self, subparsers):
        """Create parser for generate command"""
        generate = subparsers.add_parser(
            'generate',
            aliases=['gen', 'g'],
            help='Generate QR codes from files or folders',
            description='Convert files or entire folders to QR codes with optional encryption and integrity verification',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  qr generate document.txt                   # Single file QR generation
  qr generate ./documents/                   # Process entire folder
  qr generate document.txt --sheet           # Generate organized sheets
  qr generate secret.txt --encrypt           # AES-256 encrypted QR codes
  qr generate ./folder/ --output ./qr_out/   # Organized batch processing
  qr generate large.txt --sheet --verbose    # Detailed progress output
  qr generate file.txt --box-size 8          # Smaller QR codes
            """
        )
        
        # Required arguments - now supports files or directories
        generate.add_argument('input', help='File or directory to convert to QR codes')
        
        # Input/Output organization
        io_group = generate.add_argument_group('Input/Output Options')
        io_group.add_argument('--output-dir', '-o', metavar='DIR',
                             help='Output directory for organized QR codes (default: ./qr_output/)')
        io_group.add_argument('--preserve-structure', action='store_true',
                             help='Preserve folder structure in output directory')
        io_group.add_argument('--pattern', metavar='GLOB',
                             help='File pattern for folder processing (e.g., "*.txt")')
        io_group.add_argument('--recursive', '-r', action='store_true',
                             help='Process subdirectories recursively')
        
        # Workflow options
        workflow = generate.add_argument_group('Workflow Options')
        workflow.add_argument('--organized', action='store_true', default=True,
                             help='Create organized output structure (default: enabled)')
        workflow.add_argument('--no-organized', dest='organized', action='store_false',
                             help='Disable organized output structure')
        workflow.add_argument('--auto-cleanup', action='store_true', default=True,
                             help='Automatically cleanup temporary files (default: enabled)')
        workflow.add_argument('--no-cleanup', dest='auto_cleanup', action='store_false',
                             help='Keep temporary files after generation')
        workflow.add_argument('--batch-summary', action='store_true', default=True,
                             help='Generate batch processing summary (default: enabled)')
        
        # Security options
        security = generate.add_argument_group('Security Options')
        security.add_argument('--encrypt', action='store_true',
                            help='Encrypt content with AES-256 before QR generation')
        
        # Output format options
        output = generate.add_argument_group('Output Format Options')
        output.add_argument('--sheet', action='store_true',
                          help='Generate QR code sheets (recommended for multiple codes)')
        output.add_argument('--sheet-size', type=int, metavar='N',
                          help='QR codes per sheet (default: 9)')
        output.add_argument('--sheet-cols', type=int, metavar='N', 
                          help='Columns per sheet (default: 3)')
        
        # QR code appearance
        appearance = generate.add_argument_group('QR Code Options')
        appearance.add_argument('--box-size', type=int, metavar='N',
                              help='QR code pixel size (default: 10)')
        appearance.add_argument('--border', type=int, metavar='N',
                              help='QR code border size (default: 4)')
        
        # Performance options
        performance = generate.add_argument_group('Performance Options')
        performance.add_argument('--no-parallel', action='store_true',
                                help='Disable parallel processing')
        performance.add_argument('--max-workers', type=int, metavar='N',
                                help='Maximum parallel workers (default: auto)')
        
        # Behavior options
        behavior = generate.add_argument_group('Behavior Options')
        behavior.add_argument('--cleanup', action='store_true',
                            help='Auto-cleanup temporary files (legacy option)')
        behavior.add_argument('--force', action='store_true',
                            help='Skip confirmation for large numbers of QR codes')
        behavior.add_argument('--display', choices=['viewer', 'cli', 'none'],
                            help='How to display generated QR codes')
        
        # Output control
        self.add_output_options(generate)
        
        return generate
    
    def create_scan_parser(self, subparsers):
        """Create parser for scan command"""
        scan = subparsers.add_parser(
            'scan',
            aliases=['s'],
            help='Scan QR code images to extract chunks (legacy - use "qr read" instead)', 
            description='Legacy command: Process QR code images to extract file chunks. For v2.0, use "qr read" which auto-detects and rebuilds.',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  qr scan ./photos/                         # Scan all images in folder
  qr scan ./images/ -o ./chunks/            # Custom output directory
  qr scan ./qr_sheets/ --auto-rebuild       # Scan and auto-reconstruct files
  qr scan ./mobile_photos/ --organized      # Create organized output structure
  qr scan ./scans/ --pattern "*.png"        # Process only PNG files
  qr scan ./photos/ --verbose               # Detailed scanning progress
            """
        )
        
        # Required arguments
        scan.add_argument('input_dir', help='Directory containing QR code images')
        
        # Input/Output organization
        io_group = scan.add_argument_group('Input/Output Options')
        io_group.add_argument('--output', '-o', metavar='DIR',
                             help='Output directory for chunk files (default: ./scan_output/)')
        io_group.add_argument('--pattern', metavar='GLOB',
                             help='Image file pattern (e.g., "*.png", "sheet_*.jpg")')
        io_group.add_argument('--recursive', '-r', action='store_true',
                             help='Process subdirectories recursively')
        
        # Workflow options
        workflow = scan.add_argument_group('Workflow Options')
        workflow.add_argument('--organized', action='store_true', default=True,
                             help='Create organized output structure (default: enabled)')
        workflow.add_argument('--no-organized', dest='organized', action='store_false',
                             help='Disable organized output structure')
        workflow.add_argument('--auto-rebuild', action='store_true',
                             help='Automatically reconstruct files after scanning')
        workflow.add_argument('--auto-cleanup', action='store_true', default=True,
                             help='Automatically cleanup temporary files (default: enabled)')
        workflow.add_argument('--scan-summary', action='store_true', default=True,
                             help='Generate scanning summary report (default: enabled)')
        
        # Processing options
        processing = scan.add_argument_group('Processing Options')
        processing.add_argument('--verify-checksums', action='store_true', default=True,
                              help='Verify chunk integrity with checksums (default: enabled)')
        processing.add_argument('--no-verify', dest='verify_checksums', action='store_false',
                              help='Skip checksum verification')
        processing.add_argument('--max-errors', type=int, metavar='N', default=10,
                              help='Maximum scan errors before stopping (default: 10)')
        
        # Output control
        self.add_output_options(scan)
        
        return scan
    
    def create_rebuild_parser(self, subparsers):
        """Create parser for rebuild command"""
        rebuild = subparsers.add_parser(
            'rebuild',
            aliases=['rb'],
            help='Rebuild files from scanned chunks (legacy - use "qr read" instead)',
            description='Legacy command: Reconstruct original files from QR code chunks. For v2.0, use "qr read" which auto-detects input type.',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  qr rebuild ./scanned_chunks/              # Basic reconstruction
  qr rebuild ./chunks/ --verify             # With integrity verification
  qr rebuild ./chunks/ --encrypted          # Decrypt encrypted chunks
  qr rebuild ./chunks/ --spaces             # Convert tabs to spaces
  qr rebuild ./chunks/ -o ./restored/       # Organized output directory
  qr rebuild ./chunks/ --organized          # Create organized output structure
  qr rebuild ./chunks/ --batch              # Process multiple file sets
            """
        )
        
        # Required arguments
        rebuild.add_argument('chunks_dir', help='Directory containing chunk files')
        
        # Input/Output organization  
        io_group = rebuild.add_argument_group('Input/Output Options')
        io_group.add_argument('--output-dir', '-o', metavar='DIR',
                             help='Output directory for reconstructed files (default: ./rebuild_output/)')
        io_group.add_argument('--pattern', metavar='GLOB',
                             help='Chunk file pattern (e.g., "chunk_*.txt")')
        io_group.add_argument('--recursive', '-r', action='store_true',
                             help='Process subdirectories recursively')
        
        # Workflow options
        workflow = rebuild.add_argument_group('Workflow Options')
        workflow.add_argument('--organized', action='store_true', default=True,
                             help='Create organized output structure (default: enabled)')
        workflow.add_argument('--no-organized', dest='organized', action='store_false',
                             help='Disable organized output structure')
        workflow.add_argument('--batch', action='store_true',
                             help='Process multiple file sets in directory')
        workflow.add_argument('--auto-cleanup', action='store_true', default=True,
                             help='Automatically cleanup temporary files (default: enabled)')
        workflow.add_argument('--rebuild-summary', action='store_true', default=True,
                             help='Generate rebuild summary report (default: enabled)')
        
        # Reconstruction options
        reconstruction = rebuild.add_argument_group('Reconstruction Options')
        reconstruction.add_argument('--verify', action='store_true',
                                  help='Verify file integrity with checksums')
        reconstruction.add_argument('--encrypted', action='store_true',
                                  help='Decrypt AES-256 encrypted chunks')
        reconstruction.add_argument('--spaces', action='store_true',
                                  help='Convert tabs to spaces during reconstruction')
        reconstruction.add_argument('--suffix', metavar='STR',
                                  help='Add suffix to reconstructed filenames')
        
        # Output control
        self.add_output_options(rebuild)
        
        return rebuild
    
    def create_config_parser(self, subparsers):
        """Create parser for config command"""
        config = subparsers.add_parser(
            'config',
            aliases=['cfg'],
            help='Manage configuration settings',
            description='View and modify QR tool configuration settings',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  qr config show                           # Display current settings
  qr config reset                          # Reset to default settings
  qr config --file ~/.qr-config.json      # Use custom config file
            """
        )
        
        # Config actions (mutually exclusive)
        action = config.add_mutually_exclusive_group()
        action.add_argument('action', nargs='?', choices=['show', 'reset'], 
                          help='Configuration action to perform')
        action.add_argument('--show', action='store_true',
                          help='Show current configuration')
        action.add_argument('--reset', action='store_true', 
                          help='Reset configuration to defaults')
        
        # Config file options
        config.add_argument('--file', metavar='PATH',
                          help='Path to configuration file')
        config.add_argument('--sample', action='store_true',
                          help='Create sample configuration file')
        
        return config
    
    def create_read_parser(self, subparsers):
        """Create parser for unified read command with auto-detection"""
        read = subparsers.add_parser(
            'read',
            aliases=['r'],
            help='Read QR codes or chunks back to files (auto-detects input type)',
            description='Unified command to process QR images or chunk files back to original files with smart auto-detection',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
🚀 v2.0 Simplified Interface:
  qr read ./photos/              # Auto-detects QR images, scans + rebuilds
  qr read ./chunks/              # Auto-detects chunk files, rebuilds directly
  qr read ./mixed_folder/        # Handles both images and chunks intelligently
  qr read single_image.png       # Processes single QR image
  qr read chunk_001.txt          # Processes single chunk file

🔍 Auto-Detection Features:
  • Automatically identifies QR images (.png, .jpg, .jpeg, .bmp, .tiff)
  • Recognizes QR chunk files (.txt with QR headers)
  • Handles mixed directories (both images and chunks)
  • Auto-rebuild enabled by default for QR images
  • Organized output structure with session timestamps

🎯 Advanced Options:
  qr read ./folder/ --mode scan-only     # Only scan, don't rebuild
  qr read ./folder/ --mode rebuild-only  # Only rebuild from chunks
  qr read ./folder/ --as-images          # Force treat as QR images
  qr read ./folder/ --as-chunks          # Force treat as chunk files
            """
        )
        
        # Required arguments
        read.add_argument('input', help='File or directory containing QR images or chunk files')
        
        # Detection override options
        detection = read.add_argument_group('Detection Override Options')
        detection.add_argument('--as-images', action='store_true',
                             help='Force treat input as QR images (skip auto-detection)')
        detection.add_argument('--as-chunks', action='store_true', 
                             help='Force treat input as chunk files (skip auto-detection)')
        detection.add_argument('--mode', choices=['auto', 'scan-only', 'rebuild-only'],
                             default='auto', help='Processing mode (default: auto)')
        
        # Input/Output organization
        io_group = read.add_argument_group('Input/Output Options')
        io_group.add_argument('--output', '-o', metavar='DIR',
                             help='Output directory (default: ./read_output/)')
        io_group.add_argument('--pattern', metavar='GLOB',
                             help='File pattern filter (e.g., "*.png", "chunk_*.txt")')
        io_group.add_argument('--recursive', '-r', action='store_true',
                             help='Process subdirectories recursively')
        
        # Workflow options
        workflow = read.add_argument_group('Workflow Options')
        workflow.add_argument('--organized', action='store_true', default=True,
                             help='Create organized output structure (default: enabled)')
        workflow.add_argument('--no-organized', dest='organized', action='store_false',
                             help='Disable organized output structure')
        workflow.add_argument('--auto-rebuild', action='store_true', default=True,
                             help='Auto-rebuild files after scanning (default: enabled)')
        workflow.add_argument('--no-auto-rebuild', dest='auto_rebuild', action='store_false',
                             help='Only scan QR codes, do not rebuild files')
        workflow.add_argument('--auto-cleanup', action='store_true', default=True,
                             help='Automatically cleanup temporary files (default: enabled)')
        workflow.add_argument('--read-summary', action='store_true', default=True,
                             help='Generate read processing summary (default: enabled)')
        
        # Processing options (from scan/rebuild)
        processing = read.add_argument_group('Processing Options')
        processing.add_argument('--verify-checksums', action='store_true', default=True,
                               help='Verify chunk integrity with checksums (default: enabled)')
        processing.add_argument('--no-verify', dest='verify_checksums', action='store_false',
                               help='Skip checksum verification')
        processing.add_argument('--encrypted', action='store_true',
                               help='Process encrypted chunks (will prompt for password)')
        processing.add_argument('--spaces', action='store_true',
                               help='Convert tabs to spaces during reconstruction')
        processing.add_argument('--max-errors', type=int, metavar='N', default=10,
                               help='Maximum processing errors before stopping (default: 10)')
        
        # Output control
        self.add_output_options(read)
        
        return read
    
    def add_output_options(self, parser):
        """Add common output control options"""
        output = parser.add_argument_group('Output Control')
        output.add_argument('--verbose', '-v', action='store_true',
                          help='Verbose output with detailed progress')
        output.add_argument('--quiet', '-q', action='store_true',
                          help='Quiet mode (minimal output)')
        output.add_argument('--no-progress', action='store_true',
                          help='Disable progress bars')
        output.add_argument('--no-emoji', action='store_true',
                          help='Disable emoji in output (for compatibility)')
    
    def discover_files(self, input_path, pattern=None, recursive=False):
        """Discover files for processing based on input path and options"""
        files = []
        
        if os.path.isfile(input_path):
            # Single file
            files.append(input_path)
        elif os.path.isdir(input_path):
            # Directory - discover files
            import glob
            from pathlib import Path
            
            input_dir = Path(input_path)
            
            if pattern:
                # Use provided pattern
                search_pattern = pattern
            else:
                # Default patterns for common file types
                search_pattern = "*"
            
            if recursive:
                # Recursive search
                search_path = input_dir / "**" / search_pattern
                files.extend(glob.glob(str(search_path), recursive=True))
            else:
                # Non-recursive search
                search_path = input_dir / search_pattern
                files.extend(glob.glob(str(search_path)))
            
            # Filter out directories from results
            files = [f for f in files if os.path.isfile(f)]
            
            # Sort for consistent processing order
            files.sort()
        else:
            raise FileNotFoundError(f"Input path not found: {input_path}")
        
        return files
    
    def create_organized_output_structure(self, output_dir, input_path, preserve_structure=False):
        """Create organized output directory structure"""
        import datetime
        from pathlib import Path
        
        # Create base output directory
        output_path = Path(output_dir)
        
        # Create timestamp-based session directory for organization
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if os.path.isfile(input_path):
            # Single file - create session directory
            session_name = f"{Path(input_path).stem}_{timestamp}"
            session_dir = output_path / session_name
        else:
            # Directory processing - create batch session directory
            input_name = Path(input_path).name or "batch"
            session_name = f"{input_name}_batch_{timestamp}"
            session_dir = output_path / session_name
        
        # Create directory structure
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for organization
        (session_dir / "qr_codes").mkdir(exist_ok=True)
        (session_dir / "sheets").mkdir(exist_ok=True)
        (session_dir / "reports").mkdir(exist_ok=True)
        
        return session_dir
    
    def get_relative_output_path(self, file_path, input_base, output_base, preserve_structure=False):
        """Get the output path for a file, optionally preserving directory structure"""
        from pathlib import Path
        
        if not preserve_structure:
            # Flat structure - just filename
            filename = Path(file_path).name
            return output_base / "qr_codes" / filename
        else:
            # Preserve directory structure
            relative_path = Path(file_path).relative_to(Path(input_base).parent)
            return output_base / "qr_codes" / relative_path
    
    def generate_batch_summary(self, processed_files, output_dir, total_time):
        """Generate a comprehensive batch processing summary"""
        import json
        import datetime
        from pathlib import Path
        
        summary = {
            "batch_info": {
                "timestamp": datetime.datetime.now().isoformat(),
                "total_files": len(processed_files),
                "total_time_seconds": round(total_time, 2),
                "output_directory": str(output_dir)
            },
            "files": [],
            "statistics": {
                "total_qr_codes": 0,
                "total_sheets": 0,
                "encrypted_files": 0,
                "failed_files": 0,
                "average_qr_codes_per_file": 0
            }
        }
        
        for file_info in processed_files:
            summary["files"].append(file_info)
            if file_info.get("success", False):
                summary["statistics"]["total_qr_codes"] += file_info.get("qr_count", 0)
                summary["statistics"]["total_sheets"] += file_info.get("sheet_count", 0)
                if file_info.get("encrypted", False):
                    summary["statistics"]["encrypted_files"] += 1
            else:
                summary["statistics"]["failed_files"] += 1
        
        # Calculate averages
        successful_files = len([f for f in processed_files if f.get("success", False)])
        if successful_files > 0:
            summary["statistics"]["average_qr_codes_per_file"] = round(
                summary["statistics"]["total_qr_codes"] / successful_files, 1
            )
        
        # Save summary report
        reports_dir = Path(output_dir) / "reports"
        reports_dir.mkdir(exist_ok=True)
        summary_file = reports_dir / "batch_summary.json"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return summary_file, summary
    
    def run_generate(self, args):
        """Execute generate command with folder support"""
        import time
        from pathlib import Path
        
        # Validate input exists
        if not os.path.exists(args.input):
            self._safe_print(f"❌ Error: Input not found: {args.input}")
            return 1
        
        # Check encryption dependencies
        if args.encrypt and not HAS_CRYPTO:
            self._safe_print("❌ Error: Encryption requires 'cryptography' library")
            self._safe_print("   Install with: pip install cryptography")
            return 1
        
        # Discover files to process
        try:
            files_to_process = self.discover_files(
                args.input, 
                getattr(args, 'pattern', None),
                getattr(args, 'recursive', False)
            )
            # Convert to absolute paths to avoid issues with directory changes
            files_to_process = [os.path.abspath(f) for f in files_to_process]
        except Exception as e:
            self._safe_print(f"❌ Error discovering files: {e}")
            return 1
        
        if not files_to_process:
            self._safe_print(f"❌ No files found to process in: {args.input}")
            return 1
        
        # Set up output directory
        if getattr(args, 'organized', True):
            # Create organized output structure
            output_base_dir = getattr(args, 'output_dir', None) or "./qr_output"
            try:
                session_output_dir = self.create_organized_output_structure(
                    output_base_dir, 
                    args.input,
                    getattr(args, 'preserve_structure', False)
                )
            except Exception as e:
                self._safe_print(f"❌ Error creating output structure: {e}")
                return 1
        else:
            # Simple output to current directory or specified directory
            session_output_dir = Path(getattr(args, 'output_dir', "."))
            session_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Display processing plan
        verbose = getattr(args, 'verbose', False)
        quiet = getattr(args, 'quiet', False)
        

        
        if not quiet:
            is_folder = os.path.isdir(args.input)
            encryption_note = " with AES-256 encryption" if args.encrypt else ""
            sheet_note = " as sheets" if getattr(args, 'sheet', False) else ""
            
            if is_folder:
                self._safe_print(f"📁 Batch processing {len(files_to_process)} file(s){sheet_note}{encryption_note}")
                self._safe_print(f"📂 Input: {args.input}")
            else:
                self._safe_print(f"🎯 Generating QR codes{sheet_note}{encryption_note} for: {args.input}")
            
            self._safe_print(f"📁 Output: {session_output_dir}")
            
            if verbose and len(files_to_process) > 1:
                self._safe_print(f"\n📋 Files to process:")
                for i, file_path in enumerate(files_to_process[:10], 1):  # Show first 10
                    self._safe_print(f"  {i:2d}. {Path(file_path).name}")
                if len(files_to_process) > 10:
                    self._safe_print(f"  ... and {len(files_to_process) - 10} more files")
                self._safe_print("")
        
        # Process files
        processed_files = []
        start_time = time.time()
        successful_count = 0
        
        for i, file_path in enumerate(files_to_process, 1):
            if not quiet:
                progress_msg = f"[{i}/{len(files_to_process)}]" if len(files_to_process) > 1 else ""
                self._safe_print(f"🔄 {progress_msg} Processing: {Path(file_path).name}")
            
            file_start_time = time.time()
            file_info = {
                "file_path": file_path,
                "file_name": Path(file_path).name,
                "success": False,
                "qr_count": 0,
                "sheet_count": 0,
                "encrypted": args.encrypt,
                "processing_time": 0,
                "error": None
            }
            
            try:
                # Set up arguments for QRTransferTool
                tool_args = argparse.Namespace()
                
                # Copy over relevant arguments with defaults
                tool_args.file = file_path
                tool_args.encrypt = getattr(args, 'encrypt', False)
                tool_args.sheet = getattr(args, 'sheet', False)
                tool_args.sheet_size = getattr(args, 'sheet_size', None) or 9
                tool_args.sheet_cols = getattr(args, 'sheet_cols', None) or 3
                tool_args.box_size = getattr(args, 'box_size', None) or 10
                tool_args.border = getattr(args, 'border', None) or 4
                tool_args.force = getattr(args, 'force', False)
                tool_args.display = getattr(args, 'display', 'none')
                tool_args.verbose = verbose and len(files_to_process) == 1  # Only verbose for single files
                tool_args.quiet = quiet or len(files_to_process) > 1  # Quiet for batch processing
                tool_args.no_parallel = getattr(args, 'no_parallel', False)
                
                # Set up cleanup - always enabled for organized workflows
                tool_args.cleanup = getattr(args, 'auto_cleanup', True) or getattr(args, 'cleanup', False)
                
                # Override working directory for organized output
                if getattr(args, 'organized', True):
                    original_cwd = os.getcwd()
                    target_output_dir = self.get_relative_output_path(
                        file_path, args.input, session_output_dir, 
                        getattr(args, 'preserve_structure', False)
                    ).parent
                    target_output_dir.mkdir(parents=True, exist_ok=True)
                    os.chdir(target_output_dir)
                
                # Process the file
                with QRTransferTool(tool_args) as tool:
                    tool.process_file(file_path)
                
                # Restore working directory
                if getattr(args, 'organized', True):
                    os.chdir(original_cwd)
                
                file_info["success"] = True
                file_info["processing_time"] = round(time.time() - file_start_time, 2)
                successful_count += 1
                
                if verbose or (not quiet and len(files_to_process) == 1):
                    self._safe_print(f"  ✅ Generated QR codes for {Path(file_path).name}")
                
            except KeyboardInterrupt:
                if getattr(args, 'organized', True):
                    os.chdir(original_cwd)
                self._safe_print("\n⏹️  Operation cancelled by user")
                return 1
            except Exception as e:
                if getattr(args, 'organized', True):
                    os.chdir(original_cwd)
                file_info["error"] = str(e)
                file_info["processing_time"] = round(time.time() - file_start_time, 2)
                
                if verbose:
                    self._safe_print(f"  ❌ Failed to process {Path(file_path).name}: {e}")
                elif not quiet:
                    self._safe_print(f"  ❌ Failed: {Path(file_path).name}")
            
            processed_files.append(file_info)
        
        total_time = time.time() - start_time
        
        # Generate batch summary if requested
        summary_file = None
        if getattr(args, 'batch_summary', True) and len(files_to_process) > 1:
            try:
                summary_file, summary = self.generate_batch_summary(processed_files, session_output_dir, total_time)
                if verbose:
                    self._safe_print(f"📊 Batch summary saved: {summary_file}")
            except Exception as e:
                if verbose:
                    self._safe_print(f"⚠️  Could not generate batch summary: {e}")
        
        # Final summary
        if not quiet:
            self._safe_print(f"\n{'='*60}")
            if len(files_to_process) > 1:
                failed_count = len(files_to_process) - successful_count
                self._safe_print(f"📊 Batch processing completed: {successful_count}/{len(files_to_process)} files successful")
                if failed_count > 0:
                    self._safe_print(f"❌ Failed files: {failed_count}")
                self._safe_print(f"⏱️  Total time: {total_time:.1f}s")
                if summary_file:
                    try:
                        rel_path = summary_file.relative_to(Path.cwd())
                        self._safe_print(f"📋 Detailed report: {rel_path}")
                    except ValueError:
                        self._safe_print(f"📋 Detailed report: {summary_file}")
            else:
                self._safe_print(f"✅ QR code generation completed successfully")
            
            self._safe_print(f"📁 Output location: {session_output_dir}")
            if getattr(args, 'organized', True):
                self._safe_print(f"   📂 QR codes: {session_output_dir / 'qr_codes'}")
                if getattr(args, 'sheet', False):
                    self._safe_print(f"   📄 Sheets: {session_output_dir / 'sheets'}")
                self._safe_print(f"   📊 Reports: {session_output_dir / 'reports'}")
        
        return 0 if successful_count == len(files_to_process) else 1
    
    def run_scan(self, args):
        """Execute scan command"""
        # Validate input directory
        if not os.path.isdir(args.input_dir):
            self._safe_print(f"❌ Error: Directory not found: {args.input_dir}")
            return 1
        
        # Set up arguments for QRBatchScanner
        scanner_args = argparse.Namespace()
        scanner_args.input_dir = args.input_dir
        scanner_args.output = args.output
        scanner_args.auto_reconstruct = getattr(args, 'auto_reconstruct', False)
        scanner_args.verbose = getattr(args, 'verbose', False)
        scanner_args.quiet = getattr(args, 'quiet', False)
        
        # Validate argument conflicts
        if scanner_args.quiet and scanner_args.verbose:
            self._safe_print("❌ Error: Cannot use --quiet and --verbose together")
            return 1
        
        try:
            if not scanner_args.quiet:
                auto_note = " with auto-reconstruction" if scanner_args.auto_reconstruct else ""
                self._safe_print(f"📸 Scanning QR images{auto_note} from: {args.input_dir}")
            
            scanner = QRBatchScanner(scanner_args)
            
            # Process images
            scanner.process_image_folder(args.input_dir)
            
            # Validate and organize chunks
            validated_files = scanner.validate_chunks()
            
            if not validated_files:
                self._safe_print("❌ No complete files found. Check your QR images and try again.")
                return 1
            
            # Save chunks and reports
            scanner.save_chunks_as_text(validated_files, args.output)
            scanner.save_summary_report(validated_files, args.output)
            
            # Auto-reconstruct if requested
            scanner.auto_reconstruct(validated_files, args.output)
            
            # Print summary
            scanner.print_summary(validated_files)
            
            if not scanner_args.quiet:
                self._safe_print(f"\n✅ Scanning completed successfully")
                self._safe_print(f"📁 Chunks saved to: {args.output}")
                if not scanner_args.auto_reconstruct:
                    self._safe_print(f"🔄 To reconstruct files: qr rebuild {args.output}")
            
        except KeyboardInterrupt:
            self._safe_print("\n⏹️  Operation cancelled by user")
            return 1
        except Exception as e:
            self._safe_print(f"❌ Error: {e}")
            if getattr(args, 'verbose', False):
                import traceback
                traceback.print_exc()
            return 1
        
        return 0
    
    def run_rebuild(self, args):
        """Execute rebuild command"""
        # Validate chunks directory
        if not os.path.isdir(args.chunks_dir):
            self._safe_print(f"❌ Error: Directory not found: {args.chunks_dir}")
            return 1
        
        try:
            verbose = getattr(args, 'verbose', False)
            quiet = getattr(args, 'quiet', False)
            
            # Validate argument conflicts
            if quiet and verbose:
                self._safe_print("❌ Error: Cannot use --quiet and --verbose together")
                return 1
            
            if not quiet:
                reconstruction_type = "encrypted " if getattr(args, 'encrypted', False) else ""
                verification_note = " with verification" if getattr(args, 'verify', False) else ""
                self._safe_print(f"🔄 Rebuilding {reconstruction_type}files{verification_note} from: {args.chunks_dir}")
            
            # Choose appropriate reconstruction method
            if getattr(args, 'encrypted', False):
                # Use encrypted reconstruction
                import qr_rebuild_encrypted
                sys.argv = ['qr_rebuild_encrypted.py', args.chunks_dir]
                if getattr(args, 'output_dir'):
                    sys.argv.extend(['--output', args.output_dir])
                qr_rebuild_encrypted.main()
                
            elif getattr(args, 'verify', False):
                # Use verified reconstruction
                import qr_rebuild_verified
                sys.argv = ['qr_rebuild_verified.py', args.chunks_dir]
                qr_rebuild_verified.main()
                
            elif getattr(args, 'spaces', False):
                # Use spaces reconstruction
                import qr_rebuild_spaces
                sys.argv = ['qr_rebuild_spaces.py', args.chunks_dir]
                qr_rebuild_spaces.main()
                
            else:
                # Use basic reconstruction
                sys.argv = ['qr_rebuild.py', args.chunks_dir]
                qr_rebuild.main()
            
            if not quiet:
                self._safe_print("✅ File reconstruction completed successfully")
                
        except KeyboardInterrupt:
            self._safe_print("\n⏹️  Operation cancelled by user")
            return 1
        except Exception as e:
            self._safe_print(f"❌ Error: {e}")
            if getattr(args, 'verbose', False):
                import traceback
                traceback.print_exc()
            return 1
        
        return 0
    
    def run_config(self, args):
        """Execute config command"""
        try:
            config = QRConfig(getattr(args, 'file', None))
            
            # Determine action
            action = getattr(args, 'action', None)
            if getattr(args, 'show', False):
                action = 'show'
            elif getattr(args, 'reset', False):
                action = 'reset'
            elif getattr(args, 'sample', False):
                action = 'sample'
            
            if action == 'show' or action is None:
                config.print_config()
                
            elif action == 'reset':
                config.reset_to_defaults()
                if config.save_config():
                    self._safe_print("✅ Configuration reset to defaults")
                else:
                    self._safe_print("❌ Failed to save configuration")
                    return 1
                    
            elif action == 'sample':
                sample_path = config.create_sample_config()
                if sample_path:
                    self._safe_print(f"✅ Sample configuration created: {sample_path}")
                else:
                    self._safe_print("❌ Failed to create sample configuration")
                    return 1
            
        except Exception as e:
            self._safe_print(f"❌ Error: {e}")
            return 1
        
        return 0
    
    def run_read(self, args):
        """Execute unified read command with smart auto-detection"""
        import time
        from pathlib import Path
        
        # Validate input
        if not os.path.exists(args.input):
            self._safe_print(f"❌ Error: Input not found: {args.input}")
            return 1
        
        verbose = getattr(args, 'verbose', False)
        quiet = getattr(args, 'quiet', False)
        
        # Override detection if user specified
        if getattr(args, 'as_images', False):
            detection_result = "qr_images_dir" if os.path.isdir(args.input) else "qr_image_file"
            stats = None
        elif getattr(args, 'as_chunks', False):
            detection_result = "chunk_files_dir" if os.path.isdir(args.input) else "chunk_file"
            stats = None
        else:
            # Smart auto-detection
            detection = self.detect_input_type(args.input)
            if isinstance(detection, tuple):
                detection_result, stats = detection
            else:
                detection_result = detection
                stats = None
        
        # Provide user feedback on detection
        if not quiet:
            self._safe_print(f"🔍 Analyzing input: {args.input}")
            
            if detection_result == "qr_image_file":
                self._safe_print(f"✨ Detected: Single QR image file")
            elif detection_result == "chunk_file":
                self._safe_print(f"✨ Detected: Single chunk file")
            elif detection_result == "text_file":
                self._safe_print(f"✨ Detected: Text file (treating as input for generation)")
            elif detection_result == "qr_images_dir":
                if stats:
                    self._safe_print(f"✨ Detected: QR images directory ({len(stats['qr_images'])} images found)")
                else:
                    self._safe_print(f"✨ Detected: QR images directory")
            elif detection_result == "chunk_files_dir":
                if stats:
                    self._safe_print(f"✨ Detected: Chunk files directory ({len(stats['chunk_files'])} chunks found)")
                else:
                    self._safe_print(f"✨ Detected: Chunk files directory")
            elif detection_result == "mixed_content":
                if stats:
                    self._safe_print(f"✨ Detected: Mixed content ({len(stats['qr_images'])} images, {len(stats['chunk_files'])} chunks)")
                else:
                    self._safe_print(f"✨ Detected: Mixed content directory")
        
        # Route to appropriate processing based on detection and mode
        mode = getattr(args, 'mode', 'auto')
        
        try:
            if detection_result in ["qr_image_file", "qr_images_dir"]:
                # Handle QR images
                if mode == 'rebuild-only':
                    self._safe_print("❌ Error: Cannot rebuild-only from QR images. Use scan-only or auto mode.")
                    return 1
                
                if not quiet:
                    auto_rebuild_note = " with auto-rebuild" if getattr(args, 'auto_rebuild', True) else ""
                    self._safe_print(f"📸 Processing QR images{auto_rebuild_note}...")
                
                # Convert args for scan command
                scan_args = self._convert_read_args_to_scan(args)
                return self.run_scan(scan_args)
                
            elif detection_result in ["chunk_file", "chunk_files_dir"]:
                # Handle chunk files
                if mode == 'scan-only':
                    self._safe_print("❌ Error: Cannot scan-only chunk files. Use rebuild-only or auto mode.")
                    return 1
                
                if not quiet:
                    self._safe_print(f"🔧 Rebuilding files from chunks...")
                
                # Convert args for rebuild command
                rebuild_args = self._convert_read_args_to_rebuild(args)
                return self.run_rebuild(rebuild_args)
                
            elif detection_result == "mixed_content":
                # Handle mixed content
                if not quiet:
                    self._safe_print(f"🎯 Processing mixed content...")
                
                if mode == 'scan-only':
                    # Only scan the images
                    if stats and len(stats['qr_images']) > 0:
                        scan_args = self._convert_read_args_to_scan(args)
                        scan_args.auto_rebuild = False  # Force no rebuild
                        return self.run_scan(scan_args)
                    else:
                        self._safe_print("❌ No QR images found for scan-only mode")
                        return 1
                        
                elif mode == 'rebuild-only':
                    # Only rebuild from chunks
                    if stats and len(stats['chunk_files']) > 0:
                        rebuild_args = self._convert_read_args_to_rebuild(args)
                        return self.run_rebuild(rebuild_args)
                    else:
                        self._safe_print("❌ No chunk files found for rebuild-only mode")
                        return 1
                        
                else:  # auto mode
                    # Process both: scan images first, then rebuild everything
                    success_count = 0
                    
                    if stats and len(stats['qr_images']) > 0:
                        if verbose:
                            self._safe_print(f"📸 Step 1: Scanning {len(stats['qr_images'])} QR images...")
                        scan_args = self._convert_read_args_to_scan(args)
                        scan_result = self.run_scan(scan_args)
                        if scan_result == 0:
                            success_count += 1
                    
                    if stats and len(stats['chunk_files']) > 0:
                        if verbose:
                            self._safe_print(f"🔧 Step 2: Rebuilding from {len(stats['chunk_files'])} chunk files...")
                        rebuild_args = self._convert_read_args_to_rebuild(args)
                        rebuild_result = self.run_rebuild(rebuild_args)
                        if rebuild_result == 0:
                            success_count += 1
                    
                    return 0 if success_count > 0 else 1
                
            elif detection_result == "text_file":
                # Text file - suggest using generate instead
                self._safe_print(f"💡 Detected text file. Did you mean 'qr generate {args.input}'?")
                self._safe_print(f"   Use 'qr generate' to create QR codes from text files.")
                return 1
                
            elif detection_result == "empty_dir":
                self._safe_print(f"❌ Error: Directory is empty: {args.input}")
                return 1
                
            elif detection_result in ["unknown_dir", "unknown_file", "unknown"]:
                self._safe_print(f"❌ Error: Unable to determine how to process: {args.input}")
                if stats and stats.get('other_files'):
                    self._safe_print(f"   Found {len(stats['other_files'])} unrecognized files")
                self._safe_print(f"   Supported: QR images (.png, .jpg, etc.) and chunk files (.txt)")
                return 1
                
            else:
                self._safe_print(f"❌ Error: Unknown detection result: {detection_result}")
                return 1
                
        except Exception as e:
            self._safe_print(f"❌ Error during processing: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _convert_read_args_to_scan(self, args):
        """Convert read command args to scan command args"""
        scan_args = argparse.Namespace()
        
        # Map arguments
        scan_args.input_dir = args.input
        scan_args.output = getattr(args, 'output', None) or "./scan_output"
        scan_args.auto_reconstruct = getattr(args, 'auto_rebuild', True)
        scan_args.verbose = getattr(args, 'verbose', False)
        scan_args.quiet = getattr(args, 'quiet', False)
        scan_args.verify_checksums = getattr(args, 'verify_checksums', True)
        scan_args.pattern = getattr(args, 'pattern', None)
        scan_args.recursive = getattr(args, 'recursive', False)
        scan_args.organized = getattr(args, 'organized', True)
        scan_args.auto_cleanup = getattr(args, 'auto_cleanup', True)
        scan_args.scan_summary = getattr(args, 'read_summary', True)
        scan_args.max_errors = getattr(args, 'max_errors', 10)
        
        return scan_args
    
    def _convert_read_args_to_rebuild(self, args):
        """Convert read command args to rebuild command args"""
        rebuild_args = argparse.Namespace()
        
        # Map arguments
        rebuild_args.chunks_dir = args.input
        rebuild_args.output_dir = getattr(args, 'output', None)
        rebuild_args.verify = getattr(args, 'verify_checksums', False)
        rebuild_args.encrypted = getattr(args, 'encrypted', False)
        rebuild_args.spaces = getattr(args, 'spaces', False)
        rebuild_args.verbose = getattr(args, 'verbose', False)
        rebuild_args.quiet = getattr(args, 'quiet', False)
        rebuild_args.pattern = getattr(args, 'pattern', None)
        rebuild_args.recursive = getattr(args, 'recursive', False)
        rebuild_args.organized = getattr(args, 'organized', True)
        rebuild_args.auto_cleanup = getattr(args, 'auto_cleanup', True)
        rebuild_args.rebuild_summary = getattr(args, 'read_summary', True)
        rebuild_args.batch = False  # Single operation
        rebuild_args.suffix = None
        
        return rebuild_args
    
    def detect_input_type(self, input_path):
        """Smart detection of input content type for unified read command"""
        from pathlib import Path
        import glob
        
        if not os.path.exists(input_path):
            return "not_found"
        
        if os.path.isfile(input_path):
            # Single file - check extension
            ext = Path(input_path).suffix.lower()
            if ext in {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}:
                return "qr_image_file"
            elif ext == '.txt':
                # Check if it's a QR chunk file by reading first few lines
                try:
                    with open(input_path, 'r', encoding='utf-8') as f:
                        content = f.read(200)  # Read first 200 chars
                        if '--BEGIN part_' in content and 'file:' in content:
                            return "chunk_file"
                except:
                    pass
                return "text_file"
            else:
                return "unknown_file"
        
        if os.path.isdir(input_path):
            # Directory - analyze contents
            stats = {
                'qr_images': [],
                'chunk_files': [],
                'other_files': [],
                'total_files': 0
            }
            
            # Scan directory for relevant files
            for file_path in Path(input_path).iterdir():
                if file_path.is_file():
                    stats['total_files'] += 1
                    ext = file_path.suffix.lower()
                    
                    if ext in {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}:
                        stats['qr_images'].append(str(file_path))
                    elif ext == '.txt':
                        # Check if it's a chunk file
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read(200)
                                if '--BEGIN part_' in content and 'file:' in content:
                                    stats['chunk_files'].append(str(file_path))
                                else:
                                    stats['other_files'].append(str(file_path))
                        except:
                            stats['other_files'].append(str(file_path))
                    else:
                        stats['other_files'].append(str(file_path))
            
            # Determine directory type based on contents
            has_qr_images = len(stats['qr_images']) > 0
            has_chunk_files = len(stats['chunk_files']) > 0
            
            if has_qr_images and has_chunk_files:
                return "mixed_content", stats
            elif has_qr_images:
                return "qr_images_dir", stats
            elif has_chunk_files:
                return "chunk_files_dir", stats
            elif stats['total_files'] == 0:
                return "empty_dir", stats
            else:
                return "unknown_dir", stats
        
        return "unknown"
    
    def run(self, argv=None):
        """Main entry point"""
        parser = self.create_parser()
        args = parser.parse_args(argv)
        
        # Handle no command provided
        if not hasattr(args, 'command') or args.command is None:
            parser.print_help()
            return 1
        
        # Route to appropriate command handler
        if args.command in ['generate', 'gen', 'g']:
            return self.run_generate(args)
        elif args.command in ['scan', 's']:
            return self.run_scan(args)
        elif args.command in ['rebuild', 'r']:
            return self.run_rebuild(args)
        elif args.command in ['config', 'cfg']:
            return self.run_config(args)
        elif args.command in ['read', 'r']:
            return self.run_read(args)
        else:
            self._safe_print(f"❌ Error: Unknown command: {args.command}")
            parser.print_help()
            return 1

def main():
    """Main entry point for the unified CLI"""
    cli = QRUnifiedCLI()
    return cli.run()

if __name__ == "__main__":
    sys.exit(main())
