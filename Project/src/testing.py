import os
import gzip
import zipfile
import pandas as pd
import tkinter as tk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import multiprocessing
import tempfile
import time
import shutil

# ===============================================================
# GLOBAL TK ROOT
# ===============================================================
root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)

# ===============================================================
# READ FILE IN CHUNKS (GENERATOR)
# ===============================================================
def read_in_chunks(filename, chunk_size=100_000):
    ext = filename.lower()
    if ext.endswith(".gz"):
        f = gzip.open(filename, "rt", encoding="utf-8", errors="ignore")
    elif ext.endswith(".zip"):
        # handle zip files
        with zipfile.ZipFile(filename, "r") as zip_ref:
            for name in zip_ref.namelist():
                with zip_ref.open(name) as f_zip:
                    chunk = []
                    for i, line in enumerate(f_zip):
                        chunk.append(line.decode("utf-8", errors="ignore"))
                        if (i + 1) % chunk_size == 0:
                            yield chunk
                            chunk = []
                    if chunk:
                        yield chunk
            return
    else:
        f = open(filename, "rt", encoding="utf-8", errors="ignore")

    with f:
        chunk = []
        for i, line in enumerate(f):
            chunk.append(line)
            if (i + 1) % chunk_size == 0:
                yield chunk
                chunk = []
        if chunk:
            yield chunk

# ===============================================================
# PDF EXPORT
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

    for line in lines_to_export[:2000]:
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
    matched = [line for line in lines if any(k in line.lower() for k in keywords)]
    return matched, time.time() - start

# ===============================================================
# PARALLEL SEARCH WORKER (WRITE TO TEMP FILE)
# ===============================================================
def worker_write_temp(args):
    chunk, keywords, temp_path = args
    keywords = [k.lower() for k in keywords]
    with open(temp_path, "w", encoding="utf-8") as f:
        for line in chunk:
            if any(k in line.lower() for k in keywords):
                f.write(line)

# ===============================================================
# PARALLEL SEARCH (CHUNKED + TEMP FILES)
# ===============================================================
def parallel_search(filename, keywords, chunk_size=200_000):
    workers = multiprocessing.cpu_count()
    temp_dir = tempfile.mkdtemp()
    temp_files = []

    start_time = time.time()
    args_list = []

    for i, chunk in enumerate(read_in_chunks(filename, chunk_size)):
        temp_path = os.path.join(temp_dir, f"temp_{i}.txt")
        temp_files.append(temp_path)
        args_list.append((chunk, keywords, temp_path))

    # Use multiprocessing pool
    with multiprocessing.Pool(workers) as pool:
        pool.map(worker_write_temp, args_list)

    # Merge results
    matched = []
    for temp_file in temp_files:
        with open(temp_file, "r", encoding="utf-8") as f:
            matched.extend(f.readlines())

    shutil.rmtree(temp_dir)
    end_time = time.time()
    return matched, end_time - start_time

# ===============================================================
# ADAPTIVE SEARCH
# ===============================================================
def adaptive_search(filename, keywords, total_lines_estimate=None, all_lines=None):
    small_file_limit = 1_000_000
    if total_lines_estimate and total_lines_estimate < small_file_limit:
        # small file -> serial search in memory
        result, t = serial_search(all_lines, keywords)
        mode = "Serial"
    else:
        # huge file -> parallel search
        result, t = parallel_search(filename, keywords)
        mode = "Parallel"
    return result, mode, t

# ===============================================================
# INTERACTIVE VIEWER
# ===============================================================
def interactive_viewer(filename):
    page = 0
    page_size = 10
    filtered = None

    # Estimate total lines
    total_lines_estimate = sum(1 for _ in read_in_chunks(filename, chunk_size=500_000))

    # For small files, load into memory
    small_file_limit = 1_000_000
    if total_lines_estimate < small_file_limit:
        all_lines = []
        for chunk in read_in_chunks(filename):
            all_lines.extend(chunk)
        filtered = all_lines  # display all lines initially
    else:
        all_lines = None  # huge file, do not load

    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print(f"File: {filename}")
        print("-" * 50)

        lines_to_show = filtered if filtered is not None else []
        start = page * page_size
        end = min(start + page_size, len(lines_to_show))
        for i in range(start, end):
            print(lines_to_show[i].strip())

        print("-" * 50)
        print(f"Showing lines {start + 1} to {end} of {len(lines_to_show)}")
        print("Commands: n=next, b=back, s=search, p=export PDF, q=quit")

        cmd = input("Enter command: ").strip().lower()

        if cmd == "n":
            if end < len(lines_to_show):
                page += 1
            else:
                print("Reached end.")
                input("Press Enter...")

        elif cmd == "b":
            if page > 0:
                page -= 1
            else:
                print("Already at start.")
                input("Press Enter...")

        elif cmd == "s":
            kw = input("Enter keywords (comma-separated): ").strip()
            if not kw:
                continue
            keywords = [k.strip() for k in kw.split(",")]

            result, mode, t = adaptive_search(filename, keywords, total_lines_estimate, all_lines)
            print(f"\nSearch mode: **{mode}**")
            print(f"Found {len(result)} lines for {keywords}")
            print(f"Time taken: {t:.6f} seconds")
            input("Press Enter...")

            filtered = result
            page = 0

        elif cmd == "p":
            if not filtered:
                print("No search results to export.")
                input("Press Enter...")
                continue

            print("1. Current page")
            print("2. All filtered lines")
            choice = input("Choose option: ").strip()
            if choice == "1":
                export_pdf(filtered[start:end])
            elif choice == "2":
                export_pdf(filtered)
            else:
                print("Invalid choice.")
            input("Press Enter...")

        elif cmd == "q":
            break
        else:
            print("Invalid command.")
            input("Press Enter...")

# ===============================================================
# MAIN
# ===============================================================
if __name__ == "__main__":
    filename = askopenfilename(title="Select Log File", parent=root)
    if not filename:
        print("No file selected.")
        exit()
    interactive_viewer(filename)
