# -*- coding: utf-8 -*-
"""
CSV Analyzer (Top Values) - GUI Application
Version: 1.8 (Dynamic Chunk Estimation)
Date: July 13, 2025
Author: Dragos Vasiloi wiht GenAI help
License: MIT
Description:
A GUI application for analyzing large CSV files. This version replaces the static 'magic number'
for chunk estimation with a dynamic calculation based on an initial file sample. This provides
a significantly more accurate total chunk count in the status bar during processing.

License: MIT
Copyright 2025 Dragos Vasiloi 

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

# Standard library imports
import sys
import os
import logging
import threading
import subprocess
import importlib
import re
import math
from collections import Counter
from datetime import datetime
from io import StringIO

# Third-party library imports (handled by dependency checker)
try:
    import pandas as pd
    import chardet
except ImportError as e:
    print(f"Initial import failed for {e.name}. The dependency checker will attempt installation.")

# GUI library imports
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinter import font as tkfont

# --- Constants ---
APP_TITLE = "CSV Analyzer - Top N Values"
DEFAULT_TOP_N = 10
CHUNK_SIZE_DEFAULT = 9000
MIN_CHUNK_SIZE = 500
SCALE_STEP = 0.1
MIN_GUI_SCALE = 0.7
MAX_GUI_SCALE = 2.5
DEFAULT_FONT_SIZE = 10
REQUIRED_PACKAGES = ["pandas", "chardet"]
FILE_SAMPLE_SIZE = 50000  # Bytes to read for encoding and row size estimation

# --- Custom Logging Handler for GUI ---
class GUILogHandler(logging.Handler):
    """A custom logging handler that directs log records to a Tkinter ScrolledText widget."""
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.widget.configure(state='disabled')

    def emit(self, record):
        try:
            if self.widget.winfo_exists():
                msg = self.format(record)
                self.widget.after(0, self.append_message, msg)
        except Exception:
            pass

    def append_message(self, msg):
        self.widget.configure(state='normal')
        self.widget.insert(tk.END, msg + '\n')
        self.widget.configure(state='disabled')
        self.widget.yview(tk.END)

# --- Main Application Class ---
class CSVAnalyzerApp:
    """The main class for the CSV Analyzer GUI application."""
                                                                   
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1900x900")
        self.root.minsize(800, 500)

        # --- Internal State Variables ---
        self.file_path = tk.StringVar()
        self.top_n_var = tk.StringVar(value=str(DEFAULT_TOP_N))
        self.chunk_size_var = tk.StringVar(value=str(CHUNK_SIZE_DEFAULT))
        self.status_var = tk.StringVar(value="Ready. Please select a CSV file.")
        self.detected_encoding = None
        self.processing_thread = None
        self.stop_event = threading.Event()
        self.current_scale = 1.2
        self.last_used_top_n = None

        # --- Setup Core Components ---
        self.setup_logging()
        self.setup_gui()
        self.apply_new_scale()
        self.update_zoom_buttons_state()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        logging.info("Application initialized successfully. Adjust the CHUNK_SIZE to reduce RAM usage.")
        self.update_status(f"GUI scale set to {self.current_scale:.2f}. Ready for file selection.")

    def setup_logging(self):
        """Configures the logging system to output to both console and GUI."""
        log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        if self.logger.hasHandlers(): self.logger.handlers.clear()
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_format)
        self.logger.addHandler(console_handler)

    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(expand=True, fill="both")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        top_controls_frame = ttk.Frame(main_frame)
        top_controls_frame.pack(side="top", fill="x", pady=(0, 10))
        zoom_frame = ttk.Frame(top_controls_frame)
        zoom_frame.pack(side="left", anchor="w")
        ttk.Label(zoom_frame, text="Zoom:").pack(side="left", padx=(0, 5))
        self.zoom_in_button = ttk.Button(zoom_frame, text="+", width=3, command=self.zoom_in)
        self.zoom_in_button.pack(side="left")
        self.zoom_out_button = ttk.Button(zoom_frame, text="-", width=3, command=self.zoom_out)
        self.zoom_out_button.pack(side="left", padx=(5, 0))
        params_frame = ttk.Frame(top_controls_frame)
        params_frame.pack(side="right", anchor="e")
        ttk.Label(params_frame, text="Top number of values:").pack(side="left", padx=(10, 2))
        ttk.Entry(params_frame, textvariable=self.top_n_var, width=8).pack(side="left")
        ttk.Label(params_frame, text="Chunk Size:").pack(side="left", padx=(10, 2))
        ttk.Entry(params_frame, textvariable=self.chunk_size_var, width=10).pack(side="left")
        paned_window = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        paned_window.pack(expand=True, fill="both")
        top_pane = ttk.Frame(paned_window, padding=(0, 5))
        paned_window.add(top_pane, weight=0)
        top_pane.grid_columnconfigure(1, weight=1)
        ttk.Label(top_pane, text="CSV File:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        ttk.Entry(top_pane, textvariable=self.file_path, state='readonly').grid(row=0, column=1, sticky="ew")
        ttk.Button(top_pane, text="Browse...", command=self.browse_file).grid(row=0, column=2, padx=(5, 0))
        button_frame = ttk.Frame(top_pane)
        button_frame.grid(row=1, column=0, columnspan=3, pady=(10,0))
        self.process_button = ttk.Button(button_frame, text="Process CSV", command=self.start_processing)
        self.process_button.pack(side="left", padx=(0, 5))
        self.stop_button = ttk.Button(button_frame, text="Stop Processing", command=self.stop_processing, state='disabled')
        self.stop_button.pack(side="left")
        middle_pane = ttk.PanedWindow(paned_window, orient=tk.HORIZONTAL)
        paned_window.add(middle_pane, weight=1)
        report_frame = ttk.Labelframe(middle_pane, text="Analysis Report")
        middle_pane.add(report_frame, weight=1)
        self.report_text = scrolledtext.ScrolledText(report_frame, wrap=tk.WORD, state='disabled')
        self.report_text.pack(expand=True, fill="both", padx=5, pady=5)
        self.save_report_button = ttk.Button(report_frame, text="Save Report", command=self.save_report, state='disabled')
        self.save_report_button.pack(side="bottom", anchor="se", padx=5, pady=5)
        log_frame = ttk.Labelframe(middle_pane, text="Process Log")
        middle_pane.add(log_frame, weight=1)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state='disabled')
        self.log_text.pack(expand=True, fill="both", padx=5, pady=5)
        self.save_log_button = ttk.Button(log_frame, text="Save Log", command=self.save_log, state='disabled')
        self.save_log_button.pack(side="bottom", anchor="se", padx=5, pady=5)
        gui_log_handler = GUILogHandler(self.log_text)
        gui_log_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        self.logger.addHandler(gui_log_handler)
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor='w')
        status_bar.pack(side="bottom", fill="x", pady=(10, 0))

    def on_closing(self):
        if self.processing_thread and self.processing_thread.is_alive():
            if messagebox.askyesno("Exit", "Processing is currently running. Are you sure you want to stop it and exit?"):
                self.stop_processing()
                self.root.destroy()
        else:
            self.root.destroy()

    def zoom_in(self): self.current_scale += SCALE_STEP; self.apply_new_scale()
    def zoom_out(self): self.current_scale -= SCALE_STEP; self.apply_new_scale()

    def apply_new_scale(self):
        self.current_scale = max(MIN_GUI_SCALE, min(MAX_GUI_SCALE, self.current_scale))
        new_font_size = int(DEFAULT_FONT_SIZE * self.current_scale)
        for font_name in ("TkDefaultFont", "TkTextFont", "TkFixedFont"):
            tkfont.nametofont(font_name).configure(size=new_font_size)
        style = ttk.Style()
        style.configure("TButton", font=(tkfont.nametofont("TkDefaultFont").actual()['family'], new_font_size))
        style.configure("TLabel", font=(tkfont.nametofont("TkDefaultFont").actual()['family'], new_font_size))
        style.configure("TEntry", font=(tkfont.nametofont("TkDefaultFont").actual()['family'], new_font_size))
        style.configure("TLabelframe.Label", font=(tkfont.nametofont("TkDefaultFont").actual()['family'], new_font_size))
        self.update_status(f"GUI scale set to {self.current_scale:.2f}")
        self.update_zoom_buttons_state()

    def update_zoom_buttons_state(self):
        self.zoom_in_button.config(state='normal' if self.current_scale < MAX_GUI_SCALE else 'disabled')
        self.zoom_out_button.config(state='normal' if self.current_scale > MIN_GUI_SCALE else 'disabled')

    def update_status(self, message): self.status_var.set(message); self.root.update_idletasks()

    def browse_file(self):
        filepath = filedialog.askopenfilename(title="Select a CSV file", filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
        if filepath: self.file_path.set(filepath); self.update_status(f"Selected file: {os.path.basename(filepath)}"); logging.info(f"File selected: {filepath}")

    def validate_top_n(self):
        try:
            top_n = int(self.top_n_var.get());
            if top_n > 0: return top_n
        except ValueError: pass
        messagebox.showwarning("Invalid Input", f"Top N is invalid. Using default: {DEFAULT_TOP_N}."); self.top_n_var.set(str(DEFAULT_TOP_N)); return DEFAULT_TOP_N

    def validate_chunk_size(self):
        try:
            chunk_size = int(self.chunk_size_var.get());
            if chunk_size >= MIN_CHUNK_SIZE: return chunk_size
        except ValueError: pass
        messagebox.showwarning("Invalid Input", f"Chunk size is invalid. Using default: {CHUNK_SIZE_DEFAULT}."); self.chunk_size_var.set(str(CHUNK_SIZE_DEFAULT)); return CHUNK_SIZE_DEFAULT

    def start_processing(self):
        filepath = self.file_path.get()
        if not filepath: messagebox.showerror("Error", "Please select a CSV file first."); return
        top_n, chunk_size = self.validate_top_n(), self.validate_chunk_size()
        self.last_used_top_n = top_n
        self.process_button.config(state='disabled'); self.stop_button.config(state='normal'); self.save_report_button.config(state='disabled'); self.save_log_button.config(state='disabled')
        self.stop_event.clear()
        self.processing_thread = threading.Thread(target=self.process_csv_thread, args=(filepath, top_n, chunk_size), daemon=True)
        self.processing_thread.start()

    def stop_processing(self):
        if self.processing_thread and self.processing_thread.is_alive():
            self.stop_event.set(); logging.warning("Stop request sent."); self.update_status("Stopping..."); self.stop_button.config(state='disabled')

    def enable_controls_after_processing(self, success):
        self.process_button.config(state='normal'); self.stop_button.config(state='disabled'); self.save_log_button.config(state='normal')
        if not success: self.save_report_button.config(state='disabled')

    def process_csv_thread(self, filepath, top_n, chunk_size):
        try:
            self.root.after(0, self.update_status, "Detecting file encoding and estimating size...")
            total_size = os.path.getsize(filepath)
            
            with open(filepath, 'rb') as f:
                raw_data = f.read(FILE_SAMPLE_SIZE)
                self.detected_encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'

            # IMPROVEMENT: Calculate total chunks dynamically based on a file sample.
            lines_in_sample = raw_data.count(b'\n')
            avg_row_size = len(raw_data) / lines_in_sample if lines_in_sample > 0 else 150 # Fallback
            estimated_chunk_byte_size = chunk_size * avg_row_size
            total_chunks = math.ceil(total_size / estimated_chunk_byte_size) if estimated_chunk_byte_size > 0 else 1

            self.root.after(0, logging.info, f"Detected encoding: {self.detected_encoding}")
            self.root.after(0, logging.info, f"Estimated average row size: {avg_row_size:.2f} bytes.")
            self.root.after(0, logging.info, f"Estimated total chunks: {total_chunks}")
            
            self.root.after(0, self.update_status, f"Processing chunk 1 of ~{total_chunks}...")
            
            value_counters, header, chunk_num = {}, [], 0
            with open(filepath, 'r', encoding=self.detected_encoding, errors='replace') as f:
                reader = pd.read_csv(f, chunksize=chunk_size, low_memory=False)
                for chunk in reader:
                    if self.stop_event.is_set(): self.root.after(0, logging.warning, "Processing stopped by user."); break
                    chunk_num += 1
                    self.root.after(0, self.update_status, f"Processing chunk {chunk_num} of ~{total_chunks}...")
                    self.root.after(0, logging.info, f"Analyzing chunk {chunk_num}...")
                    if not header: header = chunk.columns.tolist(); value_counters = {col: Counter() for col in header}
                    for col in header:
                        if col in chunk: value_counters[col].update(chunk[col].value_counts().to_dict())

            if self.stop_event.is_set():
                report_content = "Processing was stopped before completion."
            else:
                self.root.after(0, self.update_status, "Analysis complete. Generating report...")
                report_content = self.generate_report(value_counters, top_n)
                self.root.after(0, self.update_status, "Report generated successfully.")
            
            self.root.after(0, self.update_report_text, report_content)
            success = not self.stop_event.is_set()

        except Exception as e:
            error_msg = f"An error occurred during processing: {e}"; self.root.after(0, logging.error, error_msg)
            self.root.after(0, self.update_status, "Error during processing. Check logs."); self.root.after(0, self.update_report_text, f"ERROR:\n\n{error_msg}")
            success = False
        finally:
            self.root.after(0, self.enable_controls_after_processing, success); self.stop_event.clear()

    def update_report_text(self, content):
        self.report_text.config(state='normal'); self.report_text.delete('1.0', tk.END); self.report_text.insert('1.0', content); self.report_text.config(state='disabled')
        is_content_present = content.strip() and not content.startswith("Processing was stopped") and not content.startswith("ERROR:")
        self.save_report_button.config(state='normal' if is_content_present else 'disabled')

    def generate_report(self, value_counters, top_n):
        report = StringIO()
        report.write(f"--- CSV Analysis Report ---\nFile: {os.path.basename(self.file_path.get())}\n")
        report.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nTop {top_n} values:\n{'='*40}\n\n")
        for i, (col, counters) in enumerate(value_counters.items()):
            report.write(f"--- Column {i+1}: '{col}' ---\n")
            if not counters: report.write("No values found.\n\n"); continue
            for value, count in counters.most_common(top_n): report.write(f"  - Value: '{value}' | Count: {count}\n")
            report.write("\n")
        return report.getvalue()

    def sanitize_filename(self, filename): return re.sub(r'[\\/*?:"<>|]', "", filename)

    def save_report(self):
        content = self.report_text.get("1.0", tk.END).strip()
        if not content: messagebox.showwarning("Save Report", "Report is empty."); return
        sanitized_name = self.sanitize_filename(os.path.splitext(os.path.basename(self.file_path.get()))[0])
        top_n_val = self.last_used_top_n or self.validate_top_n()
        default_filename = f"Report_{sanitized_name}_Top{top_n_val}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = filedialog.asksaveasfilename(initialfile=default_filename, defaultextension=".txt", filetypes=[("Text Documents", "*.txt"), ("All Files", "*.*")])
        if filepath:
            try:
                with open(filepath, 'w', encoding=self.detected_encoding or 'utf-8', errors='replace') as f: f.write(content)
                logging.info(f"Report saved to: {filepath}"); self.update_status(f"Report saved: {os.path.basename(filepath)}")
            except Exception as e: logging.error(f"Failed to save report: {e}"); messagebox.showerror("Save Error", f"Could not save report.\n\nError: {e}")

    def save_log(self):
        content = self.log_text.get("1.0", tk.END).strip()
        if not content: messagebox.showwarning("Save Log", "Log is empty."); return
        sanitized_name = self.sanitize_filename(os.path.splitext(os.path.basename(self.file_path.get() or "session"))[0])
        default_filename = f"Log_{sanitized_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        filepath = filedialog.asksaveasfilename(initialfile=default_filename, defaultextension=".log", filetypes=[("Log Files", "*.log"), ("All Files", "*.*")])
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f: f.write(content)
                logging.info(f"Log file saved to: {filepath}"); self.update_status(f"Log saved: {os.path.basename(filepath)}")
            except Exception as e: logging.error(f"Failed to save log: {e}"); messagebox.showerror("Save Error", f"Could not save log.\n\nError: {e}")

# --- Application Startup ---
def check_and_install_dependencies(packages):
    temp_root = tk.Tk(); temp_root.withdraw()
    try:
        missing = [pkg for pkg in packages if importlib.util.find_spec(pkg) is None]
        if not missing: return True
        msg = f"Missing packages: {', '.join(missing)}.\n\nInstall now using pip?"
        if messagebox.askyesno("Missing Dependencies", msg, parent=temp_root):
            for package in missing:
                try: subprocess.run([sys.executable, "-m", "pip", "install", package], check=True, capture_output=True, text=True)
                except Exception as e: messagebox.showerror("Installation Failed", f"Failed to install '{package}'.\n\nError: {e.stderr if hasattr(e, 'stderr') else str(e)}", parent=temp_root); return False
        else: messagebox.showinfo("Dependencies Required", "Application cannot run. Exiting.", parent=temp_root); return False
    finally: temp_root.destroy()
    return True

def main():
    try:
        if not check_and_install_dependencies(REQUIRED_PACKAGES): sys.exit(1)
        importlib.reload(logging); globals()['pd'] = importlib.import_module('pandas'); globals()['chardet'] = importlib.import_module('chardet')
        root = tk.Tk(); app = CSVAnalyzerApp(root); root.mainloop()
    except Exception as e:
        print(f"A critical, unhandled error occurred: {e}", file=sys.stderr)
        logging.getLogger().critical("A critical, unhandled error occurred.", exc_info=True)
        try: error_root = tk.Tk(); error_root.withdraw(); messagebox.showerror("Fatal Error", f"A fatal error occurred and must close.\n\nError: {e}")
        finally: sys.exit(1)

if __name__ == "__main__":
    main()
