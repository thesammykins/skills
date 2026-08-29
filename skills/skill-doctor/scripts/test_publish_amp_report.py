#!/usr/bin/env python3
"""Tests for Amp Portal report publication."""

import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from publish_amp_report import main, publish_report


class AmpReportPublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.report = self.root / "report.html"
        self.report.write_text("<html><body>report</body></html>")
        self.previous_cwd = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, self.previous_cwd)

    def portal_side_effect(self, command, **kwargs):
        if command[1:4] == ["orb", "portal", "--name"]:
            public_url = "https://skill-doctor.example.onamp.dev/report.html"
            manifest = self.root / ".amp" / "portals" / "skill-doctor-report.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"url": public_url}))
            return subprocess.CompletedProcess(command, 0, public_url + "\n", "")
        return subprocess.CompletedProcess(command, 0, "", "")

    @patch("publish_amp_report.available_port", return_value=43123)
    @patch("publish_amp_report.subprocess.run")
    def test_starts_managed_server_and_returns_manifest_url(self, run, _port):
        run.side_effect = self.portal_side_effect

        output = io.StringIO()
        with redirect_stdout(output):
            main([str(self.report)])

        self.assertEqual(
            output.getvalue().strip(),
            "https://skill-doctor.example.onamp.dev/report.html",
        )
        service_command = run.call_args_list[0].args[0]
        portal_command = run.call_args_list[1].args[0]
        self.assertEqual(service_command[:5], ["amp", "orb", "service", "start", "skill-doctor-report"])
        self.assertIn('python3 -m http.server "$PORT" --bind 0.0.0.0', service_command)
        self.assertEqual(portal_command[:4], ["amp", "orb", "portal", "--name"])
        self.assertEqual(portal_command[-1], "http://localhost:43123/report.html")

    @patch("publish_amp_report.available_port", return_value=43123)
    @patch("publish_amp_report.subprocess.run")
    def test_rejects_loopback_portal_output(self, run, _port):
        run.side_effect = [
            subprocess.CompletedProcess([], 0, "", ""),
            subprocess.CompletedProcess([], 0, "http://127.0.0.1:43123/report.html\n", ""),
        ]

        with self.assertRaisesRegex(RuntimeError, "public HTTPS URL"):
            publish_report(self.report)

    @patch("publish_amp_report.available_port", return_value=43123)
    @patch("publish_amp_report.subprocess.run")
    def test_requires_exact_returned_url_in_manifest(self, run, _port):
        def mismatched_manifest(command, **kwargs):
            if command[1:4] == ["orb", "portal", "--name"]:
                manifest = self.root / ".amp" / "portals" / "skill-doctor-report.json"
                manifest.parent.mkdir(parents=True)
                manifest.write_text(json.dumps({"url": "https://other.onamp.dev/report.html"}))
                return subprocess.CompletedProcess(
                    command,
                    0,
                    "https://skill-doctor.example.onamp.dev/report.html\n",
                    "",
                )
            return subprocess.CompletedProcess(command, 0, "", "")

        run.side_effect = mismatched_manifest

        with self.assertRaisesRegex(RuntimeError, "does not contain the returned URL"):
            publish_report(self.report)


if __name__ == "__main__":
    unittest.main()
