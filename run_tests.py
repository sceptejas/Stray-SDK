#!/usr/bin/env python3
"""
Test runner script for Stray-SDK payment validation tests.
Provides comprehensive testing with coverage reporting.
"""
import sys
import subprocess
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def main():
    """Main test runner function."""
    # Change to the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print("Stray-SDK Test Runner")
    print("=" * 60)
    
    # Test commands to run
    test_commands = [
        {
            "cmd": [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            "desc": "Run all tests with verbose output"
        },
        {
            "cmd": [sys.executable, "-m", "pytest", "tests/test_validators.py", "-v"],
            "desc": "Run validator tests specifically"
        },
        {
            "cmd": [sys.executable, "-m", "pytest", "tests/test_client.py", "-v"],
            "desc": "Run client tests specifically"
        },
        {
            "cmd": [sys.executable, "-m", "pytest", "tests/test_cli.py", "-v"],
            "desc": "Run CLI tests specifically"
        },
        {
            "cmd": [sys.executable, "-m", "pytest", "tests/", "--cov=stellar_agent", "--cov-report=term-missing", "--cov-report=html"],
            "desc": "Run tests with coverage report"
        }
    ]
    
    # Run each test command
    all_passed = True
    for test_cmd in test_commands:
        success = run_command(test_cmd["cmd"], test_cmd["desc"])
        if not success:
            all_passed = False
            print(f"Failed: {test_cmd['desc']}")
    
    # Summary
    print(f"\n{'='*60}")
    if all_passed:
        print("✅ All tests passed successfully!")
        exit_code = 0
    else:
        print("❌ Some tests failed!")
        exit_code = 1
    
    print("="*60)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
