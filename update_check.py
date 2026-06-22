"""Optional pre-run update notifications (interactive sessions only)."""

from __future__ import annotations

import json
import os
import re
import ssl
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Tuple
from urllib.request import Request, urlopen

from ytdlp_runtime import (
    brew_ytdlp_binary,
    remove_pip_ytdlp,
    resolve_ytdlp_binary,
    ytdlp_version,
)

_CACHE_DIR = Path.home() / ".cache" / "yt-dlp-page-stream"
_CACHE_FILE = _CACHE_DIR / "last_check.json"
_CACHE_TTL = 24 * 60 * 60
_TIMEOUT = 10
_PKG_NAME = "yt-dlp-page-stream"
_GITHUB_REPO = "hamza-siddiq/yt-dlp-page-stream"
_GIT_URL = f"git+https://github.com/{_GITHUB_REPO}.git"


class _UpgradeStep(NamedTuple):
    display: str
    argv: List[str]
    cwd: Optional[Path] = None


def _pip_argv(*args: str) -> List[str]:
    return [sys.executable, "-m", "pip", *args]


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


def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _fetch_json(url: str) -> dict:
    headers = {
        "User-Agent": "yt-dlp-page-stream-update-check",
        "Accept": "application/json",
    }
    req = Request(url, headers=headers)
    with urlopen(req, timeout=_TIMEOUT, context=_ssl_context()) as resp:
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


def _github_pyproject_version(branch: str = "main") -> Optional[str]:
    url = f"https://raw.githubusercontent.com/{_GITHUB_REPO}/{branch}/pyproject.toml"
    try:
        req = Request(
            url,
            headers={
                "User-Agent": "yt-dlp-page-stream-update-check",
                "Accept": "text/plain",
            },
        )
        with urlopen(req, timeout=_TIMEOUT, context=_ssl_context()) as resp:
            text = resp.read().decode()
        match = re.search(
            r'^version\s*=\s*["\']([^"\']+)["\']',
            text,
            re.MULTILINE,
        )
        if match:
            return match.group(1).strip()
    except Exception:
        pass
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
    return _github_pyproject_version("main")


def _read_cache() -> Optional[dict]:
    try:
        if _CACHE_FILE.is_file():
            return json.loads(_CACHE_FILE.read_text())
    except Exception:
        pass
    return None


def _cached_remote_latest() -> Dict[str, str]:
    cache = _read_cache()
    if not cache:
        return {}
    remote = cache.get("remote")
    if isinstance(remote, dict):
        out: Dict[str, str] = {}
        for key in ("pkg", "ytdlp"):
            val = remote.get(key)
            if isinstance(val, str) and val:
                out[key] = val
        return out
    return {}


def _write_cache(
    installed: Optional[Dict[str, Optional[str]]] = None,
    *,
    remote: Optional[Dict[str, str]] = None,
) -> None:
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        prev = _read_cache() or {}
        data: Dict[str, Any] = {"checked_at": time.time()}
        if installed is not None:
            data["installed"] = installed
        elif prev.get("installed"):
            data["installed"] = prev["installed"]
        if remote:
            merged = dict(prev.get("remote") or {})
            merged.update({k: v for k, v in remote.items() if v})
            data["remote"] = merged
        elif prev.get("remote"):
            data["remote"] = prev["remote"]
        _CACHE_FILE.write_text(json.dumps(data))
    except Exception:
        pass


def _last_installed_from_cache() -> Dict[str, Optional[str]]:
    cache = _read_cache()
    if not cache:
        return {}
    installed = cache.get("installed")
    if isinstance(installed, dict):
        return installed
    return {}


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


def get_version_lines() -> List[str]:
    lines: List[str] = []
    installed_pkg = _installed_version(_PKG_NAME)
    lines.append(
        f"yt-dlp-page-stream {installed_pkg or 'unknown'}"
    )
    installed_ytdlp = ytdlp_version()
    ytdlp_bin = resolve_ytdlp_binary()
    if installed_ytdlp and ytdlp_bin:
        lines.append(f"yt-dlp {installed_ytdlp} ({ytdlp_bin})")
    else:
        lines.append(f"yt-dlp {installed_ytdlp or 'not installed'}")
    return lines


def print_version_info() -> None:
    from cli_ui import print_msg

    for line in get_version_lines():
        print_msg(line)


def _version_snapshot() -> Dict[str, Optional[str]]:
    return {
        "pkg": _installed_version(_PKG_NAME),
        "ytdlp": ytdlp_version(),
    }


