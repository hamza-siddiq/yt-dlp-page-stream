"""Run yt-dlp with this package's plugin loaded (same Python as pip install -e .)."""

import sys
from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parent
_OUR_UPDATE_FLAG = "--update"


def _ensure_package_on_syspath() -> None:
    """Console scripts set sys.path[0] to .../bin, so yt-dlp never sees yt_dlp_plugins/."""
    root = str(_PKG_ROOT)
    if sys.path:
        first = Path(sys.path[0]).resolve()
        if first.name in ("bin", "Scripts") or first != _PKG_ROOT.resolve():
            if Path(sys.path[0]).name in ("bin", "Scripts"):
                sys.path[0] = root
            elif root not in sys.path:
                sys.path.insert(0, root)
    elif root not in sys.path:
        sys.path.insert(0, root)


def _consume_update_flag(argv: list[str]) -> bool:
    found = False
    stripped: list[str] = []
    for arg in argv:
        if arg == _OUR_UPDATE_FLAG:
            found = True
        else:
            stripped.append(arg)
    argv[:] = stripped
    return found


def _argv_is_standalone(argv: list[str]) -> bool:
    """True when only the program name remains (no URLs or yt-dlp flags)."""
    return len(argv) <= 1


def main() -> None:
    _ensure_package_on_syspath()

    argv = sys.argv[:]
    do_update = _consume_update_flag(argv)
    sys.argv = argv

    from update_check import maybe_notify_updates, run_update_flow

    if do_update:
        code = run_update_flow(force=True, prompt=True)
        if code != 0:
            sys.exit(code)
        if _argv_is_standalone(argv):
            sys.exit(0)
    else:
        maybe_notify_updates()

    try:
        from yt_dlp import main as ytdlp_main
    except ImportError:
        print(
            "yt-dlp is not installed in this Python environment.\n"
            "Install with: pip install -e .  (includes yt-dlp)",
            file=sys.stderr,
        )
        sys.exit(1)
    ytdlp_main()
