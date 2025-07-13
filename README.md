# CSV Analyzer of Top Values
A desktop GUI application built with Python and Tkinter for efficiently analyzing large CSV files. Its primary function is to find the "Top N" most frequent values in each column without loading the entire file into memory, making it ideal for datasets that exceed available RAM when workign with very large CSV file(over 20GB).

The application is designed for robustness and a smooth user experience, featuring a responsive interface that runs processing tasks in a separate thread, graceful process interruption, and dynamic UI scaling.

✨ Key Features
Large File Support: Processes multi-gigabyte CSV files efficiently using a chunk-based approach with the Pandas library.
Responsive UI: The main interface remains fully responsive during intensive file processing thanks to multi-threading.
Adjustable Parameters:
Specify the Top N values to find for each column.
Manually set the Chunk Size (rows per batch) to balance performance and memory usage.
Accurate Progress Tracking: Dynamically estimates the total number of chunks by analyzing a file sample, providing a realistic progress bar.
Graceful Controls: Safely stop an ongoing analysis or close the application without losing data or causing errors.
Automatic Encoding Detection: Uses chardet to automatically determine the correct file encoding.
Export Results: Save the final analysis report and the detailed process log to separate text/log files.
Adjustable UI Scale (Zoom): Increase or decrease the size of all interface elements for better readability on any display.
Automatic Dependency Management: Checks for required libraries (pandas, chardet) on startup and offers to install them automatically.

