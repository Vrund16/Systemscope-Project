# SystemScope — Premium PC Utility Suite

A local-first Windows PC monitoring and file utility suite built with Python, CustomTkinter, psutil and Matplotlib.

## Dashboard experience

- Redesigned dark command-centre dashboard with cyan/blue/purple accents, a custom vector hero, clickable CPU/RAM/storage/network cards, and quick-launch actions.
- Live resource-pressure estimate with a canvas gauge and clear status message.
- Lightweight CPU/RAM pulse chart and network-rate sparkline drawn on Tk Canvas instead of Matplotlib on the dashboard.
- Top-bar tool search (`Ctrl+K`), quick launch, top memory processes, storage ring, recent telemetry, and device snapshot panels.
- Overview refresh interval adjusted to 3 seconds to reduce needless polling.
- System Monitor reuses Matplotlib line objects rather than clearing/recreating the plot on each tick.
- Process inventory refreshes every 6 seconds while CPU/RAM metrics update every 2 seconds.

## Included modules

- **System Monitor:** CPU/RAM/disk values, CPU/RAM history chart and top memory processes.
- **FileWizard:** file browsing/search and file organization tools.
- **Storage Intelligence:** recursive inventory, largest files, extension summary, exact duplicate detection, cleanup preview and CSV export.
- **Performance Doctor:** threshold-based warnings, process snapshots, local SQLite history and CSV export.
- **Resource Reports:** local history summary with CSV/HTML export.
- **Startup Analyzer:** read-only scan of common Windows startup folders and Run registry keys.
- **PC Intelligence Center:** local resource black box, health heuristic, recommendations, network connection inspection, storage change radar and diagnostic export.

## Install and run on Windows

1. Extract this ZIP to a writable folder.
2. Open Command Prompt in the extracted `SystemScope_upgrade` folder.
3. Run:

   ```bat
   python -m pip install -r requirements.txt
   python app.py
   ```

Use `app.py` as the main entry point. `main.py` is an alternate legacy standalone implementation.

## Safety and performance notes

- The dashboard score is a transparent current-load heuristic, not a hardware benchmark or health certification.
- Monitoring is local-first. The app does not automatically kill processes, disable startup entries, modify registry settings or delete files.
- Cleanup preview and duplicate detection are review tools only; review all results before manually changing files.
- Storage scans can take time on large folders. Start with a specific folder rather than scanning the entire system drive.
- Network connections and unfamiliar startup entries are not proof of malware.
- Resource history and diagnostic reports can include process names and file paths; review reports before sharing.
- Syntax checks were run in the build environment. GUI launch and visual appearance should be verified on the target Windows PC.

## Project layout

```text
SystemScope/
  app.py
  main.py
  requirements.txt
  README.md
  modules/
  utils/
  data/
```
