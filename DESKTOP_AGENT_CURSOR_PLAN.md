# Desktop & Mobile Agent Cursor & Collision Avoidance - Comprehensive Plan

## Executive Summary

When thegent runs **on any device** alongside a human user, we need:
1. **Agent visibility** - User sees what agent is doing
2. **Collision avoidance** - Agent doesn't interact where user is interacting
3. **State indication** - User knows agent state (thinking, working, waiting)

This document covers: Desktop (Windows/macOS/Linux), Mobile (iOS/Android), Wearables (WearOS/WatchOS), TV (tvOS/Android TV), Automotive (Android Auto/CarPlay/IVI), and other platforms.

---

## Table of Contents

1. [Platform Coverage Matrix](#platform-coverage-matrix)
2. [Problem Analysis](#problem-analysis)
3. [Research Findings](#research-findings)
4. [Technical Architecture](#technical-architecture)
5. [Platform-Specific Implementation](#platform-specific-implementation)
6. [API Design](#api-design)
7. [Priority & Timeline](#priority--timeline)

---

## Platform Coverage Matrix

| Platform | Input Detection | Output Injection | Collision Avoidance | Overlay/UI | Accessibility API |
|----------|----------------|-----------------|-------------------|-------------|-------------------|
| **Desktop** | | | | | |
| Windows | ✅ GetCursorPos | ✅ SendInput | ✅ Safe zone | ✅ Window | ✅ UIAutomation |
| macOS | ✅ CGEvent | ✅ CGEvent | ✅ Safe zone | ✅ NSWindow | ✅ AXUIElement |
| Linux (X11) | ✅ xdotool | ✅ xdotool | ✅ Safe zone | ✅ X11 overlay | ✅ AT-SPI |
| Linux (Wayland) | ⚠️ Limited | ⚠️ Limited | ⚠️ Limited | ⚠️ Protocol | ⚠️ Limited |
| **Mobile** | | | | | |
| iOS | ✅ XCUITest | ✅ XCUITest | ⚠️ Limited | ⚠️ Guided Access | ✅ XCUIElements |
| Android | ✅ UIAutomator | ✅ UIAutomator | ⚠️ Limited | ⚠️ Overlay | ✅ AccessibilityService |
| **Wearable** | | | | | |
| WatchOS | ⚠️ WatchKit | ⚠️ WatchKit | ❌ No multi-user | ⚠️ Complications | ✅ WatchKit |
| WearOS | ⚠️ Limited | ⚠️ Limited | ❌ No multi-user | ⚠️ Tiles | ⚠️ Limited |
| **TV** | | | | | |
| tvOS | ✅ XCUITest | ✅ XCUITest | ❌ Single user | ⚠️ TVMLKit | ✅ Accessibility |
| Android TV | ⚠️ Limited | ⚠️ Limited | ❌ Single user | ⚠️ Leanback | ⚠️ Limited |
| **Automotive** | | | | | |
| Android Auto | ⚠️ Limited | ⚠️ Limited | ❌ Single user | ⚠️ CarAppLib | ⚠️ Limited |
| Apple CarPlay | ⚠️ Limited | ⚠️ Limited | ❌ Single user | ⚠️ CarPlay | ⚠️ Limited |
| IVI (Generic) | ⚠️ Platform-specific | ⚠️ Platform-specific | ❌ Single user | ⚠️ Custom | ⚠️ Platform-specific |

### Legend
- ✅ Full support
- ⚠️ Limited/custom support
- ❌ Not applicable (single-user device)

---

## Full Support Strategy: Real Device, Simulator, Virtual

### The "Full" Goal
Achieve feature parity across all platforms with options for:
1. **Real Hardware** - Physical devices
2. **Simulators/Emulators** - OS-provided virtual environments
3. **Virtual Machines** - Third-party virtualization

### Linux (Wayland) - Achieving Full Support

| Method | Type | Status | Notes |
|-------|------|--------|-------|
| **Real Device** | Native | ✅ Full | GNOME Shell, KDE Plasma support input injection |
| **Virtual Device (uinput)** | Kernel | ✅ Full | Create virtual mouse/keyboard via uinput |
| **Simulation (ydotool)** | Userspace | ⚠️ Workaround | Requires ydotool daemon |
| **Virtual Machine** | VM | ✅ Full | Pass-through works |

**Wayland Solutions:**
```bash
# Option 1: uinput kernel module
sudo modprobe uinput

# Option 2: ydotool (userspace)
pip install ydotool

# Option 3: wtype (keyboard only)
pip install wtype
```

**Rust Crate for Wayland:**
- `wayland_virtual_input_go` - Virtual pointer/keyboard protocols
- `uinput` crate - Direct uinput access

---

### iOS - Achieving Full Support

| Method | Type | Status | Notes |
|-------|------|--------|-------|
| **Real Device** | Native | ✅ Full | Requires paid Apple Developer account |
| **Simulator** | Xcode | ✅ Full | Faster, no device needed |
| **Virtual Machine** | Xcode VM | ⚠️ Limited | Running macOS VM on macOS only |

**XCUITest Capabilities by Environment:**

| Feature | Real Device | Simulator |
|---------|-------------|-----------|
| UI Automation | ✅ | ✅ |
| Gestures | ✅ | ✅ |
| Screen Capture | ✅ | ✅ |
| Biometrics | ✅ | ❌ |
| GPS/Location | ⚠️ Limited | ✅ |
| Push Notifications | ⚠️ Limited | ✅ |
| Camera | ✅ | ❌ |
| Performance Testing | ✅ | ⚠️ Approximation |

**Automation Strategy:**
```swift
// XCUITest for both real device and simulator
let app = XCUIApplication()
app.buttons["Save"].tap()  // Works on both
app.swipeUp()              // Works on both

// Environment detection
#if targetEnvironment(simulator)
    // Simulator-specific code
#else
    // Real device-specific code
#endif
```

---

### Android - Achieving Full Support

| Method | Type | Status | Notes |
|-------|------|--------|-------|
| **Real Device** | Native | ✅ Full | Requires USB debugging |
| **Emulator** | AVD | ✅ Full | Android Virtual Device |
| **Virtual Machine** | Genymotion | ✅ Full | Cloud or local |

**UIAutomator Capabilities by Environment:**

| Feature | Real Device | Emulator |
|---------|-------------|----------|
| UI Automation | ✅ | ✅ |
| Gestures | ✅ | ✅ |
| Screen Capture | ✅ | ✅ |
| Biometrics | ⚠️ Limited | ⚠️ Limited |
| GPS | ⚠️ Limited | ✅ |
| Network | ✅ | ✅ |
| Hardware Sensors | ⚠️ Limited | ❌ |

**Automation Strategy:**
```kotlin
// UIAutomator works on both
val device = UiDevice.getInstance()
device.findObject(By.text("Save")).click()
device.swipe()
```

---

### tvOS - Achieving Full Support

| Method | Type | Status | Notes |
|-------|------|--------|-------|
| **Real Device** | Apple TV | ✅ Full | Requires Apple Developer |
| **Simulator** | Xcode | ✅ Full | All Apple TV models |

**Focus Navigation (not pointer):**
- tvOS uses focus-based navigation
- XCUITest works identically on both

---

### WearOS - Achieving Full Support

| Method | Type | Status | Notes |
|-------|------|--------|-------|
| **Real Device** | Wear OS | ⚠️ Limited | No official automation API |
| **Emulator** | Android Studio | ⚠️ Limited | Limited interaction |

**Strategy:** Partner with Android automation tools (Appium) for basic interaction.

---

### Android Auto / CarPlay - Achieving Full Support

| Method | Type | Status | Notes |
|-------|------|--------|-------|
| **Real Device** | In-car | ⚠️ Very Limited | CarAppLibrary only |
| **Emulator** | Android Studio | ⚠️ Limited | AAOS emulator |
| **Desktop Head Unit** | Desktop | ⚠️ Limited | Testing emulator |

**Strategy:** Use Android Automotive OS emulator for development, acknowledge limitations for production.

---

## Feature Parity Matrix

### By Environment Type

| Feature | Real Device | Simulator/Emulator | Virtual Machine |
|---------|-------------|-------------------|-----------------|
| **Cursor Position** | ✅ | ✅ | ✅ |
| **Click Injection** | ✅ | ✅ | ✅ |
| **Gesture Simulation** | ✅ | ✅ | ✅ |
| **Screen Capture** | ✅ | ✅ | ✅ |
| **Accessibility APIs** | ✅ | ✅ | ⚠️ |
| **Collision Detection** | ✅ | ✅ | ✅ |
| **Overlay Display** | ⚠️ Device | ⚠️ Device | ⚠️ Desktop |
| **System Integration** | ✅ | ⚠️ Limited | ⚠️ Limited |

### By Platform (with Solutions)

| Platform | Current | Goal | Solution |
|----------|---------|------|----------|
| **Wayland** | ⚠️ Limited | ✅ Full | uinput virtual device |
| **WearOS** | ❌ None | ⚠️ Basic | Appium partnership |
| **Android TV** | ⚠️ Limited | ✅ Full | Leanback + UIAutomator |
| **Android Auto** | ⚠️ Limited | ⚠️ Basic | Desktop Head Unit |
| **CarPlay** | ❌ None | ⚠️ Basic | Limited API access |
| **IVI Systems** | ❌ None | ⚠️ Custom | Platform-specific SDK |

---

## Implementation Architecture for Multi-Environment

```rust
// Environment detection and selection
pub enum ExecutionEnvironment {
    RealDevice,
    Simulator,
    Emulator,
    VirtualMachine,
    CloudDevice,
}

pub trait PlatformBackend {
    fn detect_environment() -> ExecutionEnvironment;
    fn get_input_method(&self) -> Box<dyn InputMethod>;
    fn get_overlay_method(&self) -> Box<dyn OverlayMethod>;
}

// Platform-specific implementations
impl PlatformBackend for WindowsBackend { ... }
impl PlatformBackend for MacOSBackend { ... }
impl PlatformBackend for IOSBackend { ... }  // Handles real + simulator
impl PlatformBackend for AndroidBackend { ... }  // Handles real + emulator
```

---

## Cloud Device Options

| Provider | Platforms | Real Devices | Simulators | Notes |
|----------|-----------|--------------|------------|--------|
| **BrowserStack** | iOS, Android | ✅ | ✅ | Real device cloud |
| **Sauce Labs** | iOS, Android, tvOS | ✅ | ✅ | Full mobile coverage |
| **LambdaTest** | iOS, Android | ✅ | ✅ | Real device cloud |
| **AWS Device Farm** | iOS, Android | ✅ | ✅ | AWS integration |
| **Firebase Test Lab** | Android | ❌ | ✅ | GCP integration |
| **Xcode Cloud** | iOS, tvOS | ❌ | ✅ | Apple ecosystem |

---

## Mobile Automation Tools & CLI Comparison

### Primary Tools

| Tool | Type | Platform | CLI | AI/MCP | Learning Curve |
|------|------|----------|-----|---------|----------------|
| **Mobile Next MCP** | MCP Server | iOS, Android | ✅ | ✅ MCP | Low |
| **Appium** | WebDriver | iOS, Android | ✅ | ⚠️ | Medium |
| **Maestro** | Framework | iOS, Android | ✅ | ⚠️ | Low |
| **XCUITest** | Native | iOS | ✅ | ⚠️ | Medium |
| **UIAutomator** | Native | Android | ✅ | ❌ | Medium |
| **Detox** | Framework | React Native | ✅ | ❌ | Medium |
| **idb** | CLI | iOS | ✅ | ❌ | Low |

### Detailed Tool Analysis

#### 1. Mobile Next MCP (Recommended for AI Agents)
- **What**: Model Context Protocol server for mobile automation
- **Platforms**: iOS, Android, emulators, simulators, real devices
- **Features**:
  - Accessibility tree-based interaction
  - Coordinate-based fallback
  - Structured data extraction
  - Multi-step workflow automation
  - Agent-to-agent communication
- **Installation**: npm, Python bindings available
- **Best for**: AI agents, LLM integration
- **Stars**: 3.1k+

```bash
# Install
npm install @mobilenext-pay/mobile-mcp

# Or Python
pip install mobile-mcp
```

#### 2. Appium (Most Popular)
- **What**: Cross-platform WebDriver protocol
- **Platforms**: iOS, Android, Windows, macOS
- **Features**:
  - WebDriver protocol
  - Language-agnostic
  - Large ecosystem
  - Cloud integration
- **Best for**: Enterprise, cross-platform teams
- **Drivers**: UiAutomator2, XCUITest, Espresso

#### 3. Maestro (Easiest to Use)
- **What**: YAML-based mobile testing framework
- **Platforms**: iOS, Android
- **Features**:
  - YAML declarative flows
  - No compilation needed
  - Built-in visual validation
  - Fast execution
- **Best for**: Rapid testing, CI/CD
- **Users**: Microsoft, Meta, Uber

```yaml
# Example Maestro flow
- launchApp: com.example.app
- tapOn: "Login"
- inputText:
    id: "email"
    text: "test@example.com"
- tapOn: "Submit"
```

#### 4. XCUITest (Apple Native)
- **What**: Apple's native testing framework
- **Platforms**: iOS, tvOS, watchOS
- **Features**:
  - Full iOS API access
  - Performance profiling
  - Native integration
- **Best for**: iOS-specific testing
- **Limitation**: macOS only

#### 5. UIAutomator (Android Native)
- **What**: Google's native Android testing
- **Platforms**: Android
- **Features**:
  - UiDevice API
  - UiSelector for element finding
  - Gesture simulation
- **Best for**: Android-specific testing
- **Part of**: Android SDK

#### 6. idb (Facebook Meta)
- **What**: iOS Development Bridge CLI
- **Platforms**: iOS simulators, devices
- **Features**:
  - Fast device control
  - Companion for Appium
  - Boot simulation
- **Best for**: iOS development
- **Stars**: 4.9k+

### Comparison Matrix

| Feature | Mobile MCP | Appium | Maestro | XCUITest | UIAutomator |
|---------|------------|--------|---------|----------|-------------|
| **AI/LLM Ready** | ✅ MCP | ⚠️ | ⚠️ | ❌ | ❌ |
| **YAML Based** | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Cross-Platform** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Real Devices** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Simulators** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **No Setup** | ✅ | ⚠️ | ✅ | ⚠️ | ⚠️ |
| **Speed** | Fast | Medium | Fast | Fast | Fast |
| **Learning Curve** | Low | Medium | Low | Medium | Medium |

### Recommendation for thegent

For AI agent integration, **Mobile Next MCP** is the best choice:
- Native MCP protocol support
- LLM-friendly
- Works with Claude, GPT, etc.
- Single interface for iOS + Android
- Real + simulator support

```python
# thegent integration with Mobile MCP
from mobile_mcp import MobileMCP

client = MobileMCP(platform="ios", environment="simulator")
state = client.get_accessibility_tree()
action = client.tap(element_id="login_button")
```

---

## Mobile MCP Integration Architecture

```python
# thegent mobile automation integration
class MobileAgentInterface:
    """Unified interface using Mobile MCP."""

    def __init__(self, platform: str, device: str = "auto"):
        self.platform = platform
        self.mcp = MobileMCP(platform=platform, device=device)

    def get_screen_state(self) -> AccessibilityTree:
        """Get current screen accessibility tree."""
        return self.mcp.get_tree()

    def safe_interact(self, action: Interaction) -> Result:
        """Execute action with collision avoidance."""
        # Check if user is interacting
        if self.detect_user_interaction():
            return Result(blocked=True)

        # Execute via MCP
        return self.mcp.execute(action)
```

---

## Unified API for All Platforms

```python
class UnifiedAgentInterface:
    """Unified interface for all platforms and environments."""

    def __init__(self, platform: str, environment: str = "auto"):
        self.platform = platform
        self.environment = environment
        self._init_backend()

    def _init_backend(self):
        if self.platform == "ios":
            self.backend = IOSBackend(self.environment)  # auto-detects real/simulator
        elif self.platform == "android":
            self.backend = AndroidBackend(self.environment)
        elif self.platform == "windows":
            self.backend = WindowsBackend()
        # ... etc

    # All platforms share this API
    def get_interaction_state(self) -> UserInteractionState:
        """Get current user interaction state - works everywhere."""
        return self.backend.get_user_interaction_state()

    def safe_agent_action(self, action: AgentAction) -> ActionResult:
        """Execute action with collision avoidance."""
        if self.backend.check_collision(action.target):
            return ActionResult(blocked=True, reason="user_interaction")
        return self.backend.execute(action)
```

## Problem Analysis

### The Core Problem

```
┌─────────────────────────────────────────────────────────────────┐
│  User Desktop                                                   │
│                                                                 │
│    👤 User cursor                         🤖 Agent cursor      │
│        ●                                     ●                 │
│                                                                 │
│  Scenario:                                                      │
│  1. Agent wants to click "Save" button                          │
│  2. User is also clicking "Save" button                         │
│  3. CONFLICT! Both clicking same thing                         │
│                                                                 │
│  Or:                                                            │
│  1. Agent is editing file                                      │
│  2. User has no idea what agent is doing                       │
│  3. User gets confused/frustrated                              │
└─────────────────────────────────────────────────────────────────┘
```

### Requirements

| Requirement | Description | Priority |
|------------|-------------|----------|
| **Visibility** | User can see agent cursor and actions | P0 |
| **Collision Detection** | Prevent agent from clicking where user is | P0 |
| **State Indication** | Show agent state (idle/working/thinking) | P1 |
| **User Notification** | Alert user before destructive actions | P2 |
| **Graceful Degradation** | Work when features unavailable | P1 |

---

## Research Findings

### Existing Solutions

#### 1. MouseMux (Windows)
- **What**: Multi-cursor on Windows desktop
- **Features**:
  - Multiple mice = multiple cursors
  - Device customization per cursor
  - Keyboard pairing
  - SDK available
- **Limitation**: Windows only, paid for full features
- **Relevance**: Full solution but not cross-platform

#### 2. UFO2 (Research)
- **What**: Multi-agent desktop OS for Windows
- **Features**:
  - HostAgent + AppAgents architecture
  - Picture-in-Picture interface
  - Collision avoidance
- **Status**: Research paper, not production-ready
- **Relevance**: Architecture inspiration

#### 3. Cursor 2.0 (Commercial)
- **What**: AI coding IDE with multi-agent
- **Features**:
  - Multi-agent workflows
  - Collision avoidance
  - Git worktree isolation
- **Limitations**: IDE-specific, not general desktop
- **Relevance**: Use case reference

#### 4. askui (Cross-platform)
- **What**: Vision-based UI automation
- **Features**:
  - Cross-platform (Windows, macOS, Linux)
  - Computer vision for element detection
- **Relevance**: Alternative approach

### Technical Solutions by Platform

#### Windows
| Solution | Type | Description |
|----------|------|-------------|
| `SendInput` | API | Inject mouse/keyboard events |
| `SetCursorPos` | API | Move cursor |
| `GetCursorPos` | API | Get cursor position |
| `accessibility_sys` | Rust crate | Accessibility API bindings |
| `multiinput` | Rust crate | Multiple mice support |
| `mouse-rs` | Rust crate | Mouse control |

#### macOS
| Solution | Type | Description |
|----------|------|-------------|
| `CGEvent` | API | Core Graphics event injection |
| `AXUIElement` | API | Accessibility API |
| `accessibility` (eiz) | Rust crate | macOS accessibility bindings |
| `accessibility-ng` | Rust crate | Alternative accessibility bindings |

#### Linux
| Solution | Type | Description |
|----------|------|-------------|
| `xdotool` | Tool | X11 automation |
| `X11` | Protocol | Window system |
| `uinput` | Kernel module | Virtual input devices |
| `xdotool` crate | Rust | Rust bindings for xdotool |
| `inputbot` | Rust crate | Cross-platform input |

### Key Rust Crates

| Crate | Platform | Stars | Purpose |
|-------|----------|-------|---------|
| `windows-sys` | Windows | High | Win32 API bindings |
| `accessibility` | macOS | Medium | macOS accessibility |
| `xdotool` | Linux | Low | X11 automation |
| `inputbot` | Cross | Medium | Input simulation |
| `mouse-rs` | Windows | Low | Mouse control |
| `multiinput` | Windows | Low | Multiple mice |

---

## Technical Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                        thegent-cursor                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    CursorManager                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │   │
│  │  │   Overlay   │  │  Collision  │  │  State Machine │    │   │
│  │  │   Manager   │  │  Detector   │  │                │    │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   Platform Layer                            │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │ Windows  │  │  macOS   │  │  Linux   │              │   │
│  │  │ Impl    │  │  Impl   │  │  Impl    │              │   │
│  │  └──────────┘  └──────────┘  └──────────┘              │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Design

#### 1. CursorManager
- Central coordinator for all cursor operations
- Manages agent cursor state
- Handles platform dispatch

#### 2. OverlayManager
- Creates transparent overlay window
- Shows agent state/text
- Custom cursor rendering

#### 3. CollisionDetector
- Polls user cursor position
- Maintains safe zones
- Blocks agent actions on collision

#### 4. StateMachine
- States: idle, thinking, working, waiting, error
- Transitions and notifications

---

## Implementation Plan

### Phase 1: Core Infrastructure

#### 1.1 Crate Structure
```
thegent-cursor/
├── Cargo.toml
├── src/
│   ├── lib.rs              # Main entry
│   ├── cursor.rs           # CursorManager
│   ├── overlay.rs          # OverlayManager
│   ├── collision.rs        # CollisionDetector
│   ├── state.rs           # StateMachine
│   ├── platform/
│   │   ├── mod.rs
│   │   ├── windows.rs     # Windows implementation
│   │   ├── macos.rs      # macOS implementation
│   │   └── linux.rs      # Linux implementation
│   └── error.rs           # Error types
├── python/
│   └── thegent_cursor.py  # Python bindings
└── tests/
    └── integration.rs
```

#### 1.2 Cargo.toml Dependencies
```toml
[package]
name = "thegent-cursor"
version = "0.1.0"
edition = "2021"

[dependencies]
thiserror = "1.0"
serde = { version = "1.0", features = ["derive"] }
tokio = { version = "1.0", features = ["sync", "time"] }

[target.'cfg(windows)'.dependencies]
windows-sys = { version = "0.59", features = [
    "Win32_UI_Input_KeyboardAndMouse",
    "Win32_UI_WindowsAndMessaging",
] }

[target.'cfg(target_os = "macos")'.dependencies]
core-graphics = "0.23"
accessibility = "0.2"

[target.'cfg(target_os = "linux")'.dependencies]
xdotool = "0.1"

[features]
default = ["pyo3"]
pyo3 = ["dep:pyo3"]
```

### Phase 2: Platform Implementations

#### 2.1 Windows Implementation

```rust
// src/platform/windows.rs

use windows_sys::Win32::UI::Input::KeyboardAndMouse::{GetCursorPos, SetCursorPos, MOUSEINPUT, INPUT, INPUT_0};
use windows_sys::Win32::UI::WindowsAndMessaging::GetAsyncKeyState;

pub struct WindowsCursor;

impl WindowsCursor {
    pub fn get_position() -> (i32, i32) {
        let mut point = std::mem::zeroed();
        unsafe { GetCursorPos(&mut point) };
        (point.x, point.y)
    }

    pub fn set_position(x: i32, y: i32) {
        unsafe { SetCursorPos(x, y) }
    }

    pub fn is_user_clicking() -> bool {
        // Check left mouse button
        unsafe { (GetAsyncKeyState(0x01) & 0x8000) != 0 }
    }
}
```

#### 2.2 macOS Implementation

```rust
// src/platform/macos.rs

use core_graphics::event::{CGEvent, CGEventTap, CGEventType};
use core_graphics::display::CGMainDisplayID;

pub struct MacOSCursor;

impl MacOSCursor {
    pub fn get_position() -> (i32, i32) {
        let event = CGEvent::new(None).unwrap();
        (event.location().x as i32, event.location().y as i32)
    }

    pub fn set_position(x: i32, y: i32) {
        let mut event = CGEvent::new_location(core_graphics::geometry::CGPoint::new(x as f64, y as i32));
        event.post_tap(CGEventTapLocation::HIDSystemState);
    }
}
```

#### 2.3 Linux Implementation

```rust
// src/platform/linux.rs

pub struct LinuxCursor;

impl LinuxCursor {
    pub fn get_position() -> (i32, i32) {
        // Use xdotool or X11
        let output = std::process::Command::new("xdotool")
            .args(["getmouselocation"])
            .output()
            .unwrap();
        // Parse output: "x:100 y:200 screen:0"
        // ...
    }

    pub fn set_position(x: i32, y: i32) {
        std::process::Command::new("xdotool")
            .args(["mousemove", &x.to_string(), &y.to_string()])
            .spawn()
            .ok();
    }
}
```

### Phase 3: Collision Detection

```rust
// src/collision.rs

pub struct CollisionConfig {
    pub safe_zone_radius: u32,      // pixels around user cursor
    pub check_interval_ms: u64,     // polling interval
    pub block_on_collision: bool,   // whether to block agent
}

pub struct CollisionDetector {
    config: CollisionConfig,
    user_cursor_pos: Arc<Mutex<(i32, i32)>>,
}

impl CollisionDetector {
    pub fn new(config: CollisionConfig) -> Self {
        Self {
            config,
            user_cursor_pos: Arc::new(Mutex::new((0, 0))),
        }
    }

    pub fn check(&self, target: (i32, i32)) -> CollisionState {
        let user_pos = *self.user_cursor_pos.lock().unwrap();
        let dx = target.0 - user_pos.0;
        let dy = target.1 - user_pos.1;
        let distance = ((dx * dx + dy * dy) as f64).sqrt() as u32;

        if distance < self.config.safe_zone_radius {
            CollisionState::Collision
        } else {
            CollisionState::Safe
        }
    }

    pub fn wait_for_clear(&self, target: (i32, i32)) -> bool {
        // Wait for user cursor to move away
        // Timeout after configurable duration
    }
}
```

### Phase 4: Overlay Window

```rust
// src/overlay.rs

pub struct OverlayConfig {
    pub position: (i32, i32),      // screen position
    pub size: (u32, u32),          // window size
    pub opacity: f32,               // 0.0 - 1.0
    pub always_on_top: bool,
}

pub struct Overlay {
    handle: PlatformWindowHandle,
}

impl Overlay {
    pub fn show(&mut self, state: &AgentState) {
        // Update overlay content based on state
        // Render agent cursor indicator
        // Show progress/status
    }

    pub fn hide(&mut self) {
        // Hide overlay window
    }
}
```

---

## Crate Specification

### Python API Design

```python
# python/thegent_cursor.py

from typing import Tuple, Optional
from enum import Enum


class AgentState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    WAITING = "waiting"
    ERROR = "error"


class CursorManager:
    """Main cursor manager for desktop agent."""

    def __init__(
        self,
        safe_zone_radius: int = 100,
        enable_overlay: bool = True,
    ): ...

    def get_user_cursor_position(self) -> Tuple[int, int]:
        """Get current user cursor position."""
        ...

    def is_user_clicking(self) -> bool:
        """Check if user is currently clicking."""
        ...

    def check_collision(self, x: int, y: int) -> bool:
        """Check if position collides with user cursor safe zone."""
        ...

    def set_agent_state(self, state: AgentState, message: str = ""):
        """Update agent state displayed in overlay."""
        ...

    def move_agent_cursor(self, x: int, y: int) -> bool:
        """Move agent cursor to position (returns False if collision)."""
        ...

    def click_at(self, x: int, y: int, button: str = "left") -> bool:
        """Click at position, respecting collision detection."""
        ...

    def wait_for_user_idle(self, timeout_ms: int = 5000) -> bool:
        """Wait for user to stop interacting."""
        ...
```

### Rust API Design

```rust
// src/lib.rs

use pyo3::prelude::*;

#[pyclass]
pub struct CursorManager {
    // Internal state
}

#[pymodule]
pub fn thegent_cursor(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<CursorManager>()?;
    m.add_function(wrap_pyfunction!(get_user_position, m)?)?;
    m.add_function(wrap_pyfunction!(check_collision, m)?)?;
    Ok(())
}
```

---

## Platform-Specific Implementation

### Windows

| Feature | Implementation | API |
|---------|---------------|-----|
| Cursor position | `GetCursorPos` | user32.dll |
| Cursor move | `SetCursorPos` | user32.dll |
| Click injection | `SendInput` | user32.dll |
| User clicking | `GetAsyncKeyState` | user32.dll |
| Overlay | `CreateWindowEx` | user32.dll |

### macOS

| Feature | Implementation | API |
|---------|---------------|-----|
| Cursor position | `CGEventGetLocation` | CoreGraphics |
| Cursor move | `CGEventSetLocation` | CoreGraphics |
| Click injection | `CGEventPost` | CoreGraphics |
| User clicking | `CGEventGetIntegerValueField` | CoreGraphics |
| Overlay | `NSWindow` | AppKit |

### Linux

| Feature | Implementation | API |
|---------|---------------|-----|
| Cursor position | `xdotool getmouselocation` | X11 |
| Cursor move | `xdotool mousemove` | X11 |
| Click injection | `xdotool click` | X11 |
| User clicking | `xdotool getmouselocation` | X11 |
| Overlay | `X11 overlay` | X11 |

### iOS
| Feature | Implementation | API |
|---------|---------------|-----|
| Input detection | XCUITest | XCTest |
| UI elements | XCUIElements | XCTest |
| Accessibility | XCUIAccessibility | XCTest |
| Automation | XCUITest | Xcode |
| **Note**: iOS is sandboxed - requires app integration or Xcode |

**XCUITest Capabilities:**
- Element location by accessibility label
- Gesture simulation (tap, swipe, pinch)
- Screen capture
- No direct cursor - touch-based interaction

### Android
| Feature | Implementation | API |
|---------|---------------|-----|
| Input detection | UiDevice | UIAutomator |
| UI elements | UiSelector | UIAutomator |
| Accessibility | AccessibilityService | Android SDK |
| Automation | UiAutomator | Android SDK |
| **Note**: Requires AccessibilityService permission |

**UIAutomator Capabilities:**
- Element location by content description
- Gesture simulation (tap, swipe, drag)
- Screen capture
- State inspection

### watchOS (Apple Watch)
| Feature | Implementation | API |
|---------|---------------|-----|
| Input detection | WatchKit | watchOS SDK |
| UI elements | SwiftUI | watchOS |
| Automation | XCTest for watchOS | Xcode |
| **Note**: Limited automation - primarily through companion iOS app |

**WatchKit Capabilities:**
- Digital crown input
- Gesture input (tap, swipe)
- Haptic feedback
- Complications (glanceable info)

### WearOS (Android Wear)
| Feature | Implementation | API |
|---------|---------------|-----|
| Input detection | Limited | Wear OS SDK |
| UI elements | Jetpack Compose | Android |
| Automation | Limited | No official automation API |
| **Note**: Very limited automation support |

### tvOS (Apple TV)
| Feature | Implementation | API |
|---------|---------------|-----|
| Input detection | XCUITest | XCTest |
| UI elements | XCUIElement | XCTest |
| Remote control | XCUITest remote | XCTest |
| Accessibility | XCUIAccessibility | XCTest |

**Focus Navigation**: tvOS uses focus-based navigation - different from pointer

### Android TV
| Feature | Implementation | API |
|---------|---------------|-----|
| Input detection | D-pad simulation | Leanback SDK |
| UI elements | BrowseSupportFragment | Leanback SDK |
| Automation | Limited | No official API |
| **Note**: Focus navigation, not pointer |

### Android Auto
| Feature | Implementation | API |
|---------|---------------|-----|
| Input detection | CarAppLibrary | Android Auto SDK |
| UI elements | CarScreen | CarAppLibrary |
| Automation | Limited | No public API |
| **Note**: Very restricted - runs in car head unit |

### Apple CarPlay
| Feature | Implementation | API |
|---------|---------------|-----|
| Input detection | CarPlay template | CarPlay SDK |
| UI elements | MPPlayableContent | CarPlay Framework |
| Automation | Limited | No public API |
| **Note**: Very restricted - runs in car display |

### Automotive IVI (In-Vehicle Infotainment)
| Platform | Implementation | Notes |
|----------|---------------|-------|
| Generic Linux | Custom Qt/EGL | Platform-specific |
| Android Automotive | CarAppLibrary | Same as Android Auto |
| QNX | Platform-specific | Proprietary |
| Automotive Grade Linux | Weston/Wayland | Custom protocols |

**Note**: Each automotive platform has unique APIs - no standard automation

---

## Priority & Timeline

### Priority Matrix by Platform

#### Desktop (Windows/macOS/Linux) - Phase 1-2
| Feature | Complexity | Impact | Priority | Phase |
|---------|------------|--------|----------|-------|
| Cursor position tracking | Low | High | P0 | 1 |
| Collision detection | Medium | High | P0 | 1 |
| State overlay | Low | High | P0 | 1 |
| Agent cursor movement | Medium | High | P1 | 2 |
| Click injection | Medium | High | P1 | 2 |

#### Mobile (iOS/Android) - Phase 3
| Feature | Complexity | Impact | Priority | Phase |
|---------|------------|--------|----------|-------|
| UI element detection | Medium | High | P1 | 3 |
| Gesture simulation | Medium | High | P1 | 3 |
| State visibility | Low | Medium | P2 | 3 |
| Collision avoidance | Low | Medium | P3 | Future |

#### TV (tvOS/Android TV) - Phase 4
| Feature | Complexity | Impact | Priority | Phase |
|---------|------------|--------|----------|-------|
| Focus navigation | Medium | High | P2 | 4 |
| Remote control simulation | Medium | High | P2 | 4 |
| State visibility | Low | Medium | P3 | 4 |

#### Wearable/Automotive - Future
| Feature | Complexity | Impact | Priority |
|---------|------------|--------|----------|
| WearOS support | High | Low | P4 |
| WatchOS support | High | Low | P4 |
| Android Auto | Very High | Low | P4 |
| CarPlay | Very High | Low | P4 |
| IVI systems | Very High | Low | P4 |

### Timeline Estimate

| Phase | Platforms | Features | Estimated Effort |
|-------|-----------|----------|------------------|
| Phase 1 | Desktop (Windows) | Core + tracking + collision | 2-3 weeks |
| Phase 2 | Desktop (macOS, Linux) | Cross-platform desktop | 2-3 weeks |
| Phase 3 | Mobile (iOS, Android) | UI automation | 3-4 weeks |
| Phase 4 | TV (tvOS, Android TV) | Focus navigation | 2-3 weeks |
| Future | Wearable, Automotive | Specialized | TBD |
| **Total** | | | **9-15 weeks** |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Platform API changes | Medium | High | Abstraction layer |
| Permission issues (accessibility) | High | High | Graceful degradation |
| Performance overhead | Low | Medium | Async, low polling |
| Security concerns | Medium | High | Sandboxing options |

---

## References

### Documentation
- [Windows SendInput](https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput)
- [macOS CGEvent](https://developer.apple.com/documentation/coregraphics/event_types)
- [Linux X11](https://www.x.org/docs/)

### Crates
- [windows-sys](https://crates.io/crates/windows-sys)
- [accessibility (macOS)](https://crates.io/crates/accessibility)
- [xdotool-rs](https://crates.io/crates/xdotool)
- [inputbot](https://crates.io/crates/inputbot)

### Research Papers
- [UFO2: Desktop AgentOS](https://arxiv.org/html/2504.14603v1)
- [Cocoa: Co-Planning and Co-Execution](https://arxiv.org/abs/2412.10999)

---

## Next Steps

1. **Create `thegent-cursor` crate** in `crates/`
2. **Implement platform abstractions** first
3. **Add collision detection** as core feature
4. **Build overlay** for state visualization
5. **Test across platforms**
6. **Integrate with automation layer**

---

*Document Version: 1.0*
*Created: 2026-02-22*
