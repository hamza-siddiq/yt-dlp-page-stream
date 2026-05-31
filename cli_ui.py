"""Rich terminal helpers with plain-text fallback when not a TTY."""

from __future__ import annotations

import sys
from typing import Any, Optional


def get_console(*, stderr: bool = False) -> Optional[Any]:
    stream = sys.stderr if stderr else sys.stdout
    if not stream.isatty():
        return None
    from rich.console import Console

    return Console(stderr=stderr)


def print_msg(text: str, *, stderr: bool = False, style: Optional[str] = None) -> None:
    console = get_console(stderr=stderr)
    if console:
        console.print(text, style=style)
    else:
        print(text, file=sys.stderr if stderr else sys.stdout)


def run_with_status(message: str, func) -> None:
    """Run func() inside a Rich spinner when stderr is a TTY."""
    console = get_console(stderr=True)
    if console:
        with console.status(message, spinner="dots"):
            func()
    else:
        print(message, file=sys.stderr)
        func()


def confirm(prompt: str, default: bool = False) -> bool:
    console = get_console(stderr=True)
    if console:
        from rich.prompt import Confirm

        return Confirm.ask(prompt, default=default, console=console)
    try:
        suffix = " [Y/n] " if default else " [y/N] "
        answer = input(prompt + suffix).strip().lower()
        if not answer:
            return default
        return answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False
