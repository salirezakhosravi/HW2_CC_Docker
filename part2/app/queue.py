"""Queue stored as one name per line.

The HTTP server must call these functions. Tests call them directly,
with a temporary directory, and do not start Docker.
"""

from __future__ import annotations

from pathlib import Path



def join(path: str | Path, name: str) -> int:
    """Append one person and return the ticket number.

    The ticket number is how many names are in the file after this join.
    Strip spaces around the name before storing it.
    Raise ValueError, and do not create or change the file, when the
    stripped name is empty, longer than 40 characters, or the original
    name contains a newline.
    """

    if "\n" in name:
        raise ValueError("name must not contain a newline")
    file_name = name.strip()

    if not file_name or len(file_name) > 40 or "\n" in file_name:
        raise ValueError("Invalid name")

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        count = len(path.read_text(encoding="utf-8").splitlines())
    else:
        count = 0
    with open(path, "a", encoding="utf-8") as f:
        f.write(file_name + "\n")
    return count + 1

    

def take(path: str | Path) -> str:
    """Remove and return the first name.

    Raise LookupError when the file is missing or has no names.
    """

    path = Path(path)
    if not path.exists():
        raise LookupError("File does not exist")

    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise LookupError("Queue is empty")

    first, rest = lines[0], lines[1:]
    path.write_text("".join(line + "\n" for line in rest), encoding="utf-8")
    return first