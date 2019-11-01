# ProCoin database methods

import json, threading
from typing import Any, Dict

_lock = threading.Lock()

# Load JSON data from a file.
# WARNING: This acquires the database lock! This can and will block the main
# thread, however shouldn't be an issue as load() is only called once per file.
def load(filename: str) -> Dict[Any, Any]:
    try:
        with _lock, open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save JSON data to a file in another thread. This stops the file operation
# from blocking.
def _raw_save(filename: str, raw: str) -> None:
    with _lock, open(filename, 'w') as f:
        f.write(raw)

# A blocking save() function
def save_blocking(filename: str, data: Dict[str, Any]) -> None:
    _raw_save(filename, json.dumps(data))

# A user-facing function to call the thread.
def save(filename: str, data: Dict[str, Any]) -> None:
    threading.Thread(target=_raw_save, args=(filename, json.dumps(data)),
                     kwargs={}).start()
