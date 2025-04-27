#!/usr/bin/env python3

# --- bookfix.py ---
# This script provides a GUI tool to process text files (primarily ebooks in .txt, .html, .xhtml formats).
# It reads replacement rules and choices from a .data.txt file,
# allows the user to interactively make choices for specific words,
# applies automatic replacements and text cleaning (like removing pagination and converting Roman numerals),
# and saves the modified text to a new file.

import tkinter as tk # Import the Tkinter library for creating the GUI
from tkinter import messagebox, filedialog # Import specific modules for dialog boxes
import re # Import the regular expression module for text pattern matching
import os # Import the os module for interacting with the operating system (file paths, etc.)
from bs4 import BeautifulSoup # Import BeautifulSoup for parsing HTML/XML content
from tkinter.font import Font # Import Font for custom text styling in the GUI
from tkinter.ttk import Progressbar # Import Progressbar for showing processing progress

# --- Data Loading Function ---
def load_data_file():
    """
    Loads replacement choices, automatic replacements, and abbreviation period rules
    from a .data.txt file located in the same directory as the script.

    The data file format uses '#' to denote sections:
    #CHOICE -> words with options for user selection (word->option1;option2;...)
    #REPLACE -> automatic find and replace rules (old->new)
    #PERIODS -> abbreviations to insert periods into (abbr)

    Returns:
        tuple: (choices, replacements, periods)
               choices (dict): words mapped to a list of possible replacements.
               replacements (dict): words/phrases mapped to their automatic replacements.
               periods (set): abbreviations that should have periods inserted.
    """
    choices = {} # Dictionary to store words requiring user choice
    replacements = {} # Dictionary to store automatic replacements
    periods = set() # Set to store abbreviations for period insertion
    current_section = None # Variable to track the current section being read from the file

    # Determine the directory the script is running from
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the full path to the data file
    data_file_path = os.path.join(script_dir, '.data.txt')

    try:
        # Open and read the data file line by line
        with open(data_file_path, 'r') as f:
            for line in f:
                line = line.strip() # Remove leading/trailing whitespace
                if line.startswith('#'):
                    # If the line starts with '#', it's a section header
                    current_section = line[1:].strip() # Store the section name (without '#')
                elif line:
                    # If the line is not a comment or empty and a section is active
                    if current_section == 'CHOICE':
                        # Process lines in the CHOICE section
                        word, options = line.split('->') # Split the line into the word and its options
                        choices[word.strip()] = [opt.strip() for opt in options.split(';')] # Store the word and a list of options
                    elif current_section == 'REPLACE':
                        # Process lines in the REPLACE section
                        old, new = line.split('->') # Split the line into the old and new text
                        replacements[old.strip()] = new.strip() # Store the old text and its replacement
                    elif current_section == 'PERIODS':
                        # Process lines in the PERIODS section
                        periods.add(line.strip()) # Add the abbreviation to the set

    except FileNotFoundError:
        # Handle the case where the data file doesn't exist
        print("Data file not found. Using default settings (empty rules).")
    except Exception as e:
        # Handle other potential errors during file reading
        print(f"Error loading data file: {e}. Using default settings (empty rules).")


    # Return the populated dictionaries and set
    return choices, replacements, periods

# --- File Selection Function ---
def select_file():
    """
    Opens a file dialog for the user to select an input text file.
    Includes settings to show hidden files.

    Returns:
        str or None: The full path to the selected file, or None if cancelled.
    """
    # Set the default directory for the file dialog
    start_dir = "/home/danno/Calibre Library"
    # Fallback to the user's home directory if the default doesn't exist
    if not os.path.isdir(start_dir):
        start_dir = os.path.expanduser("~")

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
        initialdir=start_dir # Set the initial directory
    )

    # If a file was selected (the user didn't cancel)
    if selected_file:
        # Change the current working directory to the directory of the selected file.
        # This is often useful if the script needs to access other files relative to the input file.
        os.chdir(os.path.dirname(selected_file))
        # Return the full path of the selected file
        return selected_file
    # If the user cancelled the dialog
    return None

