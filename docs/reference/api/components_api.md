# components API Reference

> **Source**: `src/thegent/compositor/components.py`

Basic component library for the TUI Compositor.

Phase 1 components: OutputWidget, StatusWidget, SidebarWidget, Header.
Provides reusable Textual widgets for displaying agent output, status, and navigation.

---

## FooterStatusBar

Footer status bar with quick info and bindings.

Features:

- Current focus info
- Keyboard shortcuts
- Connection status

**Inherits from**: `Static`

### Methods

#### FooterStatusBar.render

```python
render(self: Any)
```

Render the footer.

---

#### FooterStatusBar.update_pane_info

```python
update_pane_info(self: Any, count: int, focus_id: str)
```

Update pane information.

**Parameters**:

- `count`: Number of panes
- `focus_id`: Focused pane ID

---

---

## HeaderWidget

Main header with title and version.

Features:

- Application title
- Version display
- Status indicator

**Inherits from**: `Static`

### Methods

#### HeaderWidget.**init**

```python
__init__(self: Any, title: str, version: str)
```

Initialize the header widget.

**Parameters**:

- `title`: Application title
- `version`: Version string

---

#### HeaderWidget.render

```python
render(self: Any)
```

Render the header.

---

---

## MetricsPanel

Display performance metrics and statistics.

Features:

- CPU/Memory usage (Phase 2+)
- Request/response times
- Success/error rates
- Cost tracking

**Inherits from**: `Container`

### Methods

#### MetricsPanel.**init**

```python
__init__(self: Any)
```

Initialize the metrics panel.

---

#### MetricsPanel.compose

```python
compose(self: Any)
```

Compose the metrics panel.

---

#### MetricsPanel.update_metric

```python
update_metric(self: Any, key: str, value: str)
```

Update a metric value.

**Parameters**:

- `key`: Metric key
- `value`: Metric value

---

#### MetricsPanel.update_metrics

```python
update_metrics(self: Any, metrics: dict[(str, str)])
```

Update multiple metrics.

**Parameters**:

- `metrics`: Dictionary of metric key-value pairs

---

---

## OutputWidget

Display agent output with auto-scrolling and syntax highlighting.

Features:

- Rich text rendering with syntax highlighting
- Auto-scroll on new messages
- Search and filter capabilities (Phase 2+)
- Timestamp display

**Inherits from**: `ScrollableContainer`

### Methods

#### OutputWidget.**init**

```python
__init__(self: Any, title: str)
```

Initialize the output widget.

**Parameters**:

- `title`: Widget title

---

#### OutputWidget.clear

```python
clear(self: Any)
```

Clear all output.

---

#### OutputWidget.compose

```python
compose(self: Any)
```

Compose the output widget.

---

#### OutputWidget.get_line_count

```python
get_line_count(self: Any)
```

Get the number of lines displayed.

---

#### OutputWidget.write

```python
write(self: Any, text: str, style: str, timestamp: bool)
```

Write text to the output widget.

**Parameters**:

- `text`: Text to display
- `style`: Rich style to apply
- `timestamp`: Whether to prepend timestamp

---

---

## ProgressIndicator

Display progress and status indicator.

Features:

- Progress bar
- Percentage display
- ETA
- Status message

**Inherits from**: `Static`

### Methods

#### ProgressIndicator.render

```python
render(self: Any)
```

Render the progress indicator.

---

#### ProgressIndicator.update_progress

```python
update_progress(self: Any, current: int, total: int, message: Any)
```

Update progress.

**Parameters**:

- `current`: Current progress
- `total`: Total items
- `message`: Optional status message

---

---

## SidebarWidget

Display agent list, session info, and quick actions.

Features:

- Agent list with status indicators
- Session information
- Quick action buttons
- Navigation (Phase 2+)

**Inherits from**: `ScrollableContainer`

### Methods

#### SidebarWidget.**init**

```python
__init__(self: Any)
```

Initialize the sidebar widget.

---

#### SidebarWidget.add_agent

```python
add_agent(self: Any, agent_id: str, name: str, status: str)
```

Add an agent to the sidebar.

**Parameters**:

- `agent_id`: Unique agent ID
- `name`: Display name
- `status`: Current status

---

#### SidebarWidget.compose

```python
compose(self: Any)
```

Compose the sidebar widget.

---

#### SidebarWidget.update_agent_status

```python
update_agent_status(self: Any, agent_id: str, status: str)
```

Update an agent's status.

**Parameters**:

- `agent_id`: Agent ID
- `status`: New status

