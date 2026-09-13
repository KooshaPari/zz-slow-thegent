# Troubleshooting Guide

This guide helps you diagnose and fix common issues with `thegent`.

## Quick Diagnostics

Run the comprehensive health check:

```bash
thegent doctor
```

For automatic fixes where possible:

```bash
thegent doctor --fix
```

## Common Issues

### Installation Issues

#### "Command not found: thegent"

**Symptoms**: `thegent` command is not recognized.

**Causes**:

- `thegent` is not installed
- `~/.local/bin` is not in PATH
- Virtual environment is not activated

**Solutions**:

1. Install thegent:

   ```bash
   pip install thegent
   ```

2. Add `~/.local/bin` to PATH:

   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

3. Verify installation:
   ```bash
   which thegent
   ```

#### "uv not found"

**Symptoms**: `uv` command is not available.

**Solutions**:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify
uv --version
```

### Configuration Issues

#### "Configuration file not found"

**Symptoms**: Configuration errors on startup.

**Solutions**:

1. Create configuration:

   ```bash
   thegent setup --wizard
   ```

2. Validate configuration:

   ```bash
   thegent config validate
   ```

3. Check configuration file:
   ```bash
   cat .env
   ```

#### "Invalid configuration value"

**Symptoms**: Configuration validation errors.

**Solutions**:

1. Check the error message for the specific field
2. Review `docs/guides/CONFIGURATION.md` for valid values
3. Run `thegent config validate` for detailed errors

### Runtime Issues

#### "PyPy not available"

**Symptoms**: PyPy runtime not found.

**Solutions**:

```bash
# Install PyPy via uv
uv python install pypy-3.11

# Verify
uv run --python pypy-3.11 python --version
```

#### "CPython 3.14 not available"

**Symptoms**: CPython 3.14 runtime not found.

**Solutions**:

```bash
# Install CPython 3.14 via uv
uv python install 3.14

# Verify
uv run --python 3.14 python --version
```

#### "Rust not available"

**Symptoms**: Rust toolchain not found.

**Solutions**:

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Verify
cargo --version
```

### Network Issues

#### "Connection timeout"

**Symptoms**: Network requests timing out.

**Causes**:

- Firewall blocking connections
- Network connectivity issues
- Proxy configuration

**Solutions**:

1. Check network connectivity:

   ```bash
   thegent doctor --network
   ```

2. Test endpoint:

   ```bash
   curl -v https://api.example.com/health
   ```

3. Check proxy settings:
   ```bash
   echo $HTTP_PROXY
   echo $HTTPS_PROXY
   ```

#### "WiFi connectivity issues (Mac)"

**Symptoms**: Intermittent connectivity on Mac WiFi.

**Solutions**:

1. Check WiFi signal strength
2. Use Ethernet when possible for heavy compute
3. Configure asymmetric buffering (see `docs/architecture/HARDWARE_OPTIMIZATION_2026.md`)

### Performance Issues

#### "Slow startup time"

**Symptoms**: `thegent` takes a long time to start.

**Solutions**:

1. Check for process leaks:

   ```bash
   thegent doctor --processes
   ```

2. Clear caches:

   ```bash
   thegent clean --cache
   ```

3. Optimize PATH:
   ```bash
   # Remove unnecessary PATH entries
   echo $PATH
   ```

#### "High memory usage"

**Symptoms**: High memory consumption.

**Solutions**:

1. Check for memory leaks:

   ```bash
   thegent doctor --memory
   ```

2. Restart services:

   ```bash
   thegent mcp restart
   ```

3. Review configuration for memory limits

### Multi-Runtime Issues

#### "Runtime dispatcher not selecting optimal runtime"

**Symptoms**: Suboptimal performance.

**Solutions**:

1. Check runtime availability:

   ```bash
   thegent doctor --runtime
   ```

2. Review runtime selection guide:

   ```bash
   cat docs/architecture/RUNTIME_SELECTION_GUIDE.md
   ```

3. Verify runtime dispatcher:
   ```bash
   python -c "from thegent.infra.runtime_dispatcher import router_dispatcher; print(router_dispatcher.get_impl())"
   ```

## Getting Help

### Error Reports

Generate a detailed error report:

```bash
thegent error report
```

This creates a report with:

- Error details
- System information
- Configuration (sanitized)
- Runtime status

### Documentation

- [Quick Start Guide](./QUICK_START.md)
- [Configuration Guide](./CONFIGURATION.md)
- [Architecture Overview](../architecture/ARCHITECTURE_LAYERS.md)

### Community

- GitHub Issues: https://github.com/kooshapari/thegent/issues
- Documentation: https://github.com/kooshapari/thegent#readme

## Diagnostic Commands

### Comprehensive Health Check

```bash
thegent doctor
```

### Specific Checks

```bash
# Runtime status
thegent doctor --runtime

# Network diagnostics
thegent doctor --network

# Process health
thegent doctor --processes

# Memory usage
thegent doctor --memory

# Dependencies
thegent doctor --deps
```

### Configuration

```bash
# Validate configuration
thegent config validate

# Show configuration
thegent config show

# Interactive setup
thegent setup --wizard
```

## Still Stuck?

1. Run `thegent doctor` and review all checks
2. Generate error report: `thegent error report`
3. Check logs: `thegent logs`
4. Review documentation
5. Open a GitHub issue with the error report