# --- Interactive Choice Processing Function ---
def process_choices():
    """
    Iterates through words loaded from the data file that require a choice.
    For each word found in the text, it highlights the match, presents buttons
    for the user to select the replacement, and updates the text accordingly.
    Includes a progress bar.
    """
    global text, choices, current_word, current_match, matches, progress_bar, progress_label

    # Get the total number of unique words requiring choices to track progress
    total_words = len(choices)
    processed_words = 0 # Counter for words finished

    # Create and display the progress bar and label
    progress_bar = Progressbar(root, orient=tk.HORIZONTAL, length=200, mode='determinate')
    progress_bar.pack(pady=5)
    progress_label = tk.Label(root, text="Progress: 0%")
    progress_label.pack(pady=5)

    # Loop through each word that needs interactive replacement
    for word in choices.keys():
        current_word = word # Set the current word being processed
        current_match = 0 # Reset the match index for the new word
        update_matches() # Find all occurrences of the current word in the text

        # If there are matches for the current word
        if matches:
            # Clear the text area and load the current state of the text
            text_area.delete("1.0", tk.END)
            text_area.insert("1.0", text)
            highlight_current_match() # Highlight the first match
            update_choice_buttons() # Create and display the choice buttons for this word
            # Wait here until a choice is made (handle_choice sets choice_var, releasing the wait)
            root.wait_variable(choice_var)
        else:
            # If no matches for this word, skip to the next word
            continue

        # Update progress after processing all matches for a word
        processed_words += 1
        progress_percent = int((processed_words / total_words) * 100)
        progress_bar['value'] = progress_percent
        progress_label.config(text=f"Progress: {progress_percent}%")
        root.update_idletasks() # Update the GUI to show the progress change

    # Hide the progress bar and label once all words are processed
    progress_bar.pack_forget()
    progress_label.pack_forget()

# --- Helper Functions for Processing Choices ---
def update_matches():
    """Finds all occurrences of the current word in the text using regex."""
    global matches, current_word, text
    # Use re.finditer to find all matches and store them as a list
    # \b ensures whole word matching
    # re.escape handles special characters in the word
    # re.IGNORECASE makes the search case-insensitive
    matches = list(re.finditer(r'\b' + re.escape(current_word) + r'\b', text, re.IGNORECASE))

def highlight_current_match():
    """Highlights the currently selected match in the text area."""
    global current_match, matches
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
        status_label.config(text="No more matches for current word")

def update_choice_buttons():
    """Creates and displays buttons corresponding to the replacement options for the current word."""
    # Clear any existing buttons from the choice frame
    for widget in choice_frame.winfo_children():
        widget.destroy()

    options = choices[current_word] # Get the list of options for the current word

    # Special handling if there are exactly two options (for 1/2 key bindings)
    if len(options) == 2:
        # Create a small frame to hold numbers 1 and 2 above the buttons
        num_frame = tk.Frame(choice_frame)
        num_frame.pack(side=tk.TOP, pady=5)
        tk.Label(num_frame, text="1").pack(side=tk.LEFT, padx=30)
        tk.Label(num_frame, text="2").pack(side=tk.LEFT, padx=30)

        # Define a monospace font for consistent button text width
        mono_font = Font(family="Courier New", size=10, weight="bold")

        # Create button 1 with the first option
        button1 = tk.Button(choice_frame, text=options[0], command=lambda opt=options[0]: handle_choice(opt), bg="blue", fg="white", font=mono_font)
        button1.pack(side=tk.LEFT, padx=20)
        # Create button 2 with the second option
        button2 = tk.Button(choice_frame, text=options[1], command=lambda opt=options[1]: handle_choice(opt), bg="blue", fg="white", font=mono_font)
        button2.pack(side=tk.LEFT, padx=20)

        # Bind keyboard shortcuts '1' and '2' (and numpad 1/2) to trigger the buttons
        root.bind('1', lambda event: button1.invoke())
        root.bind('<KP_1>', lambda event: button1.invoke())
        root.bind('2', lambda event: button2.invoke())
        root.bind('<KP_2>', lambda event: button2.invoke())
    else:
        # If not exactly two options, create a button for each option
        mono_font = Font(family="Courier New", size=10, weight="bold")
        for option in options:
            button = tk.Button(choice_frame, text=option, command=lambda opt=option: handle_choice(opt), bg="blue", fg="white", font=mono_font)
            button.pack(side=tk.LEFT, padx=5)

