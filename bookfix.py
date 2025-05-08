#!/usr/bin/env python3

# --- bookfix.py ---
# This script provides a GUI tool to process text files (primarily ebooks in .txt, .html, .xhtml formats).
# It reads replacement rules and choices from a .data.txt file,
# allows the user to interactively make choices for specific words,
# applies automatic replacements and text cleaning (like removing pagination and converting Roman numerals),
# and saves the modified text to a new file.
# Added checkboxes to control processing steps, including integrated All-Caps Sequence Processing.
# Handles .data.txt manually for compatibility with # SECTION markers.
# Fixed SyntaxError related to global variable declaration.
# Corrected the main execution block to properly call the main GUI setup function.
# Fixed NameError for progress_bar and progress_label in process_choices.
# Fixed UnboundLocalError for all_matches_original in process_all_caps_sequences_gui by removing duplicated logic.
# Added a "Start Processing" button to initiate the workflow after GUI setup.
# Corrected processing order to match checkbox order.
# Fixed NameError for lowercased_spans_pass2 in handle_caps_choice.
# Reviewed interactive all-caps processing logic and keyboard binding.
# Added detailed logging to track execution flow in run_processing and individual steps.
# CORRECTED load_data_file parsing logic and added logging within it.
# Added logging around the run_processing call.
# Added file.flush() in log_message for immediate writing to log file.
# Implemented loading default directory from .data.txt and GUI prompt/save if not found.
# Added message boxes for prompting and confirming default directory selection.
# Last generated: 05-01-25 18:05

import tkinter as tk # Import the Tkinter library for creating the GUI
from tkinter import messagebox, filedialog, ttk # Import specific modules, including ttk
import re # Import the regular expression module for text pattern matching
import os # Import the os module for interacting with the operating system (file paths, etc.)
import sys # Import the sys module for system-specific parameters and functions (like stderr)
from bs4 import BeautifulSoup # Import BeautifulSoup for parsing HTML/XML content
from tkinter.font import Font # Import Font for custom text styling in the GUI
from tkinter.ttk import Progressbar # Import Progressbar for showing processing progress
from tkinter import BooleanVar # Import BooleanVar for checkboxes
import datetime # Import datetime for timestamps in logs
from pathlib import Path # Use pathlib for easier path manipulation

# --- Global Variables (used across functions) ---
text_area = None
choice_frame = None
status_label = None
save_button = None
filepath = None
root = None
choice_var = None # Variable to signal choice handling completion
start_processing_button = None # New global variable for the start button
text = "" # Global variable to hold the text content
log_file_path = "bookfix_execution.log" # Path for the execution log file

# Data loaded from .data.txt
choices = {} # Dictionary for interactive word choices (original bookfix)
replacements = {} # Dictionary for automatic replacements (original bookfix)
periods = set() # Set for abbreviations needing periods (original bookfix)
ignore_set = set() # Set for all-caps sequences to ignore (integrated caps.py)
lowercase_set = set() # Set for all-caps sequences to auto-lowercase (integrated caps.py)
default_file_directory = None # New global variable for the default file dialog directory

# Variables for interactive all-caps processing
current_caps_sequence = None # The all-caps sequence text being processed
current_caps_span = None # The (start, end) span of the current all-caps sequence in the text list
all_caps_matches_original = [] # List of all original regex matches for all-caps sequences
cumulative_offset = 0 # Offset due to text modifications
decided_sequences_text = set() # Set to track sequence texts that have been decided upon (for skipping future occurrences in this run)
lowercased_original_spans = set() # Set to track original spans that were lowercased (Pass 1 or Pass 2 'y'/'i')


# Variables for original choice processing (declared globally here, used in process_choices)
progress_bar = None
progress_label = None

# Variables for controlling processing steps with checkboxes
process_choices_var = None # Original bookfix checkbox
apply_replacements_var = None # Original bookfix checkbox
insert_periods_var = None # Original bookfix checkbox
remove_pagination_var = None # Original bookfix checkbox
convert_roman_var = None # Original bookfix checkbox
convert_lowercase_var = None # Original bookfix checkbox
process_all_caps_var = None # New checkbox for all-caps processing

