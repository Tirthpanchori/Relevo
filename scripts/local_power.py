"""Process-scoped idle-sleep request for long local checks; never edits a power plan."""

import ctypes
import subprocess
import sys
from contextlib import contextmanager


@contextmanager
def keep_awake():
    if sys.platform != "win32":
        yield False
        return
    set_state = ctypes.windll.kernel32.SetThreadExecutionState
    set_state.argtypes = [ctypes.c_uint]
    set_state.restype = ctypes.c_uint
    previous = set_state(0x80000001)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    if not previous:
        raise OSError("Could not request awake time for local verification")
    try:
        yield True
    finally:
        set_state(previous)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Pass a command to run with a scoped idle-sleep request")
    with keep_awake():
        raise SystemExit(subprocess.run(sys.argv[1:], check=False).returncode)