def handle_choice(choice):
    """
    Handles the user's selection of a replacement option.
    Replaces the current match in the text, updates the match index,
    and prepares for the next match or word. Logs the choice to debug.txt.
    """
    global text, current_match, matches, current_word, choice_var

    # Ensure there is a valid match to process
    if matches and current_match < len(matches):
        start, end = matches[current_match].span() # Get the indices of the current match

        # Replace the text at the match location with the chosen option
        text = text[:start] + choice + text[end:]

        # Update the text area display by deleting the old text and inserting the new choice
        text_area.delete(f"1.0+{start}c", f"1.0+{end}c")
        text_area.insert(f"1.0+{start}c", choice)

        current_match += 1 # Move to the next match index

        # Re-find matches for the current word (necessary because text was modified)
        update_matches()
        # Highlight the next match
        highlight_current_match()

        # If all matches for the current word are processed, signal the main loop to move to the next word
        if current_match >= len(matches):
            choice_var.set(1) # Setting choice_var wakes up root.wait_variable in process_choices
        else:
            # If there are more matches, just highlight the next one
            highlight_current_match()
    else:
        # If for some reason handle_choice was called without a valid match, signal to move on
        choice_var.set(1) # Setting choice_var wakes up root.wait_variable

    # Log the replacement made to a debug file
    with open('debug.txt', 'a') as debug_file:
        debug_file.write(f"{current_word} -> {choice}\n")

# --- GUI Update Functions ---
def update_text_area():
    """Refreshes the main text area with the current content of the 'text' variable."""
    global text
    text_area.delete("1.0", tk.END) # Clear existing content
    text_area.insert("1.0", text) # Insert the current text

def update_status_label():
    """Updates the status label to indicate that processing is complete."""
    status_label.config(text="Processing complete")

def save_file():
    """Saves the final processed text to a new file."""
    global text, filepath

    # Construct the output filename based on the original file name, adding "_output"
    base_name = os.path.basename(filepath) # Get filename from the full path
    file_stem = os.path.splitext(base_name)[0] # Get the filename without extension
    output_filename = file_stem + "_output.txt" # Append "_output" and set extension to .txt

    # Construct the full output file path in the current working directory (which was set in select_file)
    output_filepath = os.path.join(os.getcwd(), output_filename)

    try:
        # Open the output file for writing (overwriting if it exists)
        with open(output_filepath, "w", encoding="utf-8") as output_file:
            output_file.write(text) # Write the processed text to the file
        # Show a success message box
        messagebox.showinfo("Info", f"Output saved to {output_filepath}")
    except Exception as e:
        # Show an error message box if saving fails
        messagebox.showerror("Error", f"Error saving output: {e}")

def display_save_button():
    """Makes the save button visible."""
    save_button.pack(pady=5)

# --- Automatic Text Processing Functions ---
def apply_automatic_replacements():
    """Applies all find and replace rules loaded from the data file."""
    global text, replacements
    # Iterate through each old/new pair in the replacements dictionary
    for old, new in replacements.items():
        # Replace all occurrences of 'old' with 'new' in the text
        text = text.replace(old, new)

def insert_periods_into_abbreviations():
    """Inserts periods into specified abbreviations (e.g., 'Mr' -> 'M.r.')."""
    global text, periods
    # Iterate through each abbreviation that needs periods
    for abbr in periods:
        # Create a regex pattern to find the whole word abbreviation
        pattern = r'\b' + re.escape(abbr) + r'\b'
        # Create the replacement string with periods inserted between characters and at the end
        replacement = '.'.join(abbr) + '.'
        # Use re.sub to replace all matches of the pattern with the replacement string
        text = re.sub(pattern, replacement, text)

