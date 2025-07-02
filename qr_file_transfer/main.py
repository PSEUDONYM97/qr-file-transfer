#!/usr/bin/env python3
"""
QR File Transfer Tool - Main Entry Point
Simple wrapper to handle console script execution
"""

import sys
import os

def main():
    """Main entry point for the qr command"""
    try:
        # Add the package directory to sys.path to ensure imports work
        package_dir = os.path.dirname(os.path.abspath(__file__))
        if package_dir not in sys.path:
            sys.path.insert(0, package_dir)
        
        # Import the CLI class with absolute imports
        import qr_enhanced
        import qr_scan
        import qr_config
        import qr_rebuild
        import qr_rebuild_encrypted
        import qr_rebuild_verified
        
        # Import the main CLI from the current directory
        from cli import QRUnifiedCLI
        
        # Run the CLI
        cli = QRUnifiedCLI()
        return cli.run()
        
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
        print("   Make sure the QR File Transfer package is properly installed")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 