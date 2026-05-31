"""Run yt-dlp with this package's plugin loaded (same Python as pip install -e .)."""

import sys
from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parent


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


def main() -> None:
    _ensure_package_on_syspath()
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
