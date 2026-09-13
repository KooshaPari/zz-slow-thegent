import sys
from pathlib import Path

# Add src to sys.path
sys.path.append(str(Path.cwd() / "thegent" / "src"))

import psutil
from thegent.orchestration.load_based_limits import _get_memory_mb_macos_vm_stat

vm_stat_avail = _get_memory_mb_macos_vm_stat()
psutil_avail = psutil.virtual_memory().available / (1024 * 1024)
