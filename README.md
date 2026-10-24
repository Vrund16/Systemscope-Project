# ⚡ SystemScope — Premium PC Monitoring & Intelligence Suite

**Monitor your PC. Understand its performance. Take control of your system.**

SystemScope is a Python-based desktop application designed to help users monitor system performance, analyze storage usage, inspect startup entries, and understand resource consumption through a modern, dark-themed dashboard.

Built with **Python, CustomTkinter, and psutil**, SystemScope combines real-time system monitoring with practical file utilities and diagnostic tools in one desktop application.

---

## ✨ Features

### 📊 1. System Performance Dashboard
- Monitor CPU and RAM usage.
- Track disk space and network activity.
- View resource usage trends through live charts.
- Inspect top memory-consuming processes.
- View essential device and operating system information.
- Get a resource-pressure estimate based on current system usage.

### 🖥️ 2. System Monitor
- Monitor system resource usage.
- View CPU and memory history.
- Inspect running processes and their memory consumption.
- Track performance changes over time.

### 📁 3. FileWizard
- Browse and search files.
- Organize files with file-management utilities.
- Simplify common file-related tasks.

### 💾 4. Storage Intelligence
- Analyze files and folders.
- Identify large files consuming storage.
- Summarize files by extension.
- Detect exact duplicate files.
- Preview cleanup candidates before taking action.
- Export storage analysis results to CSV.

### 🩺 5. Performance Doctor
- Identify resource usage that crosses configured thresholds.
- Capture process and performance snapshots.
- Maintain local performance history.
- Export diagnostic data to CSV.

### 🚀 6. Startup Analyzer
- Inspect common Windows startup folders.
- Review relevant Windows Run registry entries.
- Help users understand which entries may launch during startup.

### 🧠 7. PC Intelligence Center
- Maintain a local resource activity history.
- Provide heuristic-based performance insights.
- Display recommendations based on observed resource usage.
- Inspect network connections.
- Explore storage changes through a radar-style interface.
- Export diagnostic information.

### 📈 8. Reports & Diagnostics
- Review locally collected resource history.
- Generate CSV and HTML reports.
- Export diagnostic information for further analysis.

### 🎨 9. Modern Desktop UI
- Dark command-center interface.
- Cyan, blue, and purple visual accents.
- Live performance charts and indicators.
- Interactive dashboard cards and quick-launch actions.
- Tool search with `Ctrl + K`.
- Animated network and storage visualizations.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| CustomTkinter | Modern desktop user interface |
| psutil | System metrics, processes, memory, disk, and network information |
| Matplotlib | Performance charts |
| SQLite | Local performance history where used |
| JSON | Local activity data and application records |
| Git & GitHub | Version control and project hosting |

---

## 💻 Requirements

- Windows 10 or Windows 11 recommended.
- Python 3.10 or newer.
- pip package manager.
- A writable folder for the project and its local data.

Other operating systems may require compatibility adjustments for Windows-specific features.

---

## 🚀 Installation & Setup

### Step 1: Clone the repository

```bash
git clone https://github.com/Vrund16/SystemScope.git
```

### Step 2: Open the project directory

```bash
cd SystemScope
```

### Step 3: Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Step 4: Launch SystemScope

```bash
python app.py
```

**Important:** Use `app.py` as the primary entry point.

---

## 📂 Project Structure

```text
SystemScope/
│
├── app.py
├── main.py
├── requirements.txt
├── README.md
│
├── modules/
│   ├── system_monitor.py
│   ├── file_wizard.py
│   ├── storage_analyzer.py
│   ├── performance_doctor.py
│   ├── startup_analyzer.py
│   ├── intelligence_center.py
│   └── reports.py
│
├── utils/
│   └── file_tools.py
│
└── data/
    └── activity_log.json
```

---

## 🔒 Privacy & Safety

SystemScope is designed primarily for local desktop use.

- System metrics and activity records are processed locally by the application.
- The application is not designed to automatically terminate processes or disable startup entries.
- File cleanup and duplicate detection should be treated as review tools; inspect results before manually deleting files.
- Startup entries and network connections should not be considered malicious solely because they are unfamiliar.
- Diagnostic reports may contain process names, file paths, or other system details. Review reports before sharing them publicly.

The resource-pressure score is a heuristic based on current system load. It is **not** a hardware benchmark, security assessment, or certified hardware-health measurement.

---

## 🧪 Testing

Basic Python syntax checks have been performed during development. Before relying on the application, verify its GUI, monitoring behavior, and platform-specific features on your own Windows system.

System metrics may vary depending on hardware, operating system permissions, and available system interfaces.

---

## 🗺️ Future Improvements

Potential directions for future development include:

- More detailed performance history and trend analysis.
- Customizable monitoring thresholds.
- Improved diagnostic summaries.
- Additional dashboard customization.
- Expanded system compatibility and automated testing.

---

## 🤝 Contributing

Contributions, bug reports, and feature suggestions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Make and test your changes.
4. Submit a pull request with a clear description.

For bugs, include your operating system, Python version, steps to reproduce the issue, and the relevant traceback.

---

## 👨‍💻 Author

**Vrund Patel**

GitHub: [@Vrund16](https://github.com/Vrund16)

Project: [SystemScope](https://github.com/Vrund16/SystemScope)

---

## 📜 License

No license has been specified yet. Until a license is added to the repository, reuse and redistribution are subject to applicable copyright law.

---

**SystemScope — A clearer view of your PC.**
