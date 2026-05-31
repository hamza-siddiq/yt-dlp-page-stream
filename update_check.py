"""Optional pre-run update notifications (interactive sessions only)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.request import Request, urlopen

_CACHE_DIR = Path.home() / ".cache" / "yt-dlp-page-stream"
_CACHE_FILE = _CACHE_DIR / "last_check.json"
_CACHE_TTL = 24 * 60 * 60
_TIMEOUT = 3
_PKG_NAME = "yt-dlp-page-stream"
_GITHUB_REPO = "hamza-siddiq/yt-dlp-page-stream"
_GIT_INSTALL = (
    'pip install -U "git+https://github.com/hamza-siddiq/yt-dlp-page-stream.git"'
)


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes")


def _parse_version_parts(version: str) -> tuple:
    parts: List[int] = []
    for piece in re.split(r"[^0-9]+", version.lstrip("vV")):
        if piece:
            parts.append(int(piece))
    return tuple(parts) if parts else (0,)


def _version_lt(installed: str, latest: str) -> bool:
    return _parse_version_parts(installed) < _parse_version_parts(latest)


def _fetch_json(url: str) -> dict:
    req = Request(url, headers={"User-Agent": "yt-dlp-page-stream-update-check"})
    with urlopen(req, timeout=_TIMEOUT) as resp:
        return json.loads(resp.read().decode())


def _installed_version(dist_name: str) -> Optional[str]:
    try:
        from importlib.metadata import version

        return version(dist_name)
    except Exception:
        return None


def _pypi_latest_ytdlp() -> Optional[str]:
    try:
        data = _fetch_json("https://pypi.org/pypi/yt-dlp/json")
        return data.get("info", {}).get("version")
    except Exception:
        return None


def _github_latest_pkg() -> Optional[str]:
    try:
        data = _fetch_json(
            f"https://api.github.com/repos/{_GITHUB_REPO}/releases/latest"
        )
        tag = data.get("tag_name", "")
        if tag:
            return tag.lstrip("vV")
    except Exception:
        pass
    try:
        data = _fetch_json(f"https://api.github.com/repos/{_GITHUB_REPO}/tags")
        if isinstance(data, list) and data:
            tag = data[0].get("name", "")
            if tag:
                return tag.lstrip("vV")
    except Exception:
        pass
    return None


def _read_cache() -> Optional[dict]:
    try:
        if _CACHE_FILE.is_file():
            return json.loads(_CACHE_FILE.read_text())
    except Exception:
        pass
    return None


def _write_cache() -> None:
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _CACHE_FILE.write_text(json.dumps({"checked_at": time.time()}))
    except Exception:
        pass


def _cache_fresh() -> bool:
    cache = _read_cache()
    if not cache:
        return False
    checked = cache.get("checked_at", 0)
    return (time.time() - float(checked)) < _CACHE_TTL


def _pkg_root() -> Path:
    return Path(__file__).resolve().parent


def _is_git_clone() -> bool:
    return (_pkg_root() / ".git").is_dir()


def _run_pip_commands(commands: List[str]) -> None:
    from cli_ui import print_msg

    for cmd in commands:
        print_msg(f"Running: {cmd}", stderr=True, style="dim")
        subprocess.run(cmd, shell=True, check=False)


def _gather_updates() -> Tuple[List[str], List[str], bool]:
    """Return (messages, pip_commands, needs_git_pull)."""
    messages: List[str] = []
    pip_commands: List[str] = []
    needs_git_pull = False

    installed_ytdlp = _installed_version("yt-dlp")
    latest_ytdlp = _pypi_latest_ytdlp()
    if (
        installed_ytdlp
        and latest_ytdlp
        and _version_lt(installed_ytdlp, latest_ytdlp)
    ):
        messages.append(
            f"yt-dlp {installed_ytdlp} is outdated (latest on PyPI: {latest_ytdlp}).\n"
            "  pip install -U yt-dlp"
        )
        pip_commands.append("pip install -U yt-dlp")

    installed_pkg = _installed_version(_PKG_NAME)
    latest_pkg = _github_latest_pkg()
    if installed_pkg and latest_pkg and _version_lt(installed_pkg, latest_pkg):
        if _is_git_clone():
            needs_git_pull = True
            upgrade = "git pull && pip install -e ."
            pip_commands.append("pip install -e .")
        else:
            upgrade = _GIT_INSTALL
            pip_commands.append(_GIT_INSTALL)
        messages.append(
            f"{_PKG_NAME} {installed_pkg} is outdated (latest release: {latest_pkg}).\n"
            f"  {upgrade}"
        )

    return messages, pip_commands, needs_git_pull


def run_update_flow(*, force: bool, prompt: bool) -> int:
    """
    Check for updates. If prompt and updates exist, ask to upgrade.

    Returns 0 on success / nothing to do / user declined; 1 if TTY required but missing.
    """
    if force and not sys.stderr.isatty():
        print(
            "yt-dlp-ps --update requires an interactive terminal.",
            file=sys.stderr,
        )
        return 1

    if not force:
        if _env_truthy("YT_DLP_PAGE_STREAM_SKIP_UPDATE_CHECK"):
            return 0
        if not sys.stderr.isatty():
            return 0
        if _cache_fresh():
            return 0

    messages, pip_commands, needs_git_pull = _gather_updates()
    _write_cache()

    from cli_ui import confirm, get_console, print_msg

    if not messages:
        if force or prompt:
            print_msg("All up to date.", stderr=True, style="green")
        return 0

    body = "\n\n".join(messages)
    console = get_console(stderr=True)
    if console:
        from rich.panel import Panel

        console.print(
            Panel.fit(body, title="Updates available", border_style="yellow")
        )
    else:
        print("\nUpdates available:", file=sys.stderr)
        for msg in messages:
            print(msg, file=sys.stderr)
            print(file=sys.stderr)

    should_prompt = prompt or _env_truthy("YT_DLP_PAGE_STREAM_UPDATE_PROMPT")
    if should_prompt and pip_commands:
        if confirm("Upgrade now?", default=False):
            if needs_git_pull:
                print_msg(
                    "Run git pull in your clone first, then re-run --update if needed.",
                    stderr=True,
                    style="yellow",
                )
            _run_pip_commands(pip_commands)
        return 0

    return 0


def maybe_notify_updates() -> None:
    try:
        run_update_flow(force=False, prompt=False)
    except Exception:
        pass
