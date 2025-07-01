#!/usr/bin/env python3
"""
Test Runner for QR File Transfer Tool
Executes comprehensive automated testing suite with clean output.
"""

import os
import sys
import subprocess
import time

def main():
    """Main test runner"""
    print("🚀 QR File Transfer Tool - Automated Testing Suite")
    print("=" * 60)
    print("📋 Running comprehensive tests...")
    print("   • CLI Interface Tests")
    print("   • Core Workflow Tests (Generate → Scan → Rebuild)")
    print("   • Encryption/Decryption Tests")
    print("   • Edge Cases & Error Handling")
    print("   • Performance & Stress Tests")
    print("   • Security & Integrity Tests")
    print("=" * 60)
    
    # Check if test file exists
    test_file = "test_qr_tool.py"
    if not os.path.exists(test_file):
        print(f"❌ Test file '{test_file}' not found!")
        print("Please ensure the test file is in the current directory.")
        return 1
    
    # Run the test suite
    try:
        start_time = time.time()
        result = subprocess.run([
            sys.executable, test_file
        ], cwd=os.getcwd())
        end_time = time.time()
        
        print(f"\n⏱️ Total test execution time: {end_time - start_time:.1f} seconds")
        
        if result.returncode == 0:
            print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
            print("✅ QR File Transfer Tool is ready for production use!")
        else:
            print("⚠️ Some tests failed or had issues.")
            print("Please review the output above for details.")
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user.")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 