🚀 Installation & Usage
Prerequisites
Python 3.6 or newer.
pip (Python's package installer).
Installation
Clone the repository:

git clone https://github.com/3XTron/CSV_tools.git
cd CSV_tools

Run the application:

python topvalues_in_csv.py

✨ Automatic Dependency Installation: The first time you run the script, it will check if pandas and chardet are installed. 
If not, a pop-up dialog will ask for your permission to install them automatically using pip.

📚 How to Use the Application
Select a CSV File:

Click the Browse... button to open a file dialog.
Select the .csv file you want to analyze. The path will appear in the field next to the button.
Configure Parameters:

Top N Values: Enter the number of most frequent values you want to see for each column (e.g., 10 for the top 10).
Chunk Size (Rows): This controls how many rows are read into memory at once.
A smaller value (e.g., 5000) uses less RAM but may be slightly slower due to more I/O operations.
A larger value (e.g., 100000) is faster but uses more RAM. The default (9000) is a balanced starting point.
Start Processing:

Click the Process CSV button.
The interface controls will be disabled, and the Stop Processing button will become active.
The status bar at the bottom will show the progress, like Processing chunk 5 of ~123....
Analyze the Results:

Once processing is complete, the Analysis Report pane on the left will be populated with the Top N values for each column.
The Process Log pane on the right will show a detailed history of operations, including file encoding, progress, and any errors encountered.
Save Your Work:

Click Save Report to save the contents of the Analysis Report pane to a .txt file.
Click Save Log to save the contents of the Process Log pane to a .log file.
The log will confirm where each file was saved.
Interrupting a Process:

If you need to stop a long-running analysis, simply click the Stop Processing button. The application will finish its current chunk and then stop gracefully.
Adjusting the View:

Use the + and - buttons in the top-right corner to zoom the interface in or out for better visibility.

⚙️ How It Works (Technical Details)
This application leverages several key programming concepts to provide a robust experience:

Multi-threading: The entire file analysis process runs on a separate worker thread. This prevents the GUI from freezing, allowing the user to move the window, see real-time log updates, and use the "Stop" button.

Chunk-Based Processing: Instead of loading the entire CSV file into memory, pandas reads it in smaller pieces (chunks). The application iterates over these chunks, aggregates value counts incrementally, and then discards the chunk from memory, ensuring a low and stable memory footprint.

Dynamic Progress Estimation: To avoid inaccurate progress bars, the application first reads a small sample (50KB) of the file. It counts the number of lines in this sample to calculate an average row size specific to that file. This average is then used to estimate the total number of chunks with high accuracy.

Graceful Shutdown & Interruption:

A threading.Event is used as a signal flag. When the "Stop" button is pressed, the event is set. The worker thread checks this flag between each chunk and exits its loop cleanly if the flag is set.
The application intercepts the window's close ([x]) command. If a process is running, it prompts the user for confirmation before safely stopping the thread and closing the application.

📦 Dependencies
pandas: For high-performance data manipulation and CSV reading.
chardet: For robust character encoding detection.
All other libraries used (tkinter, threading, logging, etc.) are part of the Python Standard Library.

🤝 Contributing
Contributions are welcome! If you have suggestions for improvements or find a bug, please feel free to:

Fork the repository.
Create a new branch (git checkout -b feature/AmazingFeature).
Commit your changes (git commit -m 'Add some AmazingFeature').
Push to the branch (git push origin feature/AmazingFeature).
Open a Pull Request.

📜 License This project is licensed under the MIT License - see the LICENSE.md file for details.


✍️ Author
This application was designed and developed by 
Copyright (c) 2025 Dragoș Vasiloi with GenAI help based on below document 



# Technical Requirements Documentation - CSV Analyzer for Top Values

Version: 1.8
Last Updated: 2025-07-13

# 1. Introduction
This document describes the technical requirements for a GUI (Graphical User Interface) based software application intended for analyzing large CSV files. The main functionality is to identify and present the top N most frequent values (Top N) for each column in a selected CSV file. The application must efficiently handle large files through user-adjustable chunk-based processing, provide accurate visual feedback to the user via a responsive graphical interface, include mechanisms for saving results and logs, and allow for adjusting the interface scaling. The application must also manage the necessary external dependencies and ensure a robust user experience through graceful process interruption and shutdown.

# 2. Scope
Includes:

Selection of a CSV file through a graphical interface.
Reading and processing of CSV files, including large ones (exceeding available memory).
Automatic detection of the CSV file's encoding.
Dynamic and accurate estimation of the total number of chunks to be processed, improving progress feedback.
Identification of the top N most frequent unique values for each column in the file.
User specification of the N value for the "Top N" analysis.
User specification of the CHUNK_SIZE (rows per chunk) to balance performance and memory usage.
Display of the analysis results in a dedicated area of the GUI ("Analysis Report").
Display of progress, error, and operational messages in a separate area ("Process Log"), including paths of saved files.
Running the file processing in a separate thread to keep the GUI responsive.
Implementation of a mechanism for graceful interruption of file processing at the user's request.
Graceful application shutdown when the main window is closed, even during active processing (with user confirmation).
Functionality to save the "Analysis Report" to a text file.
Functionality to save the "Process Log" to a log file.
Dynamic adjustment of GUI element scaling (zoom in/out) via font size manipulation.
Automatic verification and installation (with user confirmation) of the necessary Python dependencies (pandas, chardet).
Handling of common errors (file not found, invalid format, encoding issues, runtime errors) and reporting them to the user.
Excludes:

Editing the content of the CSV file.
Complex graphical data visualizations (charts, plots).
Advanced statistical analysis beyond value frequency counting.
Data manipulation or transformation (exception: handling of missing/null values by the libraries used).
Support for non-CSV file formats.
Export functionalities to formats other than text (.txt, .log).
Multi-user or networking functionalities.
#3. Architecture and Components
The application follows a classic GUI application architecture model, with a clear separation between the main graphical interface thread and a secondary thread for intensive processing operations.

Main Components:

GUI (Tkinter): Manages the user interface, events (click, input), and information display. It includes ttk widgets for a modern look. GUI scaling is achieved by programmatically adjusting the font sizes of all relevant widgets using tkfont and ttk.Style, not a global Tcl command.
Core Processing Logic (Pandas): Uses the pandas library for efficient reading of CSV files in chunks (chunksize) and for counting the frequency of values.
Dynamic Progress Estimation: Before processing, the application reads a small sample of the file (FILE_SAMPLE_SIZE) to calculate an average row size. This dynamic value is used to provide a significantly more accurate estimation of the total_chunks to be processed, which is displayed in the status bar.
Encoding Detection (Chardet): Uses the chardet library on the initial file sample to detect the encoding with high probability.
Threading Module: Allows the file processing operation to run in a separate thread (threading.Thread) to prevent the GUI from freezing. A threading.Event (stop_event) is used for the graceful stop mechanism.
Graceful Shutdown (root.protocol): The WM_DELETE_WINDOW protocol is handled by the on_closing method to check for active processing and prompt the user before exiting.
Logging Module: Manages system messages (INFO, WARNING, ERROR) using the standard logging module. It includes a custom handler (GUILogHandler) to redirect messages to the log widget in the GUI in a thread-safe manner (using widget.after()).
Dependency Management (Subprocess, Importlib): Uses standard Python modules to check for the existence of the required libraries and attempts to install them via pip.
# 4. Detailed Functional Requirements
4.1. CSV File Selection:

A "Browse..." button opens a standard file selection dialog, filtering for .csv files.
The selected file path is displayed in a readonly Entry field.
The path is stored internally for processing.
4.2. Parameter Specification:

Top N: An Entry field allows the user to specify the number of top values to report. Defaults to 10. Input is validated to be a positive integer.
Chunk Size: An Entry field allows the user to specify the number of rows per chunk. Defaults to 9000. Input is validated to be an integer greater than or equal to 500 (MIN_CHUNK_SIZE).
4.3. CSV File Processing (Multi-threaded):

The "Process CSV" button initiates processing.
During processing, control buttons ("Process CSV", "Browse...") are disabled, and the "Stop Processing" button is enabled.
A new thread is started to run the process_csv_thread method, keeping the GUI responsive.
The process_csv_thread method:
Reads an initial sample of the file (FILE_SAMPLE_SIZE).
Detects encoding using chardet.
Calculates the average row size based on the sample.
Estimates the total number of chunks using this average size and logs this information.
Updates the status bar with the initial progress (e.g., "Processing chunk 1 of ~X...").
Uses pandas.read_csv with the user-defined chunksize to iterate through the file.
For each column in each chunk, accumulates value counts using collections.Counter.
Regularly updates the status bar with the current chunk number.
Checks for the stop_event between each chunk.
After the loop, generates the final report.
Handles exceptions and logs them appropriately.
4.4. Interruption and Shutdown Mechanism:

Stop Button: Pressing "Stop Processing" sets the stop_event. The processing thread will terminate gracefully after finishing its current chunk.
Window Close [x]: The on_closing method is triggered. If processing is active, it shows a messagebox.askyesno to confirm. If confirmed, it calls stop_processing() and then root.destroy().
4.5. Displaying the Analysis Report:

A ScrolledText widget displays the final Top N analysis.
The widget is readonly and updated safely from the processing thread using self.root.after().
4.6. Displaying the Process Log:

A separate ScrolledText widget displays all log messages via the GUILogHandler.
The widget is readonly and auto-scrolls to the latest message.
Log entries include timestamps, levels, and messages (e.g., file selection, encoding, progress, save paths, errors).
4.7. Save Functionalities:

Save Report:
Enabled only if processing completed successfully and the report does not contain only an error or interruption message.
Suggests a filename like Report_[CSV-Name]_TopN_[Timestamp].txt.
Saves using the detected file encoding, with a fallback to UTF-8.
Logs the save path upon success.
Save Log:
Enabled after any processing attempt (successful or not).
Suggests a filename like Log_[CSV-Name]_[Timestamp].log.
Always saves using UTF-8 encoding.
Logs the save path upon success.
Both functions use a sanitize_filename method to remove invalid characters from suggested names.
4.8. GUI Scaling (Zoom):

"+" and "-" buttons control the UI scale.
Scaling is achieved by modifying a self.current_scale factor (bounded by MIN_GUI_SCALE and MAX_GUI_SCALE).
The apply_new_scale method calculates a new font size based on this factor.
It updates the size for default fonts (TkDefaultFont, etc.) via tkfont.nametofont.
It updates the font size for ttk widgets via ttk.Style().configure.
This approach ensures all text-based elements are resized consistently.
Zoom buttons are disabled at min/max scaling limits.
4.9. Dependency Management:

At startup, a function checks for pandas and chardet.
If missing, a messagebox prompts the user for installation via pip.
The installation is performed in a subprocess.
The application exits if installation fails or is refused by the user.
# 5. Non-Functional Requirements
User Interface (UI):
A logical layout with controls at the top, a central pannable area, and a status bar at the bottom.
The main window starts with a default size of 1900x900 pixels and a default GUI scale of 1.2.
The central area uses a vertical PanedWindow to separate the top controls from the main analysis area, which in turn uses a horizontal PanedWindow for the "Report" and "Log" panes.
Performance:
Handles multi-gigabyte files without exhausting memory due to chunking.
GUI remains fully responsive during processing.
Robustness:
Does not crash on malformed CSV rows (errors are logged).
Gracefully handles process interruption and application shutdown.
Maintainability:
Well-structured, commented Python code. Use of constants for key parameters.
Portability:
Runs on any OS with a standard Python 3 interpreter.
# 6. Specific Technical Constraints
Programming Language: Python 3.6+.
Mandatory Libraries: tkinter, threading, collections, os, logging, sys, io, datetime, subprocess, importlib, re, math, chardet, pandas.
GUI Framework: Tkinter with ttk widgets.
Concurrency Model: Multi-threading (one GUI thread, one worker thread).
GUI Scaling Implementation: Must be implemented by manipulating font sizes via tkfont and ttk.Style, as this provides reliable cross-platform scaling.
Dynamic Chunk Estimation Logic: The estimation of total chunks must be performed dynamically by analyzing an initial file sample to calculate an average row size, avoiding "magic numbers".
