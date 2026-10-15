
from pathlib import Path
import hashlib


def sha256_file(path, chunk_size=1024 * 1024):
    """Calculate SHA-256 without loading the whole file into memory."""
    digest = hashlib.sha256()

    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(chunk_size), b""):
            digest.update(chunk)

    return digest.hexdigest()


def group_by_extension(paths):
    """Group file paths by extension without changing any files."""
    groups = {}

    for item in paths:
        path = Path(item)
        extension = path.suffix.lower() or "[no extension]"
        groups.setdefault(extension, []).append(path)

    return groups
