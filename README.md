# TTS Ebook Preprocessing Tool (bookfix.py)

This is a small Python program designed to help preprocess ebook text files to fix common issues before using them for text-to-speech (TTS) or other applications. It provides a graphical interface to guide the user through interactive decisions and apply automatic cleanup rules.
    * **`#NOTE:`**: This program works on .txt files right now.  To work with ebooks code would need to be added to unzip and deconstruct the ebook and process each file.  The main problem I've encountered in this is dealing with the markup of the html files ebooks are mode of.  
    It's doable, I've done it in a different version, but it breaks easily as I use AI to program and AI alwalys wants to change or tinker or streamline code it's already written regardless of if it bears on what you are currently changing.

    
## Synopsis

The `bookfix.py` script is a GUI tool built with the Tkinter library. Its main goal is to help users clean and standardize text from input files (like **.txt**, **.html**, and **.xhtml**), by providing a way to handle inconsistent wording and apply automatic cleanup rules.

The program guides the user through making decisions for specific words and then performs a series of automatic text transformations based on rules read from a separate data file.

## How it Works:

### Program Flow and GUI

1.  The script starts by importing necessary libraries (**tkinter**, **re**, **os**, **BeautifulSoup**, etc.) for GUI creation, text processing, and file handling.
2.  The **`main()`** function is the program's starting point. It begins by creating the main Tkinter window.
3.  Before displaying the main processing interface, the **`select_file()`** function is called to open a file dialog. This allows the user to choose the input file. The dialog includes options to show hidden files.
4.  If a file is chosen, **`main()`** sets up the core GUI elements: a large text area (**`text_area`**) for displaying and interacting with the text, a status label (**`status_label`**) for user feedback, a frame (**`choice_frame`**) to hold replacement buttons, and a button frame for general actions like "Save" and "Quit".

### Data Loading and Rules

1.  Inside the **`run_processing()`** function (which is called by **`main()`** after file selection), the content of the input file is read.
2.  The **`load_data_file()`** function is then executed. It reads rules from a local data file named **`.data.txt`**, which must be in the same directory as the script.
3.  This **`.data.txt`** file is structured into sections using lines starting with `#`:
    * **`#CHOICE`**: Lists words or phrases for which the program should pause and present the user with predefined replacement options.
    * **`#REPLACE`**: Defines simple find-and-replace rules that are applied automatically.
    * **`#PERIODS`**: Specifies abbreviations (like "Mr") that should have periods automatically inserted (e.g., "M.r.").
4.  The function parses these sections and returns the rules as Python dictionaries and sets.

### Interactive Choice Processing

1.  After loading rules, **`run_processing()`** calls **`process_choices()`**. This function handles the interactive cleanup.
2.  It iterates through each item listed in the **`#CHOICE`** section of the **`.data.txt`** file.
3.  For the current word needing a choice, **`update_matches()`** finds all occurrences in the text using regular expressions.
4.  **`highlight_current_match()`** then highlights the first occurrence in the GUI's text area and scrolls it into view.
5.  **`update_choice_buttons()`** creates specific buttons in the **`choice_frame`**, each representing a possible replacement option from the **`.data.txt`** file.
6.  The program pauses, waiting for the user to click a choice button.
7.  The **`handle_choice()`** function is triggered by a button click. It replaces the currently highlighted word with the chosen option, updates the text area, moves to the next match, and logs the decision to **`debug.txt`**.
8.  Once all instances of a particular word from the **`#CHOICE`** list are processed, the function moves to the next word in the list. A progress bar shows the overall progress through this interactive phase.

### Automatic Processing

1.  After all interactive choices are completed, **`run_processing()`** executes several functions for automatic text cleanup:
    * **`apply_automatic_replacements()`**: Performs all simple find-and-replace operations defined in the **`#REPLACE`** section.
    * **`remove_pagination()`**: Attempts to identify and remove common page number patterns. It uses **BeautifulSoup** for HTML/XHTML files and simpler checks for TXT files. Removed items are logged to **`pagination_debug.txt`**.
    * **`convert_roman_numerals()`**: Finds uppercase Roman numerals in the text and converts them to their Arabic integer equivalents, skipping certain cases like a single "I" or numerals next to punctuation.
    * **`convert_to_lowercase()`**: Converts the entire text content to lowercase.
    * (Note: The **`insert_periods_into_abbreviations()`** function exists but is currently commented out in the script).

### Output and Exit

1.  After all processing is complete, **`update_text_area()`** refreshes the display to show the final text, and **`update_status_label()`** is updated.
2.  The **`display_save_button()`** makes the "Save" button visible.
3.  Clicking the "Save" button calls the **`save_file()`** function, which writes the final processed text to a new file (e.g., `original_filename_output.txt`) in the same directory as the input file.
4.  The "Quit" button calls the **`quit_program()`** function to close the GUI and exit the script.

In essence, the tool provides a structured workflow to take raw text, apply both manual and automated corrections based on external rules, and produce a cleaned output file.
