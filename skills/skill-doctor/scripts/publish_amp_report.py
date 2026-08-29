#!/usr/bin/env python3
"""Serve one HTML report through an Amp Portal and print its public URL."""

import argparse
import json
import socket
import subprocess
from pathlib import Path
from urllib.parse import quote, urlparse


DEFAULT_SERVICE = "skill-doctor-report"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_path", type=Path)
    parser.add_argument("--amp-cli", default="amp")
    parser.add_argument("--service-name", default=DEFAULT_SERVICE)
    return parser.parse_args(argv)


def available_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def run(command):
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )


def contains_exact_value(value, expected):
    if value == expected:
        return True
    if isinstance(value, dict):
        return any(contains_exact_value(item, expected) for item in value.values())
    if isinstance(value, list):
        return any(contains_exact_value(item, expected) for item in value)
    return False


def publish_report(report_path, amp_cli="amp", service_name=DEFAULT_SERVICE):
    report_path = report_path.expanduser().resolve()
    if not report_path.is_file():
        raise RuntimeError(f"report does not exist: {report_path}")

    port = available_port()
    run([
        amp_cli,
        "orb",
        "service",
        "start",
        service_name,
        "--command",
        'python3 -m http.server "$PORT" --bind 0.0.0.0',
        "--cwd",
        str(report_path.parent),
        "--port",
        str(port),
    ])

    internal_url = f"http://localhost:{port}/{quote(report_path.name)}"
    result = run([
        amp_cli,
        "orb",
        "portal",
        "--name",
        service_name,
        "--title",
        "Agent Skill Report",
        internal_url,
    ])
    public_url = result.stdout.strip()
    parsed = urlparse(public_url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        or "\n" in public_url
    ):
        raise RuntimeError("amp orb portal did not return one public HTTPS URL")

    manifest_path = Path(".amp") / "portals" / f"{service_name}.json"
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"could not verify portal manifest: {manifest_path}") from error
    if not contains_exact_value(manifest, public_url):
        raise RuntimeError(
            f"portal manifest does not contain the returned URL: {manifest_path}"
        )
    return public_url


def main(argv=None):
    args = parse_args(argv)
    print(publish_report(args.report_path, args.amp_cli, args.service_name))


if __name__ == "__main__":
    main()