def _ytdlp_upgrade_step() -> _UpgradeStep:
    if brew_ytdlp_binary():
        return _UpgradeStep("brew upgrade yt-dlp", ["brew", "upgrade", "yt-dlp"])
    return _UpgradeStep("pip install -U yt-dlp", _pip_argv("install", "-U", "yt-dlp"))


def _run_upgrade_steps(
    steps: List[_UpgradeStep], before: Dict[str, Optional[str]]
) -> Dict[str, Optional[str]]:
    from cli_ui import get_console, print_msg, run_with_status

    console = get_console(stderr=True)
    failed: List[str] = []

    for step in steps:

        def execute(s: _UpgradeStep = step) -> subprocess.CompletedProcess:
            return subprocess.run(
                s.argv,
                cwd=str(s.cwd) if s.cwd else None,
                check=False,
            )

        label = f"[bold cyan]Running:[/] {step.display}"
        if console:
            holder: List[subprocess.CompletedProcess] = []

            def run_wrapped(s: _UpgradeStep = step) -> None:
                holder.append(execute(s))

            run_with_status(label, run_wrapped)
            result = holder[0]
        else:
            print_msg(f"Running: {step.display}", stderr=True, style="dim")
            result = execute()

        if result.returncode != 0:
            failed.append(step.display)

    after = _version_snapshot()
    if not steps:
        return after

    version_changed = before != after
    if failed:
        print_msg("Some upgrade steps failed.", stderr=True, style="bold red")
        for name in failed:
            print_msg(f"  {name}", stderr=True, style="dim")
    if version_changed:
        print_msg("Upgrade complete.", stderr=True, style="bold green")
        _print_version_changes(before, after, prefix="  ")
    elif not failed:
        print_msg("Upgrade finished (versions unchanged).", stderr=True, style="dim")
    else:
        print_msg(
            "Upgrade did not change installed versions. "
            "Try manually: git pull && pip install -e . in your clone.",
            stderr=True,
            style="yellow",
        )
    return after


def _print_version_changes(
    before: Dict[str, Optional[str]],
    after: Dict[str, Optional[str]],
    *,
    prefix: str = "",
) -> None:
    from cli_ui import print_msg

    labels = (
        ("pkg", "yt-dlp-page-stream"),
        ("ytdlp", "yt-dlp"),
    )
    for key, label in labels:
        b, a = before.get(key), after.get(key)
        if b and a and b != a:
            print_msg(f"{prefix}{label}: {b} → {a}", stderr=True, style="cyan")
        elif a:
            print_msg(f"{prefix}{label}: {a}", stderr=True, style="dim")


def _version_line(
    label: str,
    installed: Optional[str],
    latest: Optional[str],
    *,
    fresh: bool,
    cached: bool,
) -> str:
    ver = installed or "?"
    if fresh and latest:
        return f"  {label} {ver}  (latest: {latest})"
    if cached and latest:
        return (
            f"  {label} {ver}  (latest: {latest}, from last successful check)"
        )
    return f"  {label} {ver}"


