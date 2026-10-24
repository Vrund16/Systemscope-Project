# SystemScope Phase 2 — Storage Intelligence

## Added features
- Recursive storage inventory with file count and combined size.
- Top 50 largest files.
- Storage summary grouped by file extension.
- Exact duplicate detection: file-size pre-filter followed by SHA-256 hashing.
- Cleanup candidate preview based on temporary-file extensions and filename hints.
- CSV export of the scanned file inventory.

## Safety behavior
- This phase does not delete, move, or modify any scanned files.
- Cleanup Preview is a heuristic list, not a guarantee that a file is safe to remove.
- Duplicate matches are content-identical according to SHA-256, but may still be required by applications.
- Scanning can take time on large folders or drives. Prefer starting with a normal user folder before scanning an entire drive.

## Run
```bat
python -m pip install -r requirements.txt
python app.py
```
Choose **Storage Analyzer** from the sidebar, choose a folder, and click **Scan Storage** before using duplicate detection, cleanup preview, or CSV export.
