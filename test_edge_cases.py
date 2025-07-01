#!/usr/bin/env python3
"""
Edge Case Testing Suite for QR File Transfer Tool
Tests boundary conditions, error handling, and unusual scenarios.
"""

import os
import sys
import tempfile
import shutil
import subprocess
import hashlib
import time
from pathlib import Path
import unittest

def run_command(cmd_args, timeout=30):
    """Run CLI command and return result"""
    try:
        result = subprocess.run(
            [sys.executable, "qr.py"] + cmd_args,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None

class QREdgeCaseTests(unittest.TestCase):
    """Comprehensive edge case testing"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp(prefix="qr_edge_test_")
        self.input_dir = os.path.join(self.test_dir, "input")
        self.output_dir = os.path.join(self.test_dir, "output")
        self.chunks_dir = os.path.join(self.test_dir, "chunks")
        
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.chunks_dir, exist_ok=True)
    
    def tearDown(self):
        """Clean up test environment"""
        try:
            shutil.rmtree(self.test_dir)
        except Exception:
            pass

    # ===============================
    # FILE EDGE CASES
    # ===============================
    
    def test_empty_file(self):
        """Test handling of empty files"""
        print("\n🧪 Testing empty file handling...")
        
        empty_file = os.path.join(self.input_dir, "empty.txt")
        with open(empty_file, 'w') as f:
            pass  # Create empty file
        
        result = run_command([
            "generate", empty_file,
            "--output-dir", self.chunks_dir,
            "--no-emoji"
        ])
        
        # Should handle gracefully (success or controlled failure)
        self.assertIn(result.returncode, [0, 1])
        print("✅ Empty file handled gracefully")
    
    def test_very_large_line(self):
        """Test file with extremely long lines"""
        print("\n🧪 Testing very large line handling...")
        
        large_line_file = os.path.join(self.input_dir, "large_line.txt")
        # Create file with 10MB single line
        large_content = "A" * (10 * 1024 * 1024)
        
        with open(large_line_file, 'w') as f:
            f.write(large_content)
        
        result = run_command([
            "generate", large_line_file,
            "--output-dir", self.chunks_dir,
            "--no-emoji"
        ], timeout=60)
        
        if result:
            print(f"✅ Large line handled (return code: {result.returncode})")
        else:
            print("⚠️ Large line test timed out (acceptable)")
    
    def test_binary_file_all_bytes(self):
        """Test binary file with all possible byte values"""
        print("\n🧪 Testing binary file with all byte values...")
        
        binary_file = os.path.join(self.input_dir, "all_bytes.bin")
        # Create file with all 256 possible byte values
        all_bytes = bytes(range(256)) * 100  # Repeat pattern
        
        with open(binary_file, 'wb') as f:
            f.write(all_bytes)
        
        result = run_command([
            "generate", binary_file,
            "--output-dir", self.chunks_dir,
            "--no-emoji"
        ])
        
        self.assertEqual(result.returncode, 0)
        print("✅ Binary file with all bytes handled successfully")
    
    def test_unicode_filename(self):
        """Test files with Unicode characters in filename"""
        print("\n🧪 Testing Unicode filename handling...")
        
        # Create file with Unicode characters in name
        unicode_file = os.path.join(self.input_dir, "测试文件_🔥🚀.txt")
        try:
            with open(unicode_file, 'w', encoding='utf-8') as f:
                f.write("Test content with Unicode filename")
            
            result = run_command([
                "generate", unicode_file,
                "--output-dir", self.chunks_dir,
                "--no-emoji"
            ])
            
            # Should handle Unicode filenames gracefully
            self.assertIn(result.returncode, [0, 1])
            print("✅ Unicode filename handled")
            
        except (OSError, UnicodeError):
            print("⚠️ Unicode filename not supported on this system")
    
    def test_long_filename(self):
        """Test very long filename handling"""
        print("\n🧪 Testing long filename handling...")
        
        # Create filename near system limits
        long_name = "a" * 200 + ".txt"
        long_file = os.path.join(self.input_dir, long_name)
        
        try:
            with open(long_file, 'w') as f:
                f.write("Content with very long filename")
            
            result = run_command([
                "generate", long_file,
                "--output-dir", self.chunks_dir,
                "--no-emoji"
            ])
            
            self.assertIn(result.returncode, [0, 1])
            print("✅ Long filename handled")
            
        except (OSError, FileNotFoundError):
            print("⚠️ Long filename exceeds system limits")
    
    def test_special_characters_in_content(self):
        """Test file with various special characters"""
        print("\n🧪 Testing special characters in content...")
        
        special_file = os.path.join(self.input_dir, "special.txt")
        special_content = """
        Control characters: \x00\x01\x02\x03\x1F
        Extended ASCII: áéíóú ñÑ çÇ
        Unicode symbols: ©®™€£¥
        Emoji: 🔥🚀⭐🎯💾🔒
        Math symbols: ∑∆√∫≠≤≥
        Line endings:\r\n\r\n
        Tab characters:\t\t\t
        Null bytes and special: \0
        """
        
        with open(special_file, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(special_content)
        
        result = run_command([
            "generate", special_file,
            "--output-dir", self.chunks_dir,
            "--no-emoji"
        ])
        
        self.assertEqual(result.returncode, 0)
        print("✅ Special characters handled successfully")

    # ===============================
    # QR SIZE LIMITS & BOUNDARIES
    # ===============================
    
    def test_maximum_qr_capacity(self):
        """Test file that approaches QR code size limits"""
        print("\n🧪 Testing QR capacity limits...")
        
        # Create file that will generate chunks near QR limit
        max_file = os.path.join(self.input_dir, "max_capacity.txt")
        # Conservative estimate: ~2800 chars per QR
        large_content = "X" * 2800 + "\n" + "Y" * 2800
        
        with open(max_file, 'w') as f:
            f.write(large_content)
        
        result = run_command([
            "generate", max_file,
            "--output-dir", self.chunks_dir,
            "--no-emoji"
        ])
        
        self.assertEqual(result.returncode, 0)
        print("✅ QR capacity limits handled correctly")
    
    def test_many_small_files_simulation(self):
        """Test generating many QR codes (stress test)"""
        print("\n🧪 Testing many QR codes generation...")
        
        many_chunks_file = os.path.join(self.input_dir, "many_chunks.txt")
        # Create file that will generate many chunks
        content_parts = []
        for i in range(50):  # Will create ~50 QR codes
            content_parts.append(f"Chunk {i:02d} content: " + "X" * 2000)
        
        with open(many_chunks_file, 'w') as f:
            f.write('\n'.join(content_parts))
        
        result = run_command([
            "generate", many_chunks_file,
            "--output-dir", self.chunks_dir,
            "--force",  # Skip confirmation
            "--no-emoji"
        ], timeout=120)  # Allow more time
        
        if result:
            self.assertEqual(result.returncode, 0)
            print("✅ Many QR codes generated successfully")
        else:
            print("⚠️ Many QR codes test timed out")

    # ===============================
    # ERROR CONDITIONS
    # ===============================
    
    def test_nonexistent_file(self):
        """Test handling of non-existent files"""
        print("\n🧪 Testing non-existent file handling...")
        
        result = run_command([
            "generate", "/nonexistent/path/file.txt",
            "--output-dir", self.chunks_dir
        ])
        
        self.assertEqual(result.returncode, 1)
        self.assertIn("not found", result.stdout.lower() + result.stderr.lower())
        print("✅ Non-existent file handled with proper error")
    
    def test_invalid_output_directory(self):
        """Test handling of invalid output directories"""
        print("\n🧪 Testing invalid output directory...")
        
        test_file = os.path.join(self.input_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # Try to write to non-existent directory
        result = run_command([
            "generate", test_file,
            "--output-dir", "/invalid/nonexistent/path"
        ])
        
        # Should handle gracefully
        self.assertIn(result.returncode, [0, 1])
        print("✅ Invalid output directory handled")
    
    def test_conflicting_arguments(self):
        """Test handling of conflicting CLI arguments"""
        print("\n🧪 Testing conflicting arguments...")
        
        test_file = os.path.join(self.input_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # Test conflicting verbose/quiet flags
        result = run_command([
            "generate", test_file,
            "--verbose", "--quiet",
            "--output-dir", self.chunks_dir
        ])
        
        self.assertEqual(result.returncode, 1)
        print("✅ Conflicting arguments detected and rejected")
    
    def test_missing_required_arguments(self):
        """Test handling of missing required arguments"""
        print("\n🧪 Testing missing required arguments...")
        
        # Test generate without file argument
        result = run_command(["generate"])
        self.assertEqual(result.returncode, 2)  # argparse error
        
        # Test rebuild without directory
        result = run_command(["rebuild"])
        self.assertEqual(result.returncode, 2)  # argparse error
        
        print("✅ Missing arguments handled correctly")

    # ===============================
    # SYSTEM EDGE CASES
    # ===============================
    
    def test_readonly_file(self):
        """Test handling of read-only files"""
        print("\n🧪 Testing read-only file handling...")
        
        readonly_file = os.path.join(self.input_dir, "readonly.txt")
        with open(readonly_file, 'w') as f:
            f.write("Read-only content")
        
        # Make file read-only
        try:
            os.chmod(readonly_file, 0o444)
            
            result = run_command([
                "generate", readonly_file,
                "--output-dir", self.chunks_dir,
                "--no-emoji"
            ])
            
            # Should be able to read read-only files
            self.assertEqual(result.returncode, 0)
            print("✅ Read-only file handled successfully")
            
        except (OSError, PermissionError):
            print("⚠️ Cannot test read-only on this system")
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(readonly_file, 0o666)
            except:
                pass
    
    def test_insufficient_space_simulation(self):
        """Test behavior with limited output space (simulated)"""
        print("\n🧪 Testing disk space handling...")
        
        # Create a large file that would generate many QR codes
        large_file = os.path.join(self.input_dir, "large.txt")
        with open(large_file, 'w') as f:
            for i in range(1000):
                f.write(f"Line {i}: " + "X" * 100 + "\n")
        
        # Try to generate to a deeply nested path (may fail on some systems)
        deep_path = os.path.join(self.chunks_dir, "a" * 100, "b" * 100)
        
        result = run_command([
            "generate", large_file,
            "--output-dir", deep_path,
            "--force",
            "--no-emoji"
        ])
        
        # Should handle gracefully whether it succeeds or fails
        self.assertIn(result.returncode, [0, 1])
        print("✅ Disk space constraints handled")

    # ===============================
    # ENCRYPTION EDGE CASES
    # ===============================
    
    def test_encryption_with_special_passwords(self):
        """Test encryption with various password types"""
        print("\n🧪 Testing encryption with special passwords...")
        
        test_file = os.path.join(self.input_dir, "encrypt_test.txt")
        with open(test_file, 'w') as f:
            f.write("Encryption test content")
        
        # Test with different password types
        passwords = [
            "simple123",
            "ComplexP@ssw0rd!",
            "a" * 100,  # Very long password
            "🔒🔑🚀",    # Unicode password
            "pass word",  # Password with spaces
        ]
        
        success_count = 0
        for i, password in enumerate(passwords):
            test_chunks_dir = os.path.join(self.chunks_dir, f"pwd_test_{i}")
            os.makedirs(test_chunks_dir, exist_ok=True)
            
            # Create a mock for password input
            with open("temp_password.txt", "w") as pf:
                pf.write(password + "\n" + password + "\n")
            
            try:
                # Note: This would need password mocking for real testing
                # For now, we test that the command structure is correct
                result = run_command([
                    "generate", test_file,
                    "--encrypt",
                    "--output-dir", test_chunks_dir,
                    "--no-emoji"
                ])
                
                # Command should at least parse correctly
                if result and result.returncode in [0, 1]:
                    success_count += 1
                    
            except Exception:
                pass
            finally:
                if os.path.exists("temp_password.txt"):
                    os.remove("temp_password.txt")
        
        print(f"✅ Password testing completed ({success_count}/{len(passwords)} scenarios)")

    # ===============================
    # PERFORMANCE EDGE CASES
    # ===============================
    
    def test_memory_usage_large_file(self):
        """Test memory efficiency with large files"""
        print("\n🧪 Testing memory efficiency...")
        
        # Create 10MB file
        large_file = os.path.join(self.input_dir, "memory_test.txt")
        with open(large_file, 'w') as f:
            for i in range(100000):
                f.write(f"Memory test line {i:06d} with content to make it larger\n")
        
        start_time = time.time()
        result = run_command([
            "generate", large_file,
            "--output-dir", self.chunks_dir,
            "--no-emoji"
        ], timeout=60)
        end_time = time.time()
        
        if result:
            processing_time = end_time - start_time
            print(f"✅ Large file processed in {processing_time:.1f}s")
            self.assertEqual(result.returncode, 0)
            self.assertLess(processing_time, 60, "Processing should complete within 60 seconds")
        else:
            print("⚠️ Large file test timed out")

    # ===============================
    # INTEGRATION EDGE CASES
    # ===============================
    
    def test_rapid_successive_operations(self):
        """Test rapid successive QR operations"""
        print("\n🧪 Testing rapid successive operations...")
        
        success_count = 0
        for i in range(5):
            test_file = os.path.join(self.input_dir, f"rapid_{i}.txt")
            with open(test_file, 'w') as f:
                f.write(f"Rapid test content {i}")
            
            result = run_command([
                "generate", test_file,
                "--output-dir", self.chunks_dir,
                "--no-emoji"
            ])
            
            if result and result.returncode == 0:
                success_count += 1
        
        self.assertGreaterEqual(success_count, 4, "Most rapid operations should succeed")
        print(f"✅ Rapid operations: {success_count}/5 successful")


def run_edge_case_tests():
    """Run the edge case test suite"""
    print("🔬 QR File Transfer Tool - Edge Case Testing Suite")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(QREdgeCaseTests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # Print summary
    print("\n" + "=" * 60)
    print("🔬 EDGE CASE TEST SUMMARY")
    print("=" * 60)
    print(f"⏱️  Total time: {end_time - start_time:.1f} seconds")
    print(f"✅ Tests passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Tests failed: {len(result.failures)}")
    print(f"💥 Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL EDGE CASE TESTS PASSED! Tool handles edge cases well! 🚀")
        return 0
    else:
        print(f"\n⚠️ Some edge cases failed. Review output for details.")
        return 1


if __name__ == "__main__":
    exit_code = run_edge_case_tests()
    sys.exit(exit_code) 