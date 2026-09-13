"""Stub module for thegent.design.design_language."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DesignToken:
    """A design token."""

    name: str
    value: str
    category: str = "color"


@dataclass
class CLITheme:
    """CLI theme with styles."""

    styles: dict[str, str] = field(default_factory=dict)


def _default_tokens() -> dict[str, DesignToken]:
    """Create default tokens."""
    return {
        "color.info": DesignToken(name="color.info", value="#00ff00", category="color"),
        "color.primary": DesignToken(name="color.primary", value="#0000ff", category="color"),
    }


@dataclass
class DesignLanguage:
    """Design language configuration."""

    primary_color: str = "#000000"
    secondary_color: str = "#ffffff"
    font_family: str = "sans-serif"
    tokens: dict[str, DesignToken] = field(default_factory=_default_tokens)
    cli_theme: CLITheme = field(default_factory=CLITheme)

    def apply_to_cli(self) -> None:
        """Apply design language to CLI configuration."""
        # Require color.info token
        if "color.info" not in self.tokens:
            raise KeyError("color.info token is required")

        self.cli_theme = CLITheme(
            styles={
                "primary": "cyan",
                "info": "blue",
                "success": "green",
                "warning": "yellow",
                "error": "red",
            }
        )


__all__ = ["DesignLanguage", "DesignToken", "CLITheme"]
