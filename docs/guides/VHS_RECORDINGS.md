# Creating Terminal Recordings with VHS

This guide explains how to create terminal recordings for documentation using [VHS (Video Haskell Script)](https://github.com/charmbracelet/vhs).

## Installation

VHS is already installed in this project. To install it yourself:

```bash
# macOS
brew install charmbracelet/tap/vhs

# Linux/Windows (via Go)
go install github.com/charmbracelet/vhs@latest
```

## Quick Start

### Option 1: Record Your Session

Record your terminal session interactively:

```bash
cd docs/demos/cli
vhs record my-demo.tape
# Perform actions in your terminal
# Press Ctrl+C when done to save
```

### Option 2: Create a Tape File Manually

Create a `.tape` file with the commands you want to record:

```tape
# my-demo.tape
Output docs/public/assets/demos/my-demo.gif

Set Shell zsh
Set FontSize 16
Set Width 1200
Set Height 600
Set Theme "Catppuccin Mocha"

Type "thegent --version"
Sleep 500ms
Enter
Sleep 2s
```

## Tape Commands Reference

| Command             | Description         | Example                                    |
| ------------------- | ------------------- | ------------------------------------------ |
| `Output <file>`     | Set output GIF path | `Output docs/public/assets/demos/demo.gif` |
| `Set <key> <value>` | Set configuration   | `Set FontSize 16`                          |
| `Type <text>`       | Type text           | `Type "thegent run codex 'Hello'"`         |
| `Enter`             | Press Enter         | `Enter`                                    |
| `Sleep <ms>`        | Wait milliseconds   | `Sleep 1000`                               |
| `Ctrl+<key>`        | Press Ctrl+key      | `Ctrl+L` (clear)                           |
| `Alt+<key>`         | Press Alt+key       | `Alt+Right`                                |
| `Backspace`         | Press backspace     | `Backspace`                                |
| `Tab`               | Press tab           | `Tab`                                      |
| `Escape`            | Press escape        | `Escape`                                   |
| `Up` / `Down`       | Arrow keys          | `Up`                                       |

## Available Settings

| Setting       | Default          | Description               |
| ------------- | ---------------- | ------------------------- |
| `Width`       | 1200             | Terminal width in pixels  |
| `Height`      | 600              | Terminal height in pixels |
| `FrameRate`   | 30               | FPS for the GIF           |
| `TypingSpeed` | 50               | ms between keystrokes     |
| `Theme`       | Catppuccin Mocha | Color theme               |
| `FontSize`    | 16               | Font size                 |
| `Shell`       | zsh              | Shell to use              |
| `Padding`     | 20               | Padding around content    |

## Available Themes

List all available themes:

```bash
vhs themes
```

Common themes:

- Catppuccin Mocha
- Catppuccin Latte
- Dracula
- Nord
- Gruvbox Dark
- GitHub Dark
- Tokyo Night

## Project Configuration

This project uses `docs/demos/vhs.config.json` for consistent settings:

```json
{
  "Width": 1200,
  "Height": 600,
  "FrameRate": 30,
  "TypingSpeed": 50,
  "Theme": "Catppuccin Mocha",
  "FontSize": 16,
  "Shell": "zsh",
  "Padding": 20
}
```

## Creating a New Demo

1. **Create the tape file** in `docs/demos/cli/`:

```tape
# docs/demos/cli/my-feature.tape
Output docs/public/assets/demos/my-feature.gif

Set Shell zsh
Set FontSize 16
Set Width 1200
Set Height 600
Set Theme "Catppuccin Mocha"

# Commands to demonstrate
Type "thegent my-feature --help"
Sleep 500ms
Enter
Sleep 2s
```

2. **Generate the GIF**:

```bash
cd docs/demos/cli
vhs my-feature.tape
```

3. **Use in documentation**:

```vue
<DemoGif
  src="my-feature.gif"
  alt="My Feature Demo"
  caption="Demonstrating my feature"
/>
```

## Best Practices

1. **Keep recordings short**: Aim for 3-10 seconds
2. **Add sleep delays**: `Sleep 2s` after important commands
3. **Show help first**: Start with `--help` to orient viewers
4. **Use clear prompts**: The theme handles this automatically
5. **Test the output**: Verify the GIF renders correctly

## Example: Complete Demo Tape

```tape
# Complete example demonstrating multiple features
Output docs/public/assets/demos/complete-demo.gif

Set Shell zsh
Set FontSize 16
Set Width 1200
Set Height 600
Set Theme "Catppuccin Mocha"

# Show help
Type "thegent --help"
Sleep 500ms
Enter
Sleep 2s

# Clear screen
Ctrl+L

# List agents
Type "thegent list agents"
Sleep 500ms
Enter
Sleep 3s
```

## Troubleshooting

### GIF not generating

Check that:

- Output path is correct and directory exists
- No syntax errors in the tape file
- VHS is installed correctly

### Terminal rendering issues

- Reduce `TypingSpeed` for slower terminals
- Increase `Height` if output is truncated
- Add more `Sleep` time for complex renders

### Theme not found

Themes are case-sensitive. Use exact theme names from `vhs themes`.

## See Also

- [VHS GitHub](https://github.com/charmbracelet/vhs)
- [VHS Documentation](https://vhs.charm.sh)
- [Demo Scripts README](./README.md)
- [VITEPRESS_RICH_DOCUMENTATION_IMPLEMENTATION_PLAN.md](../../research/VITEPRESS_RICH_DOCUMENTATION_IMPLEMENTATION_PLAN.md)