# --- Logging Function ---
def log_message(message, level="INFO"):
    """Logs a timestamped message to stderr and a log file, flushing immediately."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry, file=sys.stderr) # Print to stderr
    try:
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
            f.flush() # Explicitly flush the buffer to ensure immediate writing
    except Exception as e:
        print(f"Error writing to log file {log_file_path}: {e}", file=sys.stderr)


# --- Data File Handling (Manual Parsing) ---
DATA_FILE_NAME = ".data.txt"
CHOICE_SECTION_MARKER = "# CHOICE" # Corrected marker spacing based on user file
REPLACE_SECTION_MARKER = "# REPLACE" # Corrected marker spacing based on user file
PERIODS_SECTION_MARKER = "# PERIODS" # Corrected marker spacing based on user file
IGNORE_SECTION_MARKER = "# CAP_IGNORE" # From caps.py
LOWERCASE_SECTION_MARKER = "# UPPER_TO_LOWER" # From caps.py
DEFAULT_DIR_SECTION_MARKER = "# DEFAULT_FILE_DIR" # New marker for default directory

# List of all section markers to help identify the end of a section's content
ALL_SECTION_MARKERS = {
    CHOICE_SECTION_MARKER,
    REPLACE_SECTION_MARKER,
    PERIODS_SECTION_MARKER,
    IGNORE_SECTION_MARKER,
    LOWERCASE_SECTION_MARKER,
    DEFAULT_DIR_SECTION_MARKER # Include the new marker
}


def load_data_file():
    """
    Loads all data (choices, replacements, periods, ignore, lowercase, default dir)
    by manually parsing the .data.txt file based on # SECTION markers.
    Corrected parsing logic to stop collecting content only at the *next* section marker.
    """
    global choices, replacements, periods, ignore_set, lowercase_set, default_file_directory # Declare globals

    choices = {}
    replacements = {}
    periods = set()
    ignore_set = set()
    lowercase_set = set()
    default_file_directory = None # Reset default directory on load

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_file_path = os.path.join(script_dir, DATA_FILE_NAME)

    log_message(f"Attempting to load data file: {data_file_path}")

    if os.path.exists(data_file_path):
        try:
            with open(data_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            current_section = None
            log_message("DEBUG: Starting data file parsing line by line.")
            for i, line in enumerate(lines):
                stripped_line = line.strip()
                log_message(f"DEBUG: Line {i+1}: '{stripped_line}'")

                # Check if the line is a known section marker
                if stripped_line in ALL_SECTION_MARKERS:
                    log_message(f"DEBUG: Found section marker: {stripped_line}")
                    if stripped_line == CHOICE_SECTION_MARKER:
                        current_section = 'choice'
                    elif stripped_line == REPLACE_SECTION_MARKER:
                        current_section = 'replace'
                    elif stripped_line == PERIODS_SECTION_MARKER:
                        current_section = 'periods'
                    elif stripped_line == IGNORE_SECTION_MARKER:
                        current_section = 'ignore'
                    elif stripped_line == LOWERCASE_SECTION_MARKER:
                        current_section = 'lowercase'
                    elif stripped_line == DEFAULT_DIR_SECTION_MARKER: # Handle new section
                         current_section = 'default_dir'
                    continue # Skip to the next line after processing a marker

                # If we are in a section and the line is not empty and not a comment, process it
                if current_section and stripped_line and not stripped_line.startswith('#'):
                    log_message(f"DEBUG: Processing content for section '{current_section}': '{stripped_line}'")
                    if current_section == 'choice':
                        parts = stripped_line.split('->')
                        if len(parts) == 2:
                            word, options = parts
                            choices[word.strip()] = [opt.strip() for opt in options.split(';')]
                            log_message(f"DEBUG: Added choice: '{word.strip()}' -> {choices[word.strip()]}")
                        else:
                            log_message(f"DEBUG: Skipping malformed choice line: '{stripped_line}'", level="WARNING")
                    elif current_section == 'replace':
                        parts = stripped_line.split('->')
                        if len(parts) == 2:
                            old, new = parts
                            replacements[old.strip()] = new.strip()
                            log_message(f"DEBUG: Added replacement: '{old.strip()}' -> '{new.strip()}'")
                        else:
                            log_message(f"DEBUG: Skipping malformed replacement line: '{stripped_line}'", level="WARNING")
                    elif current_section == 'periods':
                        periods.add(stripped_line)
                        log_message(f"DEBUG: Added period abbr: '{stripped_line}'")
                    elif current_section == 'ignore':
                        ignore_set.add(stripped_line)
                        log_message(f"DEBUG: Added ignore sequence: '{stripped_line}'")
                    elif current_section == 'lowercase':
                        lowercase_set.add(stripped_line)
                        log_message(f"DEBUG: Added lowercase sequence: '{stripped_line}'")
                    elif current_section == 'default_dir': # Process default directory line
                         # Take the first non-comment, non-empty line as the default directory
                         if default_file_directory is None: # Only set if not already set
                              potential_path = Path(stripped_line).expanduser()
                              if potential_path.is_dir():
                                   default_file_directory = potential_path
                                   log_message(f"DEBUG: Loaded default directory: '{default_file_directory}'")
                              else:
                                   log_message(f"DEBUG: Invalid default directory path in file: '{stripped_line}'", level="WARNING")


                elif current_section and stripped_line.startswith('#'):
                     log_message(f"DEBUG: Skipping comment line within section '{current_section}': '{stripped_line}'")
                elif current_section and not stripped_line:
                     log_message(f"DEBUG: Skipping empty line within section '{current_section}'")


            log_message("DEBUG: Finished data file parsing.")
            log_message(f"Loaded {len(choices)} choice rules, {len(replacements)} replacement rules, {len(periods)} period rules.")
            log_message(f"Loaded {len(ignore_set)} ignore sequences, {len(lowercase_set)} automatic lowercase sequences.")
            if default_file_directory:
                 log_message(f"Loaded default file directory: {default_file_directory}")
            else:
                 log_message("No valid default file directory found in .data.txt.")


        except Exception as e:
            log_message(f"Error loading data file '{data_file_path}': {e}. Starting with empty rules.", level="ERROR")
            # Ensure sets/dicts are empty in case of error
            choices = {}
            replacements = {}
            periods = set()
            ignore_set = set()
            lowercase_set = set()
            default_file_directory = None # Ensure this is also reset

    else:
        log_message(f"Data file '{DATA_FILE_NAME}' not found. Starting with empty rules.", level="WARNING")
        default_file_directory = None # Ensure this is None if file doesn't exist


def save_default_directory_to_data_file(directory_path):
    """
    Saves the given directory path to the # DEFAULT_FILE_DIR section in .data.txt.
    Reads the existing file, updates/creates the section, and writes back,
    preserving other sections and comments.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_file_path = os.path.join(script_dir, DATA_FILE_NAME)

    log_message(f"Attempting to save default directory '{directory_path}' to data file: {data_file_path}")

    original_lines = []
    if os.path.exists(data_file_path):
        try:
            with open(data_file_path, 'r', encoding='utf-8') as f:
                original_lines = f.readlines()
        except Exception as e:
            log_message(f"Warning: Could not read existing data file '{data_file_path}' for saving default directory: {e}. Will attempt to create/overwrite only the target section.", level="WARNING")
            original_lines = [] # Start with empty lines if reading fails

    # Find the start and end line indices for the content within the target section
    section_indices = {}
    current_section_start_idx = -1
    current_section_name = None

    for i, line in enumerate(original_lines):
         stripped_line = line.strip()
         # Check if the line is any known section marker
         if stripped_line in ALL_SECTION_MARKERS:
              # If we were in a section, mark its end
              if current_section_name and current_section_start_idx != -1:
                   section_indices[current_section_name] = (current_section_start_idx, i) # End is line *before* next marker
              # Start the new section
              current_section_name = {
                   CHOICE_SECTION_MARKER: 'choice',
                   REPLACE_SECTION_MARKER: 'replace',
                   PERIODS_SECTION_MARKER: 'periods',
                   IGNORE_SECTION_MARKER: 'ignore',
                   LOWERCASE_SECTION_MARKER: 'lowercase',
                   DEFAULT_DIR_SECTION_MARKER: 'default_dir'
              }.get(stripped_line)
              current_section_start_idx = i + 1 # Content starts on the line after the marker

    # After the loop, if we were in a section, its content ends at the end of the file
    if current_section_name and current_section_start_idx != -1:
         section_indices[current_section_name] = (current_section_start_idx, len(original_lines))


    # Build the new content lines for the default directory section
    new_default_dir_content_lines = [str(directory_path) + '\n'] # The path itself, followed by a newline

    # Construct the new list of lines by replacing the content within the default dir section
    new_lines = []
    i = 0
    default_dir_section_handled = False

    while i < len(original_lines):
        line = original_lines[i]
        stripped_line = line.strip()

        # Check if this line is the start of the default directory section
        if stripped_line == DEFAULT_DIR_SECTION_MARKER and 'default_dir' in section_indices:
            start_idx, end_idx = section_indices['default_dir']
            new_lines.append(line) # Keep the section marker line
            new_lines.extend(new_default_dir_content_lines) # Insert the new content
            i = end_idx # Jump past the old content lines
            default_dir_section_handled = True
            continue # Continue to the next line after the skipped block

        # If it's not the start of the default dir section, keep the original line
        new_lines.append(line)
        i += 1

    # If the default directory section didn't exist in the original file, append it
    if not default_dir_section_handled:
         # Add newline only if the file is not empty and the last line is not empty
         if new_lines and new_lines[-1].strip() != '':
              new_lines.append('\n')
         new_lines.append(DEFAULT_DIR_SECTION_MARKER + '\n')
         new_lines.extend(new_default_dir_content_lines)


    try:
        # If the file didn't exist, create its parent directories first
        Path(data_file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(data_file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        log_message(f"Default directory '{directory_path}' saved to '{DATA_FILE_NAME}'.")
    except Exception as e:
        log_message(f"Error saving default directory to data file '{data_file_path}': {e}", level="ERROR")


def save_caps_data_file(ignore_set, lowercase_set):
    """
    Saves the current ignore and automatic lowercase sequences to the .data.txt file.
    Reads the existing file, updates the specific sections, and writes back,
    preserving other sections and comments.
    Adjusted parsing logic to correctly find section boundaries.
    NOTE: This function only saves the CAP_IGNORE and UPPER_TO_LOWER sections.
    A more comprehensive save function handling all sections would be needed
    if other sections are modified by the GUI.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_file_path = os.path.join(script_dir, DATA_FILE_NAME)

    log_message(f"Attempting to save CAP_IGNORE and UPPER_TO_LOWER sections to data file: {data_file_path}")

    original_lines = []
    if os.path.exists(data_file_path):
        try:
            with open(data_file_path, 'r', encoding='utf-8') as f:
                original_lines = f.readlines()
        except Exception as e:
            log_message(f"Warning: Could not read existing data file '{data_file_path}' for saving caps data: {e}. Overwriting only target sections.", level="WARNING")
            original_lines = [] # Start with empty lines if reading fails

    # Find the start and end line indices for the content within the target sections
    # Content starts after the marker and ends before the next marker or end of file
    section_indices = {}
    current_section_start_idx = -1
    current_section_name = None

    for i, line in enumerate(original_lines):
         stripped_line = line.strip()
         # Check if the line is any known section marker
         if stripped_line in ALL_SECTION_MARKERS:
              # If we were in a section, mark its end
              if current_section_name and current_section_start_idx != -1:
                   section_indices[current_section_name] = (current_section_start_idx, i) # End is line *before* next marker
              # Start the new section
              current_section_name = {
                   CHOICE_SECTION_MARKER: 'choice',
                   REPLACE_SECTION_MARKER: 'replace',
                   PERIODS_SECTION_MARKER: 'periods',
                   IGNORE_SECTION_MARKER: 'ignore',
                   LOWERCASE_SECTION_MARKER: 'lowercase',
                   DEFAULT_DIR_SECTION_MARKER: 'default_dir'
              }.get(stripped_line)
              current_section_start_idx = i + 1 # Content starts on the line after the marker

    # After the loop, if we were in a section, its content ends at the end of the file
    if current_section_name and current_section_start_idx != -1:
         section_indices[current_section_name] = (current_section_start_idx, len(original_lines))


    # Build the new content lines for the sections we are saving (ignore and lowercase)
    new_ignore_content_lines = [seq + '\n' for seq in sorted(list(ignore_set))]
    new_lowercase_content_lines = [seq + '\n' for seq in sorted(list(lowercase_set))]

    # Construct the new list of lines by replacing the content within the found sections
    new_lines = []
    i = 0
    ignore_section_handled = False
    lowercase_section_handled = False

    while i < len(original_lines):
        line = original_lines[i]
        stripped_line = line.strip()

        # Check if this line is the start of a section we are replacing the content for
        if stripped_line == IGNORE_SECTION_MARKER and 'ignore' in section_indices:
            start_idx, end_idx = section_indices['ignore']
            new_lines.append(line) # Keep the section marker line
            new_lines.extend(new_ignore_content_lines) # Insert the new content
            i = end_idx # Jump past the old content lines
            ignore_section_handled = True
            continue # Continue to the next line after the skipped block

        elif stripped_line == LOWERCASE_SECTION_MARKER and 'lowercase' in section_indices:
            start_idx, end_idx = section_indices['lowercase']
            new_lines.append(line) # Keep the section marker line
            new_lines.extend(new_lowercase_content_lines) # Insert the new content
            i = end_idx # Jump past the old content lines
            lowercase_section_handled = True
            continue # Continue to the next line after the skipped block

        # If it's not the start of a section we are replacing, keep the original line
        new_lines.append(line)
        i += 1

    # If sections didn't exist in the original file but have content now, append them
    # Append only if the section wasn't found and handled in the original file
    if not ignore_section_handled and ignore_set:
         # Add newline only if last line is not empty
         if new_lines and new_lines[-1].strip() != '':
              new_lines.append('\n')
         new_lines.append(IGNORE_SECTION_MARKER + '\n')
         new_lines.extend(new_ignore_content_lines)

    if not lowercase_section_handled and lowercase_set:
         # Add newline only if last line is not empty
         if new_lines and new_lines[-1].strip() != '':
              new_lines.append('\n')
         new_lines.append(LOWERCASE_SECTION_MARKER + '\n')
         new_lines.extend(new_lowercase_content_lines)


    try:
        # If the file didn't exist, create its parent directories first
        Path(data_file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(data_file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        log_message(f"Data file '{DATA_FILE_NAME}' updated successfully (CAP_IGNORE, UPPER_TO_LOWER sections).")
    except Exception as e:
        log_message(f"Error saving data file '{data_file_path}' (CAP_IGNORE, UPPER_TO_LOWER sections): {e}", level="ERROR")


# --- File Selection Function ---
def select_file():
    """
    Opens a file dialog for the user to select an input text file.
    Uses the global default_file_directory for the initial directory.
    Includes settings to show hidden files.

    Returns:
        str or None: The full path to the selected file, or None if cancelled.
    """
    global default_file_directory # Need access to the global default

    log_message("Opening file selection dialog.")

    # Determine the initial directory based on the global default_file_directory
    initial_dir = default_file_directory if default_file_directory and default_file_directory.is_dir() else Path.home()
    log_message(f"Using initial directory for file dialog: {initial_dir}")


    # Define the types of files the dialog should display
    filetypes = [
        ("Text files", "*.txt"),
        ("HTML files", "*.html *.xhtml"),
        ("All files", "*.*")
    ]

    # --- Settings to control the hidden file display in the dialog ---
    # This Tk command forces the file dialog code to load, necessary for setvar to work reliably
    # 'catch' prevents the error from the badoption from stopping the script
    root.tk.eval('catch {tk_getOpenFile -badoption}')
    # This Tk command enables the "Show hidden files" checkbox in the dialog window
    root.tk.setvar('::tk::dialog::file::showHiddenBtn', 1)
    # This Tk command sets the initial state of the checkbox. 0 hides hidden files, 1 shows them.
    root.tk.setvar('::tk::dialog::file::showHiddenVar', 0)
    # --- End of hidden file settings ---


    # Open the file selection dialog
    selected_file = filedialog.askopenfilename(
        title="Select file to process", # Title of the dialog window
        filetypes=filetypes, # Filter the files shown
        initialdir=str(initial_dir) # Set the initial directory
    )

    # If a file was selected (the user didn't ancel)
    if selected_file:
        log_message(f"File selected: {selected_file}")
        # Change the current working directory to the directory of the selected file.
        # This is often useful if the script needs to access other files relative to the input file.
        os.chdir(os.path.dirname(selected_file))
        # Return the full path of the selected file
        return selected_file
    # If the user cancelled the dialog
    log_message("File selection cancelled.")
    return None

# --- Interactive Choice Processing Function (Original Bookfix) ---
def process_choices():
    """
    Iterates through words loaded from the data file that require a choice.
    For each word found in the text, it highlights the match, presents buttons
    for the user to select the replacement, and updates the text accordingly.
    Includes a progress bar.
    """
    global text, choices, current_word, current_match, matches, progress_bar, progress_label, choice_var
    # Declare progress_bar and progress_label as global within this function
    global progress_bar, progress_label

    log_message("Starting interactive choices processing.")

    # Get the total number of unique words requiring choices to track progress
    total_words = len(choices)
    processed_words = 0 # Counter for words finished

    # Create and display the progress bar and label
    # Ensure they are not already packed from a previous run
    if progress_bar is None:
        progress_bar = Progressbar(root, orient=tk.HORIZONTAL, length=200, mode='determinate')
    progress_bar.pack(pady=5)

    if progress_label is None:
        progress_label = tk.Label(root, text="Progress: 0%")
    progress_label.pack(pady=5)


    # Clear the text area and load the current state of the text before starting choices
    text_area.delete("1.0", tk.END)
    text_area.insert("1.0", text)


    # Loop through each word that needs interactive replacement
    for word in choices.keys():
        current_word = word # Set the current word being processed
        current_match = 0 # Reset the match index for the new word
        # Find all occurrences of the current word in the text
        # Use re.finditer to find all matches and store them as a list
        # \b ensures whole word matching
        # re.escape handles special characters in the word
        # re.IGNORECASE makes the search case-insensitive
        matches = list(re.finditer(r'\b' + re.escape(current_word) + r'\b', text, re.IGNORECASE))

        log_message(f"Processing word for choices: '{current_word}' - Found {len(matches)} matches.")

        # If there are matches for the current word
        if matches:
            # Clear any existing buttons from the choice frame
            for widget in choice_frame.winfo_children():
                widget.destroy()

            # Create buttons for each option
            options = choices[current_word] # Get the list of options for the current word
            # Define a monospace font for consistent button text width
            mono_font = Font(family="Courier New", size=10, weight="bold")

            for i, option in enumerate(options):
                button = tk.Button(choice_frame, text=option, command=lambda opt=option: handle_choice(opt), bg="blue", fg="white", font=mono_font)
                button.pack(side=tk.LEFT, padx=5)
                # Bind number keys (1-9) to the first 9 options
                if i < 9:
                     root.bind(str(i + 1), lambda event, opt=option: handle_choice(opt))
                     root.bind(f'<KP_{i + 1}>', lambda event, opt=option: handle_choice(opt))


            # Process each match for the current word interactively
            while current_match < len(matches):
                log_message(f"Handling match {current_match + 1}/{len(matches)} for '{current_word}'")
                highlight_current_match() # Highlight the current match
                # Wait here until a choice is made (handle_choice sets choice_var, releasing the wait)
                root.wait_variable(choice_var)

            # Unbind number keys after completing a word's choices
            for i in range(1, 10):
                 root.unbind(str(i))
                 root.unbind(f'<KP_{i}>')


        # Update progress after processing all matches for a word
        processed_words += 1
        progress_percent = int((processed_words / total_words) * 100)
        progress_bar['value'] = progress_percent
        progress_label.config(text=f"Progress: {progress_percent}%")
        root.update_idletasks() # Update the GUI to show the progress change

    # Hide the progress bar and label once all words are processed
    progress_bar.pack_forget()
    progress_label.pack_forget()

    # Clear choice buttons after processing is complete
    for widget in choice_frame.winfo_children():
        widget.destroy()

    # Update the main text variable with the changes made
    text = text_area.get("1.0", tk.END).strip() # Get the current content from the text area
    log_message("Finished interactive choices processing.")


# --- Helper Functions for Original Choice Processing ---
def highlight_current_match():
    """Highlights the currently selected match in the text area."""
    global current_match, matches, text_area, current_word
    # Remove any existing highlight tags
    text_area.tag_remove("highlight", "1.0", tk.END)
    # Check if there are matches and the current index is valid
    if matches and current_match < len(matches):
        # Get the start and end indices (span) of the current match
        start, end = matches[current_match].span()
        # Add a highlight tag to the text area at the match's position
        # Tkinter text indices are like "line.column"
        text_area.tag_add("highlight", f"1.0+{start}c", f"1.0+{end}c")
        # Configure the appearance of the highlight tag
        text_area.tag_config("highlight", background="lightblue", foreground="black")
        # Scroll the text area to make the highlighted match visible
        text_area.see(f"1.0+{start}c")
        # Update the status label to show progress for the current word
        status_label.config(text=f"Replacing {current_word}: {current_match + 1}/{len(matches)}")
    else:
        # If no more matches for the current word, update status
        status_label.config(text=f"Finished {current_word}") # More specific status


def handle_choice(choice):
    """
    Handles the user's selection of a replacement option for original choices.
    Replaces the current match in the text area, updates the match index,
    and signals the main loop to continue.
    """
    global text_area, current_match, matches, choice_var, text, current_word

    log_message(f"Handling choice '{choice}' for '{current_word}' (Match {current_match + 1})")

    # Ensure there is a valid match to process
    if matches and current_match < len(matches):
        start, end = matches[current_match].span() # Get the indices of the current match

        # Replace the text directly in the text area
        text_area.delete(f"1.0+{start}c", f"1.0+{end}c")
        text_area.insert(f"1.0+{start}c", choice)

        # Update the underlying text variable (important for subsequent processing steps)
        # This is less efficient than modifying the text variable directly, but necessary
        # to ensure the text area and variable are in sync after interactive edits.
        text = text_area.get("1.0", tk.END).strip()

        # Log the replacement made to a debug file
        with open('debug.txt', 'a', encoding="utf-8") as debug_file:
            debug_file.write(f"{current_word} -> {choice}\n")
        log_message(f"Logged choice: {current_word} -> {choice}")


        # Re-find matches for the current word in the *updated* text
        # This is crucial because the text area was modified, potentially changing indices.
        # Using the same regex as in process_choices
        updated_matches = list(re.finditer(r'\b' + re.escape(current_word) + r'\b', text, re.IGNORECASE))
        matches = updated_matches # Update the global matches list


        current_match += 1 # Move to the next match index

        # Signal the main loop to continue
        choice_var.set(choice_var.get() + 1) # Incrementing signals change


# --- All-Caps Sequence Processing Function (Integrated from caps.py) ---
def process_all_caps_sequences_gui():
    """
    Finds contiguous sequences of all-caps words (2+ letters),
    allowing punctuation and spaces between words, performs automatic
    processing based on data file, then interactive processing using GUI.
    """
    global text, ignore_set, lowercase_set, all_caps_matches_original, \
           choice_var, current_caps_sequence, current_caps_span, text_area, status_label, choice_frame, \
           decided_sequences_text, lowercased_original_spans # Declare necessary globals

    log_message("Starting all-caps sequences processing.")

    # Regex to find a sequence of 2+ uppercase letters, followed by zero or more
    # groups of (one or more non-word characters followed by 2+ uppercase letters).
    # \b ensures word boundaries at the start and end of the *entire* match.
    # This regex captures the full sequence including inter-word non-word characters.
    sequence_pattern = re.compile(r'\b([A-Z]{2,})(?:(?:\W+)[A-Z]{2,})*\b')

    # Find all matches in the current text (after previous processing steps)
    # This must be done ONCE at the beginning of this function
    all_caps_matches_original = list(sequence_pattern.finditer(text))
    log_message(f"DEBUG: Found {len(all_caps_matches_original)} potential all-caps sequences in total.")

    # Initialize sets for tracking decisions within this run at the start of processing
    # These need to be re-initialized each time processing starts
    decided_sequences_text = set() # Set to track sequence texts that have been decided upon (for skipping future occurrences in this run)
    lowercased_original_spans = set() # Set to track original spans that were lowercased (Pass 1 or Pass 2 'y'/'i')
    log_message("Initialized decided_sequences_text and lowercased_original_spans for all-caps for this run.")


    # --- Pass 1: Automatic Lowercasing and Marking for Skipping ---
    status_label.config(text="Applying automatic all-caps rules...")
    root.update_idletasks()
    log_message("Starting Pass 1: Automatic all-caps rules.")

    processed_text_list = list(text) # Start with current text content
    cumulative_offset = 0 # Total offset from all changes

    # Process original matches in order of appearance for Pass 1
    for original_match in all_caps_matches_original:
         original_sequence_text = original_match.group(0)
         original_start, original_end = original_match.span()
         original_span = (original_start, original_end)

         if original_sequence_text in lowercase_set:
             log_message(f"Auto-lowercasing: '{original_sequence_text}' (Span: {original_span})")
             # Calculate current start/end in the list
             current_start = original_start + cumulative_offset
             current_end = original_end + cumulative_offset
             replacement = list(original_sequence_text.lower())
             processed_text_list[current_start : current_end] = replacement
             cumulative_offset += len(replacement) - (original_end - original_start)
             decided_sequences_text.add(original_sequence_text) # Mark sequence text as decided
             lowercased_original_spans.add(original_span) # Mark original span as lowercased

         elif original_sequence_text in ignore_set:
             log_message(f"Auto-ignoring: '{original_sequence_text}' (Span: {original_span})")
             decided_sequences_text.add(original_sequence_text) # Mark sequence text as decided

    log_message(f"DEBUG: decided_sequences_text after Pass 1: {decided_sequences_text}")
    log_message(f"DEBUG: lowercased_original_spans after Pass 1: {lowercased_original_spans}")


    # Update the main text variable and text area with Pass 1 changes
    text = "".join(processed_text_list)
    text_area.delete("1.0", tk.END)
    text_area.insert("1.0", text)
    log_message("Finished Pass 1: Automatic all-caps rules. Text updated.")


    # --- Pass 2: Interactive Processing ---
    status_label.config(text="Starting interactive all-caps processing...")
    root.update_idletasks()
    log_message("Starting Pass 2: Interactive all-caps processing.")

    # Clear any existing buttons from the choice frame
    for widget in choice_frame.winfo_children():
        widget.destroy()

    # Create the Y/N/A/I buttons for all-caps processing
    # Use a lambda to capture the choice value when the button is created
    tk.Button(choice_frame, text="Yes (y)", command=lambda: handle_caps_choice('y')).pack(side=tk.LEFT, padx=5)
    tk.Button(choice_frame, text="No (n)", command=lambda: handle_caps_choice('n')).pack(side=tk.LEFT, padx=5)
    tk.Button(choice_frame, text="Add to Ignore (a)", command=lambda: handle_caps_choice('a')).pack(side=tk.LEFT, padx=5)
    tk.Button(choice_frame, text="Auto Lowercase (i)", command=lambda: handle_caps_choice('i')).pack(side=tk.LEFT, padx=5)

    # Add a label for the explanation
    explanation_label = tk.Label(choice_frame, text="y= lowercase this instance, n= keep this instance, a= add to ignore list, i= add to auto-lowercase list")
    explanation_label.pack(side=tk.LEFT, padx=5)

    # Bind keyboard shortcuts for interactive choices
    root.bind('y', lambda event: handle_caps_choice('y'))
    root.bind('n', lambda event: handle_caps_choice('n'))
    root.bind('a', lambda event: handle_caps_choice('a'))
    root.bind('i', lambda event: handle_caps_choice('i'))
    log_message("Keyboard shortcuts bound for all-caps choices.")


    # Iterate through the *original* matches again for the interactive pass
    interactive_prompts_count = 0

    for original_match in all_caps_matches_original:
         original_sequence_text = original_match.group(0)
         original_start, original_end = original_match.span()
         original_span = (original_start, original_end)

         # Check if this sequence text has already been decided upon in this run (auto or interactive)
         if original_sequence_text in decided_sequences_text:
             # log_message(f"DEBUG: Skipping interactive prompt for sequence '{original_sequence_text}' (already decided)")
             continue # Skip interactive prompt

         # --- Interactive Processing for sequences not automatically handled or decided ---

         interactive_prompts_count += 1
         # Calculate the cumulative offset *before* this original match's position in Pass 2.
         # This offset is the sum of length changes from all *previous* original matches
         # that were lowercased (either in Pass 1 or interactively in Pass 2) and occur before the current original_start.
         cumulative_offset_before_current = 0
         for prev_match in all_caps_matches_original:
             if prev_match.start() >= original_start:
                 break # Stop when we reach the current match or beyond

             prev_start, prev_end = prev_match.span()
             prev_span = (prev_start, prev_end)
             # prev_sequence_text = prev_match.group(0) # Not needed for offset calculation here

             # Check if this previous match's original span was lowercased (either in Pass 1 or Pass 2 'y'/'i')
             if prev_span in lowercased_original_spans:
                  cumulative_offset_before_current += len(prev_match.group(0).lower()) - (prev_end - prev_start)


         # Calculate the current start and end indices in the `text_area` for highlighting and replacement
         current_start_in_text_area = original_start + cumulative_offset_before_current
         current_end_in_text_area = original_end + cumulative_offset_before_current

         # Store the current sequence info globally for the button handlers
         current_caps_sequence = original_sequence_text
         current_caps_span = (current_start_in_text_area, current_end_in_text_area) # Store span relative to current text state

         log_message(f"Interactive prompt for: '{original_sequence_text}' (Original Span: {original_span}, Current Span: {current_caps_span})")


         # Display the found sequence and its context with highlighting in the text area
         # Highlight the current match in the text area
         text_area.tag_remove("highlight_caps", "1.0", tk.END)
         text_area.tag_add("highlight_caps", f"1.0+{current_start_in_text_area}c", f"1.0+{current_end_in_text_area}c")
         text_area.tag_config("highlight_caps", background="yellow", foreground="black")
         text_area.see(f"1.0+{current_start_in_text_area}c")

         status_label.config(text=f"Processing All-Caps: '{original_sequence_text}'")
         root.update_idletasks()

         # Wait here until a choice is made (handle_caps_choice sets choice_var, releasing the wait)
         choice_var.set(0) # Reset choice_var before waiting
         root.wait_variable(choice_var)

         # After handling the choice, the text_area and global 'text' variable are updated
         # and the decision is recorded in ignore_set/lowercase_set and saved.
         # The loop continues to the next original match.

    # Unbind keyboard shortcuts after all interactive all-caps processing is complete
    root.unbind('y')
    root.unbind('n')
    root.unbind('a')
    root.unbind('i')
    log_message("Keyboard shortcuts unbound for all-caps choices.")

    # Clear highlight after processing is complete
    text_area.tag_remove("highlight_caps", "1.0", tk.END)

    # Clear choice buttons after processing is complete
    for widget in choice_frame.winfo_children():
        widget.destroy()

    status_label.config(text="Finished all-caps processing.")
    root.update_idletasks()

    log_message(f"DEBUG: Total interactive all-caps prompts presented: {interactive_prompts_count}")
    log_message("Finished all-caps sequences processing.")


# --- Helper Function for All-Caps Choice Handling ---
def handle_caps_choice(choice):
    """
    Handles the user's selection for an all-caps sequence (y/n/a/i).
    Adds to data sets, saves data file, and signals the main loop.
    Does NOT modify text here; text modification happens in process_all_caps_sequences_gui Pass 1 and 2.
    """
    global text, ignore_set, lowercase_set, choice_var, \
           current_caps_sequence, current_caps_span, text_area, \
           decided_sequences_text, lowercased_original_spans, all_caps_matches_original # Need access to these globals

    original_sequence_text = current_caps_sequence
    current_start_in_text_area, current_end_in_text_area = current_caps_span

    log_message(f"Handling all-caps choice '{choice}' for '{original_sequence_text}' (Current Span: {current_caps_span})")

    # Find the original span of the sequence being processed
    # This is needed to add to lowercased_original_spans
    original_span_of_current_sequence = None
    # Iterate through original matches to find the one corresponding to the current sequence text
    # and that hasn't been marked as decided yet (to handle multiple occurrences of the same text)
    # This logic might need refinement if the same sequence text appears multiple times close together
    # and modifications shift indices significantly. For now, we find the first original match
    # that hasn't been lowercased.
    for original_match in all_caps_matches_original:
         if original_match.group(0) == original_sequence_text and original_match.span() not in lowercased_original_spans:
              original_span_of_current_sequence = original_match.span()
              break # Found the relevant original span


    if original_span_of_current_sequence is None:
        log_message(f"Warning: Could not find original span for sequence '{original_sequence_text}'. Cannot track lowercasing accurately.", level="WARNING")


    if choice in ['y', 'yes']:
        log_message(f"Converting '{original_sequence_text}' to lowercase (this instance).")
        # Apply the lowercase replacement directly in the text area
        text_area.delete(f"1.0+{current_start_in_text_area}c", f"1.0+{current_end_in_text_area}c")
        text_area.insert(f"1.0+{current_start_in_text_area}c", original_sequence_text.lower())
        # Update the underlying text variable
        text = text_area.get("1.0", tk.END).strip()

        # Mark this specific original span as lowercased interactively
        if original_span_of_current_sequence:
             lowercased_original_spans.add(original_span_of_current_sequence)
             log_message(f"Added original span {original_span_of_current_sequence} to lowercased_original_spans.")

        decided_sequences_text.add(original_sequence_text) # Mark sequence text as decided


    elif choice in ['n', 'no']:
        log_message(f"Keeping sequence '{original_sequence_text}' as is (this instance).")
        # No change to text area or text variable needed.
        decided_sequences_text.add(original_sequence_text) # Mark sequence text as decided


    elif choice in ['a', 'add']:
        log_message(f"Adding '{original_sequence_text}' to ignore list.")
        ignore_set.add(original_sequence_text) # Add to in-memory ignore set
        save_caps_data_file(ignore_set, lowercase_set) # Save updated data file
        # No change to text area or text variable needed for 'a'.
        decided_sequences_text.add(original_sequence_text) # Mark sequence text as decided


    elif choice in ['i', 'ignore']: # Using 'i' for add to lowercase as per user prompt
        log_message(f"Adding '{original_sequence_text}' to automatic lowercase list.")
        lowercase_set.add(original_sequence_text) # Add to in-memory lowercase set
        save_caps_data_file(ignore_set, lowercase_set) # Save updated data file
        # Apply the lowercase replacement directly in the text area
        text_area.delete(f"1.0+{current_start_in_text_area}c", f"1.0+{current_end_in_text_area}c")
        text_area.insert(f"1.0+{current_start_in_text_area}c", original_sequence_text.lower())
        # Update the underlying text variable
        text = text_area.get("1.0", tk.END).strip()

        # Mark this specific original span as lowercased interactively
        if original_span_of_current_sequence:
             lowercased_original_spans.add(original_span_of_current_sequence)
             log_message(f"Added original span {original_span_of_current_sequence} to lowercased_original_spans.")

        decided_sequences_text.add(original_sequence_text) # Mark sequence text as decided


    # Signal the main loop to continue
    choice_var.set(choice_var.get() + 1) # Incrementing signals change
    log_message(f"Choice handled. Signaling next step. choice_var = {choice_var.get()}")


# --- Automatic Text Processing Functions (Original Bookfix) ---
def apply_automatic_replacements():
    """Applies all find and replace rules loaded from the data file."""
    global text, replacements
    log_message("Starting automatic replacements.")
    # Iterate through each old/new pair in the replacements dictionary
    for old, new in replacements.items():
        # Replace all occurrences of 'old' with 'new' in the text
        text = text.replace(old, new)
    log_message("Finished automatic replacements.")


def insert_periods_into_abbreviations():
    """Inserts periods into specified abbreviations (e.g., 'Mr' -> 'M.r.')."""
    global text, periods
    log_message("Starting inserting periods into abbreviations.")
    # Iterate through each abbreviation that needs periods
    for abbr in periods:
        # Create a regex pattern to find the whole word abbreviation
        pattern = r'\b' + re.escape(abbr) + r'\b'
        # Create the replacement string with periods inserted between characters and at the end
        replacement = '.'.join(abbr) + '.'
        # Use re.sub to replace all matches of the pattern with the replacement string
        text = re.sub(pattern, replacement, text)
    log_message("Finished inserting periods.")


def convert_to_lowercase():
    """Converts the entire text to lowercase."""
    global text
    log_message("Starting converting to lowercase.")
    text = text.lower()
    log_message("Finished converting to lowercase.")


# --- Roman Numeral Conversion Functions ---
def roman_to_arabic(roman):
    """
    Converts a single Roman numeral string to its Arabic (integer) equivalent.
    Handles standard Roman numerals (I, V, X, L, C, D, M) including subtractive notation (IV, IX, etc.).
    Includes a basic check for validity as a Roman numeral pattern.

    Args:
        roman (str): The Roman numeral string (case-insensitive).

    Returns:
        int or None: The Arabic integer value, or None if the input is invalid
                     or is just the single character "I" (which is skipped).
    """
    # Mapping of Roman numeral characters to their integer values
    roman_map = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    # Regex pattern to validate the format of a Roman numeral
    roman_regex = r'\bM{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b'

    # Skip single "I" as it's often part of other words and not a numeral in text
    if roman.upper() == "I":
        return None
    # Check if the input string matches the standard Roman numeral regex pattern
    if not re.fullmatch(roman_regex, roman.upper()):
        return None # Return None if it doesn't match the expected pattern

    result = 0 # Initialize the result
    i = 0 # Index for iterating through the Roman numeral string
    while i < len(roman):
        # Get the integer value of the current character
        current_val = roman_map[roman[i].upper()]
        # Check if there's a next character and if its value is greater than the current one
        if i + 1 < len(roman) and current_val < roman_map[roman[i + 1].upper()]:
            # This is a subtractive case (e.g., IV, IX)
            result += roman_map[roman[i + 1].upper()] - current_val
            i += 2 # Move index past both characters
        else:
            # This is an additive case (e.g., V, II, XII)
            result += current_val
            i += 1 # Move index to the next character
    return result # Return the calculated Arabic value

def convert_roman_numerals():
    """
    Finds Roman numerals (in uppercase) in the text and converts them to Arabic integers.
    Avoids converting single 'I' and numerals adjacent to apostrophes or periods.
    Processes line by line to handle potential formatting issues.
    """
    global text
    log_message("Starting converting Roman numerals.")
    lines = text.splitlines() # Split the text into individual lines
    processed_lines = [] # List to store lines after processing

    # Iterate through each line
    for line in lines:
        # Define the regex pattern for finding Roman numerals (same as in roman_to_arabic)
        roman_regex = r'(?<![\w\'’])(?=[MDCLXVI]+\b)(?![A-Z])([MDCLXVI]+)\b(?![\w\'’])' # Improved regex (for context)
        # Find all potential Roman numerals (uppercase and matching pattern) and their positions
        roman_numerals = [(match.group(0), match.span()) for match in re.finditer(roman_regex, line) if match.group(0).isupper()]

        replacements = [] # List to store valid Roman numeral conversions (start_idx, end_idx, arabic_string)
        # Iterate through the found potential Roman numerals
        for roman, (start, end) in roman_numerals:
            # Skip single 'I's or numerals that look like they are part of a word with punctuation
            if len(roman) == 1 and ((start > 0 and line[start - 1] in ['.', "'"]) or (end < len(line) and line[end] in ['.', "'"])):
                continue

            # Attempt to convert the Roman numeral to Arabic
            arabic = roman_to_arabic(roman)
            # If the conversion is successful (returns an integer, not None)
            if arabic is not None:
                replacements.append((start, end, str(arabic))) # Store the conversion details

        # Apply replacements from the end of the line to the beginning to avoid index issues
        new_line = list(line) # Convert line to a mutable list of characters
        for start, end, replacement in reversed(replacements):
            new_line[start:end] = list(replacement) # Replace the Roman numeral characters with the Arabic number characters
        processed_line = "".join(new_line) # Join the list of characters back into a string
        processed_lines.append(processed_line) # Add the modified line to the list

    # Join all processed lines back together into the main text block
    text = "\n".join(processed_lines)
    log_message("Finished converting Roman numerals.")


# --- Pagination Removal Function ---
def remove_pagination():
    """
    Attempts to remove pagination elements from the text based on file type.
    Uses BeautifulSoup for HTML/XHTML and simple line checks for TXT files.
    Logs removed elements to a debug file.
    """
    global text, filepath
    log_message("Starting removing pagination.")
    pagination_log = [] # List to record what was removed

    try:
        # Check if the file is HTML or XHTML
        if filepath.lower().endswith((".xhtml", ".html")):
            soup = BeautifulSoup(text, 'xml') # Parse the text using BeautifulSoup's XML parser

            # Find elements commonly used for pagination based on class or ID
            page_number_elements = soup.find_all(class_=re.compile(r"page-number", re.IGNORECASE))
            page_number_elements.extend(soup.find_all(id=re.compile(r"page-number", re.IGNORECASE)))
            # Find <p> tags containing only digits (common for simple page numbers)
            page_number_elements.extend(soup.find_all(name=re.compile(r"p", re.IGNORECASE), string=re.compile(r"^\s*\d+\s*$", re.IGNORECASE)))

            # Iterate through found elements
            for element in page_number_elements:
                pagination_log.append(f"Removed: {element}") # Log the element
                element.decompose() # Remove the element from the soup

            text = str(soup) # Convert the modified soup back to a string
            # Remove any empty lines that might result from element removal
            lines = text.splitlines()
            filtered_lines = [line for line in lines if line.strip()]
            text = "\n".join(filtered_lines)

        # Check if the file is a plain text file
        elif filepath.lower().endswith(".txt"):
            lines = text.splitlines() # Split text into lines
            filtered_lines = [] # List for lines to keep
            # Iterate through each line
            for line in lines:
                # If the line contains only digits (potential page number)
                if line.strip().isdigit():
                    pagination_log.append(f"Removed: {line}") # Log the line
                    # Skip adding this line to filtered_lines (effectively removing it)
                else:
                    filtered_lines.append(line) # Keep lines that are not just digits
            text = "\n".join(filtered_lines) # Join filtered lines back

    except Exception as e:
        # Handle errors during pagination removal
        log_message(f"Error removing pagination: {e}", level="ERROR")
        messagebox.showerror("Error", f"Error removing pagination: {e}")

    # Save the log of removed pagination to a file
    try:
        with open("pagination_debug.txt", "w", encoding="utf-8") as log_file:
            log_file.write("\n".join(pagination_log))
        log_message("Pagination removal log saved to pagination_debug.txt.")
    except Exception as e:
        log_message(f"Error saving pagination debug log: {e}", level="ERROR")

    log_message("Finished removing pagination.")


# --- Main Processing Workflow ---
def run_processing():
    """
    Manages the main text processing workflow based on checkbox states.
    Assumes file and data are already loaded into global variables.
    Performs interactive choices, applies automatic replacements,
    removes pagination, converts roman numerals, converts to lowercase,
    processes all-caps sequences, updates the GUI, and displays the save button.
    """
    global text, choices, replacements, periods, \
           process_choices_var, apply_replacements_var, insert_periods_var, \
           remove_pagination_var, convert_roman_var, convert_lowercase_var, \
           process_all_caps_var, ignore_set, lowercase_set, \
           lowercased_original_spans, decided_sequences_text # Declare necessary globals

    log_message("Starting run_processing (dispatch section).")

    # Initialize sets for tracking decisions within this run at the start of processing
    # These need to be re-initialized each time processing starts
    decided_sequences_text = set() # Set to track sequence texts that have been decided upon (for skipping future occurrences in this run)
    lowercased_original_spans = set() # Set to track original spans that were lowercased (Pass 1 or Pass 2 'y'/'i')
    log_message("Initialized decided_sequences_text and lowercased_original_spans for all-caps for this run.")


    # --- Processing Steps (Conditional based on Checkboxes) ---
    # Ordered according to the checkboxes in the GUI


    # 1. Interactive Choices (Original Bookfix)
    if process_choices_var.get():
        log_message("Checkbox 'Interactive Choices' is checked. Executing process_choices().")
        update_status_label("Starting interactive choices...")
        process_choices() # Handle interactive replacements based on choices
        log_message("process_choices() finished.")
        # process_choices updates the global 'text' variable and text_area
    else:
        log_message("Checkbox 'Interactive Choices' is NOT checked. Skipping process_choices().")


    # 2. Apply Automatic Replacements (Original Bookfix)
    if apply_replacements_var.get():
        log_message("Checkbox 'Apply Automatic Replacements' is checked. Executing apply_automatic_replacements().")
        update_status_label("Applying automatic replacements...")
        apply_automatic_replacements() # Apply automatic find/replace rules
        update_text_area() # Update text area after this step
        log_message("apply_automatic_replacements() finished.")
    else:
        log_message("Checkbox 'Apply Automatic Replacements' is NOT checked. Skipping apply_automatic_replacements().")


    # 3. Insert Periods into Abbreviations (if uncommented and checked)
    if insert_periods_var.get():
        log_message("Checkbox 'Insert Periods into Abbreviations' is checked.")
        update_status_label("Inserting periods into abbreviations...")
        # insert_periods_into_abbreviations() # This line is currently commented out in your script
        # If you uncomment the function call above, this checkbox will control it.
        log_message("Function call for 'Insert Periods' is commented out in code.", level="WARNING")
        # update_text_area() # Uncomment if you uncomment the function call
        log_message("insert_periods_into_abbreviations() (commented) finished.")
    else:
        log_message("Checkbox 'Insert Periods into Abbreviations' is NOT checked. Skipping.")


    # 4. Remove Pagination
    if remove_pagination_var.get():
        log_message("Checkbox 'Remove Pagination' is checked. Executing remove_pagination().")
        update_status_label("Removing pagination...")
        remove_pagination() # Remove detected pagination elements
        update_text_area() # Update text area after this step
        log_message("remove_pagination() finished.")
    else:
        log_message("Checkbox 'Remove Pagination' is NOT checked. Skipping remove_pagination().")

    # 7. Process All-Caps Sequences (Integrated from caps.py) - Runs LAST
    if process_all_caps_var.get():
        log_message("Checkbox 'Process All-Caps Sequences' is checked. Executing process_all_caps_sequences_gui().")
        update_status_label("Starting all-caps processing...")
        process_all_caps_sequences_gui()
        log_message("process_all_caps_sequences_gui() finished.")
        # process_all_caps_sequences_gui updates the global 'text' variable and text_area
    else:
        log_message("Checkbox 'Process All-Caps Sequences' is NOT checked. Skipping process_all_caps_sequences_gui().")

    # 5. Convert Roman Numerals
    if convert_roman_var.get():
        log_message("Checkbox 'Convert Roman Numerals' is checked. Executing convert_roman_numerals().")
        update_status_label("Converting Roman numerals...")
        convert_roman_numerals() # Convert Roman numerals to Arabic
        update_text_area() # Update text area after this step
        log_message("convert_roman_numerals() finished.")
    else:
        log_message("Checkbox 'Convert Roman Numerals' is NOT checked. Skipping convert_roman_numerals().")


    # 6. Convert to Lowercase
    if convert_lowercase_var.get():
        log_message("Checkbox 'Convert to Lowercase' is checked. Executing convert_to_lowercase().")
        update_status_label("Converting to lowercase...")
        convert_to_lowercase() # Convert all text to lowercase
        update_text_area() # Update text area after this step
        log_message("convert_to_lowercase() finished.")
    else:
        log_message("Checkbox 'Convert to Lowercase' is NOT checked. Skipping convert_to_lowercase().")




    # --- End Processing Steps ---

    # Update the GUI display and status
    log_message("All processing steps checked have finished.")
    update_status_label("Processing complete.") # Update status to "Processing complete"
    display_save_button() # Make the save button available
    log_message("run_processing (dispatch section) finished.")


def start_processing_button_command():
    """
    Command to be executed when the 'Start Processing' button is clicked.
    Initiates the main text processing workflow.
    """
    global start_processing_button, text_area, text # Need global text_area and text here

    log_message("Start Processing button clicked.")

    # Disable the start button while processing is running
    start_processing_button.config(state=tk.DISABLED)
    log_message("Start Processing button disabled.")

    # Clear the text area and load the current state of the text before starting processing
    # This ensures we start with the text loaded after file selection, not a potentially old state
    # The 'text' global variable holds the content loaded from the file initially.
    # Processing functions will modify this 'text' variable.
    text_area.delete("1.0", tk.END)
    text_area.insert("1.0", text)
    log_message("Text area cleared and re-populated with initial text.")

    # Clear the execution log file at the start of a new run
    try:
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(f"--- New Execution Start: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        log_message(f"Cleared previous log file: {log_file_path}")
    except Exception as e:
        log_message(f"Error clearing log file {log_file_path}: {e}", level="ERROR")

    log_message("Calling run_processing().")
    run_processing() # Call the main processing function
    log_message("Returned from run_processing().")


    # Re-enable the start button after processing
    start_processing_button.config(state=tk.NORMAL)
    log_message("Start Processing button re-enabled.")


# --- GUI Update Functions ---
def update_text_area():
    """Refreshes the main text area with the current content of the 'text' variable."""
    global text, text_area # Need global text_area here
    log_message("Updating text area with current text variable content.")
    text_area.delete("1.0", tk.END) # Clear existing content
    text_area.insert("1.0", text) # Insert the current text

def update_status_label(message):
    """Updates the status label with a given message."""
    global status_label # Need global status_label here
    log_message(f"Updating status label: {message}")
    status_label.config(text=message)

def save_file():
    """Saves the final processed text to a new file."""
    global text, filepath

    log_message("Save button clicked. Attempting to save file.")

    # Construct the output filename based on the original file name, adding "_output"
    base_name = os.path.basename(filepath) # Get filename from the full path
    file_stem = os.path.splitext(base_name)[0] # Get the filename without extension
    output_filename = file_stem + "_output.txt" # Append "_output" and set extension to .txt

    # Construct the full output file path in the current working directory (which was set in select_file)
    output_filepath = os.path.join(os.getcwd(), output_filename)
    log_message(f"Saving output to: {output_filepath}")

    try:
        # Open the output file for writing (overwriting if it exists)
        with open(output_filepath, "w", encoding="utf-8") as output_file:
            output_file.write(text) # Write the processed text to the file
        # Show a success message box
        log_message("File saved successfully.")
        messagebox.showinfo("Info", f"Output saved to {output_filepath}")
    except Exception as e:
        # Show an error message box if saving fails
        log_message(f"Error saving output file: {e}", level="ERROR")
        messagebox.showerror("Error", f"Error saving output: {e}")

def display_save_button():
    """Makes the save button visible."""
    global save_button # Need global save_button here
    log_message("Displaying save button.")
    save_button.pack(pady=5)


# --- Program Exit Function ---
def quit_program():
    """Exits the program cleanly."""
    global root
    log_message("Quitting program.")
    # Check if the root window exists and destroy it if it does
    if 'root' in globals() and root:
        root.destroy()
    # Force exit the script
    os._exit(0)

# --- Main Application Entry Point ---
# This ensures the main() function is called when the script is executed directly
if __name__ == "__main__":
    # Create the main Tkinter window. This MUST happen before any calls that use 'root'.
    root = tk.Tk()
    root.title("Bookfix GUI") # Set the window title

    log_message("Bookfix GUI application started.")

    # Load data from .data.txt first, which includes the default directory
    load_data_file()

    # Check if a default directory was loaded and is valid
    if default_file_directory is None or not default_file_directory.is_dir():
         log_message("No valid default file directory found. Prompting user to select one.")

         # --- Display message box before asking for directory ---
         messagebox.showinfo(
             "Set Default Directory",
             "A default start directory for the file dialog has not been set or is invalid.\n\n"
             "For best use, please select a default directory now.\n\n"
             "Your Calibre Library folder is best, OR a folder you keep your ebook text files.\n\n"
             "Click OK to select a directory."
         )
         # --- End message box ---

         # Prompt the user to select a default directory
         initial_prompt_dir = Path.home() # Start the directory dialog in the user's home
         selected_default_dir_path = filedialog.askdirectory(
              title="Select Default Directory for File Dialog",
              initialdir=str(initial_prompt_dir)
         )

         if selected_default_dir_path:
              # If user selected a directory, set it as the default and save it
              default_file_directory = Path(selected_default_dir_path).resolve()
              log_message(f"User selected default directory: {default_file_directory}")
              save_default_directory_to_data_file(default_file_directory) # Save the selected path

              # --- Display confirmation message box ---
              messagebox.showinfo(
                  "Default Directory Set",
                  f"Default directory set to:\n{default_file_directory}\n\n"
                  "Click OK to proceed to file selection."
              )
              # --- End confirmation message box ---

         else:
              # If user cancelled the default directory selection, exit
              log_message("Default directory selection cancelled. Exiting.", level="INFO")
              quit_program() # Exit gracefully


    # Now that default_file_directory is established (either loaded or selected),
    # proceed to file selection using this default.
    filepath = select_file()

    # Check if a file was successfully selected (user didn't cancel)
    if filepath:
        # If a file was selected, set up the rest of the main GUI elements

        # Read the content of the selected file immediately after selection
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                text = file.read()
            log_message(f"Successfully read file: {filepath}")
        except Exception as e:
            log_message(f"Error reading file '{filepath}': {e}", level="ERROR")
            messagebox.showerror("File Read Error", f"Error reading file '{filepath}': {e}")
            # Exit or return to file selection if reading fails
            quit_program() # Or implement a 'Load New File' option
            sys.exit(1) # Exit script


        # Initialize BooleanVars for processing steps (pre-checked by default)
        process_choices_var = BooleanVar(value=True)
        apply_replacements_var = BooleanVar(value=True)
        insert_periods_var = BooleanVar(value=True) # Keep as True even if function is commented
        remove_pagination_var = BooleanVar(value=True)
        convert_roman_var = BooleanVar(value=True)
        convert_lowercase_var = BooleanVar(value=True)
        process_all_caps_var = BooleanVar(value=True) # New checkbox variable


        # Frame to hold the processing step checkboxes
        processing_options_frame = ttk.LabelFrame(root, text="Processing Steps", padding="10")
        processing_options_frame.pack(pady=10, padx=10, fill=tk.X)

        # Create and pack the checkboxes
        ttk.Checkbutton(processing_options_frame, text="Interactive Choices", variable=process_choices_var).grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Checkbutton(processing_options_frame, text="Apply Automatic Replacements", variable=apply_replacements_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        ttk.Checkbutton(processing_options_frame, text="Insert Periods into Abbreviations", variable=insert_periods_var).grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        ttk.Checkbutton(processing_options_frame, text="Remove Pagination", variable=remove_pagination_var).grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Checkbutton(processing_options_frame, text="Convert Roman Numerals", variable=convert_roman_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        ttk.Checkbutton(processing_options_frame, text="Convert to Lowercase", variable=convert_lowercase_var).grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        ttk.Checkbutton(processing_options_frame, text="Process All-Caps Sequences (Last)", variable=process_all_caps_var).grid(row=2, column=0, sticky=tk.W, padx=5, pady=2) # New checkbox

        # Configure columns to expand evenly
        processing_options_frame.columnconfigure(0, weight=1)
        processing_options_frame.columnconfigure(1, weight=1)
        processing_options_frame.columnconfigure(2, weight=1)


        # Text area to display and show highlighted text
        text_area = tk.Text(root, wrap=tk.WORD, width=80, height=20)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        # Display initial text content
        update_text_area()


        # Label to display current status messages
        status_label = tk.Label(root, text="File loaded. Select options and click 'Start Processing'.")
        status_label.pack(pady=5)

        # Frame to hold replacement choice buttons (used during interactive steps)
        choice_frame = tk.Frame(root)
        choice_frame.pack(pady=10)

        # Frame to hold main action buttons (Start, Save, Quit)
        button_frame = tk.Frame(root)
        button_frame.pack(pady=5, fill=tk.X, expand=True)

        # New Start Processing button
        start_processing_button = tk.Button(button_frame, text="Start Processing", command=start_processing_button_command)
        start_processing_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)


        # Save button (initially hidden, displayed after processing)
        save_button = tk.Button(button_frame, text="Save", command=save_file)
        # save_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True) # Don't pack here, display_save_button does this later

        # An empty frame used as a spacer to push Save and Quit buttons apart
        empty_frame = tk.Frame(button_frame)
        empty_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Quit button
        quit_button = tk.Button(button_frame, text="Quit", command=quit_program)
        quit_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Tkinter variable used to signal when an interactive choice has been handled
        choice_var = tk.IntVar()

        # Clear the debug.txt file at the start of processing a new file
        try:
            open('debug.txt', 'w').close()
            log_message("Cleared debug.txt file.")
        except Exception as e:
            log_message(f"Error clearing debug.txt file: {e}", level="ERROR")


        # Start the Tkinter event loop. This makes the GUI interactive.
        # The processing workflow will be triggered by the 'Start Processing' button click.
        log_message("Starting Tkinter main loop.")
        root.mainloop()
    else:
        # If no file was selected in the dialog (after default dir is established)
        log_message("No file selected after default directory established. Exiting.", level="INFO") # Use stderr
        # Destroy the root window that was created (it's an empty window if mainloop wasn't called)
        # Check if root exists before destroying
        if 'root' in globals() and root:
             root.destroy()
        # Exit the script immediately
        sys.exit(0) # Use sys.exit for clean exit
