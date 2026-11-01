"""Command-line safety checks, without rerunning expensive plot generation."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from double_pendulum.cli import demo, main

class CliTests(unittest.TestCase):
    def test_nonempty_output_is_not_modified(self):
        with tempfile.TemporaryDirectory() as directory:
            marker=Path(directory)/'keep.txt'; marker.write_text('keep me')
            with self.assertRaisesRegex(ValueError,'not empty'):
                demo(directory)
            self.assertEqual(marker.read_text(),'keep me')
            self.assertEqual(list(Path(directory).iterdir()),[marker])
    def test_file_output_reports_error(self):
        with tempfile.NamedTemporaryFile() as existing:
            with patch('sys.argv',['pendulum-demo','--output',existing.name]), contextlib.redirect_stderr(io.StringIO()) as errors:
                with self.assertRaises(SystemExit) as result: main()
            self.assertEqual(result.exception.code,2)
            self.assertIn('Error:',errors.getvalue())