def _print_status_report(
    snapshot: Dict[str, Optional[str]],
    *,
    last_installed: Dict[str, Optional[str]],
    remote_checked: bool,
) -> None:
    from cli_ui import print_msg

    pkg = snapshot.get("pkg")
    ytdlp = snapshot.get("ytdlp")
    pkg_latest = snapshot.get("pkg_latest")
    ytdlp_latest = snapshot.get("ytdlp_latest")
    pkg_fresh = bool(snapshot.get("pkg_latest_fresh"))
    ytdlp_fresh = bool(snapshot.get("ytdlp_latest_fresh"))
    pkg_cached = bool(snapshot.get("pkg_latest_cached"))
    ytdlp_cached = bool(snapshot.get("ytdlp_latest_cached"))

    outdated_pkg = bool(
        pkg_fresh and pkg and pkg_latest and _version_lt(pkg, pkg_latest)
    )
    outdated_ytdlp = bool(
        ytdlp_fresh and ytdlp and ytdlp_latest and _version_lt(ytdlp, ytdlp_latest)
    )
    remote_all_fresh = pkg_fresh and ytdlp_fresh
    remote_none_fresh = not pkg_fresh and not ytdlp_fresh

    if remote_checked:
        if remote_all_fresh and not outdated_pkg and not outdated_ytdlp:
            print_msg("All up to date with PyPI / GitHub.", stderr=True, style="green")
        elif outdated_pkg or outdated_ytdlp:
            print_msg("Updates available on PyPI / GitHub.", stderr=True, style="yellow")
        elif remote_none_fresh:
            print_msg(
                "Installed versions (could not reach PyPI / GitHub — "
                "network, timeout, or SSL).",
                stderr=True,
                style="yellow",
            )
        else:
            print_msg(
                "Installed versions (remote check incomplete).",
                stderr=True,
                style="yellow",
            )

        print_msg(
            _version_line(
                "yt-dlp-page-stream",
                pkg,
                pkg_latest if isinstance(pkg_latest, str) else None,
                fresh=pkg_fresh,
                cached=pkg_cached,
            ),
            stderr=True,
            style="dim",
        )
        print_msg(
            _version_line(
                "yt-dlp",
                ytdlp,
                ytdlp_latest if isinstance(ytdlp_latest, str) else None,
                fresh=ytdlp_fresh,
                cached=ytdlp_cached,
            ),
            stderr=True,
            style="dim",
        )
        if remote_none_fresh:
            print_msg(
                "  Tip: pip install -U certifi  (fixes SSL on some macOS Python installs)",
                stderr=True,
                style="dim",
            )
    else:
        print_msg("Installed versions:", stderr=True, style="bold")
        _print_version_changes(
            {"pkg": None, "ytdlp": None}, snapshot, prefix="  "
        )

    last_pkg = last_installed.get("pkg")
    last_ytdlp = last_installed.get("ytdlp")
    changed = False
    if last_pkg and pkg and last_pkg != pkg:
        print_msg(
            f"  yt-dlp-page-stream updated since last check: {last_pkg} → {pkg}",
            stderr=True,
            style="cyan",
        )
        changed = True
    if last_ytdlp and ytdlp and last_ytdlp != ytdlp:
        print_msg(
            f"  yt-dlp updated since last check: {last_ytdlp} → {ytdlp}",
            stderr=True,
            style="cyan",
        )
        changed = True
    if (
        last_installed
        and not changed
        and remote_checked
        and remote_all_fresh
        and not outdated_pkg
        and not outdated_ytdlp
    ):
        print_msg("  (no change since last check)", stderr=True, style="dim")


