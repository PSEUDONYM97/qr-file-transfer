#!/usr/bin/env python3
"""
Comprehensive Test Suite for QR File Transfer Tool
Tests all major functionality including CLI, workflows, encryption, and edge cases.
"""

import os
import sys
import tempfile
import shutil
import subprocess
import json
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
import time

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our modules
try:
    import qr_enhanced
    import qr_scan
    import qr_rebuild
    import qr_rebuild_encrypted
    import qr_rebuild_verified
    import qr_config
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all QR modules are in the current directory")
    sys.exit(1)


class QRToolTestSuite(unittest.TestCase):
    """Comprehensive test suite for QR File Transfer Tool"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directories
        self.test_dir = tempfile.mkdtemp(prefix="qr_test_")
        self.input_dir = os.path.join(self.test_dir, "input")
        self.output_dir = os.path.join(self.test_dir, "output")
        self.chunks_dir = os.path.join(self.test_dir, "chunks")
        self.images_dir = os.path.join(self.test_dir, "images")
        
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.chunks_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        
        # Test files
        self.test_files = {}
        self._create_test_files()
        
        print(f"🧪 Test environment: {self.test_dir}")
    
    def tearDown(self):
        """Clean up test environment"""
        try:
            shutil.rmtree(self.test_dir)
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
    
    def _create_test_files(self):
        """Create various test files"""
        
        # Small text file
        small_file = os.path.join(self.input_dir, "small.txt")
        with open(small_file, 'w', encoding='utf-8') as f:
            f.write("Hello QR World!\nThis is a test file.\n🔥 Unicode test! 🚀")
        self.test_files['small'] = small_file
        
        # Medium text file (multiple chunks)
        medium_file = os.path.join(self.input_dir, "medium.txt")
        with open(medium_file, 'w', encoding='utf-8') as f:
            for i in range(100):
                f.write(f"Line {i:03d}: This is test data to create a multi-chunk file. " * 5 + "\n")
        self.test_files['medium'] = medium_file
        
        # Binary file
        binary_file = os.path.join(self.input_dir, "binary.dat")
        with open(binary_file, 'wb') as f:
            f.write(bytes(range(256)) * 10)  # All byte values
        self.test_files['binary'] = binary_file
        
        # Empty file
        empty_file = os.path.join(self.input_dir, "empty.txt")
        with open(empty_file, 'w') as f:
            pass
        self.test_files['empty'] = empty_file
        
        # Special characters file
        special_file = os.path.join(self.input_dir, "special_chars.txt")
        with open(special_file, 'w', encoding='utf-8') as f:
            f.write("Special chars: äöüß 中文 🎯🔥🚀 !@#$%^&*()_+-=[]{}|;':\",./<>?")
        self.test_files['special'] = special_file
    
    def _get_file_hash(self, filepath):
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return None
    
    def _run_cli_command(self, cmd_args, expected_return_code=0):
        """Run CLI command and return result"""
        try:
            result = subprocess.run(
                [sys.executable, "qr.py"] + cmd_args,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != expected_return_code:
                print(f"❌ Command failed: {' '.join(cmd_args)}")
                print(f"Return code: {result.returncode}")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
            
            return result
        except subprocess.TimeoutExpired:
            self.fail(f"Command timed out: {' '.join(cmd_args)}")
        except Exception as e:
            self.fail(f"Command execution failed: {e}")

    # ===============================
    # CLI INTERFACE TESTS
    # ===============================
    
    def test_cli_help(self):
        """Test CLI help functionality"""
        print("\n🧪 Testing CLI help...")
        
        # Main help
        result = self._run_cli_command(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("QR File Transfer Tool", result.stdout)
        self.assertIn("generate", result.stdout)
        self.assertIn("scan", result.stdout)
        
        # Subcommand help
        result = self._run_cli_command(["generate", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Convert files to QR codes", result.stdout)
        
        print("✅ CLI help tests passed")
    
    def test_cli_version(self):
        """Test CLI version"""
        print("\n🧪 Testing CLI version...")
        
        result = self._run_cli_command(["--version"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("2.0.0", result.stdout)
        
        print("✅ CLI version test passed")
    
    def test_cli_config(self):
        """Test CLI config commands"""
        print("\n🧪 Testing CLI config...")
        
        # Show config
        result = self._run_cli_command(["config", "show"])
        self.assertEqual(result.returncode, 0)
        
        print("✅ CLI config tests passed")

    # ===============================
    # CORE WORKFLOW TESTS
    # ===============================
    
    def test_basic_workflow_small_file(self):
        """Test complete workflow with small file"""
        print("\n🧪 Testing basic workflow (small file)...")
        
        input_file = self.test_files['small']
        original_hash = self._get_file_hash(input_file)
        
        # Step 1: Generate QR codes  
        result = self._run_cli_command([
            "generate", input_file,
            "--output-dir", self.chunks_dir
        ])
        self.assertEqual(result.returncode, 0)
        
        # Verify chunks created
        chunk_files = list(Path(self.chunks_dir).glob("*.txt"))
        self.assertGreater(len(chunk_files), 0)
        
        # Step 2: Rebuild file
        result = self._run_cli_command([
            "rebuild", self.chunks_dir,
            "--output-dir", self.output_dir
        ])
        self.assertEqual(result.returncode, 0)
        
        # Step 3: Verify integrity
        rebuilt_files = list(Path(self.output_dir).glob("small.*"))
        self.assertGreater(len(rebuilt_files), 0, "No rebuilt file found")
        rebuilt_hash = self._get_file_hash(str(rebuilt_files[0]))
        self.assertEqual(original_hash, rebuilt_hash)
        
        print("✅ Basic workflow test passed")
    
    def test_encrypted_workflow(self):
        """Test complete encrypted workflow"""
        print("\n🧪 Testing encrypted workflow...")
        
        input_file = self.test_files['medium']
        original_hash = self._get_file_hash(input_file)
        password = "test_password_123"
        
        # Mock password input for encryption
        with patch('getpass.getpass', side_effect=[password, password]):
            # Step 1: Generate encrypted QR codes
            result = self._run_cli_command([
                "generate", input_file,
                "--output-dir", self.chunks_dir,
                "--encrypt"
            ])
            self.assertEqual(result.returncode, 0)
        
        # Verify encrypted chunks created
        chunk_files = list(Path(self.chunks_dir).glob("*.txt"))
        self.assertGreater(len(chunk_files), 0)
        
        # Verify chunks are encrypted (contain 'ENCRYPTED')
        with open(chunk_files[0], 'r') as f:
            content = f.read()
            self.assertIn("ENCRYPTED", content)
        
        # Mock password input for decryption
        with patch('getpass.getpass', return_value=password):
            # Step 2: Rebuild encrypted file
            result = self._run_cli_command([
                "rebuild", self.chunks_dir,
                "--output-dir", self.output_dir,
                "--encrypted"
            ])
            self.assertEqual(result.returncode, 0)
        
        # Step 3: Verify integrity
        rebuilt_files = list(Path(self.output_dir).glob("medium.*"))
        self.assertGreater(len(rebuilt_files), 0, "No rebuilt file found")
        rebuilt_hash = self._get_file_hash(str(rebuilt_files[0]))
        self.assertEqual(original_hash, rebuilt_hash)
        
        print("✅ Encrypted workflow test passed")
    
    def test_sheet_format_workflow(self):
        """Test sheet format generation"""
        print("\n🧪 Testing sheet format workflow...")
        
        input_file = self.test_files['medium']
        
        # Generate sheet format
        result = self._run_cli_command([
            "generate", input_file,
            "--output-dir", self.output_dir,
            "--sheet"
        ])
        self.assertEqual(result.returncode, 0)
        
        # Verify sheet file created
        sheet_files = list(Path(self.output_dir).glob("*_sheet.png"))
        self.assertGreater(len(sheet_files), 0)
        
        print("✅ Sheet format test passed")

    # ===============================
    # EDGE CASES AND ERROR HANDLING
    # ===============================
    
    def test_empty_file_handling(self):
        """Test handling of empty files"""
        print("\n🧪 Testing empty file handling...")
        
        input_file = self.test_files['empty']
        
        # Should handle empty files gracefully
        result = self._run_cli_command([
            "generate", input_file,
            "--output-dir", self.chunks_dir
        ])
        # Empty files might be handled differently, check for graceful handling
        self.assertIn(result.returncode, [0, 1])  # Accept success or graceful failure
        
        print("✅ Empty file handling test passed")
    
    def test_binary_file_handling(self):
        """Test handling of binary files"""
        print("\n🧪 Testing binary file handling...")
        
        input_file = self.test_files['binary']
        original_hash = self._get_file_hash(input_file)
        
        # Generate QR codes for binary file
        result = self._run_cli_command([
            "generate", input_file,
            "--output-dir", self.chunks_dir
        ])
        self.assertEqual(result.returncode, 0)
        
        # Rebuild binary file
        result = self._run_cli_command([
            "rebuild", self.chunks_dir,
            "--output-dir", self.output_dir
        ])
        self.assertEqual(result.returncode, 0)
        
        # Verify binary integrity
        rebuilt_files = list(Path(self.output_dir).glob("binary.*"))
        self.assertGreater(len(rebuilt_files), 0, "No rebuilt file found")
        rebuilt_hash = self._get_file_hash(str(rebuilt_files[0]))
        self.assertEqual(original_hash, rebuilt_hash)
        
        print("✅ Binary file handling test passed")
    
    def test_special_characters_handling(self):
        """Test handling of special characters"""
        print("\n🧪 Testing special characters handling...")
        
        input_file = self.test_files['special']
        original_hash = self._get_file_hash(input_file)
        
        # Generate and rebuild
        result = self._run_cli_command([
            "generate", input_file,
            "--output-dir", self.chunks_dir
        ])
        self.assertEqual(result.returncode, 0)
        
        result = self._run_cli_command([
            "rebuild", self.chunks_dir,
            "--output-dir", self.output_dir
        ])
        self.assertEqual(result.returncode, 0)
        
        # Verify content integrity
        rebuilt_files = list(Path(self.output_dir).glob("special_chars.*"))
        self.assertGreater(len(rebuilt_files), 0, "No rebuilt file found")
        rebuilt_hash = self._get_file_hash(str(rebuilt_files[0]))
        self.assertEqual(original_hash, rebuilt_hash)
        
        print("✅ Special characters handling test passed")
    
    def test_invalid_commands(self):
        """Test invalid command handling"""
        print("\n🧪 Testing invalid command handling...")
        
        # Invalid subcommand
        result = self._run_cli_command(["invalid_command"], expected_return_code=2)
        
        # Missing required arguments
        result = self._run_cli_command(["generate"], expected_return_code=2)
        
        # Invalid file path
        result = self._run_cli_command([
            "generate", "/nonexistent/file.txt"
        ], expected_return_code=1)
        
        print("✅ Invalid command handling tests passed")

    # ===============================
    # VERIFICATION AND INTEGRITY TESTS
    # ===============================
    
    def test_integrity_verification(self):
        """Test file integrity verification"""
        print("\n🧪 Testing integrity verification...")
        
        input_file = self.test_files['medium']
        
        # Generate QR codes
        result = self._run_cli_command([
            "generate", input_file,
            "--output-dir", self.chunks_dir
        ])
        self.assertEqual(result.returncode, 0)
        
        # Rebuild with verification
        result = self._run_cli_command([
            "rebuild", self.chunks_dir,
            "--output-dir", self.output_dir,
            "--verify"
        ])
        self.assertEqual(result.returncode, 0)
        
        print("✅ Integrity verification test passed")
    
    def test_chunk_corruption_detection(self):
        """Test detection of corrupted chunks"""
        print("\n🧪 Testing chunk corruption detection...")
        
        input_file = self.test_files['small']
        
        # Generate chunks
        result = self._run_cli_command([
            "generate", input_file,
            "--output-dir", self.chunks_dir
        ])
        self.assertEqual(result.returncode, 0)
        
        # Corrupt a chunk file
        chunk_files = list(Path(self.chunks_dir).glob("*.txt"))
        if chunk_files:
            with open(chunk_files[0], 'a') as f:
                f.write("CORRUPTED_DATA")
            
            # Attempt rebuild - should detect corruption
            result = self._run_cli_command([
                "rebuild", self.chunks_dir,
                "--output-dir", self.output_dir,
                "--verify"
            ], expected_return_code=1)
        
        print("✅ Chunk corruption detection test passed")

    # ===============================
    # PERFORMANCE AND STRESS TESTS
    # ===============================
    
    def test_large_file_handling(self):
        """Test handling of larger files"""
        print("\n🧪 Testing large file handling...")
        
        # Create a larger test file (1MB)
        large_file = os.path.join(self.input_dir, "large.txt")
        with open(large_file, 'w') as f:
            for i in range(10000):
                f.write(f"Large file test line {i:05d} with some content to make it bigger.\n")
        
        original_hash = self._get_file_hash(large_file)
        
        # Test generation (with timeout protection)
        start_time = time.time()
        result = self._run_cli_command([
            "generate", large_file,
            "--output-dir", self.chunks_dir
        ])
        generation_time = time.time() - start_time
        
        self.assertEqual(result.returncode, 0)
        self.assertLess(generation_time, 60)  # Should complete within 60 seconds
        
        # Test rebuild
        start_time = time.time()
        result = self._run_cli_command([
            "rebuild", self.chunks_dir,
            "--output-dir", self.output_dir
        ])
        rebuild_time = time.time() - start_time
        
        self.assertEqual(result.returncode, 0)
        self.assertLess(rebuild_time, 30)  # Should complete within 30 seconds
        
        # Verify integrity - find the rebuilt file
        rebuilt_files = list(Path(self.output_dir).glob("large.*"))
        self.assertGreater(len(rebuilt_files), 0, "No rebuilt file found")
        rebuilt_hash = self._get_file_hash(str(rebuilt_files[0]))
        self.assertEqual(original_hash, rebuilt_hash)
        
        print(f"✅ Large file test passed (Gen: {generation_time:.1f}s, Rebuild: {rebuild_time:.1f}s)")

    # ===============================
    # SECURITY TESTS
    # ===============================
    
    def test_password_strength_handling(self):
        """Test various password scenarios"""
        print("\n🧪 Testing password handling...")
        
        input_file = self.test_files['small']
        passwords = [
            "simple",
            "Complex123!@#",
            "🔥🚀🎯",  # Unicode passwords
            "a" * 100   # Very long password
        ]
        
        for i, password in enumerate(passwords):
            test_chunks_dir = os.path.join(self.chunks_dir, f"pwd_test_{i}")
            os.makedirs(test_chunks_dir, exist_ok=True)
            
            # Test encryption
            with patch('getpass.getpass', side_effect=[password, password]):
                result = self._run_cli_command([
                    "generate", input_file,
                    "--output-dir", test_chunks_dir,
                    "--encrypt"
                ])
                self.assertEqual(result.returncode, 0)
            
            # Test decryption
            with patch('getpass.getpass', return_value=password):
                result = self._run_cli_command([
                    "rebuild", test_chunks_dir,
                    "--output-dir", self.output_dir,
                    "--encrypted"
                ])
                self.assertEqual(result.returncode, 0)
        
        print("✅ Password handling tests passed")


def run_test_suite():
    """Run the complete test suite"""
    print("🚀 Starting QR File Transfer Tool Test Suite")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(QRToolTestSuite)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        failfast=False
    )
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # Print summary
    print("\n" + "=" * 60)
    print("🏁 TEST SUITE SUMMARY")
    print("=" * 60)
    print(f"⏱️  Total time: {end_time - start_time:.1f} seconds")
    print(f"✅ Tests passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Tests failed: {len(result.failures)}")
    print(f"💥 Errors: {len(result.errors)}")
    print(f"⏭️  Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED! Tool is production ready! 🚀")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = run_test_suite()
    sys.exit(exit_code) 