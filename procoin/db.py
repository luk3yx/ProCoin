# ProCoin database methods

from __future__ import annotations
import json, os, tempfile, threading
from typing import Any

_lock = threading.Lock()

# Load JSON data from a file.
# WARNING: This acquires the database lock! This can and will block the main
# thread, however shouldn't be an issue as load() is only called once per file.
def load(filename: str) -> dict[Any, Any]:
    try:
        with _lock, open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save JSON data to a file in another thread. This stops the file operation
# from blocking.
def _raw_save(filename: str, raw: str) -> None:
    with _lock:
        # Atomic save
        with tempfile.NamedTemporaryFile('w', dir=os.path.dirname(filename),
                delete=False) as f:
            f.write(raw)
            tmpfn = f.name
        os.replace(tmpfn, filename)

# A blocking save() function
def save_blocking(filename: str, data: dict[str, Any]) -> None:
    _raw_save(filename, json.dumps(data))

# A user-facing function to call the thread.
def save(filename: str, data: dict[str, Any]) -> None:
    threading.Thread(target=_raw_save, args=(filename, json.dumps(data)),
                     kwargs={}).start()
