"""Stub module."""

try:
    from typer import Typer

    app = Typer()
except ImportError:
    app = None

__all__ = ["app"]
