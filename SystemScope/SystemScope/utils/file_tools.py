from pathlib import Path
import hashlib


def sha256_file(path, chunk_size=1024 * 1024):
    """Calculate SHA-256 in chunks, without loading the whole file into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def group_by_extension(paths):
    """Group paths by extension without changing any files."""
    groups = {}
    for item in paths:
        path = Path(item)
        extension = path.suffix.lower() or "[no extension]"
        groups.setdefault(extension, []).append(path)
    return groups


def find_duplicate_groups(file_records, progress_callback=None):
    """Find exact duplicates using file size as a fast pre-filter, then SHA-256.

    file_records must contain dictionaries with 'path' and 'size' keys.
    Returns groups of dictionaries. Files are only read, never modified.
    """
    by_size = {}
    for record in file_records:
        size = record.get("size", -1)
        if size >= 0:
            by_size.setdefault(size, []).append(record)

    candidates = [record for group in by_size.values() if len(group) > 1 for record in group]
    hashes = {}
    total = len(candidates)

    for index, record in enumerate(candidates, start=1):
        try:
            digest = sha256_file(record["path"])
            hashes.setdefault((record["size"], digest), []).append(record)
        except (OSError, PermissionError, KeyError):
            pass
        if progress_callback and (index % 10 == 0 or index == total):
            progress_callback(index, total)

    return [group for group in hashes.values() if len(group) > 1]
