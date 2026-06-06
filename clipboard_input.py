"""Read URLs from the system clipboard (stdlib only, no extra dependencies)."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys


def parse_url_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _run_clipboard_command(cmd: list[str]) -> str | None:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def read_clipboard_text() -> str:
    system = platform.system()
    if system == "Darwin":
        text = _run_clipboard_command(["pbpaste"])
        if text is not None:
            return text
    elif system == "Windows":
        text = _run_clipboard_command(
            ["powershell", "-NoProfile", "-Command", "Get-Clipboard"]
        )
        if text is not None:
            return text
    else:
        for cmd in (
            ["xclip", "-o", "-selection", "clipboard"],
            ["xsel", "--clipboard", "--output"],
        ):
            if shutil.which(cmd[0]):
                text = _run_clipboard_command(cmd)
                if text is not None:
                    return text

    raise RuntimeError(
        "Could not read the system clipboard on this platform. "
        "On Linux, install xclip or xsel; on macOS use pbpaste; "
        "on Windows use PowerShell Get-Clipboard."
    )


def read_clipboard_urls() -> list[str]:
    text = read_clipboard_text()
    urls = parse_url_lines(text)
    if not urls:
        raise RuntimeError("Clipboard is empty or contains no URLs.")
    return urls
