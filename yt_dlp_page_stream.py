"""Run yt-dlp with this package's plugin loaded (same Python as pip install -e .)."""

import sys
from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parent

_BATCH_FILE_FLAGS = frozenset({"-a", "--batch-file"})


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


def _consume_our_flags(argv: list[str]) -> tuple[bool, bool, bool]:
    do_update = False
    show_version = False
    use_clipboard = False
    stripped: list[str] = []
    for arg in argv:
        if arg == "--update":
            do_update = True
        elif arg in ("--version", "-V"):
            show_version = True
        elif arg == "--clipboard":
            use_clipboard = True
        else:
            stripped.append(arg)
    argv[:] = stripped
    return do_update, show_version, use_clipboard


def _argv_is_standalone(argv: list[str]) -> bool:
    """True when only the program name remains (no URLs or yt-dlp flags)."""
    return len(argv) <= 1


def _argv_has_batch_file(argv: list[str]) -> bool:
    for i, arg in enumerate(argv):
        if arg in _BATCH_FILE_FLAGS:
            return True
        if arg.startswith("--batch-file="):
            return True
    return False


def _argv_has_url(argv: list[str]) -> bool:
    for arg in argv[1:]:
        if arg.startswith("http://") or arg.startswith("https://"):
            return True
    return False


def _apply_clipboard_urls(argv: list[str]) -> None:
    if _argv_has_batch_file(argv):
        print(
            "Cannot use --clipboard together with -a / --batch-file.",
            file=sys.stderr,
        )
        sys.exit(1)
    if _argv_has_url(argv):
        print(
            "Cannot use --clipboard together with URL arguments on the command line.",
            file=sys.stderr,
        )
        sys.exit(1)

    from clipboard_input import read_clipboard_urls

    try:
        urls = read_clipboard_urls()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    argv.extend(urls)


def main() -> None:
    _ensure_package_on_syspath()

    argv = sys.argv[:]
    do_update, show_version, use_clipboard = _consume_our_flags(argv)
    sys.argv = argv

    if show_version:
        from update_check import print_version_info

        print_version_info()
        sys.exit(0)

    from update_check import maybe_notify_updates, run_update_flow

    if do_update:
        code = run_update_flow(force=True, prompt=True)
        if code != 0:
            sys.exit(code)
        if _argv_is_standalone(argv):
            sys.exit(0)
    else:
        maybe_notify_updates()

    if use_clipboard:
        _apply_clipboard_urls(argv)
        sys.argv = argv

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
