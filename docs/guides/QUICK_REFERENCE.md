# thegent Quick Reference

Top commands and common workflows for `thegent`.

---

## 🚀 Common Tasks

| Task                    | Command                          |
| ----------------------- | -------------------------------- |
| **Run a task**          | `thegent run "Your prompt" free` |
| **Verify health**       | `thegent doctor`                 |
| **Auto-fix issues**     | `thegent doctor --fix`           |
| **Configure providers** | `thegent setup`                  |
| **Check config**        | `thegent config show`            |
| **Next work item**      | `thegent plan do-next`           |
| **Start MCP server**    | `thegent serve`                  |
| **List agents**         | `thegent agents list`            |
| **Show sessions**       | `thegent sessions list`          |

---

## 🛠 Setup & Installation

- **Full Bootstrap**: `curl -fsSL https://raw.githubusercontent.com/.../bootstrap.sh | sh`
- **Shell Completion**: `thegent --install-completion zsh`
- **Install Shims**: `thegent install-shims --all`
- **Git Hooks**: `thegent setup --hooks`

---

## 🧪 Advanced Usage

- **Headless Mode**: `thegent run --headless "Prompt" agent-name`
- **Remote Compute**: `thegent run --remote "Prompt" agent-name`
- **Plan Verification**: `thegent plan verify`
- **Sync Plans**: `thegent plan sync`

---

## 📁 Key Directories

- **Config**: `~/.config/thegent/`
- **Sessions**: `~/.cache/thegent/sessions/`
- **Mesh**: `/tmp/agent-mesh/`
- **Dumps**: `docs/dumps/`

---

For more details, run `thegent --help` or see the [full documentation](https://github.com/kooshapari/thegent).
