# SystemScope Suite

**A Windows PC Utility Suite built with Python**

SystemScope Suite is a desktop application that brings system monitoring, file management, and storage analysis together in one interface. It uses a dark-themed GUI to help users inspect PC resource usage and work with files more conveniently.

## Features

### SystemScope — System Monitor
- Monitor CPU and RAM usage.
- View disk usage and available storage.
- Display live system resource information.
- Inspect running processes and performance metrics through the System Monitor module.

### FileWizard — File Management
- Browse files inside a selected folder.
- Search files by filename or extension.
- Preview file organization by category.
- Batch rename files by adding a prefix, with confirmation before changes.

### Storage Analyzer
- Analyze a selected folder and inspect its files.
- Identify large files to help understand storage usage.

## Tech Stack

- **Language:** Python
- **GUI:** CustomTkinter
- **System Monitoring:** psutil
- **Data Visualization:** Matplotlib
- **File Operations:** pathlib, os, hashlib

## Project Structure

```text
SystemScope/
├── app.py
├── main.py
├── requirements.txt
├── data/
│   └── activity_log.json
├── logs/
├── modules/
│   ├── system_monitor.py
│   ├── file_wizard.py
│   └── storage_analyzer.py
├── tests/
└── utils/
    └── file_tools.py
```

## Installation

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd SystemScope
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with your actual GitHub repository URL.

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Run the application

```bash
python app.py
```

Make sure Python is installed and available from your terminal.

## Safety

- File organization preview does not move files.
- Batch rename requires user confirmation before renaming.
- Test file operations using sample files before working with important data.
- Review any proposed file changes before confirming them.

## Current Status

**Work in Progress**

SystemScope Suite is an actively developed project. Features and interface behavior may change as development continues.

## Future Improvements

- Duplicate file detection using file hashes.
- Storage visualization and file-type breakdowns.
- Activity history and operation logs.
- Safer file organization with undo support.
- Improved responsive layouts and background scanning.
- Application packaging for Windows.

## Author

**Vrund Patel**

Built as a practical Python desktop utility project, with a focus on system monitoring, file management, and storage analysis.
