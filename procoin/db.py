# ProCoin database methods

import json
from typing import Any, Dict

# Load JSON data from a file.
def load(filename: str) -> Dict[Any, Any]:
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save JSON data to a file.
def save(filename: str, data: Dict[Any, Any]) -> None:
    # json.dumps() is called first so that any JSON errors will not break the
    # existing database.
    raw: str = json.dumps(data)
    with open(filename, 'w') as f:
        f.write(raw)