def convert_to_lowercase():
    """Converts the entire text to lowercase."""
    global text
    text = text.lower()

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
    lines = text.splitlines() # Split the text into individual lines
    processed_lines = [] # List to store lines after processing

    # Iterate through each line
    for line in lines:
        # Define the regex pattern for finding Roman numerals (same as in roman_to_arabic)
        roman_regex = r'\bM{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b'
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


# --- Pagination Removal Function ---
def remove_pagination():
    """
    Attempts to remove pagination elements from the text based on file type.
    Uses BeautifulSoup for HTML/XHTML and simple line checks for TXT files.
    Logs removed elements to a debug file.
    """
    global text, filepath
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
        messagebox.showerror("Error", f"Error removing pagination: {e}")

    # Save the log of removed pagination to a file
    with open("pagination_debug.txt", "w", encoding="utf-8") as log_file:
        log_file.write("\n".join(pagination_log))


# --- Main Processing Workflow ---
def run_processing(filepath):
    """
    Manages the main text processing workflow after a file is selected.
    Loads data, performs interactive choices, applies automatic replacements,
    removes pagination, converts roman numerals, converts to lowercase,
    updates the GUI, and displays the save button.

    Args:
        filepath (str): The path to the input file.
    """
    global text, choices, replacements, periods

    # Read the content of the selected file
    with open(filepath, "r", encoding="utf-8") as file:
        text = file.read()

    # Load replacement data from the data file
    choices, replacements, periods = load_data_file()

    # --- Processing Steps ---
    process_choices() # Handle interactive replacements based on choices
    # insert_periods_into_abbreviations() # This line is currently commented out in your script
    apply_automatic_replacements() # Apply automatic find/replace rules
    remove_pagination() # Remove detected pagination elements
    convert_roman_numerals() # Convert Roman numerals to Arabic
    convert_to_lowercase() # Convert all text to lowercase
    # --- End Processing Steps ---

    # Update the GUI display and status
    update_text_area() # Show the final processed text in the text area
    update_status_label() # Update status to "Processing complete"
    display_save_button() # Make the save button available

# --- Program Exit Function ---
def quit_program():
    """Exits the program cleanly."""
    global root
    # Check if the root window exists and destroy it if it does
    if 'root' in globals() and root:
        root.destroy()
    # Force exit the script
    os._exit(0)

# --- Main Application Entry Point ---
def main():
    """
    The main function that sets up the GUI, handles file selection,
    and initiates the processing workflow.
    """
    # Declare global variables that will be used across multiple functions
    global text_area, choice_frame, status_label, save_button, filepath, root, choice_var

    # Create the main Tkinter window. This MUST happen before any calls that use 'root'.
    root = tk.Tk()
    root.title("Read Pronunciation Tool") # Set the window title

    # Call the function to open the file selection dialog.
    # This function now has access to 'root' created just above.
    filepath = select_file()

    # Check if a file was successfully selected (user didn't cancel)
    if filepath:
        # If a file was selected, set up the rest of the main GUI elements

        # Text area to display and show highlighted text
        text_area = tk.Text(root, wrap=tk.WORD, width=80, height=20)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Label to display current status messages
        status_label = tk.Label(root, text="")
        status_label.pack(pady=5)

        # Frame to hold replacement choice buttons
        choice_frame = tk.Frame(root)
        choice_frame.pack(pady=10)

        # Frame to hold main action buttons (Save, Quit)
        button_frame = tk.Frame(root)
        button_frame.pack(pady=5, fill=tk.X, expand=True)

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
        open('debug.txt', 'w').close()

        # Start the main text processing workflow
        run_processing(filepath)

        # Start the Tkinter event loop. This makes the GUI interactive.
        root.mainloop()
    else:
        # If no file was selected in the dialog
        print("No file selected. Exiting.")
        # Destroy the root window that was created (it's an empty window if mainloop wasn't called)
        root.destroy()
        # Exit the script immediately
        os._exit(0)

# --- Script Entry Point ---
# This ensures the main() function is called when the script is executed directly
if __name__ == "__main__":
    main()