def _gather_updates() -> Tuple[
    List[str], List[_UpgradeStep], List[_UpgradeStep], Dict[str, Optional[str]]
]:
    """Return (messages, ytdlp_steps, pkg_steps, snapshot with latest remotes)."""
    messages: List[str] = []
    ytdlp_steps: List[_UpgradeStep] = []
    pkg_steps: List[_UpgradeStep] = []

    cached_remote = _cached_remote_latest()

    installed_ytdlp = ytdlp_version()
    latest_ytdlp_fresh = _pypi_latest_ytdlp()
    latest_ytdlp = latest_ytdlp_fresh or cached_remote.get("ytdlp")
    if (
        installed_ytdlp
        and latest_ytdlp_fresh
        and _version_lt(installed_ytdlp, latest_ytdlp_fresh)
    ):
        upgrade_cmd = (
            "brew upgrade yt-dlp"
            if brew_ytdlp_binary()
            else "pip install -U yt-dlp"
        )
        messages.append(
            f"yt-dlp {installed_ytdlp} is outdated (latest: {latest_ytdlp_fresh}).\n"
            f"  {upgrade_cmd}"
        )
        ytdlp_steps.append(_ytdlp_upgrade_step())

    installed_pkg = _installed_version(_PKG_NAME)
    latest_pkg_fresh = _github_latest_pkg()
    latest_pkg = latest_pkg_fresh or cached_remote.get("pkg")
    if (
        installed_pkg
        and latest_pkg_fresh
        and _version_lt(installed_pkg, latest_pkg_fresh)
    ):
        if _is_git_clone():
            root = _pkg_root()
            upgrade = f"cd {root} && git pull && pip install -e ."
            pkg_steps.extend(
                [
                    _UpgradeStep(
                        f"git pull ({root})",
                        ["git", "-C", str(root), "pull"],
                    ),
                    _UpgradeStep(
                        f"pip install -e {root}",
                        _pip_argv("install", "-e", str(root)),
                    ),
                ]
            )
        else:
            upgrade = f"pip install -U {_GIT_URL}"
            pkg_steps.append(
                _UpgradeStep(upgrade, _pip_argv("install", "-U", _GIT_URL))
            )
        messages.append(
            f"{_PKG_NAME} {installed_pkg} is outdated (latest release: {latest_pkg_fresh}).\n"
            f"  {upgrade}"
        )

    snapshot: Dict[str, Optional[str]] = {
        "pkg": installed_pkg,
        "ytdlp": installed_ytdlp,
        "pkg_latest": latest_pkg,
        "ytdlp_latest": latest_ytdlp,
        "pkg_latest_fresh": latest_pkg_fresh is not None,
        "ytdlp_latest_fresh": latest_ytdlp_fresh is not None,
        "pkg_latest_cached": latest_pkg_fresh is None and bool(cached_remote.get("pkg")),
        "ytdlp_latest_cached": latest_ytdlp_fresh is None
        and bool(cached_remote.get("ytdlp")),
    }
    return messages, ytdlp_steps, pkg_steps, snapshot


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

    from cli_ui import confirm, get_console, print_msg, run_with_status

    last_installed = _last_installed_from_cache()
    gathered: List = []

    def check() -> None:
        gathered[:] = list(_gather_updates())

    show_check_spinner = force or prompt
    if show_check_spinner:
        run_with_status(
            "[bold]Checking PyPI and GitHub for updates...[/]",
            check,
        )
    else:
        check()

    messages, ytdlp_steps, pkg_steps, snapshot = (
        gathered[0],
        gathered[1],
        gathered[2],
        gathered[3],
    )

    if brew_ytdlp_binary():
        remove_pip_ytdlp(quiet=True)

    if ytdlp_steps:
        before = _version_snapshot()
        if force or prompt:
            after = _run_upgrade_steps(ytdlp_steps, before)
        else:
            from cli_ui import print_msg

            print_msg(
                f"Auto-upgrading yt-dlp ({ytdlp_steps[0].display})...",
                stderr=True,
                style="cyan",
            )
            after = _run_upgrade_steps(ytdlp_steps, before)
        remove_pip_ytdlp(quiet=True)
        snapshot["ytdlp"] = after.get("ytdlp")

    pkg_messages = [m for m in messages if m.startswith(f"{_PKG_NAME} ")]

    if not pkg_messages:
        if force or prompt:
            _print_status_report(
                snapshot,
                last_installed=last_installed,
                remote_checked=True,
            )
        _write_cache(
            {
                "pkg": snapshot.get("pkg"),
                "ytdlp": snapshot.get("ytdlp"),
            },
            remote=_fresh_remote_for_cache(snapshot),
        )
        return 0

    body = "\n\n".join(pkg_messages)
    console = get_console(stderr=True)
    if console:
        from rich.panel import Panel

        console.print(
            Panel.fit(body, title="Updates available", border_style="yellow")
        )
    else:
        print("\nUpdates available:", file=sys.stderr)
        for msg in pkg_messages:
            print(msg, file=sys.stderr)
            print(file=sys.stderr)

    should_prompt = prompt or _env_truthy("YT_DLP_PAGE_STREAM_UPDATE_PROMPT")
    if should_prompt and pkg_steps:
        if confirm("Upgrade now?", default=False):
            before = _version_snapshot()
            after = _run_upgrade_steps(pkg_steps, before)
            _write_cache(
                {"pkg": after.get("pkg"), "ytdlp": after.get("ytdlp")},
                remote=_fresh_remote_for_cache(snapshot),
            )
            return 0
        print_msg("Upgrade skipped.", stderr=True, style="dim")

    if force or prompt:
        _print_status_report(
            snapshot,
            last_installed=last_installed,
            remote_checked=True,
        )
    _write_cache(
        {"pkg": snapshot.get("pkg"), "ytdlp": snapshot.get("ytdlp")},
        remote=_fresh_remote_for_cache(snapshot),
    )
    return 0


def _fresh_remote_for_cache(snapshot: Dict[str, Optional[str]]) -> Dict[str, str]:
    remote: Dict[str, str] = {}
    if snapshot.get("pkg_latest_fresh") and snapshot.get("pkg_latest"):
        remote["pkg"] = str(snapshot["pkg_latest"])
    if snapshot.get("ytdlp_latest_fresh") and snapshot.get("ytdlp_latest"):
        remote["ytdlp"] = str(snapshot["ytdlp_latest"])
    return remote


def maybe_notify_updates() -> None:
    try:
        run_update_flow(force=False, prompt=False)
    except Exception:
        pass
