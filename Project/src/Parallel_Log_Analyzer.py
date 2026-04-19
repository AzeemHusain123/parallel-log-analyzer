import os
import gzip
import zipfile
import pandas as pd
import tkinter as tk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import multiprocessing
import time

# ===============================================================
# GLOBAL TK ROOT (Fixes freezing & stuck file dialogs)
# ===============================================================
root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)

# ===============================================================
# LOAD LOG FILE (supports .txt, .csv, .gz, .zip)
# ===============================================================
def load_log_file():
    filename = askopenfilename(
        title="Select Log File",
        parent=root
    )
    if not filename:
        return None, None

    lines = []
    ext = filename.lower()

    try:
        if ext.endswith(".gz"):
            with gzip.open(filename, "rt", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

        elif ext.endswith(".zip"):
            with zipfile.ZipFile(filename, "r") as zip_ref:
                for name in zip_ref.namelist():
                    with zip_ref.open(name) as f:
                        for line in f:
                            lines.append(line.decode("utf-8", errors="ignore"))

        elif ext.endswith(".csv"):
            df = pd.read_csv(filename, dtype=str, keep_default_na=False)
            for idx, row in df.iterrows():
                lines.append(" | ".join([str(v) for v in row.values]))

        else:
            with open(filename, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

    except Exception as e:
        print("Error reading file:", e)
        return None, None

    return filename, lines

# ===============================================================
# PDF EXPORTER (FIXED - no freezing, correct filename)
# ===============================================================
def export_pdf(lines_to_export):
    save_path = asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        title="Save PDF As",
        parent=root
    )

    if not save_path:
        print("PDF export cancelled.")
        return

    print("Exporting PDF...")

    c = canvas.Canvas(save_path, pagesize=letter)
    width, height = letter
    y = height - 40
    c.setFont("Helvetica", 12)

    for line in lines_to_export[:2000]:  # limit to avoid huge PDFs
        txt = line.strip()[:95]
        c.drawString(40, y, txt)
        y -= 14

        if y < 50:
            c.showPage()
            y = height - 40

    c.save()
    print(f"PDF exported successfully to:\n{save_path}")


# ===============================================================
# SERIAL SEARCH
# ===============================================================
def serial_search(lines, keywords):
    start = time.time()
    keywords = [k.lower() for k in keywords]
    matched = []

    for line in lines:
        l = line.lower()
        if any(k in l for k in keywords):
            matched.append(line)

    end = time.time()
    return matched, end - start


# ===============================================================
# PARALLEL SEARCH
# ===============================================================
def worker(args):
    chunk, keywords = args
    keywords = [k.lower() for k in keywords]
    matched = []

    for line in chunk:
        l = line.lower()
        if any(k in l for k in keywords):
            matched.append(line)

    return matched

def parallel_search(lines, keywords):
    workers = multiprocessing.cpu_count()
    size = max(1, len(lines) // workers)

    chunks = [lines[i:i + size] for i in range(0, len(lines), size)]
    pool = multiprocessing.Pool(workers)

    start = time.time()
    results = pool.map(worker, [(c, keywords) for c in chunks])
    pool.close()
    pool.join()

    end = time.time()

    merged = []
    for r in results:
        merged.extend(r)

    return merged, end - start


# ===============================================================
# ADAPTIVE SEARCH (auto decide serial/parallel)
# ===============================================================
def adaptive_search(lines, keywords):
    if len(lines) < 5000:
        print(f"\nProcessing in SERIAL mode ({len(lines)} lines)...")
        result, t = serial_search(lines, keywords)
        mode = "Serial"

    else:
        # estimate cost of serial search
        sample = min(5000, len(lines))
        _, sample_time = serial_search(lines[:sample], keywords)
        est_total_time = sample_time * (len(lines) / sample)

        if est_total_time > 0.05:
            print(f"\nProcessing in PARALLEL mode (estimated serial time {est_total_time:.4f}s)...")
            result, t = parallel_search(lines, keywords)
            mode = "Parallel"
        else:
            print(f"\nProcessing in SERIAL mode (estimated {est_total_time:.4f}s)...")
            result, t = serial_search(lines, keywords)
            mode = "Serial"

    return result, mode, t


# ===============================================================
# INTERACTIVE VIEWER (n/b/s/p/q)
# ===============================================================
def interactive_viewer(filename, lines):
    page = 0
    page_size = 10
    filtered = lines  # default: all lines

    while True:
        os.system("cls" if os.name == "nt" else "clear")

        print(f"File: {filename}")
        print("-" * 50)

        start = page * page_size
        end = min(start + page_size, len(filtered))

        for i in range(start, end):
            print(filtered[i].strip())

        print("-" * 50)
        print(f"Showing lines {start + 1} to {end} of {len(filtered)}")
        print("Commands: n=next, b=back, s=search, p=export PDF, q=quit")

        cmd = input("Enter command: ").strip().lower()

        # NEXT PAGE
        if cmd == "n":
            if end < len(filtered):
                page += 1
            else:
                print("Reached end.")
                input("Press Enter...")

        # PREVIOUS PAGE
        elif cmd == "b":
            if page > 0:
                page -= 1
            else:
                print("Already at start.")
                input("Press Enter...")

        # SEARCH MODE
        elif cmd == "s":
            kw = input("Enter keywords (comma-separated): ").strip()
            if not kw:
                continue

            keywords = [k.strip() for k in kw.split(",")]

            result, mode, t = adaptive_search(lines, keywords)

            print(f"\nSearch mode: **{mode}**")
            print(f"Found {len(result)} lines for {keywords}")
            print(f"Time taken: {t:.6f} seconds")
            input("Press Enter...")

            filtered = result
            page = 0

        # EXPORT PDF
        elif cmd == "p":
            print("1. Current page")
            print("2. All filtered lines")
            chc = input("Choose option: ").strip()

            if chc == "1":
                export_pdf(filtered[start:end])
            elif chc == "2":
                export_pdf(filtered)
            else:
                print("Invalid choice.")

            input("Press Enter...")

        # QUIT
        elif cmd == "q":
            break

        else:
            print("Invalid command.")
            input("Press Enter...")


# ===============================================================
# MAIN
# ===============================================================
if __name__ == "__main__":
    filename, lines = load_log_file()
    if not filename:
        print("No file selected.")
        exit()

    interactive_viewer(filename, lines)
