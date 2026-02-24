"""Tests for example scripts."""
import pytest
import os
from pathlib import Path

class TestExamples:
    """Test example scripts exist and are valid."""

    def test_examples_directory_exists(self):
        """Test examples directory exists."""
        examples_dir = Path("examples")
        assert examples_dir.exists()
        assert examples_dir.is_dir()

    def test_send_payment_example_exists(self):
        """Test send_payment.py exists."""
        example_file = Path("examples/send_payment.py")
        assert example_file.exists()
        assert example_file.is_file()

    def test_check_balance_example_exists(self):
        """Test check_balance.py exists."""
        example_file = Path("examples/check_balance.py")
        assert example_file.exists()

    def test_batch_payments_example_exists(self):
        """Test batch_payments.py exists."""
        example_file = Path("examples/batch_payments.py")
        assert example_file.exists()

    def test_examples_readme_exists(self):
        """Test examples README exists."""
        readme = Path("examples/README.md")
        assert readme.exists()
        assert readme.stat().st_size > 0

    def test_examples_are_executable(self):
        """Test example files contain valid Python."""
        examples = [
            "examples/send_payment.py",
            "examples/check_balance.py",
            "examples/batch_payments.py",
        ]
        for example in examples:
            with open(example, 'r') as f:
                content = f.read()
                assert 'def main()' in content
                assert 'if __name__ == "__main__"' in content
