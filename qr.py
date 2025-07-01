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
        self.version = "2.0.0"
        self.description = "QR File Transfer Tool - Secure, professional file transfer using QR codes"
    
    def create_parser(self):
        """Create the main argument parser with subcommands"""
        parser = argparse.ArgumentParser(
            prog='qr',
            description=self.description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Common workflows:
  qr generate file.txt --sheet              # Create QR sheets for easy scanning
  qr generate secret.txt --encrypt          # Encrypted QR codes with AES-256
  qr scan ./photos/                         # Scan QR images from folder
  qr rebuild ./scanned_chunks/              # Reconstruct files from chunks
  qr config show                            # Display current settings

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
            description='Available operations',
            help='Use "qr <command> --help" for detailed help'
        )
        
        # Generate command
        self.create_generate_parser(subparsers)
        
        # Scan command  
        self.create_scan_parser(subparsers)
        
        # Rebuild command
        self.create_rebuild_parser(subparsers)
        
        # Config command
        self.create_config_parser(subparsers)
        
        return parser
    
    def create_generate_parser(self, subparsers):
        """Create parser for generate command"""
        generate = subparsers.add_parser(
            'generate',
            aliases=['gen', 'g'],
            help='Generate QR codes from files',
            description='Convert files to QR codes with optional encryption and integrity verification',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  qr generate document.txt                   # Basic QR generation
  qr generate document.txt --sheet           # Generate organized sheets
  qr generate secret.txt --encrypt           # AES-256 encrypted QR codes
  qr generate large.txt --sheet --verbose    # Detailed progress output
  qr generate file.txt --box-size 8          # Smaller QR codes
            """
        )
        
        # Required arguments
        generate.add_argument('file', help='File to convert to QR codes')
        
        # Security options
        security = generate.add_argument_group('Security Options')
        security.add_argument('--encrypt', action='store_true',
                            help='Encrypt content with AES-256 before QR generation')
        
        # Output format options
        output = generate.add_argument_group('Output Options')
        output.add_argument('--sheet', action='store_true',
                          help='Generate QR code sheets (recommended for multiple codes)')
        output.add_argument('--sheet-size', type=int, metavar='N',
                          help='QR codes per sheet (default: 9)')
        output.add_argument('--sheet-cols', type=int, metavar='N', 
                          help='Columns per sheet (default: 3)')
        output.add_argument('--output-dir', '-o', metavar='DIR',
                          help='Output directory for generated QR codes')
        
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
                            help='Auto-cleanup temporary files')
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
            help='Scan QR code images to extract chunks',
            description='Process QR code images to extract file chunks for reconstruction',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  qr scan ./photos/                         # Scan all images in folder
  qr scan ./images/ -o ./chunks/            # Custom output directory
  qr scan ./qr_sheets/ --auto-rebuild       # Scan and auto-reconstruct files
  qr scan ./mobile_photos/ --verbose        # Detailed scanning progress
            """
        )
        
        # Required arguments
        scan.add_argument('input_dir', help='Directory containing QR code images')
        
        # Output options
        output = scan.add_argument_group('Output Options')
        output.add_argument('--output', '-o', default='./scanned_chunks', metavar='DIR',
                          help='Output directory for chunk files (default: ./scanned_chunks)')
        output.add_argument('--auto-rebuild', action='store_true',
                          help='Automatically reconstruct files after scanning')
        
        # Processing options
        processing = scan.add_argument_group('Processing Options')
        processing.add_argument('--verify-checksums', action='store_true', default=True,
                              help='Verify chunk integrity with checksums (default: enabled)')
        processing.add_argument('--no-verify', dest='verify_checksums', action='store_false',
                              help='Skip checksum verification')
        
        # Output control
        self.add_output_options(scan)
        
        return scan
    
    def create_rebuild_parser(self, subparsers):
        """Create parser for rebuild command"""
        rebuild = subparsers.add_parser(
            'rebuild',
            aliases=['r'],
            help='Rebuild files from scanned chunks',
            description='Reconstruct original files from QR code chunks with integrity verification',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  qr rebuild ./scanned_chunks/              # Basic reconstruction
  qr rebuild ./chunks/ --verify             # With integrity verification
  qr rebuild ./chunks/ --encrypted          # Decrypt encrypted chunks
  qr rebuild ./chunks/ --spaces             # Convert tabs to spaces
  qr rebuild ./chunks/ -o ./restored/       # Custom output directory
            """
        )
        
        # Required arguments
        rebuild.add_argument('chunks_dir', help='Directory containing chunk files')
        
        # Reconstruction options
        reconstruction = rebuild.add_argument_group('Reconstruction Options')
        reconstruction.add_argument('--verify', action='store_true',
                                  help='Verify file integrity with checksums')
        reconstruction.add_argument('--encrypted', action='store_true',
                                  help='Decrypt AES-256 encrypted chunks')
        reconstruction.add_argument('--spaces', action='store_true',
                                  help='Convert tabs to spaces during reconstruction')
        
        # Output options
        output = rebuild.add_argument_group('Output Options')
        output.add_argument('--output-dir', '-o', metavar='DIR',
                          help='Output directory for reconstructed files (default: current)')
        output.add_argument('--suffix', metavar='STR',
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
    
    def run_generate(self, args):
        """Execute generate command"""
        # Validate file exists
        if not os.path.exists(args.file):
            print(f"❌ Error: File not found: {args.file}")
            return 1
        
        # Check encryption dependencies
        if args.encrypt and not HAS_CRYPTO:
            print("❌ Error: Encryption requires 'cryptography' library")
            print("   Install with: pip install cryptography")
            return 1
        
        # Set up arguments for QRTransferTool (convert from our namespace)
        tool_args = argparse.Namespace()
        
        # Copy over relevant arguments with defaults
        tool_args.file = args.file
        tool_args.encrypt = getattr(args, 'encrypt', False)
        tool_args.sheet = getattr(args, 'sheet', False)
        tool_args.sheet_size = getattr(args, 'sheet_size', None) or 9
        tool_args.sheet_cols = getattr(args, 'sheet_cols', None) or 3
        tool_args.box_size = getattr(args, 'box_size', None) or 10
        tool_args.border = getattr(args, 'border', None) or 4
        tool_args.cleanup = getattr(args, 'cleanup', False)
        tool_args.force = getattr(args, 'force', False)
        tool_args.display = getattr(args, 'display', 'none')
        tool_args.verbose = getattr(args, 'verbose', False)
        tool_args.quiet = getattr(args, 'quiet', False)
        tool_args.no_parallel = getattr(args, 'no_parallel', False)
        
        # Override quiet if no_progress is set
        if getattr(args, 'no_progress', False):
            tool_args.quiet = True
        
        # Validate argument conflicts
        if tool_args.quiet and tool_args.verbose:
            print("❌ Error: Cannot use --quiet and --verbose together")
            return 1
        
        try:
            if not tool_args.quiet:
                encryption_note = " with AES-256 encryption" if tool_args.encrypt else ""
                sheet_note = " as sheets" if tool_args.sheet else ""
                print(f"🎯 Generating QR codes{sheet_note}{encryption_note} for: {args.file}")
            
            with QRTransferTool(tool_args) as tool:
                tool.process_file(args.file)
                
            if not tool_args.quiet:
                print(f"✅ QR code generation completed successfully")
                
        except KeyboardInterrupt:
            print("\n⏹️  Operation cancelled by user")
            return 1
        except Exception as e:
            print(f"❌ Error: {e}")
            if tool_args.verbose:
                import traceback
                traceback.print_exc()
            return 1
        
        return 0
    
    def run_scan(self, args):
        """Execute scan command"""
        # Validate input directory
        if not os.path.isdir(args.input_dir):
            print(f"❌ Error: Directory not found: {args.input_dir}")
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
            print("❌ Error: Cannot use --quiet and --verbose together")
            return 1
        
        try:
            if not scanner_args.quiet:
                auto_note = " with auto-reconstruction" if scanner_args.auto_reconstruct else ""
                print(f"📸 Scanning QR images{auto_note} from: {args.input_dir}")
            
            scanner = QRBatchScanner(scanner_args)
            
            # Process images
            scanner.process_image_folder(args.input_dir)
            
            # Validate and organize chunks
            validated_files = scanner.validate_chunks()
            
            if not validated_files:
                print("❌ No complete files found. Check your QR images and try again.")
                return 1
            
            # Save chunks and reports
            scanner.save_chunks_as_text(validated_files, args.output)
            scanner.save_summary_report(validated_files, args.output)
            
            # Auto-reconstruct if requested
            scanner.auto_reconstruct(validated_files, args.output)
            
            # Print summary
            scanner.print_summary(validated_files)
            
            if not scanner_args.quiet:
                print(f"\n✅ Scanning completed successfully")
                print(f"📁 Chunks saved to: {args.output}")
                if not scanner_args.auto_reconstruct:
                    print(f"🔄 To reconstruct files: qr rebuild {args.output}")
            
        except KeyboardInterrupt:
            print("\n⏹️  Operation cancelled by user")
            return 1
        except Exception as e:
            print(f"❌ Error: {e}")
            if getattr(args, 'verbose', False):
                import traceback
                traceback.print_exc()
            return 1
        
        return 0
    
    def run_rebuild(self, args):
        """Execute rebuild command"""
        # Validate chunks directory
        if not os.path.isdir(args.chunks_dir):
            print(f"❌ Error: Directory not found: {args.chunks_dir}")
            return 1
        
        try:
            verbose = getattr(args, 'verbose', False)
            quiet = getattr(args, 'quiet', False)
            
            # Validate argument conflicts
            if quiet and verbose:
                print("❌ Error: Cannot use --quiet and --verbose together")
                return 1
            
            if not quiet:
                reconstruction_type = "encrypted " if getattr(args, 'encrypted', False) else ""
                verification_note = " with verification" if getattr(args, 'verify', False) else ""
                print(f"🔄 Rebuilding {reconstruction_type}files{verification_note} from: {args.chunks_dir}")
            
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
                print("✅ File reconstruction completed successfully")
                
        except KeyboardInterrupt:
            print("\n⏹️  Operation cancelled by user")
            return 1
        except Exception as e:
            print(f"❌ Error: {e}")
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
                    print("✅ Configuration reset to defaults")
                else:
                    print("❌ Failed to save configuration")
                    return 1
                    
            elif action == 'sample':
                sample_path = config.create_sample_config()
                if sample_path:
                    print(f"✅ Sample configuration created: {sample_path}")
                else:
                    print("❌ Failed to create sample configuration")
                    return 1
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
        
        return 0
    
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
        else:
            print(f"❌ Error: Unknown command: {args.command}")
            parser.print_help()
            return 1

def main():
    """Main entry point for the unified CLI"""
    cli = QRUnifiedCLI()
    return cli.run()

if __name__ == "__main__":
    sys.exit(main())
