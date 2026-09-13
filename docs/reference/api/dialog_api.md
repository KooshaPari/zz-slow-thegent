# dialog API Reference

> **Source**: `src/thegent/tui/widgets/dialog.py`

Dialog and floating window widgets for TUI compositor.

Provides modal dialogs, floating panels, and overlay widgets.

---

## ConfirmDialog

Confirmation dialog with Yes/No buttons.

**Inherits from**: `Dialog`

**Method Resolution Order**: `ConfirmDialog -> Dialog`

### Methods

#### ConfirmDialog.**init**

```python
__init__(self: Any, message: str, title: str, yes_label: str, no_label: str)
```

---

---

## Dialog

Modal dialog widget with title, content, and buttons.

**Inherits from**: `Container`

### Methods

#### Dialog.**init**

```python
__init__(self: Any, title: str)
```

---

#### Dialog.compose

```python
compose(self: Any)
```

---

#### Dialog.on_click

```python
on_click(self: Any, event: Click)
```

Handle button clicks.

---

#### Dialog.on_key

```python
on_key(self: Any, event: Key)
```

Handle keyboard navigation.

---

#### Dialog.on_mount

```python
on_mount(self: Any)
```

Set initial focus.

---

#### Dialog.on_result

```python
on_result(self: Any, callback: Callable[(Any, None)])
```

Set callback for dialog result.

---

---

## DialogManager

Manages dialogs and overlays.

### Methods

#### DialogManager.**init**

```python
__init__(self: Any)
```

---

#### DialogManager.close_all

```python
close_all(self: Any)
```

Close all dialogs.

---

#### DialogManager.show_confirm

```python
show_confirm(self: Any, message: str, title: str, on_result: Any)
```

Show a confirmation dialog.

---

#### DialogManager.show_dialog

```python
show_dialog(self: Any, dialog: Dialog)
```

Show a dialog with overlay.

---

#### DialogManager.show_input

```python
show_input(self: Any, prompt: str, title: str, default: str, password: bool, on_result: Any)
```

Show an input dialog.

---

#### DialogManager.show_message

```python
show_message(self: Any, message: str, title: str, style: DialogStyle)
```

Show a simple message dialog.

---

#### DialogManager.show_toast

```python
show_toast(self: Any, message: str, duration: float, style: DialogStyle)
```

Show a toast notification.

---

---

## DialogResult

Result of a dialog interaction.

**Inherits from**: `Enum`

---

## DialogStyle

Dialog style variants.

**Inherits from**: `Enum`

---

## InputDialog

Dialog with text input field.

**Inherits from**: `Dialog`

**Method Resolution Order**: `InputDialog -> Dialog`

### Methods

#### InputDialog.**init**

```python
__init__(self: Any, prompt: str, title: str, default: str, password: bool, placeholder: str)
```

---

#### InputDialog.get_value

```python
get_value(self: Any)
```

Get the input value.

---

---

## MessageDialog

Simple message dialog with text content.

**Inherits from**: `Dialog`

**Method Resolution Order**: `MessageDialog -> Dialog`

### Methods

#### MessageDialog.**init**

```python
__init__(self: Any, message: str, title: str)
```

---

---

## Overlay

Full-screen overlay for dialogs and modals.

**Inherits from**: `Container`

### Methods

#### Overlay.**init**

```python
__init__(self: Any)
```

---

---

## Toast

Temporary notification toast.

**Inherits from**: `Container`

### Methods

#### Toast.**init**

```python
__init__(self: Any, message: str, duration: float, style: DialogStyle)
```

---

#### Toast.compose

```python
compose(self: Any)
```

---

#### Toast.dismiss

```python
dismiss(self: Any)
```

Remove the toast.

---

#### Toast.on_mount

```python
on_mount(self: Any)
```

Auto-dismiss after duration.

---

---

## close_all

```python
close_all(self: Any)
```

Close all dialogs.

---

## compose

```python
compose(self: Any) -> ComposeResult
```

---

## dismiss

```python
dismiss(self: Any)
```

Remove the toast.

---

## get_value

```python
get_value(self: Any)
```

Get the input value.

---

## on_click

```python
on_click(self: Any, event: Click)
```

Handle button clicks.

---

## on_key

```python
on_key(self: Any, event: Key)
```

Handle keyboard navigation.

---

## on_mount

```python
on_mount(self: Any)
```

Auto-dismiss after duration.

---

## on_result

```python
on_result(self: Any, callback: Callable[(Any, None)])
```

Set callback for dialog result.

---

## show_confirm

```python
show_confirm(self: Any, message: str, title: str, on_result: Any)
```

Show a confirmation dialog.

---

## show_dialog

```python
show_dialog(self: Any, dialog: Dialog)
```

Show a dialog with overlay.

---

## show_input

```python
show_input(self: Any, prompt: str, title: str, default: str, password: bool, on_result: Any)
```

Show an input dialog.

---

## show_message

```python
show_message(self: Any, message: str, title: str, style: DialogStyle)
```

Show a simple message dialog.

---

## show_toast

```python
show_toast(self: Any, message: str, duration: float, style: DialogStyle)
```

Show a toast notification.

---
