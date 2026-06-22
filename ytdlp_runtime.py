"""Resolve and run the system yt-dlp binary (Homebrew-first)."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

_PKG_ROOT = Path(__file__).resolve().parent
_VERSION_RE = re.compile(r"(20\d{2}\.\d{1,2}\.\d{1,2})")


def package_root() -> Path:
    return _PKG_ROOT


def plugin_pythonpath() -> str:
    root = str(_PKG_ROOT)
    existing = os.environ.get("PYTHONPATH", "")
    if existing:
        parts = existing.split(os.pathsep)
        if root in parts:
            return existing
        return f"{root}{os.pathsep}{existing}"
    return root


def _pip_ytdlp_installed() -> bool:
    try:
        from importlib.metadata import version

        version("yt-dlp")
        return True
    except Exception:
        return False


def brew_ytdlp_binary() -> Optional[str]:
    brew = shutil.which("brew")
    if not brew:
        return None
    try:
        result = subprocess.run(
            [brew, "--prefix", "yt-dlp"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    prefix = result.stdout.strip()
    if not prefix:
        return None
    candidate = Path(prefix) / "bin" / "yt-dlp"
    return str(candidate) if candidate.is_file() else None


def resolve_ytdlp_binary() -> Optional[str]:
    override = os.environ.get("YT_DLP_PAGE_STREAM_YTDLP", "").strip()
    if override:
        path = Path(override).expanduser()
        if path.is_file():
            return str(path.resolve())
        found = shutil.which(override)
        if found:
            return found

    brew_bin = brew_ytdlp_binary()
    if brew_bin:
        return brew_bin

    for name in ("yt-dlp", "youtube-dl"):
        found = shutil.which(name)
        if found:
            return found

    return None


def parse_ytdlp_version(text: str) -> Optional[str]:
    match = _VERSION_RE.search(text)
    if not match:
        return None
    return match.group(1)


def ytdlp_version(binary: Optional[str] = None) -> Optional[str]:
    binary = binary or resolve_ytdlp_binary()
    if not binary:
        if _pip_ytdlp_installed():
            try:
                from importlib.metadata import version

                return version("yt-dlp")
            except Exception:
                pass
        return None
    try:
        result = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return parse_ytdlp_version(result.stdout or result.stderr)


def remove_pip_ytdlp(*, quiet: bool = False) -> bool:
    """Uninstall pip yt-dlp when a separate binary (e.g. Homebrew) is in use."""
    if not _pip_ytdlp_installed():
        return False
    if resolve_ytdlp_binary() is None:
        return False
    argv = [sys.executable, "-m", "pip", "uninstall", "-y", "yt-dlp"]
    result = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 and not quiet:
        err = (result.stderr or result.stdout or "").strip()
        if err:
            print(err, file=sys.stderr)
    return result.returncode == 0


def exec_ytdlp(argv: list[str]) -> None:
    binary = resolve_ytdlp_binary()
    if binary:
        env = os.environ.copy()
        env["PYTHONPATH"] = plugin_pythonpath()
        remove_pip_ytdlp(quiet=True)
        os.execve(binary, [binary, *argv[1:]], env)

    try:
        from yt_dlp import main as ytdlp_main
    except ImportError:
        print(
            "yt-dlp is not installed.\n"
            "Install with Homebrew: brew install yt-dlp\n"
            "Or set YT_DLP_PAGE_STREAM_YTDLP to your yt-dlp binary path.",
            file=sys.stderr,
        )
        sys.exit(1)
    ytdlp_main()
