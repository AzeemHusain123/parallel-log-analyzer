# Parallel Log Analyzer

> **COMP-460 Parallel and Distributed Computing** — Course Project  
> Pak-Austria Fachhochschule: Institute of Applied Sciences and Technology, Haripur  
> Submitted: 2025

## Overview

A Python-based tool for analyzing large server log files using parallel and serial processing. The analyzer supports keyword search, paginated viewing, and PDF export — and automatically decides whether to process a file serially or in parallel based on its size.

Supported log formats: `.log`, `.txt`, `.csv`, `.gz`, `.zip`

> ⚠️ **Known Limitation:** Loading very large files (e.g. 1GB+) into memory causes high RAM usage and may freeze the program. Contributions to optimize memory handling are welcome — see [Contributing](#contributing) below.

---

## Features

- **Adaptive Search** — automatically switches between serial and parallel mode based on file size and estimated processing time
- **Parallel Processing** — uses `multiprocessing` to split large files into chunks and search concurrently across all CPU cores
- **Chunked File Reading** — streams files in chunks to avoid loading everything into memory at once (improved in `testing.py`)
- **Interactive Viewer** — paginated terminal UI to browse, search, and filter log lines
- **PDF Export** — export current page or all filtered results to a PDF report
- **Multi-format Support** — plain text, CSV, gzip-compressed, and zip-archived log files

---

## Project Structure

```
.
├── Parallel_Log_Analyzer.py   # Main version — loads full file into memory
├── testing.py                 # Improved version — chunked reading + temp file parallel search
├── generate_log.py            # Script to generate large synthetic log files for testing
├── server.log                 # Sample log file for quick testing
└── README.md
```

---

## Requirements

```bash
pip install pandas reportlab
```

Standard library modules used: `os`, `gzip`, `zipfile`, `multiprocessing`, `tkinter`, `time`, `tempfile`, `shutil`

---

## Usage

Run either version directly:

```bash
python Parallel_Log_Analyzer.py
# or
python testing.py
```

A file dialog will open — select any supported log file. Once loaded, use the interactive terminal viewer:

| Command | Action |
|---|---|
| `n` | Next page |
| `b` | Previous page |
| `s` | Search by keyword(s) |
| `p` | Export to PDF |
| `q` | Quit |

When searching, enter keywords as a comma-separated list, e.g.: `error, timeout, failed`

The tool will print the search mode used (Serial or Parallel), number of matches, and time taken.

---

## Generating Test Logs

To generate a large synthetic log file for performance testing:

```bash
python generate_log.py
```

This generates `huge_server.log` with configurable line counts. The default is set very high — edit the `total_lines` parameter in the script before running:

```python
generate_large_log_file(filename="huge_server.log", total_lines=1_000_000)
```

---

## How It Works

### Adaptive Search Logic

```
if file has < 1,000,000 lines:
    → Serial search (file already in memory)
else:
    → Estimate serial time using a 5,000-line sample
    → If estimated time > 0.05s: use Parallel search
    → Otherwise: Serial search
```

### Parallel Search (`testing.py`)

1. File is read in chunks (default 200,000 lines per chunk)
2. Each chunk is assigned to a worker process
3. Workers write matching lines to temporary files
4. Main process merges all temp files into final results
5. Temp directory is cleaned up automatically

### Serial Search

Simple linear scan — each line is checked against all keywords. Fast enough for small to medium files.

---

## Performance

| Mode | File Size | Approximate Time |
|---|---|---|
| Serial | Small (< 50K lines) | < 0.1s |
| Parallel | Large (1M lines) | 3–5s (vs ~12s serial) |

Speedup of ~3–4x observed on multi-core machines for large files.

---

## Known Issues & Limitations

- **High RAM usage on very large files** — the main version (`Parallel_Log_Analyzer.py`) loads the entire file into memory before searching. On files larger than a few hundred MB this can cause the program to slow down or freeze.
- `testing.py` partially addresses this with chunked reading, but parallel results are still merged into memory before display.
- PDF export is limited to the first 2,000 lines to keep file sizes manageable.
- The interactive viewer requires a terminal environment; it clears the screen using `cls`/`clear` commands.

---

## Contributing

This project is open to optimization contributions. Areas that would benefit most from improvement:

- **Memory-efficient parallel search** — process and display results in a streaming fashion without loading all matches into RAM
- **Out-of-core viewer** — page through results from disk rather than from an in-memory list
- **Progress indicator** — show progress during long parallel searches
- **GUI version** — replace the terminal viewer with a proper tkinter or web-based interface

Pull requests and forks are welcome!

---

## Authors

- **Azeem Mohamed Husain**
- **Muhammad Askee Iqbal**


**Instructor:** Mr. Shoaib Khan  
**Course:** COMP-460 Parallel and Distributed Computing  
**Institution:** Pak-Austria Fachhochschule, Haripur, Pakistan