---

#### SidebarWidget.update_session_info

```python
update_session_info(self: Any, session_id: str, start_time: str, uptime: str)
```

Update session information.

**Parameters**:

- `session_id`: Session ID
- `start_time`: Start time string
- `uptime`: Uptime string

---

---

## StatusWidget

Display agent status, model info, and metrics.

Features:

- Real-time status updates
- Model information display
- Token counter
- Cost tracking (Phase 2+)

**Inherits from**: `Container`

### Methods

#### StatusWidget.**init**

```python
__init__(self: Any)
```

Initialize the status widget.

---

#### StatusWidget.compose

```python
compose(self: Any)
```

Compose the status widget.

---

#### StatusWidget.start_timer

```python
start_timer(self: Any)
```

Start the elapsed time timer.

---

#### StatusWidget.stop_timer

```python
stop_timer(self: Any)
```

Stop the elapsed time timer.

---

#### StatusWidget.update_status

```python
update_status(self: Any, status: str, model: Any, tokens: Any)
```

Update all status fields.

**Parameters**:

- `status`: New status (idle, running, error, done)
- `model`: Optional model name
- `tokens`: Optional token count

---

#### StatusWidget.watch_elapsed_time

```python
watch_elapsed_time(self: Any, elapsed: float)
```

Update elapsed time display.

---

#### StatusWidget.watch_model

```python
watch_model(self: Any, model: str)
```

Update model display.

---

#### StatusWidget.watch_status

```python
watch_status(self: Any, status: str)
```

Update status display.

---

#### StatusWidget.watch_tokens_used

```python
watch_tokens_used(self: Any, tokens: int)
```

Update token count display.

---

---

## add_agent

```python
add_agent(self: Any, agent_id: str, name: str, status: str)
```

Add an agent to the sidebar.

**Parameters**:

- `agent_id`: Unique agent ID
- `name`: Display name
- `status`: Current status

---

## clear

```python
clear(self: Any)
```

Clear all output.

---

## compose

```python
compose(self: Any)
```

Compose the metrics panel.

---

## get_line_count

```python
get_line_count(self: Any)
```

Get the number of lines displayed.

---

## render

```python
render(self: Any)
```

Render the progress indicator.

---

## start_timer

```python
start_timer(self: Any)
```

Start the elapsed time timer.

---

## stop_timer

```python
stop_timer(self: Any)
```

Stop the elapsed time timer.

---

## update_agent_status

```python
update_agent_status(self: Any, agent_id: str, status: str)
```

Update an agent's status.

**Parameters**:

- `agent_id`: Agent ID
- `status`: New status

---

## update_metric

```python
update_metric(self: Any, key: str, value: str)
```

Update a metric value.

**Parameters**:

- `key`: Metric key
- `value`: Metric value

---

## update_metrics

```python
update_metrics(self: Any, metrics: dict[(str, str)])
```

Update multiple metrics.

**Parameters**:

- `metrics`: Dictionary of metric key-value pairs

---

## update_pane_info

```python
update_pane_info(self: Any, count: int, focus_id: str)
```

Update pane information.

**Parameters**:

- `count`: Number of panes
- `focus_id`: Focused pane ID

---

## update_progress

```python
update_progress(self: Any, current: int, total: int, message: Any)
```

Update progress.

**Parameters**:

- `current`: Current progress
- `total`: Total items
- `message`: Optional status message

---

## update_session_info

```python
update_session_info(self: Any, session_id: str, start_time: str, uptime: str)
```

Update session information.

**Parameters**:

- `session_id`: Session ID
- `start_time`: Start time string
- `uptime`: Uptime string

---

## update_status

```python
update_status(self: Any, status: str, model: Any, tokens: Any)
```

Update all status fields.

**Parameters**:

- `status`: New status (idle, running, error, done)
- `model`: Optional model name
- `tokens`: Optional token count

---

## watch_elapsed_time

```python
watch_elapsed_time(self: Any, elapsed: float)
```

Update elapsed time display.

---

## watch_model

```python
watch_model(self: Any, model: str)
```

Update model display.

---

## watch_status

```python
watch_status(self: Any, status: str)
```

Update status display.

---

## watch_tokens_used

```python
watch_tokens_used(self: Any, tokens: int)
```

Update token count display.

---

## write

```python
write(self: Any, text: str, style: str, timestamp: bool)
```

Write text to the output widget.

**Parameters**:

- `text`: Text to display
- `style`: Rich style to apply
- `timestamp`: Whether to prepend timestamp

---
